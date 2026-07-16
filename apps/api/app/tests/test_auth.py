import pytest


@pytest.mark.asyncio
async def test_invalid_token(client):
    response = await client.get(
        "/dashboard/stats",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
