from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field("bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = Field(None, alias="userId")
    email: Optional[str] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True

class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., alias="refreshToken")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True