from app.utils.casing import BaseCamelModel
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

# Shared User Schemas
class UserBase(BaseCamelModel):
    """Base user schema with common fields"""
    
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20, alias="phoneNumber")

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseCamelModel):
    """Schema for updating user profile"""
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20, alias="phoneNumber")
    current_company_id: Optional[str] = Field(None, alias="currentCompanyId")

class User(UserBase):
    """Schema for user (public info)"""
    
    id: str
    current_company_id: Optional[str] = Field(None, alias="currentCompanyId")
    is_active: bool = Field(..., alias="isActive")
    is_verified: bool = Field(..., alias="isVerified")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    last_login: Optional[datetime] = Field(None, alias="lastLogin")
    
    # New role system fields
    platform_roles: List[str] = Field(default_factory=list, alias="platformRoles")
    platform_permissions: List[str] = Field(default_factory=list, alias="platformPermissions")

class UserInternal(User):
    """Internal user schema with sensitive fields"""
    hashed_password: str = Field(..., alias="hashedPassword")

# Authentication-specific schemas
class UserRegister(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")

class UserLogin(BaseCamelModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class PasswordChange(BaseCamelModel):
    """Schema for password change"""
    
    current_password: str = Field(..., description="Current password", alias="currentPassword")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)", alias="newPassword")

class PasswordReset(BaseCamelModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="Email address")

class PasswordResetConfirm(BaseCamelModel):
    """Schema for password reset confirmation"""
    
    code: str = Field(..., min_length=6, max_length=6, description="Verification code")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)", alias="newPassword")

class UserProfileResponse(BaseCamelModel):
    """Response schema for user profile endpoint with tokens and company"""
    id: str
    name: str
    email: EmailStr
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    current_company_id: Optional[str] = Field(None, alias="currentCompanyId")
    is_active: bool = Field(..., alias="isActive")
    is_verified: bool = Field(..., alias="isVerified")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    last_login: Optional[datetime] = Field(None, alias="lastLogin")
    platform_roles: List[str] = Field(default_factory=list, alias="platformRoles")
    platform_permissions: List[str] = Field(default_factory=list, alias="platformPermissions")
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    expires_in: int = Field(..., alias="expiresIn")
    current_company: Optional[Dict[str, Any]] = Field(None, alias="currentCompany")

