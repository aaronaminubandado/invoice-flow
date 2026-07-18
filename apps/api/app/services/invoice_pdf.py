from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.business_settings import get_business_settings
from app.services.invoice_items import fetch_invoice_items
from app.services.pdf import PDFService


async def build_invoice_pdf_bytes(
    db: AsyncSession,
    *,
    invoice_id: UUID | None = None,
    user_id: UUID | None = None,
    share_token: str | None = None,
) -> tuple[bytes, str]:
    """Fetch invoice data and generate PDF bytes for download, email, and public paths."""
    if share_token:
        scope_clause = "i.share_token = :share_token"
        params: dict = {"share_token": share_token}
    elif invoice_id is not None and user_id is not None:
        scope_clause = "i.id = :invoice_id AND i.user_id = :user_id"
        params = {"invoice_id": invoice_id, "user_id": user_id}
    elif invoice_id is not None:
        scope_clause = "i.id = :invoice_id"
        params = {"invoice_id": invoice_id}
    else:
        raise ValueError("Invoice scope required")

    result = await db.execute(
        text(
            f"""
            SELECT
                i.id, i.user_id, i.amount, i.description, i.due_date, i.status,
                i.created_at, i.invoice_number,
                c.name AS client_name, c.email AS client_email,
                c.address AS client_address,
                COALESCE(p.paid, 0)::NUMERIC(12,2) AS paid_amount
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS paid
                FROM payments
                GROUP BY invoice_id
            ) p ON p.invoice_id = i.id
            WHERE {scope_clause}
            """
        ),
        params,
    )

    row = result.first()
    if not row:
        raise ValueError("Invoice not found")

    data = dict(row._mapping)
    items = await fetch_invoice_items(db, data["id"])
    business_info = await get_business_settings(db, data["user_id"])

    invoice_amount = Decimal(str(data["amount"]))
    paid_amount = Decimal(str(data.get("paid_amount") or 0))
    balance_due = max(invoice_amount - paid_amount, Decimal("0"))

    pdf_bytes = PDFService.generate_invoice_pdf(
        invoice_id=str(data["id"]),
        invoice_number=data.get("invoice_number"),
        amount=invoice_amount,
        description=data.get("description") or "",
        due_date=data["due_date"],
        status=data["status"],
        client_name=data["client_name"],
        client_email=data["client_email"],
        client_address=data.get("client_address"),
        created_at=data.get("created_at"),
        business_info=business_info,
        items=items,
        paid_amount=paid_amount,
        balance_due=balance_due,
    )

    filename = f"invoice_{data.get('invoice_number') or str(data['id'])[:8]}.pdf"
    return pdf_bytes, filename
