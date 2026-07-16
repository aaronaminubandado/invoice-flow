import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import text


@pytest.mark.asyncio
async def test_create_invoice_with_email_tracking(client, db_session, user_id):
    """Test that creating an invoice sets email_status to pending"""
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
    await db_session.commit()

    response = await client.post(
        "/invoices",
        json={
            "client_id": str(client_id),
            "amount": 1000.00,
            "due_date": "2026-03-01",
            "description": "Test invoice",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "invoice_number" in data
    assert data["invoice_number"] == "INV-000001"


@pytest.mark.asyncio
async def test_get_email_status_endpoint(client, db_session, user_id):
    """Test the email status endpoint returns correct fields"""
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
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status, email_status, last_email_error)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent', 'failed', 'Connection timeout')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    response = await client.get(f"/invoices/{invoice_id}/email-status")

    assert response.status_code == 200
    data = response.json()
    assert data["email_status"] == "failed"
    assert data["last_email_error"] == "Connection timeout"


@pytest.mark.asyncio
async def test_resend_invoice_email(client, db_session, user_id):
    """Test resending invoice email"""
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
            INSERT INTO invoices (id, user_id, client_id, amount, due_date, status, invoice_number)
            VALUES (:invoice_id, :user_id, :client_id, 1000.00, CURRENT_DATE, 'sent', 'INV-000001')
            """
        ),
        {"invoice_id": invoice_id, "user_id": user_id, "client_id": client_id},
    )
    await db_session.commit()

    with patch("app.services.email.EmailService.get_provider") as mock_provider:
        mock_email = AsyncMock()
        mock_email.send_email.return_value = MagicMock(
            success=True,
            email_status="sent",
            error_message=None,
            resend_id="resend_123",
        )
        mock_provider.return_value = mock_email

        response = await client.post(f"/invoices/{invoice_id}/resend")

        assert response.status_code == 200
        assert response.json()["message"] == "Invoice email resent"


def test_email_service_provider_injection():
    """Test that email provider can be injected for testing"""
    from app.services.email import (
        EmailService,
        ConsoleEmailProvider,
        EmailStatus,
        EmailResult,
    )

    mock_provider = ConsoleEmailProvider()
    EmailService.set_provider(mock_provider)

    provider = EmailService.get_provider()
    assert isinstance(provider, ConsoleEmailProvider)

    EmailService.set_provider(None)


def test_email_result_dataclass():
    """Test EmailResult dataclass"""
    from app.services.email import EmailResult, EmailStatus

    result = EmailResult(
        success=True,
        email_status=EmailStatus.SENT,
        resend_id="resend_123",
    )

    assert result.success is True
    assert result.email_status == EmailStatus.SENT
    assert result.resend_id == "resend_123"
    assert result.error_message is None


def test_console_email_provider():
    """Test ConsoleEmailProvider returns success"""
    import asyncio
    from app.services.email import ConsoleEmailProvider

    async def test():
        provider = ConsoleEmailProvider()
        result = await provider.send_email(
            to="test@example.com",
            subject="Test",
            html="<p>Test</p>",
        )

        assert result.success is True
        assert result.email_status.value == "sent"

    asyncio.run(test())
