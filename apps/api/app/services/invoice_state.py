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
    InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.PARTIAL],
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
    if not can_transition(from_status, to_status):
        allowed = get_allowed_transitions(from_status)
        if allowed:
            return (
                False,
                f"Invalid transition from '{from_status}' to '{to_status}'. Allowed: {allowed}",
            )
        return (
            False,
            f"Invalid transition from '{from_status}' to '{to_status}'. No transitions allowed from '{from_status}'.",
        )
    return True, None


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
