import logging
from datetime import datetime
from functools import partial
from typing import Optional, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class InvoiceScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.db_session_maker: Optional[async_sessionmaker] = None

    def init_scheduler(
        self, db_session_maker: async_sessionmaker = None
    ) -> AsyncIOScheduler:
        from app.core.database import AsyncSessionLocal

        self.db_session_maker = db_session_maker or AsyncSessionLocal

        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                partial(self.mark_overdue_invoices),
                CronTrigger(hour=0, minute=0),
                id="mark_overdue_invoices",
                name="Mark overdue invoices",
                replace_existing=True,
            )
            self.scheduler.add_job(
                partial(self.send_overdue_reminders),
                CronTrigger(hour=1, minute=0),
                id="send_overdue_reminders",
                name="Send overdue reminders",
                replace_existing=True,
            )
        return self.scheduler

    async def mark_overdue_invoices(self):
        logger.info("Running overdue invoice detection job")

        async with self.db_session_maker() as db:
            try:
                result = await db.execute(
                    text("""
                        UPDATE invoices
                        SET status = 'overdue'
                        WHERE status = 'sent'
                          AND due_date < CURRENT_DATE
                        RETURNING id, client_id, amount, due_date
                    """)
                )

                updated_rows = result.fetchall()
                await db.commit()

                if updated_rows:
                    for row in updated_rows:
                        invoice_data = dict(row._mapping)
                        logger.info(
                            f"Marked invoice {invoice_data['id']} as overdue "
                            f"(client: {invoice_data['client_id']}, "
                            f"amount: {invoice_data['amount']})"
                        )

                        await db.execute(
                            text("""
                                INSERT INTO invoice_status_history 
                                (invoice_id, from_status, to_status, changed_by, reason, changed_at)
                                VALUES (:invoice_id, 'sent', 'overdue', NULL, 'Auto-marked overdue by scheduler', :changed_at)
                            """),
                            {
                                "invoice_id": invoice_data["id"],
                                "changed_at": datetime.utcnow(),
                            },
                        )

                    await db.commit()

                logger.info(
                    f"Overdue detection completed. Updated {len(updated_rows)} invoices"
                )
                return len(updated_rows)

            except Exception as e:
                logger.error(f"Error in mark_overdue_invoices: {e}")
                await db.rollback()
                raise

    async def send_overdue_reminders(self):
        logger.info("Running overdue reminder email job")

        async with self.db_session_maker() as db:
            try:
                result = await db.execute(
                    text("""
                        SELECT 
                            i.id, 
                            i.amount, 
                            i.due_date, 
                            i.reminder_count,
                            c.email, 
                            c.name,
                            CURRENT_DATE - i.due_date as days_overdue
                        FROM invoices i
                        JOIN clients c ON i.client_id = c.id
                        WHERE i.status IN ('sent', 'overdue')
                          AND i.due_date < CURRENT_DATE
                    """)
                )

                overdue_invoices = result.fetchall()

                if overdue_invoices:
                    from app.services.email import EmailService

                    for row in overdue_invoices:
                        invoice = dict(row._mapping)
                        days_overdue = invoice.get("days_overdue", 0)
                        reminder_count = invoice.get("reminder_count", 0) or 0

                        reminder_type = self._determine_reminder_type(
                            days_overdue, reminder_count
                        )

                        if not reminder_type:
                            logger.debug(
                                f"Invoice {invoice['id']}: no reminder needed "
                                f"(days_overdue={days_overdue}, reminder_count={reminder_count})"
                            )
                            continue

                        idempotency_key = f"reminder_{invoice['id']}_{reminder_type}"

                        check_result = await db.execute(
                            text("""
                                SELECT id FROM reminder_log 
                                WHERE invoice_id = :invoice_id AND reminder_type = :reminder_type
                            """),
                            {
                                "invoice_id": invoice["id"],
                                "reminder_type": reminder_type,
                            },
                        )

                        if check_result.first():
                            logger.debug(
                                f"Skipping {reminder_type} for invoice {invoice['id']} - already sent"
                            )
                            continue

                        try:
                            if reminder_type == "first_reminder":
                                subject = (
                                    f"Reminder: Invoice overdue by {days_overdue} days"
                                )
                                body = (
                                    f"Dear {invoice['name']},\n\n"
                                    f"This is a friendly reminder that your invoice "
                                    f"for ${invoice['amount']} was due on {invoice['due_date']}.\n"
                                    f"Please make payment as soon as possible."
                                )
                            elif reminder_type == "second_reminder":
                                subject = (
                                    f"URGENT: Invoice overdue by {days_overdue} days"
                                )
                                body = (
                                    f"Dear {invoice['name']},\n\n"
                                    f"This is your second reminder about the overdue invoice "
                                    f"for ${invoice['amount']} that was due on {invoice['due_date']}.\n"
                                    f"Please contact us immediately to resolve this matter."
                                )

                            email_result = await EmailService.send_reminder_email(
                                invoice_id=str(invoice["id"]),
                                client_email=invoice["email"],
                                client_name=invoice["name"],
                                amount=str(invoice["amount"]),
                                due_date=str(invoice["due_date"]),
                                subject=subject,
                                body=body,
                            )

                            await db.execute(
                                text("""
                                    INSERT INTO reminder_log (invoice_id, reminder_type, sent_at, email_status, last_error, resend_id)
                                    VALUES (:invoice_id, :reminder_type, NOW(), :email_status, :last_error, :resend_id)
                                """),
                                {
                                    "invoice_id": invoice["id"],
                                    "reminder_type": reminder_type,
                                    "email_status": email_result.email_status.value,
                                    "last_error": email_result.error_message,
                                    "resend_id": email_result.resend_id,
                                },
                            )

                            await db.execute(
                                text("""
                                    UPDATE invoices SET reminder_count = reminder_count + 1
                                    WHERE id = :invoice_id
                                """),
                                {"invoice_id": invoice["id"]},
                            )

                            await db.commit()

                            logger.info(
                                f"Sent {reminder_type} for invoice {invoice['id']} "
                                f"(days_overdue={days_overdue})"
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to send {reminder_type} for invoice {invoice['id']}: {e}"
                            )
                            await db.rollback()

                logger.info(
                    f"Overdue reminder job completed. Processed {len(overdue_invoices)} invoices"
                )
                return len(overdue_invoices)

            except Exception as e:
                logger.error(f"Error in send_overdue_reminders: {e}")
                raise

    def _determine_reminder_type(
        self, days_overdue: int, reminder_count: int
    ) -> str | None:
        if days_overdue >= 7 and reminder_count < 2:
            return "second_reminder"
        elif days_overdue >= 3 and reminder_count < 1:
            return "first_reminder"
        return None

    def start(self):
        if self.scheduler:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def run_overdue_job_now(self):
        """Manual trigger for overdue detection (for testing)"""
        return self.mark_overdue_invoices()


invoice_scheduler = InvoiceScheduler()
