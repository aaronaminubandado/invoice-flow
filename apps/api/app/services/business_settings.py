from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pdf import BusinessInfo


async def get_business_settings(
    db: AsyncSession, user_id: UUID
) -> Optional[BusinessInfo]:
    """Get business settings for a user, returns None if not found."""
    result = await db.execute(
        text(
            """
            SELECT business_name, business_email, phone, address, currency, logo_url
            FROM business_settings
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )
    row = result.first()
    if not row:
        return None

    data = dict(row._mapping)
    return BusinessInfo(
        business_name=data["business_name"],
        business_email=data["business_email"],
        phone=data.get("phone"),
        address=data.get("address"),
        currency=data.get("currency", "USD"),
        logo_url=data.get("logo_url"),
    )
