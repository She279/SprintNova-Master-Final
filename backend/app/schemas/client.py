from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class ClientCreateRequest(BaseModel):
    name: str
    company_name: str | None = None
    contact_email: EmailStr
    contact_phone: str | None = None
    notes: str | None = None


class ClientUpdateRequest(BaseModel):
    name: str | None = None
    company_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    notes: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_name: str | None
    contact_email: EmailStr
    contact_phone: str | None
    notes: str | None
    created_at: datetime
