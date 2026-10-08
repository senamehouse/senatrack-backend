from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.user_schema import User, UserUpdate, UserAdminUpdate, UserStatusUpdate, UserPlatformRoleUpdate
from app.services.user_service import UserService
from app.core.dependencies import get_current_active_user, require_admin_access, ensure_company_access
from app.core.database import get_async_db
from app.models.user_model import User as UserModel

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()

@router.get("/", response_model=List[User])
async def get_all_users(limit: int = 100, current_user: User = Depends(require_admin_access)):
    """Get all users (platform admin only)"""
    return await user_service.get_all_users(max(1, min(limit, 5000)))

@router.get("/stats")
async def get_user_stats(current_user: User = Depends(require_admin_access)):
    return await user_service.get_user_stats()

@router.get("/count")
async def get_users_count(current_user: User = Depends(require_admin_access)):
    """Get users count (platform admin only)"""
    count = await user_service.get_users_count()
    return {"count": count}

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str, 
    current_user: User = Depends(get_current_active_user)
):
    """Get your own profile or, as an admin, another user."""
    if current_user.id != user_id and "admin.access" not in current_user.platform_permissions:
        raise HTTPException(status_code=403, detail="User access denied")
    user = await user_service.get_user_by_id(user_id, include_inactive="admin.access" in current_user.platform_permissions)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}/admin", response_model=User)
async def update_user_as_admin(
    user_id: str,
    data: UserAdminUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access),
):
    existing_id = await session.scalar(select(UserModel.id).where(
        func.lower(UserModel.email) == data.email.lower(), UserModel.id != user_id,
    ))
    if existing_id:
        raise HTTPException(status_code=409, detail="Email already in use")
    await user_service.update_user(user_id, {"name": data.name, "email": data.email.lower()})
    return await user_service.get_user_by_id(user_id, include_inactive=True)

@router.patch("/{user_id}/status", response_model=User)
async def update_user_status(
    user_id: str,
    data: UserStatusUpdate,
    current_user: User = Depends(require_admin_access),
):
    if user_id == current_user.id and not data.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own admin account")
    return await user_service.set_user_active(user_id, data.is_active)

@router.put("/{user_id}/platform-role", response_model=User)
async def update_user_platform_role(
    user_id: str,
    data: UserPlatformRoleUpdate,
    current_user: User = Depends(require_admin_access),
):
    if user_id == current_user.id and data.role_name != "Platform Administrator":
        raise HTTPException(status_code=400, detail="Cannot remove your own admin access")
    return await user_service.set_platform_role(user_id, data.role_name, current_user.id)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user profile (requires authentication)"""
    # Check if user is updating their own profile or has admin rights
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Not enough permissions to update this user"
        )
    if user_data.current_company_id:
        await ensure_company_access(user_data.current_company_id, current_user, session)
    
    success = await user_service.update_user(user_id, user_data.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user
    updated_user = await user_service.get_user_by_id(user_id)
    return updated_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete user (requires authentication)"""
    # Check if user is deleting their own account or has admin rights
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Not enough permissions to delete this user"
        )
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}
