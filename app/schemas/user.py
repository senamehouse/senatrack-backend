from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# Shared User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20, alias="phoneNumber")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20, alias="phoneNumber")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

class User(UserBase):
    """Schema for user (public info)"""
    id: int
    is_active: bool = Field(..., alias="isActive")
    is_verified: bool = Field(..., alias="isVerified")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    last_login: Optional[datetime] = Field(None, alias="lastLogin")

class UserInternal(User):
    """Internal user schema with sensitive fields"""
    hashed_password: str = Field(..., alias="hashedPassword")

# Authentication-specific schemas
class UserRegister(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password", alias="currentPassword")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)", alias="newPassword")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="Email address")

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)", alias="newPassword")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

