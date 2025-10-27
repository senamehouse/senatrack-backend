from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import AuthService
from app.services.user_role_service import UserRoleService
from app.services.company_role_service import CompanyRoleService
from app.schemas.user_schema import User
from app.core.settings import settings

# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Auth service instance
auth_service = AuthService()
user_role_service = UserRoleService()
company_role_service = CompanyRoleService()

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

# Company scoping - explicit header dependency for Swagger docs
async def get_company_id(
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id", description="Company ID for tenant scoping")
) -> str:
    """Dependency to get company ID from X-Company-Id header"""
    company_id = x_company_id or settings.COMPANY_ID
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="X-Company-Id header is required"
        )
    return company_id

# Optional company scoping (for endpoints that can work without it)
async def get_company_id_optional(
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id", description="Company ID for tenant scoping")
) -> Optional[str]:
    """Optional dependency to get company ID from X-Company-Id header"""
    return x_company_id or settings.COMPANY_ID

# Permission-based dependencies
async def require_permission(permission: str):
    """Dependency factory for requiring platform permissions"""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        has_permission = await user_role_service.check_permission(current_user.id, permission)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return permission_checker

async def require_company_permission(permission: str):
    """Dependency factory for requiring company permissions"""
    async def company_permission_checker(
        current_user: User = Depends(get_current_user),
        company_id: str = Depends(get_company_id)
    ) -> User:
        has_permission = await company_role_service.check_permission(current_user.id, company_id, permission)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Company permission required: {permission}"
            )
        return current_user
    return company_permission_checker

# Common permission dependencies
async def require_admin_access(current_user: User = Depends(get_current_user)) -> User:
    """Dependency for requiring admin access"""
    has_permission = await user_role_service.check_permission(current_user.id, "admin.access")
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_company_admin(
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
) -> User:
    """Dependency for requiring company admin access"""
    has_permission = await company_role_service.check_permission(current_user.id, company_id, "company.users.manage")
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company admin access required"
        )
    return current_user
