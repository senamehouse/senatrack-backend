from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from . import SCHEMA_CONFIG

# Activation Key Schemas
class ActivationKeyBase(BaseModel):
    """Base activation key schema"""
    model_config = SCHEMA_CONFIG
    
    key: str = Field(..., min_length=1, max_length=255)
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    duration: int = Field(..., gt=0)  # Duration in days
    status: str = Field(default="active", pattern="^(active|used|expired|cancelled)$")
    created_by: int = Field(..., alias="createdBy")
    notes: Optional[str] = None

class ActivationKeyCreate(BaseModel):
    """Schema for creating an activation key"""
    model_config = SCHEMA_CONFIG
    
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    duration: int = Field(..., gt=0)  # Duration in days
    created_by: int = Field(..., alias="createdBy")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    notes: Optional[str] = None

class ActivationKeyUpdate(BaseModel):
    """Schema for updating an activation key"""
    model_config = SCHEMA_CONFIG
    
    status: Optional[str] = Field(None, pattern="^(active|used|expired|cancelled)$")
    notes: Optional[str] = None

class ActivationKey(ActivationKeyBase):
    """Complete activation key schema"""
    model_config = SCHEMA_CONFIG
    
    id: int
    used_by: Optional[int] = Field(None, alias="usedBy")
    used_at: Optional[datetime] = Field(None, alias="usedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Activation Key Usage Schema
class ActivationKeyUsage(BaseModel):
    """Schema for using an activation key"""
    model_config = SCHEMA_CONFIG
    
    key: str = Field(..., min_length=1, max_length=255)
    company_id: int = Field(..., alias="companyId")
    user_id: int = Field(..., alias="userId")

class ActivationKeyUsageResponse(BaseModel):
    """Response schema for activation key usage"""
    model_config = SCHEMA_CONFIG
    
    success: bool
    message: str
    activation_key: Optional[ActivationKey] = Field(None, alias="activationKey")

# Activation Key Stats Schema
class ActivationKeyStats(BaseModel):
    """Activation key statistics schema"""
    model_config = SCHEMA_CONFIG
    
    total: int
    active: int
    used: int
    expired: int
    cancelled: int
