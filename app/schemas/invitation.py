from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from . import SCHEMA_CONFIG

# Company Invitation Schemas
class CompanyInvitationBase(BaseModel):
    """Base company invitation schema"""
    model_config = SCHEMA_CONFIG
    
    company_id: int = Field(..., alias="companyId")
    email: EmailStr
    role: str = Field(..., pattern="^(admin|manager|operator|viewer)$")
    invited_by: int = Field(..., alias="invitedBy")
    message: Optional[str] = None
    token: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="pending", pattern="^(pending|accepted|declined|expired)$")

class CompanyInvitationCreate(BaseModel):
    """Schema for creating a company invitation"""
    model_config = SCHEMA_CONFIG
    
    company_id: int = Field(..., alias="companyId")
    email: EmailStr
    role: str = Field(..., pattern="^(admin|manager|operator|viewer)$")
    invited_by: int = Field(..., alias="invitedBy")
    message: Optional[str] = None

class CompanyInvitationUpdate(BaseModel):
    """Schema for updating a company invitation"""
    model_config = SCHEMA_CONFIG
    
    status: Optional[str] = Field(None, pattern="^(pending|accepted|declined|expired)$")
    message: Optional[str] = None

class CompanyInvitation(CompanyInvitationBase):
    """Complete company invitation schema"""
    model_config = SCHEMA_CONFIG
    
    id: int
    invited_at: datetime = Field(..., alias="invitedAt")
    expires_at: datetime = Field(..., alias="expiresAt")
    accepted_at: Optional[datetime] = Field(None, alias="acceptedAt")
    accepted_by: Optional[int] = Field(None, alias="acceptedBy")
    declined_at: Optional[datetime] = Field(None, alias="declinedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Invitation with Company Details Schema
class InvitationWithCompany(CompanyInvitation):
    """Company invitation with company and inviter details"""
    model_config = SCHEMA_CONFIG
    
    company_name: str = Field(..., alias="companyName")
    invited_by_name: str = Field(..., alias="invitedByName")

# Invitation Response Schemas
class InvitationResponse(BaseModel):
    """Response schema for invitation actions"""
    model_config = SCHEMA_CONFIG
    
    success: bool
    message: str
    invitation: Optional[CompanyInvitation] = None

# Invitation Stats Schema
class InvitationStats(BaseModel):
    """Invitation statistics schema"""
    model_config = SCHEMA_CONFIG
    
    total: int
    pending: int
    accepted: int
    declined: int
    expired: int
