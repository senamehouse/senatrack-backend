from app.utils.casing import BaseCamelModel
from pydantic import Field
from typing import Optional
from datetime import datetime


class TvaRateBase(BaseCamelModel):
    """Base TVA rate schema"""
    
    name: str = Field(..., min_length=1, max_length=100)
    rate: float = Field(..., ge=0, le=100, description="TVA rate percentage (0-100)")
    is_default: bool = Field(default=False, alias="isDefault")
    is_active: bool = Field(default=True, alias="isActive")


class TvaRateCreate(TvaRateBase):
    """Schema for creating a TVA rate"""
    
    company_id: str = Field(..., alias="companyId")
    name: str = Field(..., min_length=1, max_length=100)
    rate: float = Field(..., ge=0, le=100)
    is_default: bool = Field(default=False, alias="isDefault")
    is_active: bool = Field(default=True, alias="isActive")


class TvaRateUpdate(BaseCamelModel):
    """Schema for updating a TVA rate"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[float] = Field(None, ge=0, le=100)
    is_default: Optional[bool] = Field(None, alias="isDefault")
    is_active: Optional[bool] = Field(None, alias="isActive")


class TvaRate(TvaRateBase):
    """Complete TVA rate schema"""
    
    id: str
    company_id: str = Field(..., alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")



