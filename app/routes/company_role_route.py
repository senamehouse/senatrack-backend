from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.dependencies import get_current_user, get_company_id
from app.schemas.user_schema import User
from app.schemas.company_role_schema import (
    UserCompanyRole, UserCompanyRoleCreate, UserCompanyRoleUpdate, 
    UserCompanyRoleAssignmentCreate, CompanyPermissionCheck, CompanyPermissionCheckResponse
)
from app.services.company_role_service import CompanyRoleService

router = APIRouter(prefix="/companies", tags=["Company Roles"])
company_role_service = CompanyRoleService()

@router.post("/{company_id}/roles/", response_model=UserCompanyRole, status_code=status.HTTP_201_CREATED)
async def create_company_role(
    company_id: str,
    role_data: UserCompanyRoleCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new company role"""
    # TODO: Add company permission check
    return await company_role_service.create_role(company_id, role_data)

@router.get("/{company_id}/roles/", response_model=List[UserCompanyRole])
async def get_company_roles(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all roles for a company"""
    return await company_role_service.get_company_roles(company_id)

@router.get("/{company_id}/roles/presets", response_model=List[UserCompanyRole])
async def get_company_preset_roles(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get preset roles for a company"""
    roles = await company_role_service.get_company_roles(company_id)
    return [role for role in roles if role.is_preset]

@router.get("/{company_id}/roles/{role_id}", response_model=UserCompanyRole)
async def get_company_role(
    company_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a company role by ID"""
    role = await company_role_service.get_role_by_id(company_id, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{company_id}/roles/{role_id}", response_model=UserCompanyRole)
async def update_company_role(
    company_id: str,
    role_id: str,
    role_data: UserCompanyRoleUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a company role"""
    # TODO: Add company permission check
    return await company_role_service.update_role(company_id, role_id, role_data)

@router.delete("/{company_id}/roles/{role_id}")
async def delete_company_role(
    company_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a company role"""
    # TODO: Add company permission check
    success = await company_role_service.delete_role(company_id, role_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete role")
    return {"message": "Role deleted successfully"}

@router.post("/{company_id}/roles/{role_id}/assign", response_model=dict)
async def assign_company_role_to_user(
    company_id: str,
    role_id: str,
    assignment_data: UserCompanyRoleAssignmentCreate,
    current_user: User = Depends(get_current_user)
):
    """Assign a company role to a user"""
    # TODO: Add company permission check
    assignment = await company_role_service.assign_role_to_user(
        assignment_data.user_id,
        company_id,
        role_id,
        current_user.id
    )
    return {"message": "Role assigned successfully", "assignment_id": assignment.id}

@router.delete("/{company_id}/roles/{role_id}/assign/{user_id}")
async def remove_company_role_from_user(
    company_id: str,
    role_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a company role from a user"""
    # TODO: Add company permission check
    success = await company_role_service.remove_role_from_user(user_id, company_id, role_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove role")
    return {"message": "Role removed successfully"}

@router.get("/{company_id}/users/{user_id}/roles", response_model=List[UserCompanyRole])
async def get_user_company_roles(
    company_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all company roles assigned to a user"""
    return await company_role_service.get_user_company_roles(user_id, company_id)

@router.get("/{company_id}/users/{user_id}/permissions", response_model=List[str])
async def get_user_company_permissions(
    company_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all company permissions for a user"""
    return await company_role_service.get_user_company_permissions(user_id, company_id)

@router.post("/{company_id}/check-permission", response_model=CompanyPermissionCheckResponse)
async def check_company_permission(
    company_id: str,
    permission_data: CompanyPermissionCheck,
    current_user: User = Depends(get_current_user)
):
    """Check if a user has a specific company permission"""
    user_id = permission_data.user_id or current_user.id
    has_permission = await company_role_service.check_permission(user_id, company_id, permission_data.permission)
    
    # Get user company roles for response
    user_roles = await company_role_service.get_user_company_roles(user_id, company_id)
    role_names = [role.name for role in user_roles]
    
    return CompanyPermissionCheckResponse(
        has_permission=has_permission,
        user_id=user_id,
        company_id=company_id,
        permission=permission_data.permission,
        roles=role_names
    )

@router.post("/{company_id}/create-presets", response_model=List[UserCompanyRole])
async def create_company_default_presets(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    """Create default company role presets"""
    # TODO: Add company permission check
    return await company_role_service.create_default_presets(company_id)
