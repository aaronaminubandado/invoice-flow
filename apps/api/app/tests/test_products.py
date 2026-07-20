import pytest
from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import text

from app.tests.helpers import insert_test_client


@pytest.mark.asyncio
async def test_create_and_list_product_categories(client: AsyncClient):
    create = await client.post(
        "/product-categories",
        json={"name": "Services", "description": "Billable services"},
    )
    assert create.status_code == 200
    category_id = create.json()["id"]

    listing = await client.get("/product-categories")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["name"] == "Services"

    duplicate = await client.post("/product-categories", json={"name": "Services"})
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_create_product_with_optional_sku(client: AsyncClient, db_session, user_id):
    category = await client.post("/product-categories", json={"name": "Goods"})
    category_id = category.json()["id"]

    created = await client.post(
        "/products",
        json={
            "name": "Widget",
            "sku": "WGT-001",
            "unit_price": 25.00,
            "category_id": category_id,
        },
    )
    assert created.status_code == 200
    data = created.json()
    assert data["name"] == "Widget"
    assert data["sku"] == "WGT-001"
    assert data["category_name"] == "Goods"

    duplicate_sku = await client.post(
        "/products",
        json={"name": "Other", "sku": "WGT-001", "unit_price": 10.00},
    )
    assert duplicate_sku.status_code == 409


@pytest.mark.asyncio
async def test_archived_product_hidden_from_search(client: AsyncClient):
    created = await client.post(
        "/products",
        json={"name": "Archived Item", "unit_price": 50.00},
    )
    product_id = created.json()["id"]

    search_before = await client.get("/products/search", params={"q": "Archived"})
    assert len(search_before.json()) == 1

    archive = await client.delete(f"/products/{product_id}")
    assert archive.status_code == 204

    search_after = await client.get("/products/search", params={"q": "Archived"})
    assert search_after.json() == []


@pytest.mark.asyncio
async def test_invoice_with_product_snapshots_price(client: AsyncClient, db_session, user_id):
    client_id = await insert_test_client(db_session, user_id, email="buyer@example.com")
    await db_session.commit()

    product = await client.post(
        "/products",
        json={"name": "Consulting Hour", "unit_price": 100.00},
    )
    product_id = product.json()["id"]

    invoice = await client.post(
        "/invoices",
        json={
            "client_id": str(client_id),
            "due_date": "2026-12-31",
            "send_now": False,
            "items": [
                {
                    "product_id": product_id,
                    "description": "Consulting Hour",
                    "quantity": 2,
                    "unit_price": 90.00,
                }
            ],
        },
    )
    assert invoice.status_code == 200
    assert invoice.json()["amount"] == "180.00"
    assert invoice.json()["items"][0]["unit_price"] == "90.00"
    assert invoice.json()["items"][0]["product_id"] == product_id

    await client.patch(
        f"/products/{product_id}",
        json={"unit_price": 150.00},
    )

    invoice_get = await client.get(f"/invoices/{invoice.json()['id']}")
    assert invoice_get.json()["items"][0]["unit_price"] == "90.00"


@pytest.mark.asyncio
async def test_invoice_custom_line_without_product(client: AsyncClient, db_session, user_id):
    client_id = await insert_test_client(db_session, user_id, email="custom@example.com")
    await db_session.commit()

    invoice = await client.post(
        "/invoices",
        json={
            "client_id": str(client_id),
            "due_date": "2026-12-31",
            "send_now": False,
            "items": [
                {
                    "description": "Custom work",
                    "quantity": 1,
                    "unit_price": 75.00,
                }
            ],
        },
    )
    assert invoice.status_code == 200
    assert invoice.json()["items"][0]["description"] == "Custom work"
    assert invoice.json()["items"][0].get("product_id") in (None,)


@pytest.mark.asyncio
async def test_archived_product_rejected_on_new_invoice(client: AsyncClient, db_session, user_id):
    client_id = await insert_test_client(db_session, user_id, email="archive@example.com")
    await db_session.commit()

    product = await client.post(
        "/products",
        json={"name": "Retired Service", "unit_price": 40.00},
    )
    product_id = product.json()["id"]
    await client.delete(f"/products/{product_id}")

    invoice = await client.post(
        "/invoices",
        json={
            "client_id": str(client_id),
            "due_date": "2026-12-31",
            "send_now": False,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": 40.00,
                }
            ],
        },
    )
    assert invoice.status_code == 400
    assert "archived" in invoice.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_category_nulls_product_category_id(client: AsyncClient):
    category = await client.post("/product-categories", json={"name": "Temp"})
    category_id = category.json()["id"]

    product = await client.post(
        "/products",
        json={"name": "Loose Product", "unit_price": 12.00, "category_id": category_id},
    )
    product_id = product.json()["id"]

    delete_category = await client.delete(f"/product-categories/{category_id}")
    assert delete_category.status_code == 204

    fetched = await client.get(f"/products/{product_id}")
    assert fetched.json()["category_id"] is None
