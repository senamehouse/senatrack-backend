from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import User, UserUpdate
from app.services.user_service import UserService
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.database import get_async_db

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()

@router.get("/", response_model=List[User])
async def get_all_users(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all users (requires authentication)"""
    return await user_service.get_all_users()

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID (requires authentication)"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/count")
async def get_users_count(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get users count (requires authentication)"""
    count = await user_service.get_users_count()
    return {"count": count}

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
    
    return await user_service.update_user(user_id, user_data)

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
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
