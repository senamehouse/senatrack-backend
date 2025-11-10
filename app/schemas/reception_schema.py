from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class ReceptionBase(BaseCamelModel):

    reception_number: str = Field(..., alias="receptionNumber")
    purchase_order_id: Optional[str] = Field(None, alias="purchaseOrderId")
    status: str = Field("pending")


class ReceptionCreate(ReceptionBase):
    pass


class ReceptionUpdate(BaseCamelModel):

    reception_number: Optional[str] = Field(None, alias="receptionNumber")
    purchase_order_id: Optional[str] = Field(None, alias="purchaseOrderId")
    status: Optional[str] = None


class Reception(ReceptionBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




