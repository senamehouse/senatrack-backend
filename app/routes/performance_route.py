from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.performance_schema import PerformanceReview, PerformanceReviewCreate, PerformanceReviewUpdate
from app.services.performance_service import PerformanceService


router = APIRouter(prefix="/performance-reviews", tags=["Performance Reviews"])
svc = PerformanceService()


@router.get("/", response_model=List[PerformanceReview])
async def get_reviews(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/{review_id}", response_model=PerformanceReview)
async def get_review(
    review_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    row = await svc.get_by_id(review_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return row


@router.post("/", response_model=dict)
async def create_review(
    payload: PerformanceReviewCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    review_id = await svc.create(company_id, payload)
    return {"message": "Performance review created", "review_id": review_id}


@router.put("/{review_id}", response_model=dict)
async def update_review(
    review_id: str,
    payload: PerformanceReviewUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(review_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return {"message": "Performance review updated"}


@router.delete("/{review_id}", response_model=dict)
async def delete_review(
    review_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(review_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return {"message": "Performance review deleted"}

@router.get("/stats", response_model=dict)
async def get_performance_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_stats(company_id)