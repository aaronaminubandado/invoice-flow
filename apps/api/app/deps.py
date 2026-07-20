from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_supabase_token
from app.services.users import ensure_user_exists

security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Extract and verify Supabase JWT; provision local users row if needed."""
    token = credentials.credentials
    user_id = await verify_supabase_token(token)
    await ensure_user_exists(db, user_id)
    return user_id
