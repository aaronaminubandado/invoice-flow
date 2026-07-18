import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from sqlalchemy import text

from app.tests.helpers import insert_test_client, insert_test_invoice


def test_generate_invoice_pdf():
    """Test invoice PDF generation"""
    from app.services.pdf import PDFService

    pdf_bytes = PDFService.generate_invoice_pdf(
        invoice_id="test-123",
        invoice_number="INV-001",
        amount=Decimal("1000.00"),
        description="Test services",
        due_date=date(2026, 3, 1),
        status="sent",
        client_name="John Doe",
        client_email="john@example.com",
        created_at=date(2026, 2, 1),
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_receipt_pdf():
    """Test receipt PDF generation"""
    from app.services.pdf import PDFService

    pdf_bytes = PDFService.generate_receipt_pdf(
        receipt_id="receipt-123",
        receipt_number="RCP-001",
        invoice_id="invoice-123",
        invoice_number="INV-001",
        amount=Decimal("500.00"),
        payment_method="bank_transfer",
        payment_date=date(2026, 2, 15),
        client_name="John Doe",
        client_email="john@example.com",
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_invoice_pdf_without_number():
    """Test invoice PDF generation without invoice number"""
    from app.services.pdf import PDFService

    pdf_bytes = PDFService.generate_invoice_pdf(
        invoice_id="test-456",
        invoice_number=None,
        amount=Decimal("250.00"),
        description="Consulting",
        due_date=date(2026, 4, 1),
        status="overdue",
        client_name="Jane Smith",
        client_email="jane@example.com",
        created_at=date(2026, 1, 15),
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_invoice_pdf_with_balance_due():
    from app.services.pdf import PDFService

    pdf_bytes = PDFService.generate_invoice_pdf(
        invoice_id="test-789",
        invoice_number="INV-002",
        amount=Decimal("1000.00"),
        description="Test services",
        due_date=date(2026, 3, 1),
        status="partial",
        client_name="John Doe",
        client_email="john@example.com",
        created_at=date(2026, 2, 1),
        paid_amount=Decimal("400.00"),
        balance_due=Decimal("600.00"),
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_metrics_report_pdf():
    from app.services.pdf import PDFService

    pdf_bytes = PDFService.generate_metrics_report_pdf(
        summary={
            "total_revenue": "1000.00",
            "total_paid": "400.00",
            "total_outstanding": "600.00",
            "total_overdue": "0.00",
        },
        monthly_rows=[
            {"month": "2026-01", "paid": "400.00", "outstanding": "600.00"},
        ],
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"


@pytest.mark.asyncio
@pytest.mark.parametrize("address", ["42 Ledger Lane", None])
async def test_invoice_pdf_endpoint(client, db_session, user_id, address):
    client_id = uuid4()
    invoice_id = uuid4()
    await db_session.execute(
        text("""
            INSERT INTO clients (id, user_id, name, email, address)
            VALUES (:client_id, :user_id, 'PDF Client', 'pdf@example.com', :address)
        """),
        {
            "client_id": client_id,
            "user_id": user_id,
            "address": address,
        },
    )
    await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        invoice_id=invoice_id,
        amount=250.00,
        status="sent",
        invoice_number=f"INV-{str(invoice_id)[:8]}",
    )
    await db_session.commit()

    response = await client.get(f"/invoices/{invoice_id}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=invoice_" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_invoice_pdf_endpoint_with_line_items(client, db_session, user_id):
    client_id = await insert_test_client(db_session, user_id)
    invoice_id = await insert_test_invoice(
        db_session,
        user_id,
        client_id,
        amount=300.00,
        status="sent",
        invoice_number="INV-PDF-ITEMS",
    )
    await db_session.execute(
        text(
            """
            INSERT INTO invoice_items (
                invoice_id, description, quantity, unit_price, line_total, position
            )
            VALUES
                (:invoice_id, 'Design work', 2, 100.00, 200.00, 0),
                (:invoice_id, 'Hosting', 1, 100.00, 100.00, 1)
            """
        ),
        {"invoice_id": invoice_id},
    )
    await db_session.commit()

    response = await client.get(f"/invoices/{invoice_id}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000
