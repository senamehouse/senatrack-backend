"""Utility functions for setting HTTP cookies"""
from typing import Optional
from fastapi import Response, Request
from app.core.settings import settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    company_id: Optional[str] = None,
    request: Optional[Request] = None
) -> None:
    """Set authentication cookies (session, refreshToken, and optionally companyId)"""
    # Determine if production based on URL scheme (https = production)
    is_production = False
    if request:
        url = str(request.url)
        is_production = url.startswith("https://")
    
    # For cross-domain cookies (frontend and backend on different domains),
    # we need samesite="none" with secure=True
    # For same-domain cookies, we can use samesite="lax"
    # Since we're on different domains in production, use "none"
    samesite_value = "none" if is_production else "lax"
    
    max_age_session = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    max_age_refresh = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    # Set session cookie
    response.set_cookie(
        key="session",
        value=access_token,
        max_age=max_age_session,
        httponly=True,
        secure=is_production,
        samesite=samesite_value,
        path="/"
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        max_age=max_age_refresh,
        httponly=True,
        secure=is_production,
        samesite=samesite_value,
        path="/"
    )
    
    # Set companyId cookie if provided
    if company_id:
        response.set_cookie(
            key="companyId",
            value=company_id,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            secure=is_production,
            samesite=samesite_value,
            path="/"
        )
