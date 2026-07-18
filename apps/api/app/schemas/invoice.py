from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvoiceItemCreate(BaseModel):
    description: str
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_price: Annotated[Decimal, Field(ge=0)]


class InvoiceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class InvoiceCreate(BaseModel):
    client_id: UUID
    due_date: date
    description: str | None = None
    amount: Annotated[Decimal, Field(gt=0)] | None = None
    items: list[InvoiceItemCreate] | None = None
    send_now: bool = True

    @model_validator(mode="after")
    def validate_amount_or_items(self) -> Self:
        has_items = self.items is not None and len(self.items) > 0
        has_amount = self.amount is not None

        if has_items and has_amount:
            raise ValueError("Provide either items or amount, not both")
        if not has_items and not has_amount:
            raise ValueError("Either items or amount is required")
        if self.items is not None and len(self.items) == 0:
            raise ValueError("items must contain at least one line when provided")
        return self


class PaymentCreate(BaseModel):
    amount: Annotated[Decimal, Field(gt=0)]
    payment_method: str = "bank_transfer"
    payment_date: date | None = None
    reference: str | None = None
    notes: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference: str | None
    created_at: datetime


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    client_id: UUID | None = None
    client_name: str | None = None
    client_email: str | None = None
    amount: Decimal
    description: str | None = None
    due_date: date | None = None
    status: str
    created_at: datetime | None = None
    invoice_number: str | None = None
    share_token: str | None = None
    paid_amount: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    items: list[InvoiceItemOut] = []


class InvoiceWithPaymentsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    status: str
    paid_amount: Decimal = 0
    payments: list[PaymentOut] = []


class InvoiceListOut(BaseModel):
    items: list[InvoiceOut]
    total: int


class PublicBusinessInfo(BaseModel):
    business_name: str
    business_email: str
    phone: str | None = None
    address: str | None = None
    currency: str = "USD"


class PublicInvoiceOut(BaseModel):
    invoice_number: str | None
    status: str
    description: str | None
    due_date: date
    created_at: datetime | None
    amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    client_name: str
    business: PublicBusinessInfo | None = None
    items: list[InvoiceItemOut] = []
