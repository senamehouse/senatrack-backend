from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_current_user, require_company_member, require_company_owner, require_admin_access
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.company_schema import (
    Company, CompanyCreate, CompanyUpdate, CompanyMemberCreate,
    CompanyStats, CompanySettings, CompanySubscription, CompanyPlanUpdate, CompanyAdminUpdate, CompanyMember, CompanyMemberResponse
)
from app.services.company_service import CompanyService
from app.utils.activity_logger import ActivityActor
from app.models.tva_rate_model import TvaRateModel

router = APIRouter(prefix="/companies", tags=["Companies"])
company_service = CompanyService()

@router.post("/", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new company"""
    return await company_service.create_company(company_data.model_copy(update={"owner_id": current_user.id}))

@router.get("/", response_model=List[Company])
async def get_user_companies(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all companies for the current user"""
    return await company_service.get_user_companies(current_user.id)

@router.get("/admin/all", response_model=List[Company], dependencies=[Depends(require_admin_access)])
async def get_all_companies(
    limit: int = Query(100, ge=1, le=5000),
    session: AsyncSession = Depends(get_async_db),
):
    return await company_service.get_all_companies(limit)

@router.post("/{company_id}/subscription", response_model=Company, dependencies=[Depends(require_admin_access)])
async def update_company_subscription(
    company_id: str,
    update_data: CompanyPlanUpdate,
    session: AsyncSession = Depends(get_async_db),
):
    return await company_service.update_company_plan(company_id, update_data.plan)

@router.post("/{company_id}/subscription/cancel", response_model=Company, dependencies=[Depends(require_admin_access)])
async def cancel_company_subscription(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
):
    return await company_service.cancel_company_subscription(company_id)

@router.patch("/{company_id}/admin", response_model=Company, dependencies=[Depends(require_admin_access)])
async def update_company_as_admin(
    company_id: str,
    update_data: CompanyAdminUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await company_service.update_company(
        company_id, CompanyUpdate(name=update_data.name, email=update_data.email),
        actor=ActivityActor.from_user(current_user),
    )

@router.get("/{company_id}/users", response_model=List[User], dependencies=[Depends(require_company_member)])
async def get_company_users(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users who are members of a company"""
    return await company_service.get_company_users(company_id)

@router.get("/{company_id}", response_model=Company, dependencies=[Depends(require_company_member)])
async def get_company(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get a company by ID"""
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}/settings", response_model=Company, dependencies=[Depends(require_company_owner)])
async def update_company_settings(
    company_id: str,
    settings_data: CompanySettings,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the company owner can update settings")

    settings = settings_data.model_dump(by_alias=True)
    tva = settings["tva"]
    if not isinstance(tva, dict) or not isinstance(tva.get("enabled"), bool):
        raise HTTPException(status_code=422, detail="Invalid TVA settings")
    default_rate_id = tva.get("defaultRateId")
    if default_rate_id:
        rate = await session.scalar(select(TvaRateModel).where(
            TvaRateModel.id == default_rate_id,
            TvaRateModel.company_id == company_id,
            TvaRateModel.is_active == True,
        ))
        if rate is None:
            raise HTTPException(status_code=422, detail="Invalid default TVA rate")

    merged_settings = {**(company.settings or {}), **settings}
    return await company_service.update_company(
        company_id=company_id,
        company_data=CompanyUpdate(settings=merged_settings),
        actor=ActivityActor.from_user(current_user),
    )

@router.put("/{company_id}", response_model=Company, dependencies=[Depends(require_company_owner)])
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update a company"""
    if company_data.settings is not None:
        raise HTTPException(status_code=400, detail="Use the settings endpoint to update company settings")
    return await company_service.update_company(company_id=company_id, company_data=company_data, actor=ActivityActor.from_user(current_user))

@router.delete("/{company_id}", dependencies=[Depends(require_company_owner)])
async def delete_company(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a company"""
    success = await company_service.delete_company(company_id=company_id, actor=ActivityActor.from_user(current_user))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete company")
    return {"message": "Company deleted successfully"}

@router.post("/{company_id}/members", response_model=CompanyMemberResponse, dependencies=[Depends(require_company_owner)])
async def add_company_member(
    company_id: str,
    member_data: CompanyMemberCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a company"""
    return await company_service.add_company_member(company_id, member_data)

@router.post("/{company_id}/members/simple", response_model=CompanyMemberResponse, dependencies=[Depends(require_company_owner)])
async def add_company_member_simple(
    company_id: str,
    request_data: dict,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a company (simplified endpoint for frontend)"""
    # Convert frontend format to backend format
    member_data = CompanyMemberCreate(
        user_id=request_data.get("userId"),
        is_active=request_data.get("isActive", True)
    )
    return await company_service.add_company_member(company_id, member_data)

@router.delete("/{company_id}/members/{user_id}", dependencies=[Depends(require_company_owner)])
async def remove_company_member(
    company_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a company"""
    success = await company_service.remove_company_member(company_id, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove member")
    return {"message": "Member removed successfully"}

@router.post("/{company_id}/extend-access", dependencies=[Depends(require_admin_access)])
async def extend_company_access(
    company_id: str,
    days: int = Query(..., gt=0, description="Number of days to extend access"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Extend company access by specified days"""
    success = await company_service.extend_company_access(company_id, days)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to extend access")
    return {"message": f"Access extended by {days} days"}

@router.get("/stats/overview", response_model=CompanyStats, dependencies=[Depends(require_admin_access)])
async def get_company_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get company statistics (admin only)"""
    return await company_service.get_company_stats()
