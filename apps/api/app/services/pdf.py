import io
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


@dataclass
class BusinessInfo:
    business_name: str
    business_email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    currency: str = "USD"
    logo_url: Optional[str] = None


class PDFService:
    @staticmethod
    def generate_invoice_pdf(
        invoice_id: str,
        invoice_number: Optional[str],
        amount: Decimal,
        description: str,
        due_date: date,
        status: str,
        client_name: str,
        client_email: str,
        created_at: date,
        business_info: Optional[BusinessInfo] = None,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        if business_info:
            elements.append(Paragraph(business_info.business_name, styles["Heading2"]))
            elements.append(Paragraph(business_info.business_email, styles["Normal"]))
            if business_info.phone:
                elements.append(Paragraph(business_info.phone, styles["Normal"]))
            if business_info.address:
                elements.append(Paragraph(business_info.address, styles["Normal"]))
            elements.append(Spacer(1, 20))

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
        )
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 20))

        currency_symbol = business_info.currency if business_info else "USD"
        if currency_symbol == "USD":
            currency_symbol = "$"
        elif currency_symbol == "EUR":
            currency_symbol = "€"
        elif currency_symbol == "GBP":
            currency_symbol = "£"

        info_data = [
            ["Invoice ID:", str(invoice_id)],
            ["Invoice Number:", invoice_number or "N/A"],
            ["Status:", status.upper()],
            ["Date:", created_at.strftime("%Y-%m-%d") if created_at else "N/A"],
            ["Due Date:", due_date.strftime("%Y-%m-%d")],
        ]

        info_table = Table(info_data, colWidths=[1.5 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Bill To:", styles["Heading3"]))
        elements.append(Paragraph(client_name, styles["Normal"]))
        elements.append(Paragraph(client_email, styles["Normal"]))
        elements.append(Spacer(1, 30))

        currency_symbol = "$"
        if business_info:
            if business_info.currency == "EUR":
                currency_symbol = "€"
            elif business_info.currency == "GBP":
                currency_symbol = "£"
            elif business_info.currency == "JPY":
                currency_symbol = "¥"

        items_data = [["Description", "Amount"]]
        items_data.append([description or "Invoice", f"{currency_symbol}{amount:,.2f}"])

        items_table = Table(items_data, colWidths=[4 * inch, 2 * inch])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        total_data = [["Total:", f"{currency_symbol}{amount:,.2f}"]]
        total_table = Table(total_data, colWidths=[4 * inch, 2 * inch])
        total_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        elements.append(total_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_receipt_pdf(
        receipt_id: str,
        receipt_number: str,
        invoice_id: str,
        invoice_number: Optional[str],
        amount: Decimal,
        payment_method: str,
        payment_date: date,
        client_name: str,
        client_email: str,
        business_info: Optional[BusinessInfo] = None,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        if business_info:
            elements.append(Paragraph(business_info.business_name, styles["Heading2"]))
            elements.append(Paragraph(business_info.business_email, styles["Normal"]))
            if business_info.phone:
                elements.append(Paragraph(business_info.phone, styles["Normal"]))
            if business_info.address:
                elements.append(Paragraph(business_info.address, styles["Normal"]))
            elements.append(Spacer(1, 20))

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
        )
        elements.append(Paragraph("PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 20))

        info_data = [
            ["Receipt ID:", str(receipt_id)],
            ["Receipt Number:", receipt_number],
            ["Invoice ID:", str(invoice_id)],
            ["Invoice Number:", invoice_number or "N/A"],
            ["Payment Date:", payment_date.strftime("%Y-%m-%d")],
            ["Payment Method:", payment_method],
        ]

        info_table = Table(info_data, colWidths=[1.5 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Received From:", styles["Heading3"]))
        elements.append(Paragraph(client_name, styles["Normal"]))
        elements.append(Paragraph(client_email, styles["Normal"]))
        elements.append(Spacer(1, 30))

        currency_symbol = "$"
        if business_info:
            if business_info.currency == "EUR":
                currency_symbol = "€"
            elif business_info.currency == "GBP":
                currency_symbol = "£"
            elif business_info.currency == "JPY":
                currency_symbol = "¥"

        amount_data = [["Amount Paid:", f"{currency_symbol}{amount:,.2f}"]]
        amount_table = Table(amount_data, colWidths=[4 * inch, 2 * inch])
        amount_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("BOX", (0, 0), (-1, -1), 2, colors.black),
                ]
            )
        )
        elements.append(amount_table)

        elements.append(Spacer(1, 40))
        elements.append(Paragraph("Thank you for your payment!", styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
