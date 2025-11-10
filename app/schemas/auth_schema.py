from app.utils.casing import BaseCamelModel
from pydantic import Field
from typing import Optional

class Token(BaseCamelModel):
    """Schema for authentication tokens"""
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field("bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn")

class TokenData(BaseCamelModel):
    """Schema for token payload data"""
    user_id: Optional[str] = Field(None, alias="userId")
    email: Optional[str] = None

class TokenRefresh(BaseCamelModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., alias="refreshToken")