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
    cookie_domain = None  # Default to None (current domain only)
    
    if request:
        url = str(request.url)
        is_production = url.startswith("https://")
        
        # Extract domain for cross-subdomain cookie sharing
        # For production (api.senatrack.app), set domain to .senatrack.app
        if is_production:
            host = request.headers.get("host", "")
            if "senatrack.app" in host:
                # Set domain to parent domain so cookies work across subdomains
                cookie_domain = ".senatrack.app"
    
    # For cross-domain cookies (frontend and backend on different domains),
    # we need samesite="none" with secure=True
    # For same-domain cookies, we can use samesite="lax"
    # Since we're on different domains in production, use "none"
    samesite_value = "none" if is_production else "lax"
    secure_value = is_production
    
    max_age_session = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    max_age_refresh = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    # Set session cookie
    cookie_kwargs = {
        "key": "session",
        "value": access_token,
        "max_age": max_age_session,
        "httponly": True,
        "secure": secure_value,
        "samesite": samesite_value,
        "path": "/"
    }
    if cookie_domain:
        cookie_kwargs["domain"] = cookie_domain
    response.set_cookie(**cookie_kwargs)
    
    # Set refresh token cookie
    cookie_kwargs = {
        "key": "refreshToken",
        "value": refresh_token,
        "max_age": max_age_refresh,
        "httponly": True,
        "secure": secure_value,
        "samesite": samesite_value,
        "path": "/"
    }
    if cookie_domain:
        cookie_kwargs["domain"] = cookie_domain
    response.set_cookie(**cookie_kwargs)
    
    # Set companyId cookie if provided
    if company_id:
        cookie_kwargs = {
            "key": "companyId",
            "value": company_id,
            "max_age": 365 * 24 * 60 * 60,  # 1 year
            "httponly": True,
            "secure": secure_value,
            "samesite": samesite_value,
            "path": "/"
        }
        if cookie_domain:
            cookie_kwargs["domain"] = cookie_domain
        response.set_cookie(**cookie_kwargs)


def clear_auth_cookies(
    response: Response,
    request: Optional[Request] = None,
) -> None:
    """Clear authentication cookies (session, refreshToken, companyId)."""
    is_production = False
    cookie_domain = None

    if request:
        url = str(request.url)
        is_production = url.startswith("https://")
        host = request.headers.get("host", "")
        if is_production and "senatrack.app" in host:
            cookie_domain = ".senatrack.app"

    samesite_value = "none" if is_production else "lax"
    secure_value = is_production

    for key in ["session", "refreshToken", "companyId"]:
        cookie_kwargs = {
            "key": key,
            "value": "",
            "max_age": 0,
            "httponly": True,
            "secure": secure_value,
            "samesite": samesite_value,
            "path": "/",
        }
        if cookie_domain:
            cookie_kwargs["domain"] = cookie_domain
        response.set_cookie(**cookie_kwargs)
