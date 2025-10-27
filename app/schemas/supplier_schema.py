from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from . import SCHEMA_CONFIG


class SupplierBase(BaseModel):
    model_config = SCHEMA_CONFIG

    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    model_config = SCHEMA_CONFIG

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Supplier(SupplierBase):
    model_config = SCHEMA_CONFIG

    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




