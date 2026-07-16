from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.invoice import InvoiceItemCreate, InvoiceItemOut


def compute_line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_invoice_total(items: list[InvoiceItemCreate]) -> Decimal:
    total = sum(compute_line_total(i.quantity, i.unit_price) for i in items)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def insert_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
    items: list[InvoiceItemCreate],
) -> None:
    for position, item in enumerate(items):
        line_total = compute_line_total(item.quantity, item.unit_price)
        await db.execute(
            text("""
                INSERT INTO invoice_items (
                    invoice_id, position, description, quantity, unit_price, line_total
                )
                VALUES (:invoice_id, :position, :description, :quantity, :unit_price, :line_total)
            """),
            {
                "invoice_id": invoice_id,
                "position": position,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": line_total,
            },
        )


async def replace_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
    items: list[InvoiceItemCreate],
) -> None:
    await db.execute(
        text("DELETE FROM invoice_items WHERE invoice_id = :invoice_id"),
        {"invoice_id": invoice_id},
    )
    await insert_invoice_items(db, invoice_id, items)


async def fetch_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
) -> list[InvoiceItemOut]:
    result = await db.execute(
        text("""
            SELECT id, position, description, quantity, unit_price, line_total
            FROM invoice_items
            WHERE invoice_id = :invoice_id
            ORDER BY position ASC
        """),
        {"invoice_id": invoice_id},
    )
    rows = []
    for row in result.fetchall():
        data = dict(row._mapping)
        rows.append(InvoiceItemOut(**data))
    return rows
