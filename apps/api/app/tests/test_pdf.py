import pytest
from decimal import Decimal
from datetime import date


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
