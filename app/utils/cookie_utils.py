"""Utility functions for setting HTTP cookies"""
import os
from typing import Optional
from fastapi import Response
from app.core.settings import settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    company_id: Optional[str] = None
) -> None:
    """Set authentication cookies (session, refreshToken, and optionally companyId)"""
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    max_age_session = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    max_age_refresh = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    # Set session cookie
    response.set_cookie(
        key="session",
        value=access_token,
        max_age=max_age_session,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/"
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        max_age=max_age_refresh,
        httponly=True,
        secure=is_production,
        samesite="lax",
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
            samesite="lax",
            path="/"
        )

