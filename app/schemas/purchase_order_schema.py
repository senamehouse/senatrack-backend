from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class PurchaseOrderBase(BaseCamelModel):

    order_number: str = Field(..., alias="orderNumber")
    supplier_id: Optional[str] = Field(None, alias="supplierId")
    status: str = Field("draft")
    total_amount: float = Field(0.0, ge=0, alias="totalAmount")


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderUpdate(BaseCamelModel):

    order_number: Optional[str] = Field(None, alias="orderNumber")
    supplier_id: Optional[str] = Field(None, alias="supplierId")
    status: Optional[str] = None
    total_amount: Optional[float] = Field(None, ge=0, alias="totalAmount")


class PurchaseOrder(PurchaseOrderBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




