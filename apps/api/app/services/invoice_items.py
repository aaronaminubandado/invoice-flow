from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.invoice import InvoiceItemCreate, InvoiceItemOut


def compute_line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_invoice_total(items: list[InvoiceItemCreate]) -> Decimal:
    total = sum(compute_line_total(i.quantity, i.unit_price) for i in items)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def resolve_invoice_item(
    db: AsyncSession,
    user_id: UUID,
    item: InvoiceItemCreate,
    *,
    require_active_product: bool = True,
) -> tuple[str, Decimal, UUID | None]:
    """Resolve description, unit_price snapshot, and optional product_id."""
    product_id = item.product_id
    description = item.description.strip() if item.description else None
    unit_price = item.unit_price

    if product_id is None:
        if not description:
            raise HTTPException(400, "Line item description is required")
        if unit_price is None:
            raise HTTPException(400, "Line item unit price is required")
        return description, unit_price, None

    result = await db.execute(
        text("""
            SELECT id, name, description, unit_price, is_active
            FROM products
            WHERE id = :product_id AND user_id = :uid
        """),
        {"product_id": product_id, "uid": user_id},
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Product not found")

    product = dict(row._mapping)
    if require_active_product and not product["is_active"]:
        raise HTTPException(400, "Cannot bill an archived product")

    resolved_description = description or product["name"]
    if product.get("description") and not description:
        resolved_description = product["name"]
    resolved_unit_price = (
        unit_price if unit_price is not None else Decimal(str(product["unit_price"]))
    )
    return resolved_description, resolved_unit_price, product_id


async def compute_resolved_invoice_total(
    db: AsyncSession,
    user_id: UUID,
    items: list[InvoiceItemCreate],
    *,
    require_active_product: bool = True,
) -> Decimal:
    total = Decimal("0")
    for item in items:
        _, unit_price, _ = await resolve_invoice_item(
            db,
            user_id,
            item,
            require_active_product=require_active_product,
        )
        total += compute_line_total(item.quantity, unit_price)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def insert_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
    user_id: UUID,
    items: list[InvoiceItemCreate],
    *,
    require_active_product: bool = True,
) -> None:
    for position, item in enumerate(items):
        description, unit_price, product_id = await resolve_invoice_item(
            db,
            user_id,
            item,
            require_active_product=require_active_product,
        )
        line_total = compute_line_total(item.quantity, unit_price)
        await db.execute(
            text("""
                INSERT INTO invoice_items (
                    invoice_id, position, description, quantity, unit_price,
                    line_total, product_id
                )
                VALUES (
                    :invoice_id, :position, :description, :quantity, :unit_price,
                    :line_total, :product_id
                )
            """),
            {
                "invoice_id": invoice_id,
                "position": position,
                "description": description,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "product_id": product_id,
            },
        )


async def replace_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
    user_id: UUID,
    items: list[InvoiceItemCreate],
    *,
    require_active_product: bool = True,
) -> None:
    await db.execute(
        text("DELETE FROM invoice_items WHERE invoice_id = :invoice_id"),
        {"invoice_id": invoice_id},
    )
    await insert_invoice_items(
        db,
        invoice_id,
        user_id,
        items,
        require_active_product=require_active_product,
    )


async def fetch_invoice_items(
    db: AsyncSession,
    invoice_id: UUID,
) -> list[InvoiceItemOut]:
    result = await db.execute(
        text("""
            SELECT id, position, description, quantity, unit_price, line_total, product_id
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
