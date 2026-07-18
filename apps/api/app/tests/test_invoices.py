import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import text

from app.tests.helpers import insert_test_client, insert_test_invoice


@pytest.mark.asyncio
async def test_create_payment_partial_success(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="sent"
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 500.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert Decimal(data["paid_amount"]) == Decimal("500.00")


@pytest.mark.asyncio
async def test_create_payment_prevents_overpayment(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=500.00, status="sent"
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 300.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 300.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 400
    assert "exceeds remaining" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_payment_full_payment(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="sent"
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 1000.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert Decimal(data["paid_amount"]) == Decimal("1000.00")


@pytest.mark.asyncio
async def test_mark_paid_completes_partial_payment(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="sent"
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 500.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/mark-paid")

    assert response.status_code == 200
    assert response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_mark_paid_success(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="partial"
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 1000.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/mark-paid")

    assert response.status_code == 200
    assert response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_payment_on_cancelled_invoice_fails(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=1000.00,
        status="cancelled",
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 100.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 400
    assert "Cannot add payment" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_paid_invoice_fails(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="paid"
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 400
    assert response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_already_cancelled_invoice_fails(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=1000.00,
        status="cancelled",
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 400
    assert response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_draft_invoice_succeeds(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="draft"
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_sent_invoice_succeeds(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="sent"
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_overdue_invoice_succeeds(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=1000.00,
        status="overdue",
        due_date_expr="CURRENT_DATE - INTERVAL '30 days'",
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_payment_on_draft_invoice_fails(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=1000.00, status="draft"
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 500.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]


@pytest.mark.asyncio
async def test_create_draft_invoice(client, db_session, user_id):
    client_id = await insert_test_client(
        db_session, user_id, name="Draft Client", email="draft@example.com"
    )
    await db_session.commit()

    response = await client.post(
        "/invoices",
        json={
            "client_id": str(client_id),
            "due_date": "2026-12-31",
            "amount": 250.00,
            "send_now": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_send_draft_invoice(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(
        db_session, user_id, client_id=client_id, name="Send Client", email="send@example.com"
    )
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=100.00,
        status="draft",
        share_token="tok123",
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/send")
    assert response.status_code == 200
    assert response.json()["status"] == "sent"

    again = await client.post(f"/invoices/{invoice_id}/send")
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_list_invoice_payments(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(
        db_session, user_id, client_id=client_id, name="Pay Client", email="pay@example.com"
    )
    await insert_test_invoice(
        db_session, user_id, client_id, invoice_id=invoice_id, amount=500.00, status="sent"
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 100.00, 'card', CURRENT_DATE)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.get(f"/invoices/{invoice_id}/payments")
    assert response.status_code == 200
    assert len(response.json()) == 1

    missing = await client.get(f"/invoices/{uuid4()}/payments")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_list_invoices_pagination_and_status(client, db_session, user_id):
    client_id = await insert_test_client(
        db_session, user_id, name="List Client", email="list@example.com"
    )

    for status in ("sent", "paid", "sent"):
        await insert_test_invoice(
            db_session, user_id, client_id, amount=100.00, status=status
        )
    await db_session.commit()

    all_resp = await client.get("/invoices", params={"limit": 2, "offset": 0})
    assert all_resp.status_code == 200
    body = all_resp.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2

    paid_resp = await client.get("/invoices", params={"status": "paid"})
    assert paid_resp.status_code == 200
    assert all(item["status"] == "paid" for item in paid_resp.json()["items"])


@pytest.mark.asyncio
async def test_invoice_numbers_are_unique_per_user(client, db_session, user_id):
    other_user_id = uuid4()
    await db_session.execute(
        text("INSERT INTO users (id) VALUES (:id) ON CONFLICT DO NOTHING"),
        {"id": other_user_id},
    )

    client_a = await insert_test_client(db_session, user_id, email="a@example.com")
    client_b = await insert_test_client(db_session, other_user_id, email="b@example.com")
    await db_session.commit()

    first = await client.post(
        "/invoices",
        json={
            "client_id": str(client_a),
            "due_date": "2026-12-31",
            "amount": 100.00,
            "send_now": False,
        },
    )
    assert first.status_code == 200
    assert first.json()["invoice_number"] == "INV-000001"

    from app.deps import get_current_user
    from app.core.database import get_db
    from app.main import app

    async def override_other_user():
        return other_user_id

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_other_user
    app.dependency_overrides[get_db] = override_get_db

    second = await client.post(
        "/invoices",
        json={
            "client_id": str(client_b),
            "due_date": "2026-12-31",
            "amount": 200.00,
            "send_now": False,
        },
    )
    app.dependency_overrides.clear()

    assert second.status_code == 200
    assert second.json()["invoice_number"] == "INV-000001"
