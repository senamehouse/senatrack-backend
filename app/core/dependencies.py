from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth import AuthService
from app.schemas.user import User

# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Auth service instance
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    return await auth_service.get_current_user(credentials.credentials)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not verified"
        )
    return current_user

# Optional authentication (doesn't raise error if no token)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> User | None:
    """Optional dependency to get current user (returns None if not authenticated)"""
    if not credentials:
        return None
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except HTTPException:
        return None
