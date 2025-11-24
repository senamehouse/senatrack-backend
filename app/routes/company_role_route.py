from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.company_role_schema import (
    UserCompanyRole, UserCompanyRoleCreate, UserCompanyRoleUpdate, 
    UserCompanyRoleAssignmentCreate, CompanyPermissionCheck, CompanyPermissionCheckResponse,
    CompanyRoleDeleteResponse, CompanyRoleAssignResponse, CompanyRoleRemoveResponse
)
from app.services.company_service import CompanyService
from app.utils.activity_logger import ActivityActor

router = APIRouter(prefix="/companies", tags=["Company Roles"])
company_service = CompanyService()

@router.post("/{company_id}/roles/", response_model=UserCompanyRole, status_code=status.HTTP_201_CREATED)
async def create_company_role(
    company_id: str,
    role_data: UserCompanyRoleCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new company role"""
    # TODO: Add company permission check
    return await company_service.create_company_role(company_id=company_id, role_data=role_data, actor=ActivityActor.from_user(current_user))

@router.get("/{company_id}/roles/", response_model=List[UserCompanyRole])
async def get_company_roles(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles for a company"""
    return await company_service.get_company_roles(company_id)

@router.get("/{company_id}/roles/presets", response_model=List[UserCompanyRole])
async def get_company_preset_roles(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get preset roles for a company"""
    return await company_service.get_company_preset_roles(company_id)

@router.get("/{company_id}/roles/{role_id}", response_model=UserCompanyRole)
async def get_company_role(
    company_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get a company role by ID"""
    role = await company_service.get_company_role_by_id(company_id, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{company_id}/roles/{role_id}", response_model=UserCompanyRole)
async def update_company_role(
    company_id: str,
    role_id: str,
    role_data: UserCompanyRoleUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update a company role"""
    # TODO: Add company permission check
    return await company_service.update_company_role(company_id=company_id, role_id=role_id, role_data=role_data, actor=ActivityActor.from_user(current_user))

@router.delete("/{company_id}/roles/{role_id}", response_model=CompanyRoleDeleteResponse)
async def delete_company_role(
    company_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a company role"""
    # TODO: Add company permission check
    return await company_service.delete_company_role(company_id=company_id, role_id=role_id, actor=ActivityActor.from_user(current_user))

@router.post("/{company_id}/roles/{role_id}/assign", response_model=CompanyRoleAssignResponse)
async def assign_company_role_to_user(
    company_id: str,
    role_id: str,
    assignment_data: UserCompanyRoleAssignmentCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a company role to a user"""
    # TODO: Add company permission check
    return await company_service.assign_company_role_to_user(user_id=assignment_data.user_id, company_id=company_id, role_id=role_id, assigned_by=current_user.id, actor=ActivityActor.from_user(current_user))

@router.delete("/{company_id}/roles/{role_id}/assign/{user_id}", response_model=CompanyRoleRemoveResponse)
async def remove_company_role_from_user(
    company_id: str,
    role_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a company role from a user"""
    # TODO: Add company permission check
    return await company_service.remove_company_role_from_user(user_id=user_id, company_id=company_id, role_id=role_id, actor=ActivityActor.from_user(current_user))

@router.get("/{company_id}/users/{user_id}/roles", response_model=List[UserCompanyRole])
async def get_user_company_roles(
    company_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all company roles assigned to a user"""
    return await company_service.get_user_company_roles(user_id, company_id)

@router.get("/{company_id}/users/{user_id}/permissions", response_model=List[str])
async def get_user_company_permissions(
    company_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all company permissions for a user"""
    return await company_service.get_user_company_permissions(user_id, company_id)

@router.post("/{company_id}/check-permission", response_model=CompanyPermissionCheckResponse)
async def check_company_permission(
    company_id: str,
    permission_data: CompanyPermissionCheck,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a user has a specific company permission"""
    user_id = permission_data.user_id or current_user.id
    return await company_service.check_company_permission_with_response(
        user_id, company_id, permission_data.permission
    )

@router.post("/{company_id}/create-presets", response_model=List[UserCompanyRole])
async def create_company_default_presets(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create default company role presets"""
    # TODO: Add company permission check
    return await company_service.create_company_default_presets(company_id)

