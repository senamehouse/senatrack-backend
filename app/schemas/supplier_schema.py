from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class SupplierBase(BaseCamelModel):

    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = Field(None, alias="postalCode")
    tax_number: Optional[str] = Field(None, alias="taxNumber")
    payment_terms: str = Field("net_30", alias="paymentTerms")
    currency: str = "XOF"
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    is_active: bool = Field(True, alias="isActive")


class SupplierUpdate(BaseCamelModel):

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = Field(None, alias="postalCode")
    tax_number: Optional[str] = Field(None, alias="taxNumber")
    payment_terms: Optional[str] = Field(None, alias="paymentTerms")
    currency: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Supplier(SupplierBase):
    id: str
    supplier_code: str = Field(..., alias="supplierCode")
    date: Optional[datetime] = None
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




