import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request, Header
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


@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for external payment processors to mark invoices as paid.
    Validates the invoice exists before updating.
    """
    check = await db.execute(
        text("SELECT id, status FROM invoices WHERE id = :id"),
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

    await db.execute(
        text("UPDATE invoices SET status = 'paid' WHERE id = :id"),
        {"id": payload.invoice_id},
    )
    await db.commit()

    logger.info(
        f"Webhook processed: invoice {payload.invoice_id} marked as paid"
    )

    return {"status": "payment processed", "invoice_id": payload.invoice_id}
