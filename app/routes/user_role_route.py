from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.user_role_schema import (
    UserRole, UserRoleCreate, UserRoleUpdate, UserRoleAssignmentCreate,
    PermissionCheck, PermissionCheckResponse
)
from app.services.user_role_service import UserRoleService

router = APIRouter(prefix="/user-roles", tags=["User Roles"])
user_role_service = UserRoleService()

@router.post("/", response_model=UserRole, status_code=status.HTTP_201_CREATED)
async def create_user_role(
    role_data: UserRoleCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new platform role (admin only)"""
    # TODO: Add admin permission check
    return await user_role_service.create_role(role_data)

@router.get("/", response_model=List[UserRole])
async def get_all_user_roles(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all platform roles"""
    return await user_role_service.get_all_roles()

@router.get("/presets", response_model=List[UserRole])
async def get_preset_roles(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get preset platform roles"""
    roles = await user_role_service.get_all_roles()
    return [role for role in roles if role.is_preset]

@router.get("/{role_id}", response_model=UserRole)
async def get_user_role(
    role_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get a platform role by ID"""
    role = await user_role_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=UserRole)
async def update_user_role(
    role_id: str,
    role_data: UserRoleUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update a platform role (admin only)"""
    # TODO: Add admin permission check
    return await user_role_service.update_role(role_id, role_data)

@router.delete("/{role_id}")
async def delete_user_role(
    role_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a platform role (admin only)"""
    # TODO: Add admin permission check
    success = await user_role_service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete role")
    return {"message": "Role deleted successfully"}

@router.post("/{role_id}/assign", response_model=dict)
async def assign_role_to_user(
    role_id: str,
    assignment_data: UserRoleAssignmentCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a platform role to a user (admin only)"""
    # TODO: Add admin permission check
    assignment = await user_role_service.assign_role_to_user(
        assignment_data.user_id,
        role_id,
        current_user.id
    )
    return {"message": "Role assigned successfully", "assignment_id": assignment.id}

@router.delete("/{role_id}/assign/{user_id}")
async def remove_role_from_user(
    role_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a platform role from a user (admin only)"""
    # TODO: Add admin permission check
    success = await user_role_service.remove_role_from_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove role")
    return {"message": "Role removed successfully"}

@router.get("/user/{user_id}/roles", response_model=List[UserRole])
async def get_user_roles(
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles assigned to a user"""
    return await user_role_service.get_user_roles(user_id)

@router.get("/user/{user_id}/permissions", response_model=List[str])
async def get_user_permissions(
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions for a user"""
    return await user_role_service.get_user_permissions(user_id)

@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    permission_data: PermissionCheck,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a user has a specific permission"""
    user_id = permission_data.user_id or current_user.id
    has_permission = await user_role_service.check_permission(user_id, permission_data.permission)
    
    # Get user roles for response
    user_roles = await user_role_service.get_user_roles(user_id)
    role_names = [role.name for role in user_roles]
    
    return PermissionCheckResponse(
        has_permission=has_permission,
        user_id=user_id,
        permission=permission_data.permission,
        roles=role_names
    )

@router.post("/create-presets", response_model=List[UserRole])
async def create_default_presets(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create default platform role presets (admin only)"""
    # TODO: Add admin permission check
    return await user_role_service.create_default_presets()

