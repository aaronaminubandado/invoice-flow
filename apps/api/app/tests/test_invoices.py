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
