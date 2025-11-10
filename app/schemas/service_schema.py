from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class ServiceBase(BaseCamelModel):

    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., ge=0)
    description: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseCamelModel):

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Service(ServiceBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




