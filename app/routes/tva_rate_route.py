from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.tva_rate_schema import (
    TvaRate,
    TvaRateCreate,
    TvaRateUpdate,
)
from app.services.tva_rate_service import TvaRateService
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.utils.activity_logger import ActivityActor

router = APIRouter(prefix="/tva-rates", tags=["TVA Rates"])
tva_rate_service = TvaRateService()

@router.get("/", response_model=List[TvaRate])
async def get_all_tva_rates(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get all active TVA rates for the company"""
    return await tva_rate_service.get_all(company_id)

@router.get("/default", response_model=Optional[TvaRate])
async def get_default_tva_rate(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get the default TVA rate for the company"""
    return await tva_rate_service.get_default(company_id)

@router.get("/{rate_id}", response_model=TvaRate)
async def get_tva_rate(
    rate_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get TVA rate by ID"""
    rate = await tva_rate_service.get_by_id(rate_id, company_id)
    if not rate:
        raise HTTPException(status_code=404, detail="TVA rate not found")
    return rate

@router.post("/", response_model=TvaRate)
async def create_tva_rate(
    rate_data: TvaRateCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Create a new TVA rate"""
    # Ensure company_id matches
    if rate_data.company_id != company_id:
        raise HTTPException(status_code=403, detail="Company ID mismatch")
    return await tva_rate_service.create(rate_data, actor=ActivityActor.from_user(current_user))

@router.put("/{rate_id}", response_model=TvaRate)
async def update_tva_rate(
    rate_id: str,
    rate_data: TvaRateUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Update a TVA rate"""
    return await tva_rate_service.update(rate_id, rate_data, company_id, actor=ActivityActor.from_user(current_user))

@router.delete("/{rate_id}", response_model=dict)
async def delete_tva_rate(
    rate_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Delete a TVA rate (soft delete)"""
    success = await tva_rate_service.delete(rate_id, company_id, actor=ActivityActor.from_user(current_user))
    if not success:
        raise HTTPException(status_code=404, detail="TVA rate not found")
    return {"message": "TVA rate deleted successfully"}

@router.patch("/{rate_id}/set-default", response_model=TvaRate)
async def set_default_tva_rate(
    rate_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Set a TVA rate as the default for the company"""
    return await tva_rate_service.set_default(rate_id, company_id, actor=ActivityActor.from_user(current_user))




