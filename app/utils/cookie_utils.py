"""Utility functions for setting HTTP cookies"""
import logging
from typing import Optional
from fastapi import Response, Request
from app.core.settings import settings

logger = logging.getLogger(__name__)


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
        logger.info(f"Setting cookies - URL scheme: {url.split('://')[0]}, is_production: {is_production}")
    else:
        # Fallback: check if response headers indicate HTTPS
        # This is a best-effort check
        logger.warning("No request object provided, defaulting to secure=False for cookies")
    
    max_age_session = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    max_age_refresh = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    logger.info(f"Setting auth cookies - secure: {is_production}, session_max_age: {max_age_session}, refresh_max_age: {max_age_refresh}")
    
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
    logger.debug(f"Set session cookie - httponly: True, secure: {is_production}, samesite: lax")
    
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
    logger.debug(f"Set refreshToken cookie - httponly: True, secure: {is_production}, samesite: lax")
    
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
        logger.debug(f"Set companyId cookie - value: {company_id}, secure: {is_production}")
    else:
        logger.debug("No companyId provided, skipping companyId cookie")

