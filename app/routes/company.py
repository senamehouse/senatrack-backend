from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.company import (
    Company, CompanyCreate, CompanyUpdate, CompanyMemberCreate,
    CompanyStats, CompanySettings, CompanySubscription
)
from app.services.company import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])
company_service = CompanyService()

@router.post("/", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new company"""
    return await company_service.create_company(company_data)

@router.get("/", response_model=List[Company])
async def get_user_companies(
    current_user: User = Depends(get_current_user)
):
    """Get all companies for the current user"""
    return await company_service.get_user_companies(current_user.id)

@router.get("/{company_id}", response_model=Company)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get a company by ID"""
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=Company)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a company"""
    return await company_service.update_company(company_id, company_data)

@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a company"""
    success = await company_service.delete_company(company_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete company")
    return {"message": "Company deleted successfully"}

@router.post("/{company_id}/members", response_model=dict)
async def add_company_member(
    company_id: int,
    member_data: CompanyMemberCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a member to a company"""
    member = await company_service.add_company_member(company_id, member_data)
    return {"message": "Member added successfully", "member": member.to_dict()}

@router.delete("/{company_id}/members/{user_id}")
async def remove_company_member(
    company_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a company"""
    success = await company_service.remove_company_member(company_id, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove member")
    return {"message": "Member removed successfully"}

@router.post("/{company_id}/extend-access")
async def extend_company_access(
    company_id: int,
    days: int = Query(..., gt=0, description="Number of days to extend access"),
    current_user: User = Depends(get_current_user)
):
    """Extend company access by specified days"""
    success = await company_service.extend_company_access(company_id, days)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to extend access")
    return {"message": f"Access extended by {days} days"}

@router.get("/stats/overview", response_model=CompanyStats)
async def get_company_stats(
    current_user: User = Depends(get_current_user)
):
    """Get company statistics (admin only)"""
    # TODO: Add admin check
    return await company_service.get_company_stats()
