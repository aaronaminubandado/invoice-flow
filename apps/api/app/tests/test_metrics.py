import pytest
from uuid import uuid4
from sqlalchemy import text


@pytest.mark.asyncio
async def test_revenue_summary_empty(client, db_session, user_id):
    """Test revenue summary with no invoices"""
    response = await client.get("/metrics/revenue-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == "0.00"
    assert data["total_paid"] == "0.00"
    assert data["total_outstanding"] == "0.00"
    assert data["total_overdue"] == "0.00"


@pytest.mark.asyncio
async def test_revenue_summary_with_invoices(client, db_session, user_id):
    """Test revenue summary with various invoice statuses"""
    client_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    invoices_data = [
        (uuid4(), 1000.00, "paid"),
        (uuid4(), 500.00, "sent"),
        (uuid4(), 750.00, "overdue"),
        (uuid4(), 300.00, "partial"),
        (uuid4(), 200.00, "draft"),
    ]

    for invoice_id, amount, status in invoices_data:
        await db_session.execute(
            text(
                """
                INSERT INTO invoices (id, user_id, client_id, amount, due_date, status, created_at)
                VALUES (:invoice_id, :user_id, :client_id, :amount, CURRENT_DATE, :status, NOW() - INTERVAL '1 month')
                """
            ),
            {
                "invoice_id": invoice_id,
                "user_id": user_id,
                "client_id": client_id,
                "amount": amount,
                "status": status,
            },
        )

    await db_session.commit()

    response = await client.get("/metrics/revenue-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == "2750.00"
    assert data["total_paid"] == "1000.00"
    assert data["total_outstanding"] == "1550.00"
    assert data["total_overdue"] == "750.00"


@pytest.mark.asyncio
async def test_monthly_revenue_empty(client, db_session, user_id):
    """Test monthly revenue with no invoices"""
    response = await client.get("/metrics/monthly-revenue")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_monthly_revenue_with_invoices(client, db_session, user_id):
    """Test monthly revenue breakdown"""
    client_id = uuid4()

    await db_session.execute(
        text(
            """
            INSERT INTO clients (id, user_id, name, email)
            VALUES (:client_id, :user_id, 'Test Client', 'test@example.com')
            """
        ),
        {"client_id": client_id, "user_id": user_id},
    )

    invoices_data = [
        (uuid4(), 1000.00, "paid", "NOW() - INTERVAL '1 month'"),
        (uuid4(), 500.00, "sent", "NOW() - INTERVAL '2 months'"),
        (uuid4(), 750.00, "overdue", "NOW() - INTERVAL '3 months'"),
    ]

    for invoice_id, amount, status, date_expr in invoices_data:
        await db_session.execute(
            text(
                f"""
                INSERT INTO invoices (id, user_id, client_id, amount, due_date, status, created_at)
                VALUES (:invoice_id, :user_id, :client_id, :amount, CURRENT_DATE, :status, {date_expr})
                """
            ),
            {
                "invoice_id": invoice_id,
                "user_id": user_id,
                "client_id": client_id,
                "amount": amount,
                "status": status,
            },
        )

    await db_session.commit()

    response = await client.get("/metrics/monthly-revenue")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
