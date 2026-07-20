from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.schemas.product import (
    ProductCreate,
    ProductListOut,
    ProductOut,
    ProductUpdate,
)
from app.services.catalog_errors import product_create_error_message

router = APIRouter(prefix="/products", tags=["Products"])

PRODUCT_SELECT = """
    SELECT
        p.id, p.name, p.sku, p.description, p.unit_price,
        p.category_id, c.name AS category_name,
        p.is_active, p.created_at, p.updated_at
    FROM products p
    LEFT JOIN product_categories c ON p.category_id = c.id
"""


def _row_to_product(row) -> dict:
    return dict(row._mapping)


@router.get("/search", response_model=list[ProductOut])
async def search_products(
    q: str = Query("", min_length=0),
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search active products by name, SKU, or description (invoice picker)."""
    params: dict = {"uid": user_id}
    where = "p.user_id = :uid AND p.is_active = true"
    if q.strip():
        where += """
            AND (
                p.name ILIKE :query
                OR COALESCE(p.sku, '') ILIKE :query
                OR COALESCE(p.description, '') ILIKE :query
            )
        """
        params["query"] = f"%{q.strip()}%"

    result = await db.execute(
        text(f"""
            {PRODUCT_SELECT}
            WHERE {where}
            ORDER BY p.name ASC
            LIMIT 20
        """),
        params,
    )
    return [_row_to_product(row) for row in result.fetchall()]


@router.post("", response_model=ProductOut)
async def create_product(
    payload: ProductCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.category_id:
        cat = await db.execute(
            text("""
                SELECT id FROM product_categories
                WHERE id = :category_id AND user_id = :uid
            """),
            {"category_id": payload.category_id, "uid": user_id},
        )
        if not cat.first():
            raise HTTPException(404, "Category not found")

    try:
        result = await db.execute(
            text("""
                INSERT INTO products (
                    user_id, category_id, name, sku, description, unit_price
                )
                VALUES (:uid, :category_id, :name, :sku, :description, :unit_price)
                RETURNING id
            """),
            {
                "uid": user_id,
                "category_id": payload.category_id,
                "name": payload.name.strip(),
                "sku": payload.sku.strip() if payload.sku else None,
                "description": payload.description,
                "unit_price": payload.unit_price,
            },
        )
        product_id = dict(result.first()._mapping)["id"]
        await db.commit()
    except Exception as exc:
        await db.rollback()
        status_code, detail = product_create_error_message(exc)
        raise HTTPException(status_code=status_code, detail=detail)

    full = await db.execute(
        text(f"{PRODUCT_SELECT} WHERE p.id = :id AND p.user_id = :uid"),
        {"id": product_id, "uid": user_id},
    )
    row = full.first()
    if not row:
        raise HTTPException(500, "Failed to load created product")
    return _row_to_product(row)


@router.get("", response_model=ProductListOut)
async def list_products(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    category_id: UUID | None = None,
    include_inactive: bool = False,
):
    conditions = ["p.user_id = :uid"]
    params: dict = {"uid": user_id, "limit": limit, "offset": offset}

    if not include_inactive:
        conditions.append("p.is_active = true")
    if category_id:
        conditions.append("p.category_id = :category_id")
        params["category_id"] = category_id
    if q and q.strip():
        conditions.append("""
            (
                p.name ILIKE :query
                OR COALESCE(p.sku, '') ILIKE :query
                OR COALESCE(p.description, '') ILIKE :query
            )
        """)
        params["query"] = f"%{q.strip()}%"

    where_clause = " AND ".join(conditions)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) AS total FROM products p WHERE {where_clause}"),
        params,
    )
    total = int(count_result.scalar() or 0)

    result = await db.execute(
        text(f"""
            {PRODUCT_SELECT}
            WHERE {where_clause}
            ORDER BY p.name ASC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    items = [_row_to_product(row) for row in result.fetchall()]
    return {"items": items, "total": total}


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(f"{PRODUCT_SELECT} WHERE p.id = :id AND p.user_id = :uid"),
        {"id": product_id, "uid": user_id},
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Product not found")
    return _row_to_product(row)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.category_id is not None:
        cat = await db.execute(
            text("""
                SELECT id FROM product_categories
                WHERE id = :category_id AND user_id = :uid
            """),
            {"category_id": payload.category_id, "uid": user_id},
        )
        if not cat.first():
            raise HTTPException(404, "Category not found")

    try:
        result = await db.execute(
            text("""
                UPDATE products
                SET name = COALESCE(:name, name),
                    sku = COALESCE(:sku, sku),
                    description = COALESCE(:description, description),
                    unit_price = COALESCE(:unit_price, unit_price),
                    category_id = COALESCE(:category_id, category_id),
                    updated_at = NOW()
                WHERE id = :product_id AND user_id = :uid
                RETURNING id
            """),
            {
                "name": payload.name.strip() if payload.name else None,
                "sku": payload.sku.strip() if payload.sku else payload.sku,
                "description": payload.description,
                "unit_price": payload.unit_price,
                "category_id": payload.category_id,
                "product_id": product_id,
                "uid": user_id,
            },
        )
        row = result.first()
        if not row:
            raise HTTPException(404, "Product not found")
        await db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        status_code, detail = product_create_error_message(exc)
        raise HTTPException(status_code=status_code, detail=detail)

    full = await db.execute(
        text(f"{PRODUCT_SELECT} WHERE p.id = :id AND p.user_id = :uid"),
        {"id": product_id, "uid": user_id},
    )
    return _row_to_product(full.first())


@router.delete("/{product_id}", status_code=204)
async def archive_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE products
            SET is_active = false, updated_at = NOW()
            WHERE id = :product_id AND user_id = :uid
            RETURNING id
        """),
        {"product_id": product_id, "uid": user_id},
    )
    if not result.first():
        raise HTTPException(404, "Product not found")
    await db.commit()


@router.post("/{product_id}/reactivate", response_model=ProductOut)
async def reactivate_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE products
            SET is_active = true, updated_at = NOW()
            WHERE id = :product_id AND user_id = :uid
            RETURNING id
        """),
        {"product_id": product_id, "uid": user_id},
    )
    if not result.first():
        raise HTTPException(404, "Product not found")
    await db.commit()

    full = await db.execute(
        text(f"{PRODUCT_SELECT} WHERE p.id = :id AND p.user_id = :uid"),
        {"id": product_id, "uid": user_id},
    )
    return _row_to_product(full.first())
