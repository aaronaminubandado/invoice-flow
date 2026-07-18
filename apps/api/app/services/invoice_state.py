from enum import Enum
from typing import Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy import text


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    VOID = "void"


VALID_STATUSES = [s.value for s in InvoiceStatus]

TRANSITIONS = {
    InvoiceStatus.DRAFT: [InvoiceStatus.SENT, InvoiceStatus.CANCELLED],
    InvoiceStatus.SENT: [
        InvoiceStatus.OVERDUE,
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIAL,
        InvoiceStatus.CANCELLED,
    ],
    InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.PARTIAL, InvoiceStatus.CANCELLED],
    InvoiceStatus.PAID: [],
    InvoiceStatus.PARTIAL: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE],
    InvoiceStatus.CANCELLED: [],
    InvoiceStatus.VOID: [],
}


def can_transition(from_status: str, to_status: str) -> bool:
    try:
        from_enum = InvoiceStatus(from_status)
        to_enum = InvoiceStatus(to_status)
    except ValueError:
        return False

    allowed = TRANSITIONS.get(from_enum, [])
    return to_enum in allowed


def get_allowed_transitions(from_status: str) -> list[str]:
    try:
        from_enum = InvoiceStatus(from_status)
    except ValueError:
        return []

    return [s.value for s in TRANSITIONS.get(from_enum, [])]


def validate_transition(from_status: str, to_status: str) -> tuple[bool, Optional[str]]:
    if can_transition(from_status, to_status):
        return True, None

    friendly_messages = {
        ("draft", "paid"): "Draft invoices must be sent before they can be paid.",
        ("draft", "partial"): "Draft invoices must be sent before recording payments.",
        ("draft", "overdue"): "Draft invoices must be sent before they can become overdue.",
        ("sent", "draft"): "Sent invoices cannot be moved back to draft.",
        ("paid", "cancelled"): "Paid invoices cannot be cancelled.",
        ("paid", "sent"): "Paid invoices cannot be changed back to sent.",
        ("paid", "partial"): "Paid invoices cannot be marked as partially paid.",
        ("paid", "overdue"): "Paid invoices cannot be marked as overdue.",
        ("partial", "sent"): "Partially paid invoices cannot be moved back to sent.",
        ("partial", "draft"): "Partially paid invoices cannot be moved back to draft.",
        ("cancelled", "paid"): "Cancelled invoices cannot be marked as paid.",
        ("cancelled", "sent"): "Cancelled invoices cannot be sent again.",
        ("cancelled", "partial"): "Cancelled invoices cannot receive payments.",
        ("void", "paid"): "Void invoices cannot be marked as paid.",
        ("void", "cancelled"): "Void invoices cannot be cancelled.",
    }

    message = friendly_messages.get((from_status, to_status))
    if message:
        return False, message

    if to_status == "paid":
        return False, "This invoice cannot be marked as paid in its current status."
    if to_status == "cancelled":
        return False, "This invoice cannot be cancelled in its current status."

    return False, "This action is not allowed for the current invoice status."


def is_terminal_status(status: str) -> bool:
    return status in [
        InvoiceStatus.PAID.value,
        InvoiceStatus.CANCELLED.value,
        InvoiceStatus.VOID.value,
    ]


def is_cancellable(status: str) -> bool:
    return status in [
        InvoiceStatus.DRAFT.value,
        InvoiceStatus.SENT.value,
        InvoiceStatus.OVERDUE.value,
    ]


def is_payment_allowed(status: str) -> bool:
    return status in [
        InvoiceStatus.SENT.value,
        InvoiceStatus.OVERDUE.value,
        InvoiceStatus.PARTIAL.value,
    ]


OVERDUE_SQL = text("""
    UPDATE invoices
    SET status = 'overdue'
    WHERE status = 'sent'
      AND due_date < CURRENT_DATE
    RETURNING id, status
""")
