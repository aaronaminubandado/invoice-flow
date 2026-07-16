from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import verify_supabase_token

security = HTTPBearer(auto_error=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Dependency that extracts and verifies Supabase JWT

    :param credentials: The HTTPBearer credentials
    :type credentials: str
    :return: The verified user ID
    :rtype: str
    """
    token = credentials.credentials
    user_id = await verify_supabase_token(token)
    return user_id