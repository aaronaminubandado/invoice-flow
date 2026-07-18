import pytest

from app.main import app


@app.get("/__test__/boom", include_in_schema=False)
async def raise_unhandled_error():
    raise RuntimeError("test error")


@pytest.mark.asyncio
async def test_cors_headers_are_present_on_unhandled_errors(unauthenticated_client):
    response = await unauthenticated_client.get(
        "/__test__/boom",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 500
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
