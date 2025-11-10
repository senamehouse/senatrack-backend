from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class ClientBase(BaseCamelModel):

    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    invoices: Optional[int] = Field(0, ge=0)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseCamelModel):

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    invoices: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = Field(None, alias="isActive")


class Client(ClientBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




