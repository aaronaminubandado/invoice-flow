from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.invoice import PublicInvoiceOut, PublicBusinessInfo
from app.services.business_settings import get_business_settings
from app.services.invoice_items import fetch_invoice_items
from app.services.pdf import PDFService

router = APIRouter(prefix="/public", tags=["Public"])


async def _load_public_invoice(db: AsyncSession, share_token: str) -> dict:
    result = await db.execute(
        text("""
            SELECT
                i.id, i.user_id, i.invoice_number, i.status, i.description,
                i.due_date, i.created_at, i.amount, i.share_token,
                c.name AS client_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.share_token = :token
        """),
        {"token": share_token},
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Invoice not found")
    return dict(row._mapping)


@router.get("/invoices/{share_token}", response_model=PublicInvoiceOut)
async def get_public_invoice(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    data = await _load_public_invoice(db, share_token)

    paid_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) AS paid
            FROM payments WHERE invoice_id = :invoice_id
        """),
        {"invoice_id": data["id"]},
    )
    paid_row = paid_result.first()
    paid_amount = Decimal(str(dict(paid_row._mapping)["paid"]))
    total = Decimal(str(data["amount"]))
    balance = max(total - paid_amount, Decimal("0"))

    business = await get_business_settings(db, data["user_id"])
    business_out = None
    if business:
        business_out = PublicBusinessInfo(
            business_name=business.business_name,
            business_email=business.business_email,
            phone=business.phone,
            address=business.address,
            currency=business.currency,
        )

    items = await fetch_invoice_items(db, data["id"])

    return PublicInvoiceOut(
        invoice_number=data.get("invoice_number"),
        status=data["status"],
        description=data.get("description"),
        due_date=data["due_date"],
        created_at=data.get("created_at"),
        amount=total,
        paid_amount=paid_amount,
        balance_due=balance,
        client_name=data["client_name"],
        business=business_out,
        items=items,
    )


@router.get("/invoices/{share_token}/pdf")
async def get_public_invoice_pdf(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    data = await _load_public_invoice(db, share_token)
    business_info = await get_business_settings(db, data["user_id"])
    items = await fetch_invoice_items(db, data["id"])

    client_row = await db.execute(
        text("SELECT name, email, address FROM clients c JOIN invoices i ON i.client_id = c.id WHERE i.id = :id"),
        {"id": data["id"]},
    )
    client = dict(client_row.first()._mapping)

    pdf_bytes = PDFService.generate_invoice_pdf(
        invoice_id=str(data["id"]),
        invoice_number=data.get("invoice_number"),
        amount=Decimal(str(data["amount"])),
        description=data.get("description") or "",
        due_date=data["due_date"],
        status=data["status"],
        client_name=client["name"],
        client_email=client["email"],
        client_address=client.get("address"),
        created_at=data.get("created_at"),
        business_info=business_info,
        items=items,
    )

    filename = f"invoice_{data.get('invoice_number') or share_token[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/invoices/{share_token}/receipts/{payment_id}/pdf")
async def get_public_receipt_pdf(
    share_token: str,
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await _load_public_invoice(db, share_token)

    result = await db.execute(
        text("""
            SELECT p.id, p.amount, p.payment_method, p.payment_date,
                   i.invoice_number, c.name AS client_name, c.email AS client_email
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            WHERE p.id = :payment_id AND i.id = :invoice_id AND i.share_token = :token
        """),
        {
            "payment_id": payment_id,
            "invoice_id": data["id"],
            "token": share_token,
        },
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Payment not found")

    pay = dict(row._mapping)
    business_info = await get_business_settings(db, data["user_id"])
    receipt_number = f"RCP-{payment_id.hex[:8].upper()}"

    pdf_bytes = PDFService.generate_receipt_pdf(
        receipt_id=str(pay["id"]),
        receipt_number=receipt_number,
        invoice_id=str(data["id"]),
        invoice_number=pay.get("invoice_number"),
        amount=Decimal(str(pay["amount"])),
        payment_method=pay.get("payment_method", "bank_transfer"),
        payment_date=pay["payment_date"],
        client_name=pay["client_name"],
        client_email=pay["client_email"],
        business_info=business_info,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={receipt_number}.pdf"},
    )
