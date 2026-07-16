import time
from uuid import UUID

from jose import jwt, JWTError
from fastapi import HTTPException, status
import httpx

from app.core.config import settings

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
ALGORITHMS = ["ES256"]

_jwks_cache: dict | None = None
_jwks_cached_at: float = 0.0
JWKS_TTL_SECONDS = 600


async def _fetch_jwks() -> dict:
    global _jwks_cache, _jwks_cached_at
    now = time.time()
    if _jwks_cache is not None and (now - _jwks_cached_at) < JWKS_TTL_SECONDS:
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                JWKS_URL,
                headers={"apikey": settings.SUPABASE_ANON_KEY},
                timeout=10.0,
            )
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cached_at = now
            return _jwks_cache
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication provider unavailable",
        )


async def verify_supabase_token(token: str) -> UUID:
    """Verify Supabase JWT using cached JWKS public keys."""

    try:
        jwks = await _fetch_jwks()

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if key is None:
            global _jwks_cache, _jwks_cached_at
            _jwks_cache = None
            _jwks_cached_at = 0.0
            jwks = await _fetch_jwks()
            key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
            if key is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token key",
                )

        payload = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            options={"verify_aud": False, "verify_iss": False},
        )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        return UUID(sub)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token subject",
        )
