from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    amount: Annotated[Decimal, Field(gt=0)]
    client_id: UUID
    due_date: date
    description: str | None = None


class PaymentCreate(BaseModel):
    amount: Annotated[Decimal, Field(gt=0)]
    payment_method: str = "bank_transfer"
    payment_date: date | None = None
    reference: str | None = None
    notes: str | None = None


class PaymentOut(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: UUID
    user_id: UUID | None = None
    client_id: UUID | None = None
    amount: Decimal
    description: str | None = None
    due_date: date | None = None
    status: str
    created_at: datetime | None = None
    invoice_number: str | None = None

    class Config:
        from_attributes = True


class InvoiceWithPaymentsOut(BaseModel):
    id: UUID
    amount: Decimal
    status: str
    paid_amount: Decimal = 0
    payments: list[PaymentOut] = []

    class Config:
        from_attributes = True
