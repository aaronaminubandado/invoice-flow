import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import text


@pytest.mark.asyncio
async def test_create_payment_partial_success(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 500.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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
async def test_mark_paid_requires_full_payment(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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

    assert response.status_code == 400
    assert "Cannot mark as paid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_mark_paid_success(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'partial')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'cancelled')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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
    """Cannot cancel a paid invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'paid')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_already_cancelled_invoice_fails(client, db_session, user_id):
    """Cannot cancel an already cancelled invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'cancelled')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_draft_invoice_succeeds(client, db_session, user_id):
    """Can cancel a draft invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'draft')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_sent_invoice_succeeds(client, db_session, user_id):
    """Can cancel a sent invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_overdue_invoice_succeeds(client, db_session, user_id):
    """Can cancel an overdue invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE - INTERVAL '30 days', 'overdue')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(f"/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_payment_on_draft_invoice_fails(client, db_session, user_id):
    """Cannot add payment to draft invoice"""
    client_id = uuid4()
    invoice_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'draft')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.post(
        f"/invoices/{invoice_id}/payments",
        json={"amount": 500.00, "payment_method": "bank_transfer"},
    )

    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_draft_invoice(client, db_session, user_id):
    client_id = uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Draft Client', 'draft@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
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

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Send Client', 'send@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )
    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status, share_token)
            VALUES (:invoice_id, :user_id, :client_id, 100.00, CURRENT_DATE, 'draft', 'tok123')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Pay Client', 'pay@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )
    await db_session.execute(
        text(
            """
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status)
            VALUES (:invoice_id, :user_id, :client_id, 500.00, CURRENT_DATE, 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
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
    client_id = uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'List Client', 'list@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    for status in ("sent", "paid", "sent"):
        await db_session.execute(
            text(
                """
                INSERT INTO invoices (user_id, client_id, amount, due_date, status)
                VALUES (:user_id, :client_id, 100.00, CURRENT_DATE, :status)
                """
            ),
            {"user_id": user_id, "client_id": client_id, "status": status},
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
