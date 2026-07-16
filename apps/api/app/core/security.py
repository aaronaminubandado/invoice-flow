from jose import jwt, JWTError
from fastapi import HTTPException, status
import httpx

from app.core.config import settings

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
ALGORITHMS = ["ES256"]


async def verify_supabase_token(token: str) -> str:
    """
    Verify Supabase JWT using JWKS public keys.
    Returns the authenticated user_id (sub).
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                JWKS_URL,
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY
                }
            )
            response.raise_for_status()
            jwks = response.json()

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        key = next(
            (k for k in jwks["keys"] if k["kid"] == kid),
            None,
        )

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key",
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            options={
                "verify_aud": False,
                "verify_iss": False,
            },
        )


        return payload["sub"]

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )
