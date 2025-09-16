from fastapi import APIRouter, HTTPException, Depends, status
from app.services.auth import AuthService
from app.schemas.auth import Token, TokenRefresh
from app.schemas.user import (
    UserRegister, UserLogin, PasswordChange, 
    User, UserUpdate
)
from app.core.dependencies import get_current_user, get_current_active_user
from app.schemas.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    return await auth_service.register_user(user_data)

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and get access token"""
    return await auth_service.login_user(login_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token"""
    return await auth_service.refresh_access_token(token_data.refresh_token)

@router.post("/logout")
async def logout(token_data: TokenRefresh):
    """Logout user (revoke refresh token)"""
    return await auth_service.logout_user(token_data.refresh_token)

@router.post("/logout-all")
async def logout_all_sessions(current_user: User = Depends(get_current_user)):
    """Logout user from all sessions"""
    return await auth_service.logout_all_sessions(current_user.id)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    return await auth_service.change_password(current_user.id, password_data)

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return User(**current_user.model_dump())

@router.put("/me", response_model=User)
async def update_current_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    # This would need to be implemented in the user service
    # For now, return the current user
    return User(**current_user.model_dump())
