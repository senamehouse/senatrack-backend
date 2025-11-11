from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.activity_schema import (
    ActivityLog, ActivityLogCreate, ActivityLogFilters, ActivityLogStats
)
from app.services.activity_service import ActivityService
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User

router = APIRouter(prefix="/activities", tags=["Activity Logs"])
activity_service = ActivityService()

@router.post("/", response_model=dict)
async def create_activity_log(
    activity_data: ActivityLogCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new activity log"""
    activity_id = await activity_service.create_activity_log(activity_data)
    return {"message": "Activity logged successfully", "activity_id": activity_id}

@router.get("/", response_model=List[ActivityLog])
async def get_activity_logs(
    user_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    actions: Optional[str] = Query(None),  # Comma-separated list
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get activity logs with optional filters"""
    # Parse actions if provided
    actions_list = None
    if actions:
        actions_list = [action.strip() for action in actions.split(",")]
    
    filters = ActivityLogFilters(
        user_id=user_id,
        company_id=company_id,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        actions=actions_list,
        limit=limit
    )
    
    return await activity_service.get_activity_logs(filters)

@router.get("/recent", response_model=List[ActivityLog])
async def get_recent_activities(
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get recent activity logs"""
    return await activity_service.get_recent_activities(limit, company_id)

@router.get("/{activity_id}", response_model=ActivityLog)
async def get_activity_log(
    activity_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity log by ID"""
    activity = await activity_service.get_activity_log_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity log not found")
    return activity

@router.get("/stats/overview", response_model=ActivityLogStats)
async def get_activity_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get activity log statistics"""
    return await activity_service.get_activity_stats(company_id)

@router.delete("/cleanup", response_model=dict)
async def cleanup_old_activities(
    days_to_keep: int = Query(90, ge=1, le=365),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete old activity logs (admin function)"""
    deleted_count = await activity_service.delete_old_activities(days_to_keep)
    return {
        "message": f"Deleted {deleted_count} old activity logs",
        "deleted_count": deleted_count
    }

