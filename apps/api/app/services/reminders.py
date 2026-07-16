import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.email import EmailService

logger = logging.getLogger(__name__)


async def process_overdue_invoices(db: AsyncSession):
    """
    Finds overdue invoices and sends reminder emails to clients.
    Intended to be called by a scheduler.
    """
    result = await db.execute(
        text("""
            SELECT i.id, i.amount, i.due_date,
                   c.email as client_email, c.name as client_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.due_date < CURRENT_DATE AND i.status = 'sent'
        """)
    )

    overdue_invoices = result.fetchall()

    for row in overdue_invoices:
        invoice = dict(row._mapping)
        try:
            await EmailService.send_reminder_email(
                invoice_id=str(invoice["id"]),
                client_email=invoice["client_email"],
                client_name=invoice["client_name"],
                amount=str(invoice["amount"]),
                due_date=str(invoice["due_date"]),
                subject=f"Reminder: Invoice overdue",
                body=(
                    f"This is a friendly reminder that your invoice "
                    f"for ${invoice['amount']} was due on {invoice['due_date']}. "
                    f"Please make payment as soon as possible."
                ),
            )
        except Exception as e:
            logger.error(
                f"Failed to send overdue reminder for invoice {invoice['id']}: {e}"
            )
