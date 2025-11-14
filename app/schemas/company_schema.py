from app.utils.casing import BaseCamelModel
from pydantic import Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Company Member Schemas
class CompanyMemberBase(BaseCamelModel):
    """Base company member schema"""
    
    user_id: str = Field(..., alias="userId")
    invited_by: Optional[str] = Field(None, alias="invitedBy")
    invited_at: Optional[datetime] = Field(None, alias="invitedAt")
    joined_at: Optional[datetime] = Field(None, alias="joinedAt")
    is_active: bool = Field(True, alias="isActive")
    
    # New role system fields
    company_roles: List[str] = Field(default_factory=list, alias="companyRoles")
    company_permissions: List[str] = Field(default_factory=list, alias="companyPermissions")

class CompanyMemberCreate(CompanyMemberBase):
    """Schema for creating a company member"""
    user_id: str = Field(..., alias="userId")
    invited_by: Optional[str] = Field(None, alias="invitedBy")
    invited_at: Optional[datetime] = Field(None, alias="invitedAt")
    joined_at: Optional[datetime] = Field(None, alias="joinedAt")
    is_active: bool = Field(True, alias="isActive")

class CompanyMember(CompanyMemberBase):
    """Complete company member schema"""
    
    id: str
    company_id: str = Field(..., alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Schemas
class CompanyBase(BaseCamelModel):
    """Base company schema"""
    
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
    
    owner_id: str = Field(..., alias="ownerId")

class CompanyUpdate(BaseCamelModel):
    """Schema for updating a company"""
    
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
    
    id: str
    owner_id: str = Field(..., alias="ownerId")
    members: List[CompanyMember] = []
    settings: Optional[Dict[str, Any]] = None
    subscription: Optional[Dict[str, Any]] = None
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Settings Schema
class CompanySettings(BaseCamelModel):
    """Company settings schema"""
    
    modules: Dict[str, bool] = {
        "clients": True,
        "products": True,
        "invoices": True,
        "inventory": True,
        "accounting": False,
        "hr": False,
    }
    tva: Dict[str, Any] = {
        "enabled": False,
        "defaultRateId": None,
    }

# Company Subscription Schema
class CompanySubscription(BaseCamelModel):
    """Company subscription schema"""
    
    plan: str = Field(..., pattern="^(free_trial|basic|premium|enterprise)$")
    access_end_date: str = Field(..., alias="accessEndDate")  # ISO string
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Company Stats Schema
class CompanyStats(BaseCamelModel):
    """Company statistics schema"""
    
    total: int
    recent_24h: int = Field(..., alias="recent24h")
    active_subscriptions: int = Field(..., alias="activeSubscriptions")
    expired_subscriptions: int = Field(..., alias="expiredSubscriptions")

# Company Member Response Schema
class CompanyMemberResponse(BaseCamelModel):
    """Response schema for company member operations"""
    message: str
    member: CompanyMember
