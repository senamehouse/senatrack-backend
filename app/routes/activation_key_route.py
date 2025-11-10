from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.activation_key_schema import (
    ActivationKey, ActivationKeyCreate, ActivationKeyUpdate,
    ActivationKeyStats, ActivationKeyUsage, ActivationKeyUsageResponse
)
from app.services.activation_key_service import ActivationKeyService

router = APIRouter(prefix="/activation-keys", tags=["Activation Keys"])
activation_key_service = ActivationKeyService()

@router.post("/", response_model=ActivationKey, status_code=status.HTTP_201_CREATED)
async def create_activation_key(
    key_data: ActivationKeyCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activation key (admin only)"""
    # TODO: Add admin check
    return await activation_key_service.create_activation_key(key_data)

@router.get("/", response_model=List[ActivationKey])
async def get_all_activation_keys(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all activation keys (admin only)"""
    # TODO: Add admin check
    return await activation_key_service.get_all_activation_keys()

@router.get("/{key_id}", response_model=ActivationKey)
async def get_activation_key(
    key_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get an activation key by ID"""
    key = await activation_key_service.get_activation_key_by_id(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Activation key not found")
    return key

@router.get("/key/{key}", response_model=ActivationKey)
async def get_activation_key_by_key(
    key: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get an activation key by key string"""
    activation_key = await activation_key_service.get_activation_key_by_key(key)
    if not activation_key:
        raise HTTPException(status_code=404, detail="Activation key not found")
    return activation_key

@router.put("/{key_id}", response_model=ActivationKey)
async def update_activation_key(
    key_id: str,
    key_data: ActivationKeyUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update an activation key (admin only)"""
    # TODO: Add admin check
    return await activation_key_service.update_activation_key(key_id, key_data)

@router.delete("/{key_id}")
async def delete_activation_key(
    key_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an activation key (admin only)"""
    # TODO: Add admin check
    success = await activation_key_service.delete_activation_key(key_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete activation key")
    return {"message": "Activation key deleted successfully"}

@router.post("/use", response_model=ActivationKeyUsageResponse)
async def use_activation_key(
    usage_data: ActivationKeyUsage,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Use an activation key"""
    result = await activation_key_service.use_activation_key(
        usage_data.key,
        usage_data.company_id,
        usage_data.user_id
    )
    return ActivationKeyUsageResponse(**result)

@router.get("/stats/overview", response_model=ActivationKeyStats)
async def get_activation_key_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get activation key statistics (admin only)"""
    # TODO: Add admin check
    return await activation_key_service.get_activation_key_stats()
