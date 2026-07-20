from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCategoryCreate(BaseModel):
    name: str
    description: str | None = None


class ProductCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProductCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    created_at: datetime


class ProductCategoryListOut(BaseModel):
    items: list[ProductCategoryOut]
    total: int


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    description: str | None = None
    unit_price: Annotated[Decimal, Field(ge=0)]
    category_id: UUID | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    description: str | None = None
    unit_price: Annotated[Decimal, Field(ge=0)] | None = None
    category_id: UUID | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sku: str | None = None
    description: str | None = None
    unit_price: Decimal
    category_id: UUID | None = None
    category_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
