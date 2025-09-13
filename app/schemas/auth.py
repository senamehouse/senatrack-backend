from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None

class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str