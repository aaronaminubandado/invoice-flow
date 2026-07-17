import pytest


@pytest.mark.asyncio
async def test_client_phone_address_round_trip(client, db_session, user_id):
    response = await client.post(
        "/clients",
        json={
            "name": "Acme Corp",
            "email": "billing@acme.test",
            "phone": "+1 555-0100",
            "address": "123 Main St\nSpringfield",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1 555-0100"
    assert data["address"] == "123 Main St\nSpringfield"

    client_id = data["id"]
    get_response = await client.get(f"/clients/{client_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["phone"] == "+1 555-0100"
    assert fetched["address"] == "123 Main St\nSpringfield"


@pytest.mark.asyncio
async def test_list_clients_pagination(client, db_session, user_id):
    for i in range(3):
        await client.post(
            "/clients",
            json={"name": f"Client {i}", "email": f"client{i}@paginate.test"},
        )

    page1 = await client.get("/clients", params={"limit": 2, "offset": 0})
    assert page1.status_code == 200
    body = page1.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2

    page2 = await client.get("/clients", params={"limit": 2, "offset": 2})
    assert page2.status_code == 200
    assert len(page2.json()["items"]) >= 1
