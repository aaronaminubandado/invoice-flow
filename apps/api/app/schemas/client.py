from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class ClientResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    created_at: datetime


class ClientListOut(BaseModel):
    items: list[ClientResponse]
    total: int
