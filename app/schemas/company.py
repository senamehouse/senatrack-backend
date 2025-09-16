from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from . import SCHEMA_CONFIG

# Company Member Schemas
class CompanyMemberBase(BaseModel):
    """Base company member schema"""
    model_config = SCHEMA_CONFIG
    
    user_id: int = Field(..., alias="userId")
    role: str = Field(..., pattern="^(owner|admin|manager|operator|viewer)$")
    permissions: Optional[List[str]] = None
    invited_by: Optional[int] = Field(None, alias="invitedBy")
    invited_at: Optional[datetime] = Field(None, alias="invitedAt")
    joined_at: Optional[datetime] = Field(None, alias="joinedAt")
    is_active: bool = Field(True, alias="isActive")

class CompanyMemberCreate(CompanyMemberBase):
    """Schema for creating a company member"""
    pass

class CompanyMember(CompanyMemberBase):
    """Complete company member schema"""
    model_config = SCHEMA_CONFIG
    
    id: int
    company_id: int = Field(..., alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Schemas
class CompanyBase(BaseModel):
    """Base company schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255, alias="addressLine1")
    address_line2: Optional[str] = Field(None, max_length=255, alias="addressLine2")
    website: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500, alias="logoUrl")
    currency: str = Field(default="XOF", max_length=10)
    language: str = Field(default="fr", max_length=10)
    timezone: str = Field(default="Africa/Dakar", max_length=50)
    tax_id: Optional[str] = Field(None, max_length=100, alias="taxId")
    registration_number: Optional[str] = Field(None, max_length=100, alias="registrationNumber")

class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    model_config = SCHEMA_CONFIG
    
    owner_id: int = Field(..., alias="ownerId")

class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255, alias="addressLine1")
    address_line2: Optional[str] = Field(None, max_length=255, alias="addressLine2")
    website: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500, alias="logoUrl")
    currency: Optional[str] = Field(None, max_length=10)
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=100, alias="taxId")
    registration_number: Optional[str] = Field(None, max_length=100, alias="registrationNumber")
    settings: Optional[Dict[str, Any]] = None
    subscription: Optional[Dict[str, Any]] = None

class Company(CompanyBase):
    """Complete company schema"""
    model_config = SCHEMA_CONFIG
    
    id: int
    owner_id: int = Field(..., alias="ownerId")
    members: List[CompanyMember] = []
    settings: Optional[Dict[str, Any]] = None
    subscription: Optional[Dict[str, Any]] = None
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Settings Schema
class CompanySettings(BaseModel):
    """Company settings schema"""
    model_config = SCHEMA_CONFIG
    
    modules: Dict[str, bool] = {
        "clients": True,
        "products": True,
        "invoices": True,
        "inventory": True,
        "accounting": False,
        "hr": False,
    }

# Company Subscription Schema
class CompanySubscription(BaseModel):
    """Company subscription schema"""
    model_config = SCHEMA_CONFIG
    
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    access_end_date: str = Field(..., alias="accessEndDate")  # ISO string
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Stats Schema
class CompanyStats(BaseModel):
    """Company statistics schema"""
    model_config = SCHEMA_CONFIG
    
    total: int
    recent_24h: int = Field(..., alias="recent24h")
    active_subscriptions: int = Field(..., alias="activeSubscriptions")
    expired_subscriptions: int = Field(..., alias="expiredSubscriptions")
