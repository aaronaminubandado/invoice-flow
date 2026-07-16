import pytest
from uuid import uuid4
from sqlalchemy import text


@pytest.mark.asyncio
async def test_mark_overdue_invoices(db_session, user_id):
    """Test that invoices past due date are marked overdue"""
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
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE - INTERVAL '10 days', 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    result = await db_session.execute(
        text("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'sent'
              AND due_date < CURRENT_DATE
              AND user_id = :user_id
            RETURNING id, status
        """),
        {"user_id": user_id},
    )
    updated = result.fetchall()
    await db_session.commit()

    assert len(updated) == 1
    assert dict(updated[0]._mapping)["status"] == "overdue"


@pytest.mark.asyncio
async def test_mark_overdue_invoices_skips_future_due_dates(db_session, user_id):
    """Test that invoices with future due dates are NOT marked overdue"""
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
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE + INTERVAL '10 days', 'sent')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    result = await db_session.execute(
        text("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'sent'
              AND due_date < CURRENT_DATE
              AND user_id = :user_id
            RETURNING id, status
        """),
        {"user_id": user_id},
    )
    updated = result.fetchall()
    await db_session.commit()

    assert len(updated) == 0


@pytest.mark.asyncio
async def test_mark_overdue_invoices_skips_non_sent(db_session, user_id):
    """Test that only sent invoices are marked overdue"""
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
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE - INTERVAL '10 days', 'draft')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    result = await db_session.execute(
        text("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'sent'
              AND due_date < CURRENT_DATE
              AND user_id = :user_id
            RETURNING id, status
        """),
        {"user_id": user_id},
    )
    updated = result.fetchall()
    await db_session.commit()

    assert len(updated) == 0


def test_determine_reminder_type_first_reminder():
    """Test first reminder is sent at 3+ days overdue"""
    from app.services.scheduler import InvoiceScheduler

    scheduler = InvoiceScheduler()

    assert scheduler._determine_reminder_type(3, 0) == "first_reminder"
    assert scheduler._determine_reminder_type(5, 0) == "first_reminder"
    assert scheduler._determine_reminder_type(6, 0) == "first_reminder"


def test_determine_reminder_type_second_reminder():
    """Test second reminder is sent at 7+ days overdue"""
    from app.services.scheduler import InvoiceScheduler

    scheduler = InvoiceScheduler()

    assert scheduler._determine_reminder_type(7, 1) == "second_reminder"
    assert scheduler._determine_reminder_type(10, 1) == "second_reminder"
    assert scheduler._determine_reminder_type(14, 1) == "second_reminder"


def test_determine_reminder_type_no_reminder():
    """Test no reminder is sent when conditions not met"""
    from app.services.scheduler import InvoiceScheduler

    scheduler = InvoiceScheduler()

    assert scheduler._determine_reminder_type(2, 0) is None
    assert scheduler._determine_reminder_type(6, 1) is None
    assert scheduler._determine_reminder_type(7, 2) is None
    assert scheduler._determine_reminder_type(10, 2) is None


@pytest.mark.asyncio
async def test_mark_overdue_invoices_skips_non_sent(db_session, user_id):
    """Test that only sent invoices are marked overdue"""
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
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE - INTERVAL '10 days', 'draft')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    result = await db_session.execute(
        text("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'sent'
              AND due_date < CURRENT_DATE
              AND user_id = :user_id
            RETURNING id, status
        """),
        {"user_id": user_id},
    )
    updated = result.fetchall()
    await db_session.commit()

    assert len(updated) == 0
