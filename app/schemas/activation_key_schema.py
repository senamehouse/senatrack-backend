from app.utils.casing import BaseCamelModel
from pydantic import Field
from typing import Optional
from datetime import datetime

# Activation Key Schemas
class ActivationKeyBase(BaseCamelModel):
    """Base activation key schema"""
    
    key: str = Field(..., min_length=1, max_length=255)
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    duration: int = Field(..., gt=0)  # Duration in days
    status: str = Field(default="active", pattern="^(active|used|expired|cancelled)$")
    created_by: str = Field(..., alias="createdBy")
    notes: Optional[str] = None

class ActivationKeyCreate(BaseCamelModel):
    """Schema for creating an activation key"""
    
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    duration: int = Field(..., gt=0)  # Duration in days
    created_by: str = Field(..., alias="createdBy")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    notes: Optional[str] = None

class ActivationKeyUpdate(BaseCamelModel):
    """Schema for updating an activation key"""
    
    status: Optional[str] = Field(None, pattern="^(active|used|expired|cancelled)$")
    notes: Optional[str] = None

class ActivationKey(ActivationKeyBase):
    """Complete activation key schema"""
    
    id: str
    used_by: Optional[str] = Field(None, alias="usedBy")
    used_at: Optional[datetime] = Field(None, alias="usedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Activation Key Usage Schema
class ActivationKeyUsage(BaseCamelModel):
    """Schema for using an activation key"""
    
    key: str = Field(..., min_length=1, max_length=255)
    company_id: str = Field(..., alias="companyId")
    user_id: str = Field(..., alias="userId")

class ActivationKeyUsageResponse(BaseCamelModel):
    """Response schema for activation key usage"""
    
    success: bool
    message: str
    activation_key: Optional[ActivationKey] = Field(None, alias="activationKey")

# Activation Key Stats Schema
class ActivationKeyStats(BaseCamelModel):
    """Activation key statistics schema"""
    
    total: int
    active: int
    used: int
    expired: int
    cancelled: int
