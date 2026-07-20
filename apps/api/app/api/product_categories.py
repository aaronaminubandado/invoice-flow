from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryListOut,
    ProductCategoryOut,
    ProductCategoryUpdate,
)

router = APIRouter(prefix="/product-categories", tags=["Product Categories"])


@router.get("", response_model=ProductCategoryListOut)
async def list_product_categories(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        text("SELECT COUNT(*) AS total FROM product_categories WHERE user_id = :uid"),
        {"uid": user_id},
    )
    total = int(count_result.scalar() or 0)

    result = await db.execute(
        text("""
            SELECT id, name, description, created_at
            FROM product_categories
            WHERE user_id = :uid
            ORDER BY name ASC
        """),
        {"uid": user_id},
    )
    items = [dict(row._mapping) for row in result.fetchall()]
    return {"items": items, "total": total}


@router.post("", response_model=ProductCategoryOut)
async def create_product_category(
    payload: ProductCategoryCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            text("""
                INSERT INTO product_categories (user_id, name, description)
                VALUES (:uid, :name, :description)
                RETURNING id, name, description, created_at
            """),
            {
                "uid": user_id,
                "name": payload.name.strip(),
                "description": payload.description,
            },
        )
        row = result.first()
        if not row:
            raise HTTPException(500, "Failed to create category")
        await db.commit()
    except Exception as exc:
        await db.rollback()
        from app.services.api_errors import invoice_create_error_message

        status_code, detail = invoice_create_error_message(exc)
        raise HTTPException(status_code=status_code, detail=detail)
    return dict(row._mapping)


@router.patch("/{category_id}", response_model=ProductCategoryOut)
async def update_product_category(
    category_id: UUID,
    payload: ProductCategoryUpdate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE product_categories
            SET name = COALESCE(:name, name),
                description = COALESCE(:description, description)
            WHERE id = :category_id AND user_id = :uid
            RETURNING id, name, description, created_at
        """),
        {
            "name": payload.name.strip() if payload.name else None,
            "description": payload.description,
            "category_id": category_id,
            "uid": user_id,
        },
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Category not found")
    await db.commit()
    return dict(row._mapping)


@router.delete("/{category_id}", status_code=204)
async def delete_product_category(
    category_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id FROM product_categories
            WHERE id = :category_id AND user_id = :uid
        """),
        {"category_id": category_id, "uid": user_id},
    )
    if not result.first():
        raise HTTPException(404, "Category not found")

    await db.execute(
        text("""
            UPDATE products SET category_id = NULL
            WHERE category_id = :category_id AND user_id = :uid
        """),
        {"category_id": category_id, "uid": user_id},
    )
    await db.execute(
        text("""
            DELETE FROM product_categories
            WHERE id = :category_id AND user_id = :uid
        """),
        {"category_id": category_id, "uid": user_id},
    )
    await db.commit()
