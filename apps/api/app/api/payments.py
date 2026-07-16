from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from decimal import Decimal

from app.deps import get_current_user
from app.core.database import get_db
from app.services.pdf import PDFService
from app.services.business_settings import get_business_settings

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/{payment_id}/receipt")
async def get_payment_receipt(
    payment_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download PDF receipt for a payment."""
    result = await db.execute(
        text("""
            SELECT
                p.id, p.amount, p.payment_method, p.payment_date,
                p.reference,
                i.id as invoice_id, i.invoice_number,
                c.name as client_name, c.email as client_email
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            WHERE p.id = :payment_id AND i.user_id = :uid
        """),
        {"payment_id": payment_id, "uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Payment not found")

    data = dict(row._mapping)
    business_info = await get_business_settings(db, user_id)
    receipt_number = f"RCP-{payment_id.hex[:8].upper()}"

    pdf_bytes = PDFService.generate_receipt_pdf(
        receipt_id=str(data["id"]),
        receipt_number=receipt_number,
        invoice_id=str(data["invoice_id"]),
        invoice_number=data.get("invoice_number"),
        amount=Decimal(str(data["amount"])),
        payment_method=data.get("payment_method", "bank_transfer"),
        payment_date=data["payment_date"],
        client_name=data["client_name"],
        client_email=data["client_email"],
        business_info=business_info,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={receipt_number}.pdf"},
    )
