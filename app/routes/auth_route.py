from fastapi import APIRouter, HTTPException, Depends, status, Response, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.schemas.auth_schema import Token, TokenRefresh
from app.schemas.user_schema import (
    UserRegister, UserLogin, PasswordChange, 
    User, UserUpdate, UserProfileResponse,
    PasswordReset, PasswordResetConfirm
)
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.database import get_async_db
from app.core.settings import settings
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from typing import Dict, Any, Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_db)
):
    """Register a new user"""
    result = await auth_service.register_user(user_data)
    
    # Set HTTP-only cookies
    set_auth_cookies(
        response=response,
        access_token=result["accessToken"],
        refresh_token=result["refreshToken"],
        company_id=result.get("user", {}).get("currentCompanyId"),
        request=request
    )
    
    return result

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_db)
):
    """Login user and get access token"""
    token_data = await auth_service.login_user(login_data)
    
    # Set HTTP-only cookies
    user = await auth_service.get_current_user(token_data.access_token)
    set_auth_cookies(
        response=response,
        access_token=token_data.access_token,
        refresh_token=token_data.refresh_token,
        company_id=user.current_company_id,
        request=request
    )
    
    return token_data

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    token_data: Optional[TokenRefresh] = Body(default=None),
    session: AsyncSession = Depends(get_async_db)
):
    """Refresh access token using refresh token"""
    refresh_token_value = token_data.refresh_token if token_data else request.cookies.get("refreshToken")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    token = await auth_service.refresh_access_token(refresh_token_value)
    set_auth_cookies(
        response=response,
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        company_id=request.cookies.get("companyId"),
        request=request
    )
    return token

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    return await auth_service.change_password(current_user.id, password_data)

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    request: Request,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> UserProfileResponse:
    """Get current user profile with tokens and company data"""
    # Get tokens from cookies
    access_token = request.cookies.get("session")
    refresh_token = request.cookies.get("refreshToken")
    
    # If no tokens in cookies, this shouldn't happen but handle gracefully
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Get user profile from service
    return await auth_service.get_user_profile(current_user, access_token, refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
):
    """Logout current session by revoking refresh token and clearing cookies"""
    refresh_token_value = request.cookies.get("refreshToken")
    if refresh_token_value:
        await auth_service.logout_user(refresh_token_value)

    clear_auth_cookies(response=response, request=request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/me", response_model=User)
async def update_current_user_profile(
    profile_data: UserUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    from app.services.user_service import UserService
    user_service = UserService()
    return await user_service.update_user(current_user.id, profile_data)

@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    session: AsyncSession = Depends(get_async_db)
):
    """Request password reset"""
    return await auth_service.request_password_reset(password_reset.email)

@router.post("/reset-password")
async def reset_password(
    password_reset_confirm: PasswordResetConfirm,
    session: AsyncSession = Depends(get_async_db)
):
    """Confirm password reset with token"""
    return await auth_service.confirm_password_reset(
        password_reset_confirm.code,
        password_reset_confirm.new_password
    )
