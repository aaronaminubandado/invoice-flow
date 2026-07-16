from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    email: EmailStr

class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

class ClientResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime
