import re
import logging
import base64
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.services.pdf import PDFService

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class EmailResult:
    success: bool
    email_status: EmailStatus
    error_message: Optional[str] = None
    resend_id: Optional[str] = None


def sanitize_email_input(value: str, max_length: int = 255) -> str:
    """Sanitize email-related inputs to prevent injection"""
    if not value:
        return ""
    sanitized = re.sub(r"[\r\n\x00-\x1f]", "", str(value))
    return sanitized[:max_length]


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str


class BaseEmailProvider(ABC):
    """Abstract base class for email providers"""

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> EmailResult:
        """Send an email and return the result"""
        pass


class ResendEmailProvider(BaseEmailProvider):
    """Resend.com email provider implementation"""

    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> EmailResult:
        try:
            import resend

            resend.api_key = self.api_key

            email_params = {
                "from": self.from_email,
                "to": to,
                "subject": subject,
                "html": html,
                "text": text,
            }

            if attachments:
                email_params["attachments"] = [
                    {
                        "filename": att.filename,
                        "content": base64.b64encode(att.content).decode("utf-8"),
                        "content_type": att.content_type,
                    }
                    for att in attachments
                ]

            response = resend.Emails.send(email_params)

            if response and "id" in response:
                logger.info(f"Email sent successfully via Resend: {response['id']}")
                return EmailResult(
                    success=True,
                    email_status=EmailStatus.SENT,
                    resend_id=response["id"],
                )
            else:
                logger.error(f"Resend API returned unexpected response: {response}")
                return EmailResult(
                    success=False,
                    email_status=EmailStatus.FAILED,
                    error_message="Invalid response from email provider",
                )

        except ImportError:
            logger.warning("resend package not installed, falling back to console")
            return EmailResult(
                success=False,
                email_status=EmailStatus.FAILED,
                error_message="resend package not installed",
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email via Resend: {error_msg}")
            return EmailResult(
                success=False,
                email_status=EmailStatus.FAILED,
                error_message=error_msg,
            )


class ConsoleEmailProvider(BaseEmailProvider):
    """Console/development email provider for testing"""

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> EmailResult:
        print(f"[EMAIL] To: {to}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] HTML: {html[:200]}...")
        if attachments:
            print(f"[EMAIL] Attachments: {[a.filename for a in attachments]}")
        logger.info(f"[CONSOLE EMAIL] To: {to}, Subject: {subject}")
        return EmailResult(
            success=True,
            email_status=EmailStatus.SENT,
            resend_id=f"console_{id(html)}",
        )


class EmailService:
    """
    Email sending abstraction with pluggable providers.
    Uses Resend in production, console in development.
    """

    _provider: Optional[BaseEmailProvider] = None

    @classmethod
    def set_provider(cls, provider: BaseEmailProvider):
        """Set a custom email provider (useful for testing)"""
        cls._provider = provider

    @classmethod
    def get_provider(cls) -> BaseEmailProvider:
        """Get the current email provider"""
        if cls._provider is not None:
            return cls._provider

        from app.core.config import settings

        if settings.RESEND_API_KEY:
            return ResendEmailProvider(
                api_key=settings.RESEND_API_KEY,
                from_email=settings.EMAIL_FROM,
            )

        return ConsoleEmailProvider()

    @classmethod
    async def send_invoice_email_with_tracking(
        cls, invoice_id: str, to: str, invoice_data: dict
    ) -> EmailResult:
        """Send invoice email with PDF attachment and update tracking in database"""
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        from app.services.pdf import PDFService
        from app.services.business_settings import get_business_settings
        from decimal import Decimal
        from datetime import date

        invoice_id = sanitize_email_input(invoice_id)

        async with AsyncSessionLocal() as db:
            try:
                business_info = None
                invoice_result = await db.execute(
                    text("""
                        SELECT i.user_id, i.invoice_number, i.amount, i.description,
                               i.due_date, i.status, i.created_at,
                               c.name as client_name, c.email as client_email
                        FROM invoices i
                        JOIN clients c ON i.client_id = c.id
                        WHERE i.id = :invoice_id
                    """),
                    {"invoice_id": invoice_id},
                )
                inv_row = invoice_result.first()

                attachments = []
                business_info_dict = None

                if inv_row:
                    inv_data = dict(inv_row._mapping)
                    business_info = await get_business_settings(
                        db, inv_data["user_id"]
                    )

                    if business_info:
                        business_info_dict = {
                            "business_name": business_info.business_name,
                            "business_email": business_info.business_email,
                            "phone": business_info.phone,
                            "address": business_info.address,
                            "currency": business_info.currency,
                        }

                    try:
                        pdf_bytes = PDFService.generate_invoice_pdf(
                            invoice_id=invoice_id,
                            invoice_number=inv_data.get("invoice_number"),
                            amount=Decimal(str(inv_data["amount"])),
                            description=inv_data.get("description") or "",
                            due_date=inv_data["due_date"],
                            status=inv_data.get("status", "sent"),
                            client_name=inv_data["client_name"],
                            client_email=inv_data["client_email"],
                            created_at=inv_data.get("created_at", date.today()),
                            business_info=business_info,
                        )
                        filename = f"invoice_{inv_data.get('invoice_number') or invoice_id[:8]}.pdf"
                        attachments.append(
                            EmailAttachment(
                                filename=filename,
                                content=pdf_bytes,
                                content_type="application/pdf",
                            )
                        )
                    except Exception as pdf_err:
                        logger.error(
                            f"Failed to generate invoice PDF for {invoice_id}: {pdf_err}"
                        )

                result = await cls.send_invoice_email(
                    invoice_id=invoice_id,
                    to=to,
                    invoice_data=invoice_data,
                    attachments=attachments if attachments else None,
                    business_info=business_info_dict,
                )

                await db.execute(
                    text("""
                        UPDATE invoices
                        SET email_status = :status,
                            last_email_error = :error,
                            last_email_sent_at = CASE WHEN :sent THEN NOW() ELSE last_email_sent_at END,
                            email_resend_id = :resend_id
                        WHERE id = :invoice_id
                    """),
                    {
                        "invoice_id": invoice_id,
                        "status": result.email_status.value,
                        "error": result.error_message,
                        "sent": result.success,
                        "resend_id": result.resend_id,
                    },
                )
                await db.commit()

                logger.info(
                    f"Updated email status for invoice {invoice_id}: {result.email_status.value}"
                )

            except Exception as e:
                logger.error(f"Failed to update email tracking for {invoice_id}: {e}")
                try:
                    await db.rollback()
                except Exception:
                    pass

    @classmethod
    async def send_invoice_email(
        cls,
        invoice_id: str,
        to: str,
        invoice_data: dict,
        attachments: Optional[List[EmailAttachment]] = None,
        business_info: Optional[dict] = None,
    ) -> EmailResult:
        """Send invoice email to client"""
        invoice_id = sanitize_email_input(invoice_id)

        subject = f"Invoice #{invoice_data.get('invoice_number', invoice_id[:8])}"
        if business_info and business_info.get("business_name"):
            subject = f"Invoice #{invoice_data.get('invoice_number', invoice_id[:8])} from {business_info['business_name']}"

        html = cls._build_invoice_html(invoice_data, business_info)
        text = cls._build_invoice_text(invoice_data, business_info)

        return await cls.get_provider().send_email(
            to=to,
            subject=subject,
            html=html,
            text=text,
            attachments=attachments,
        )

    @classmethod
    async def send_receipt_email(
        cls,
        invoice_id: str,
        to: str,
        receipt_data: dict,
        attachments: Optional[List[EmailAttachment]] = None,
        business_info: Optional[dict] = None,
    ) -> EmailResult:
        """Send payment receipt email to client"""
        invoice_id = sanitize_email_input(invoice_id)

        subject = (
            f"Receipt for Invoice #{receipt_data.get('invoice_number', invoice_id[:8])}"
        )
        if business_info and business_info.get("business_name"):
            subject = f"Receipt for Invoice #{receipt_data.get('invoice_number', invoice_id[:8])} from {business_info['business_name']}"

        html = cls._build_receipt_html(receipt_data, business_info)
        text = cls._build_receipt_text(receipt_data, business_info)

        return await cls.get_provider().send_email(
            to=to,
            subject=subject,
            html=html,
            text=text,
            attachments=attachments,
        )

    @classmethod
    async def send_receipt_email_with_tracking(
        cls, invoice_id: str, to: str, receipt_data: dict
    ) -> EmailResult:
        """Send receipt email with PDF attachment and update tracking in database"""
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        from app.services.pdf import PDFService
        from app.services.business_settings import get_business_settings
        from decimal import Decimal

        invoice_id = sanitize_email_input(invoice_id)

        async with AsyncSessionLocal() as db:
            try:
                payment_result = await db.execute(
                    text("""
                        SELECT p.id as payment_id, p.amount, p.payment_method, p.payment_date,
                               i.id as invoice_id, i.invoice_number, i.user_id,
                               c.name as client_name, c.email as client_email
                        FROM payments p
                        JOIN invoices i ON p.invoice_id = i.id
                        JOIN clients c ON i.client_id = c.id
                        WHERE i.id = :invoice_id
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """),
                    {"invoice_id": invoice_id},
                )
                pay_row = payment_result.first()

                attachments = []
                business_info = None
                business_info_dict = None

                if pay_row:
                    pay_data = dict(pay_row._mapping)
                    business_info = await get_business_settings(
                        db, pay_data["user_id"]
                    )

                    if business_info:
                        business_info_dict = {
                            "business_name": business_info.business_name,
                            "business_email": business_info.business_email,
                            "phone": business_info.phone,
                            "address": business_info.address,
                            "currency": business_info.currency,
                        }

                    try:
                        receipt_number = f"RCP-{str(pay_data['payment_id']).replace('-', '')[:8].upper()}"
                        pdf_bytes = PDFService.generate_receipt_pdf(
                            receipt_id=str(pay_data["payment_id"]),
                            receipt_number=receipt_number,
                            invoice_id=str(pay_data["invoice_id"]),
                            invoice_number=pay_data.get("invoice_number"),
                            amount=Decimal(str(pay_data["amount"])),
                            payment_method=pay_data.get(
                                "payment_method", "bank_transfer"
                            ),
                            payment_date=pay_data["payment_date"],
                            client_name=pay_data["client_name"],
                            client_email=pay_data["client_email"],
                            business_info=business_info,
                        )
                        attachments.append(
                            EmailAttachment(
                                filename=f"{receipt_number}.pdf",
                                content=pdf_bytes,
                                content_type="application/pdf",
                            )
                        )
                    except Exception as pdf_err:
                        logger.error(
                            f"Failed to generate receipt PDF for {invoice_id}: {pdf_err}"
                        )

                result = await cls.send_receipt_email(
                    invoice_id=invoice_id,
                    to=to,
                    receipt_data=receipt_data,
                    attachments=attachments if attachments else None,
                    business_info=business_info_dict,
                )

                await db.execute(
                    text("""
                        UPDATE invoices
                        SET email_status = :status,
                            last_email_error = :error,
                            last_email_sent_at = CASE WHEN :sent THEN NOW() ELSE last_email_sent_at END,
                            email_resend_id = :resend_id
                        WHERE id = :invoice_id
                    """),
                    {
                        "invoice_id": invoice_id,
                        "status": result.email_status.value,
                        "error": result.error_message,
                        "sent": result.success,
                        "resend_id": result.resend_id,
                    },
                )
                await db.commit()

                logger.info(
                    f"Updated receipt email status for invoice {invoice_id}: {result.email_status.value}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to update receipt email tracking for {invoice_id}: {e}"
                )

        return result

    @classmethod
    async def send_reminder_email(
        cls,
        invoice_id: str,
        client_email: str,
        client_name: str,
        amount: str,
        due_date: str,
        subject: str,
        body: str,
    ) -> EmailResult:
        """Send overdue reminder email to client"""
        invoice_id = sanitize_email_input(invoice_id)
        client_email = sanitize_email_input(client_email, 254)
        client_name = sanitize_email_input(client_name, 255)
        subject = sanitize_email_input(subject, 255)
        body = re.sub(r"[\r\n\x00-\x08\x0b\x0c\x0e-\x1f]", "", body)

        html = cls._build_reminder_html(client_name, subject, body, amount, due_date)
        text = cls._build_reminder_text(client_name, subject, body, amount, due_date)

        return await cls.get_provider().send_email(
            to=client_email,
            subject=subject,
            html=html,
            text=text,
        )

    @staticmethod
    def _build_business_header_html(business_info: Optional[dict]) -> str:
        if not business_info:
            return ""
        parts = []
        name = business_info.get("business_name", "")
        email = business_info.get("business_email", "")
        phone = business_info.get("phone", "")
        address = business_info.get("address", "")
        if name:
            parts.append(
                f'<h1 style="margin:0 0 4px 0;font-size:20px;color:#111827;">{name}</h1>'
            )
        if email:
            parts.append(
                f'<p style="margin:0;font-size:13px;color:#6b7280;">{email}</p>'
            )
        if phone:
            parts.append(
                f'<p style="margin:0;font-size:13px;color:#6b7280;">{phone}</p>'
            )
        if address:
            parts.append(
                f'<p style="margin:0;font-size:13px;color:#6b7280;">{address}</p>'
            )
        if parts:
            return (
                '<div style="margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #e5e7eb;">'
                + "\n".join(parts)
                + "</div>"
            )
        return ""

    @staticmethod
    def _build_business_footer_html(business_info: Optional[dict]) -> str:
        if not business_info:
            return '<p style="color:#9ca3af;font-size:12px;">This is an automated message from InvoiceFlow.</p>'
        name = business_info.get("business_name", "InvoiceFlow")
        email = business_info.get("business_email", "")
        phone = business_info.get("phone", "")
        parts = [f"<strong>{name}</strong>"]
        if email:
            parts.append(email)
        if phone:
            parts.append(phone)
        return f'<p style="color:#9ca3af;font-size:12px;">{" &bull; ".join(parts)}</p>'

    @staticmethod
    def _build_business_header_text(business_info: Optional[dict]) -> str:
        if not business_info:
            return ""
        parts = []
        name = business_info.get("business_name", "")
        email = business_info.get("business_email", "")
        phone = business_info.get("phone", "")
        address = business_info.get("address", "")
        if name:
            parts.append(name)
        if email:
            parts.append(email)
        if phone:
            parts.append(phone)
        if address:
            parts.append(address)
        if parts:
            return "\n".join(parts) + "\n" + "-" * 40 + "\n\n"
        return ""

    @staticmethod
    def _currency_symbol(business_info: Optional[dict]) -> str:
        code = (business_info or {}).get("currency", "USD")
        return PDFService.currency_symbol(code)

    @staticmethod
    def _public_link_html(share_token: Optional[str]) -> str:
        if not share_token or not settings.PUBLIC_APP_URL:
            return ""
        url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/i/{share_token}"
        return f"""
            <p style="margin:24px 0;">
                <a href="{url}" style="display:inline-block;background:#635bff;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:600;">
                    View invoice online
                </a>
            </p>
        """

    @staticmethod
    def _public_link_text(share_token: Optional[str]) -> str:
        if not share_token or not settings.PUBLIC_APP_URL:
            return ""
        url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/i/{share_token}"
        return f"\nView online: {url}\n"

    @staticmethod
    def _items_html(items: list, symbol: str) -> str:
        if not items:
            return ""
        rows = ""
        for item in items:
            rows += f"""
                <tr>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{item.get('description','')}</td>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">{item.get('quantity','')}</td>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">{symbol}{item.get('unit_price','')}</td>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">{symbol}{item.get('line_total','')}</td>
                </tr>
            """
        return f"""
            <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
                <thead>
                    <tr style="background:#f3f4f6;">
                        <th style="padding:8px;text-align:left;">Description</th>
                        <th style="padding:8px;text-align:right;">Qty</th>
                        <th style="padding:8px;text-align:right;">Unit</th>
                        <th style="padding:8px;text-align:right;">Total</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        """

    @staticmethod
    def _build_invoice_html(
        invoice_data: dict, business_info: Optional[dict] = None
    ) -> str:
        amount = invoice_data.get("amount", "0.00")
        description = invoice_data.get("description", "")
        due_date = invoice_data.get("due_date", "N/A")
        invoice_number = invoice_data.get("invoice_number", "N/A")
        client_name = invoice_data.get("client_name", "Customer")
        items = invoice_data.get("items") or []
        symbol = EmailService._currency_symbol(business_info)

        header = EmailService._build_business_header_html(business_info)
        footer = EmailService._build_business_footer_html(business_info)
        items_block = EmailService._items_html(items, symbol)
        link_block = EmailService._public_link_html(invoice_data.get("share_token"))

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1f2937;">
            {header}
            <h2 style="color:#111827;margin-bottom:16px;">Invoice #{invoice_number}</h2>
            <p>Dear {client_name},</p>
            <p>Please find attached your invoice for <strong>{symbol}{amount}</strong>.</p>
            {items_block}
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <tr>
                    <td style="padding:8px 0;color:#6b7280;width:140px;"><strong>Due Date:</strong></td>
                    <td style="padding:8px 0;">{due_date}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Description:</strong></td>
                    <td style="padding:8px 0;">{description}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Amount Due:</strong></td>
                    <td style="padding:8px 0;font-size:18px;font-weight:bold;">{symbol}{amount}</td>
                </tr>
            </table>
            {link_block}
            <p>Please remit payment at your earliest convenience.</p>
            <p>Thank you for your business!</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            {footer}
        </body>
        </html>
        """

    @staticmethod
    def _build_invoice_text(
        invoice_data: dict, business_info: Optional[dict] = None
    ) -> str:
        amount = invoice_data.get("amount", "0.00")
        description = invoice_data.get("description", "")
        due_date = invoice_data.get("due_date", "N/A")
        invoice_number = invoice_data.get("invoice_number", "N/A")
        client_name = invoice_data.get("client_name", "Customer")
        symbol = EmailService._currency_symbol(business_info)

        header = EmailService._build_business_header_text(business_info)
        link = EmailService._public_link_text(invoice_data.get("share_token"))

        return f"""{header}Invoice #{invoice_number}

Dear {client_name},

Please find attached your invoice for {symbol}{amount}.

Due Date: {due_date}
Description: {description}
Amount Due: {symbol}{amount}
{link}
Please remit payment at your earliest convenience.

Thank you for your business!
"""

    @staticmethod
    def _build_receipt_html(
        receipt_data: dict, business_info: Optional[dict] = None
    ) -> str:
        amount = receipt_data.get("amount", "0.00")
        invoice_number = receipt_data.get("invoice_number", "N/A")
        payment_date = receipt_data.get("payment_date", "N/A")
        paid_amount = receipt_data.get("paid_amount")
        payment_method = receipt_data.get("payment_method", "N/A")
        client_name = receipt_data.get("client_name", "Customer")
        symbol = EmailService._currency_symbol(business_info)

        outstanding = ""
        if paid_amount and float(paid_amount) > float(amount):
            outstanding = f'<tr><td style="padding:8px 0;color:#6b7280;"><strong>Overpayment:</strong></td><td style="padding:8px 0;">{symbol}{float(paid_amount) - float(amount):.2f}</td></tr>'

        header = EmailService._build_business_header_html(business_info)
        footer = EmailService._build_business_footer_html(business_info)
        link_block = EmailService._public_link_html(receipt_data.get("share_token"))
        paid_display = paid_amount if paid_amount else amount

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1f2937;">
            {header}
            <h2 style="color:#111827;margin-bottom:16px;">Payment Receipt</h2>
            <p>Dear {client_name},</p>
            <p>We have received your payment. Thank you!</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <tr>
                    <td style="padding:8px 0;color:#6b7280;width:160px;"><strong>Invoice #:</strong></td>
                    <td style="padding:8px 0;">{invoice_number}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Invoice Amount:</strong></td>
                    <td style="padding:8px 0;">{symbol}{amount}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Amount Paid:</strong></td>
                    <td style="padding:8px 0;font-size:18px;font-weight:bold;">{symbol}{paid_display}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Payment Date:</strong></td>
                    <td style="padding:8px 0;">{payment_date}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Payment Method:</strong></td>
                    <td style="padding:8px 0;">{payment_method}</td>
                </tr>
                {outstanding}
            </table>
            {link_block}
            <p>Thank you for your payment!</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            {footer}
        </body>
        </html>
        """

    @staticmethod
    def _build_receipt_text(
        receipt_data: dict, business_info: Optional[dict] = None
    ) -> str:
        amount = receipt_data.get("amount", "0.00")
        invoice_number = receipt_data.get("invoice_number", "N/A")
        payment_date = receipt_data.get("payment_date", "N/A")
        paid_amount = receipt_data.get("paid_amount")
        payment_method = receipt_data.get("payment_method", "N/A")
        client_name = receipt_data.get("client_name", "Customer")
        symbol = EmailService._currency_symbol(business_info)

        outstanding = ""
        if paid_amount and float(paid_amount) > float(amount):
            outstanding = (
                f"\nOverpayment: {symbol}{float(paid_amount) - float(amount):.2f}"
            )

        header = EmailService._build_business_header_text(business_info)
        link = EmailService._public_link_text(receipt_data.get("share_token"))
        paid_display = paid_amount if paid_amount else amount

        return f"""{header}Payment Receipt

Dear {client_name},

We have received your payment. Thank you!

Invoice #: {invoice_number}
Invoice Amount: {symbol}{amount}
Amount Paid: {symbol}{paid_display}
Payment Date: {payment_date}
Payment Method: {payment_method}{outstanding}
{link}
Thank you for your payment!
"""

    @staticmethod
    def _build_reminder_html(
        client_name: str, subject: str, body: str, amount: str, due_date: str
    ) -> str:
        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1f2937;">
            <h2 style="color:#111827;margin-bottom:16px;">Payment Reminder</h2>
            <p>Dear {client_name},</p>
            <p>{body}</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <tr>
                    <td style="padding:8px 0;color:#6b7280;width:140px;"><strong>Amount Due:</strong></td>
                    <td style="padding:8px 0;font-size:18px;font-weight:bold;">${amount}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#6b7280;"><strong>Due Date:</strong></td>
                    <td style="padding:8px 0;">{due_date}</td>
                </tr>
            </table>
            <p>Please contact us if you have any questions.</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
            <p style="color:#9ca3af;font-size:12px;">This is an automated reminder from InvoiceFlow.</p>
        </body>
        </html>
        """

    @staticmethod
    def _build_reminder_text(
        client_name: str, subject: str, body: str, amount: str, due_date: str
    ) -> str:
        return f"""Payment Reminder

Dear {client_name},

{body}

Amount Due: ${amount}
Due Date: {due_date}

Please contact us if you have any questions.
"""
