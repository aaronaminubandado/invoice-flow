from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.deps import get_current_user
from app.schemas.settings import (
    BusinessSettingsCreate,
    BusinessSettingsUpdate,
    BusinessSettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=BusinessSettingsResponse)
async def get_settings(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the authenticated user's business settings.
    """
    result = await db.execute(
        text(
            """
            SELECT id, user_id, business_name, business_email, phone, address, 
                   currency, logo_url, created_at, updated_at
            FROM business_settings
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )

    row = result.first()
    if not row:
        raise HTTPException(404, "Business settings not found")

    return dict(row._mapping)


@router.post("", response_model=BusinessSettingsResponse)
async def create_settings(
    payload: BusinessSettingsCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create business settings for the authenticated user.
    Only creates if no settings exist.
    """
    existing = await db.execute(
        text("SELECT id FROM business_settings WHERE user_id = :uid"),
        {"uid": user_id},
    )
    if existing.first():
        raise HTTPException(400, "Business settings already exist")

    result = await db.execute(
        text(
            """
            INSERT INTO business_settings (user_id, business_name, business_email, phone, address, currency, logo_url)
            VALUES (:uid, :business_name, :business_email, :phone, :address, :currency, :logo_url)
            RETURNING id, user_id, business_name, business_email, phone, address, currency, logo_url, created_at, updated_at
            """
        ),
        {
            "uid": user_id,
            "business_name": payload.business_name,
            "business_email": payload.business_email,
            "phone": payload.phone,
            "address": payload.address,
            "currency": payload.currency,
            "logo_url": payload.logo_url,
        },
    )

    row = result.first()
    if not row:
        raise HTTPException(500, "Failed to create settings")

    await db.commit()
    return dict(row._mapping)


@router.put("", response_model=BusinessSettingsResponse)
async def update_settings(
    payload: BusinessSettingsUpdate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update business settings for the authenticated user.
    """
    existing = await db.execute(
        text("SELECT id FROM business_settings WHERE user_id = :uid"),
        {"uid": user_id},
    )
    if not existing.first():
        raise HTTPException(404, "Business settings not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "No fields to update")

    set_clauses = []
    params = {"uid": user_id}

    for i, (key, value) in enumerate(update_data.items()):
        set_clauses.append(f"{key} = :val_{i}")
        params[f"val_{i}"] = value

    set_clauses.append("updated_at = NOW()")

    query = f"""
        UPDATE business_settings
        SET {", ".join(set_clauses)}
        WHERE user_id = :uid
        RETURNING id, user_id, business_name, business_email, phone, address, currency, logo_url, created_at, updated_at
    """

    result = await db.execute(text(query), params)

    row = result.first()
    if not row:
        raise HTTPException(500, "Failed to update settings")

    await db.commit()
    return dict(row._mapping)
