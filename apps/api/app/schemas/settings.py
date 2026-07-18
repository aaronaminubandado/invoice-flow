from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from uuid import UUID
from datetime import datetime


class BusinessSettingsCreate(BaseModel):
    business_name: str
    business_email: EmailStr
    phone: str | None = None
    address: str | None = None
    currency: str = "USD"
    logo_url: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not (3 <= len(v) <= 5):
            raise ValueError("Currency must be 3-5 characters")
        return v.upper()


class BusinessSettingsUpdate(BaseModel):
    business_name: str | None = None
    business_email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    currency: str | None = None
    logo_url: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None and not (3 <= len(v) <= 5):
            raise ValueError("Currency must be 3-5 characters")
        return v.upper() if v else v


class BusinessSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    business_name: str
    business_email: str
    phone: str | None = None
    address: str | None = None
    currency: str
    logo_url: str | None = None
    created_at: datetime
    updated_at: datetime
