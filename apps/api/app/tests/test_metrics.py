import pytest
from uuid import uuid4
from sqlalchemy import text

from app.tests.helpers import insert_test_client, insert_test_invoice


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
    client_id = await insert_test_client(db_session, user_id)

    invoices_data = [
        (1000.00, "paid"),
        (500.00, "sent"),
        (750.00, "overdue"),
        (300.00, "partial"),
        (200.00, "draft"),
    ]

    paid_invoice_id = None
    partial_invoice_id = None

    for amount, status in invoices_data:
        invoice_id = await insert_test_invoice(
            db_session,
            user_id,
            client_id,
            amount=amount,
            status=status,
            created_at_expr="NOW() - INTERVAL '1 month'",
        )
        if status == "paid":
            paid_invoice_id = invoice_id
        elif status == "partial":
            partial_invoice_id = invoice_id

    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 1000.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": paid_invoice_id},
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 100.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": partial_invoice_id},
    )

    await db_session.commit()

    response = await client.get("/metrics/revenue-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == "2750.00"
    assert data["total_paid"] == "1100.00"
    assert data["total_outstanding"] == "1450.00"
    assert data["total_overdue"] == "750.00"


@pytest.mark.asyncio
async def test_revenue_summary_uses_payment_totals_for_partial(client, db_session, user_id):
    client_id = uuid4()
    invoice_id = uuid4()

    await insert_test_client(db_session, user_id, client_id=client_id)
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=1000.00,
        status="partial",
    )
    await db_session.execute(
        text(
            """
            INSERT INTO payments (invoice_id, amount, payment_method, payment_date)
            VALUES (:invoice_id, 400.00, 'bank_transfer', CURRENT_DATE)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.get("/metrics/revenue-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_paid"] == "400.00"
    assert data["total_outstanding"] == "600.00"


@pytest.mark.asyncio
async def test_monthly_revenue_empty(client, db_session, user_id):
    """Test monthly revenue with no invoices"""
    response = await client.get("/metrics/monthly-revenue")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_monthly_revenue_with_invoices(client, db_session, user_id):
    """Test monthly revenue breakdown"""
    client_id = await insert_test_client(db_session, user_id)

    invoices_data = [
        (1000.00, "paid", "NOW() - INTERVAL '1 month'"),
        (500.00, "sent", "NOW() - INTERVAL '2 months'"),
        (750.00, "overdue", "NOW() - INTERVAL '3 months'"),
    ]

    for amount, status, created_at_expr in invoices_data:
        await insert_test_invoice(
            db_session,
            user_id,
            client_id,
            amount=amount,
            status=status,
            created_at_expr=created_at_expr,
        )

    await db_session.commit()

    response = await client.get("/metrics/monthly-revenue")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
