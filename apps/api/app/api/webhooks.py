import logging
import secrets
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class PaymentWebhookPayload(BaseModel):
    invoice_id: str
    amount: float | None = None
    payment_method: str | None = None

    @field_validator("invoice_id")
    @classmethod
    def validate_invoice_id(cls, v: str) -> str:
        try:
            UUID(v)
        except ValueError:
            raise ValueError("invoice_id must be a valid UUID")
        return v


def verify_webhook_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook endpoint is not configured")
    if not x_webhook_secret or not secrets.compare_digest(
        x_webhook_secret, settings.WEBHOOK_SECRET
    ):
        raise HTTPException(401, "Invalid webhook secret")


@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhookPayload,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_webhook_secret),
):
    """
    Webhook endpoint for external payment processors to mark invoices as paid.
    """
    check = await db.execute(
        text("""
            SELECT id, status, amount, user_id
            FROM invoices WHERE id = :id
            FOR UPDATE
        """),
        {"id": payload.invoice_id},
    )
    row = check.first()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = dict(row._mapping)

    if invoice["status"] in ("paid", "cancelled", "void"):
        return {
            "status": "skipped",
            "message": f"Invoice already has status '{invoice['status']}'",
        }

    total_paid_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) AS total_paid
            FROM payments WHERE invoice_id = :invoice_id
        """),
        {"invoice_id": payload.invoice_id},
    )
    total_paid = Decimal(str(dict(total_paid_result.first()._mapping)["total_paid"]))
    invoice_amount = Decimal(str(invoice["amount"]))
    outstanding = invoice_amount - total_paid

    if outstanding > 0:
        await db.execute(
            text("""
                INSERT INTO payments (
                    invoice_id, amount, payment_method, payment_date, created_by
                )
                VALUES (:invoice_id, :amount, :payment_method, CURRENT_DATE, NULL)
            """),
            {
                "invoice_id": payload.invoice_id,
                "amount": outstanding,
                "payment_method": payload.payment_method or "webhook",
            },
        )

    await db.execute(
        text("UPDATE invoices SET status = 'paid' WHERE id = :id"),
        {"id": payload.invoice_id},
    )

    await db.execute(
        text("""
            INSERT INTO invoice_status_history (
                invoice_id, from_status, to_status, changed_by, reason
            )
            VALUES (:invoice_id, :from_status, 'paid', NULL, 'Payment webhook')
        """),
        {
            "invoice_id": payload.invoice_id,
            "from_status": invoice["status"],
        },
    )

    await db.commit()

    logger.info(f"Webhook processed: invoice {payload.invoice_id} marked as paid")

    return {"status": "payment processed", "invoice_id": payload.invoice_id}
