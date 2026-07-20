from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_user_exists(db: AsyncSession, user_id: UUID) -> bool:
    """Ensure a local users row exists for the authenticated Supabase user."""
    existing = await db.execute(
        text("SELECT 1 FROM users WHERE id = :id"),
        {"id": user_id},
    )
    if existing.first() is not None:
        return False

    await db.execute(
        text("INSERT INTO users (id) VALUES (:id) ON CONFLICT DO NOTHING"),
        {"id": user_id},
    )
    await db.flush()
    return True
