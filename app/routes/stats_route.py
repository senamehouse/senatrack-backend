from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.stats_schema import DashboardStats
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Stats"])
svc = StatsService()


@router.get("/", response_model=DashboardStats)
async def get_stats(
    time_range: Optional[str] = "7d",
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id),
):
    return await svc.get_dashboard_stats(company_id, time_range or "7d")


