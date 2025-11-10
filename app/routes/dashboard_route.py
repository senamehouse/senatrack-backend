from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.dashboard_schema import DashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id),
    start_date: Optional[datetime] = Query(None, description="Start date for date range filter"),
    end_date: Optional[datetime] = Query(None, description="End date for date range filter"),
    time_range: Optional[str] = Query(None, description="Time range: '7d', '30d', '90d' (overrides start_date/end_date)")
):
    """Get aggregated dashboard statistics with optional date range"""
    return await dashboard_service.get_dashboard_stats(company_id, start_date, end_date, time_range)

