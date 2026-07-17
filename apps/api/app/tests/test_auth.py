import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
from fastapi import HTTPException
from jose import jwt

from app.core import security


@pytest.mark.asyncio
async def test_invalid_token(client):
    response = await client.get(
        "/dashboard/stats",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwks_fetch_is_cached():
    security._jwks_cache = None
    security._jwks_cached_at = 0.0

    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {"keys": [{"kid": "test-kid", "kty": "EC"}]}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.security.httpx.AsyncClient", return_value=mock_client):
        await security._fetch_jwks()
        await security._fetch_jwks()

    assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_jwks_unavailable_returns_503():
    security._jwks_cache = None
    security._jwks_cached_at = 0.0

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("network down"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.security.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc:
            await security._fetch_jwks()

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_missing_sub_claim_returns_401():
    security._jwks_cache = {
        "keys": [
            {
                "kid": "test-kid",
                "kty": "EC",
                "crv": "P-256",
                "x": "test",
                "y": "test",
            }
        ]
    }
    security._jwks_cached_at = security.time.time()

    token = jwt.encode(
        {"email": "user@example.com"},
        "secret",
        algorithm="HS256",
        headers={"kid": "test-kid"},
    )

    with patch("app.core.security.jwt.decode", return_value={"email": "user@example.com"}):
        with patch("app.core.security.jwt.get_unverified_header", return_value={"kid": "test-kid"}):
            with pytest.raises(HTTPException) as exc:
                await security.verify_supabase_token(token)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_sub_parsed_as_uuid():
    user_id = uuid4()
    security._jwks_cache = {"keys": [{"kid": "test-kid"}]}
    security._jwks_cached_at = security.time.time()

    token = "fake.token.here"

    with patch("app.core.security.jwt.get_unverified_header", return_value={"kid": "test-kid"}):
        with patch("app.core.security.jwt.decode", return_value={"sub": str(user_id)}):
            result = await security.verify_supabase_token(token)

    assert result == user_id
