from app.utils.casing import BaseCamelModel
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime

# Company Invitation Schemas
class CompanyInvitationBase(BaseCamelModel):
    """Base company invitation schema"""
    
    company_id: str = Field(..., alias="companyId")
    email: EmailStr
    role: str = Field(..., pattern="^(admin|manager|operator|viewer)$")
    invited_by: int = Field(..., alias="invitedBy")
    message: Optional[str] = None
    token: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="pending", pattern="^(pending|accepted|declined|expired)$")

class CompanyInvitationCreate(BaseCamelModel):
    """Schema for creating a company invitation"""
    
    company_id: str = Field(..., alias="companyId")
    email: EmailStr
    role: str = Field(..., pattern="^(admin|manager|operator|viewer)$")
    invited_by: int = Field(..., alias="invitedBy")
    message: Optional[str] = None

class CompanyInvitationUpdate(BaseCamelModel):
    """Schema for updating a company invitation"""
    
    status: Optional[str] = Field(None, pattern="^(pending|accepted|declined|expired)$")
    message: Optional[str] = None

class CompanyInvitation(CompanyInvitationBase):
    """Complete company invitation schema"""
    
    id: str
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
    
    company_name: str = Field(..., alias="companyName")
    invited_by_name: str = Field(..., alias="invitedByName")

# Invitation Response Schemas
class InvitationResponse(BaseCamelModel):
    """Response schema for invitation actions"""
    
    success: bool
    message: str
    invitation: Optional[CompanyInvitation] = None

class InvitationCancelResponse(BaseCamelModel):
    """Response schema for canceling invitation"""
    message: str

# Invitation Stats Schema
class InvitationStats(BaseCamelModel):
    """Invitation statistics schema"""
    
    total: int
    pending: int
    accepted: int
    declined: int
    expired: int
