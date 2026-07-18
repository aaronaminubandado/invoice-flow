import io
from datetime import date
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String


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
    def currency_symbol(currency: str = "USD") -> str:
        mapping = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
        return mapping.get(currency, currency + " ")

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
        items: Sequence | None = None,
        client_address: Optional[str] = None,
        paid_amount: Decimal = Decimal("0"),
        balance_due: Optional[Decimal] = None,
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

        currency_symbol = PDFService.currency_symbol(
            business_info.currency if business_info else "USD"
        )

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
        if client_address:
            elements.append(Paragraph(client_address, styles["Normal"]))
        elements.append(Spacer(1, 30))

        if items:
            items_data = [["Description", "Qty", "Unit Price", "Line Total"]]
            for item in items:
                desc = item.description if hasattr(item, "description") else item["description"]
                qty = item.quantity if hasattr(item, "quantity") else item["quantity"]
                unit = item.unit_price if hasattr(item, "unit_price") else item["unit_price"]
                line = item.line_total if hasattr(item, "line_total") else item["line_total"]
                items_data.append(
                    [
                        desc,
                        str(qty),
                        f"{currency_symbol}{Decimal(str(unit)):,.2f}",
                        f"{currency_symbol}{Decimal(str(line)):,.2f}",
                    ]
                )
            col_widths = [2.5 * inch, 0.7 * inch, 1.2 * inch, 1.2 * inch]
        else:
            items_data = [["Description", "Amount"]]
            items_data.append([description or "Invoice", f"{currency_symbol}{amount:,.2f}"])
            col_widths = [4 * inch, 2 * inch]

        items_table = Table(items_data, colWidths=col_widths)
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

        resolved_balance = (
            balance_due
            if balance_due is not None
            else max(amount - paid_amount, Decimal("0"))
        )
        total_rows = [["Invoice Total:", f"{currency_symbol}{amount:,.2f}"]]
        if paid_amount > 0:
            total_rows.append(["Amount Paid:", f"{currency_symbol}{paid_amount:,.2f}"])
            total_rows.append(
                ["Balance Due:", f"{currency_symbol}{resolved_balance:,.2f}"]
            )
        else:
            total_rows.append(["Total Due:", f"{currency_symbol}{amount:,.2f}"])

        total_table = Table(total_rows, colWidths=[4 * inch, 2 * inch])
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
    def generate_metrics_report_pdf(
        summary: dict[str, str],
        monthly_rows: list[dict],
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            "MetricsTitle",
            parent=styles["Heading1"],
            fontSize=22,
            spaceAfter=16,
        )
        elements.append(Paragraph("Metrics Report", title_style))
        elements.append(Spacer(1, 12))

        summary_data = [
            ["Total Revenue", f"${Decimal(summary['total_revenue']):,.2f}"],
            ["Total Paid", f"${Decimal(summary['total_paid']):,.2f}"],
            ["Outstanding", f"${Decimal(summary['total_outstanding']):,.2f}"],
            ["Overdue", f"${Decimal(summary['total_overdue']):,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 24))

        distribution = [
            ("Paid", Decimal(summary["total_paid"])),
            ("Outstanding", Decimal(summary["total_outstanding"])),
            ("Overdue", Decimal(summary["total_overdue"])),
        ]
        distribution = [(label, value) for label, value in distribution if value > 0]
        if distribution:
            elements.append(Paragraph("Revenue Distribution", styles["Heading3"]))
            elements.append(Spacer(1, 8))
            chart = Drawing(420, 180)
            bar_chart = VerticalBarChart()
            bar_chart.x = 40
            bar_chart.y = 20
            bar_chart.height = 120
            bar_chart.width = 320
            bar_chart.data = [[float(value) for _, value in distribution]]
            bar_chart.categoryAxis.categoryNames = [label for label, _ in distribution]
            bar_chart.valueAxis.valueMin = 0
            bar_chart.bars[0].fillColor = colors.HexColor("#0f766e")
            chart.add(bar_chart)
            chart.add(String(0, 160, "Amounts by status", fontSize=10))
            elements.append(chart)
            elements.append(Spacer(1, 24))

        if monthly_rows:
            elements.append(Paragraph("Monthly Paid vs Outstanding", styles["Heading3"]))
            elements.append(Spacer(1, 8))
            monthly_chart = Drawing(420, 200)
            monthly_bar = VerticalBarChart()
            monthly_bar.x = 40
            monthly_bar.y = 20
            monthly_bar.height = 130
            monthly_bar.width = 320
            monthly_bar.data = [
                [float(row.get("paid", 0) or 0) for row in monthly_rows[:6][::-1]],
                [
                    float(row.get("outstanding", 0) or 0)
                    for row in monthly_rows[:6][::-1]
                ],
            ]
            monthly_bar.categoryAxis.categoryNames = [
                str(row.get("month", "")) for row in monthly_rows[:6][::-1]
            ]
            monthly_bar.groupSpacing = 10
            monthly_bar.barSpacing = 2
            monthly_bar.bars[0].fillColor = colors.HexColor("#0f766e")
            monthly_bar.bars[1].fillColor = colors.HexColor("#d97706")
            monthly_chart.add(monthly_bar)
            monthly_chart.add(String(0, 180, "Paid vs outstanding by month", fontSize=10))
            elements.append(monthly_chart)
            elements.append(Spacer(1, 24))

            table_rows = [["Month", "Paid", "Outstanding"]]
            for row in monthly_rows:
                table_rows.append([
                    str(row.get("month", "")),
                    f"${Decimal(str(row.get('paid', 0))):,.2f}",
                    f"${Decimal(str(row.get('outstanding', 0))):,.2f}",
                ])
            monthly_table = Table(table_rows, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch])
            monthly_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            elements.append(monthly_table)

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
