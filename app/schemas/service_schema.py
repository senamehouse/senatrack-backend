from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from . import SCHEMA_CONFIG


class ServiceBase(BaseModel):
    model_config = SCHEMA_CONFIG

    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., ge=0)
    description: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    model_config = SCHEMA_CONFIG

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Service(ServiceBase):
    model_config = SCHEMA_CONFIG

    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




