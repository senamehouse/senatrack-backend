from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from . import SCHEMA_CONFIG


class ReceptionBase(BaseModel):
    model_config = SCHEMA_CONFIG

    reception_number: str = Field(..., alias="receptionNumber")
    purchase_order_id: Optional[str] = Field(None, alias="purchaseOrderId")
    status: str = Field("pending")


class ReceptionCreate(ReceptionBase):
    pass


class ReceptionUpdate(BaseModel):
    model_config = SCHEMA_CONFIG

    reception_number: Optional[str] = Field(None, alias="receptionNumber")
    purchase_order_id: Optional[str] = Field(None, alias="purchaseOrderId")
    status: Optional[str] = None


class Reception(ReceptionBase):
    model_config = SCHEMA_CONFIG

    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




