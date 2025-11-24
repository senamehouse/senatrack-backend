import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func, and_, desc
from app.core.database import get_db_session
from app.models.activity_model import ActivityLog as ActivityLogModel
from app.models.sync_model import SyncLog
from app.schemas.activity_schema import ActivityLogCreate, ActivityLog as ActivityLogSchema, ActivityLogFilters, ActivityLogStats


class ActivityService:
    """Service for activity log-related database operations"""

    async def create_activity_log(self, activity_data: ActivityLogCreate) -> str:
        """Create a new activity log and return the ID"""
        try:
            session = get_db_session()
            activity = ActivityLogModel(
                action=activity_data.action,
                details=activity_data.details,
                user_id=activity_data.user_id,
                user_email=activity_data.user_email,
                user_name=activity_data.user_name,
                company_id=activity_data.company_id,
                entity_type=activity_data.entity_type,
                entity_id=activity_data.entity_id,
                extra_data=activity_data.extra_data
            )
            session.add(activity)
            await session.commit()
            await session.refresh(activity)

            # Log sync operation
            sync_log = SyncLog(
                operation='CREATE',
                table_name='activity_logs',
                record_id=activity.id,
                data=json.dumps(activity.to_dict())
            )
            session.add(sync_log)
            await session.commit()

            return activity.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating activity log: {str(e)}")

    async def get_activity_logs(self, filters: ActivityLogFilters) -> List[ActivityLogSchema]:
        """Get activity logs with filters"""
        try:
            session = get_db_session()
            query = select(ActivityLogModel)

            # Apply filters
            if filters.user_id:
                query = query.where(ActivityLogModel.user_id == filters.user_id)
            if filters.company_id:
                query = query.where(ActivityLogModel.company_id == filters.company_id)
            if filters.entity_type:
                query = query.where(ActivityLogModel.entity_type == filters.entity_type)
            if filters.entity_id:
                query = query.where(ActivityLogModel.entity_id == filters.entity_id)
            if filters.start_date:
                query = query.where(ActivityLogModel.created_at >= filters.start_date)
            if filters.end_date:
                query = query.where(ActivityLogModel.created_at <= filters.end_date)
            if filters.actions:
                query = query.where(ActivityLogModel.action.in_(filters.actions))

            # Order by created_at descending and apply limit
            query = query.order_by(desc(ActivityLogModel.created_at))
            if filters.limit:
                query = query.limit(filters.limit)

            result = await session.execute(query)
            activities = result.scalars().all()
            return [ActivityLogSchema(**activity.to_dict()) for activity in activities]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving activity logs: {str(e)}")

    async def get_recent_activities(self, limit: int = 50, company_id: Optional[str] = None) -> List[ActivityLogSchema]:
        """Get recent activity logs"""
        filters = ActivityLogFilters(limit=limit, company_id=company_id)
        return await self.get_activity_logs(filters)

    async def get_activity_log_by_id(self, activity_id: str) -> Optional[ActivityLogSchema]:
        """Get an activity log by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(ActivityLogModel).where(ActivityLogModel.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            return ActivityLogSchema(**activity.to_dict()) if activity else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving activity log: {str(e)}")

    async def get_activity_stats(self, company_id: Optional[str] = None) -> ActivityLogStats:
        """Get activity log statistics"""
        try:
            session = get_db_session()
            base_query = select(ActivityLogModel)
            if company_id:
                base_query = base_query.where(ActivityLogModel.company_id == company_id)

            # Total count
            total_result = await session.execute(
                select(func.count(ActivityLogModel.id)).select_from(base_query.subquery())
            )
            total = total_result.scalar()

            # Today's count
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_result = await session.execute(
                select(func.count(ActivityLogModel.id))
                .where(and_(
                    ActivityLogModel.created_at >= today_start,
                    ActivityLogModel.company_id == company_id if company_id else True
                ))
            )
            today_count = today_result.scalar()

            # This week's count
            week_start = today_start - timedelta(days=today.weekday())
            week_result = await session.execute(
                select(func.count(ActivityLogModel.id))
                .where(and_(
                    ActivityLogModel.created_at >= week_start,
                    ActivityLogModel.company_id == company_id if company_id else True
                ))
            )
            week_count = week_result.scalar()

            # This month's count
            month_start = datetime.combine(today.replace(day=1), datetime.min.time())
            month_result = await session.execute(
                select(func.count(ActivityLogModel.id))
                .where(and_(
                    ActivityLogModel.created_at >= month_start,
                    ActivityLogModel.company_id == company_id if company_id else True
                ))
            )
            month_count = month_result.scalar()

            # By action
            action_result = await session.execute(
                select(ActivityLogModel.action, func.count(ActivityLogModel.id))
                .where(ActivityLogModel.company_id == company_id if company_id else True)
                .group_by(ActivityLogModel.action)
            )
            by_action = {row[0]: row[1] for row in action_result.fetchall()}

            # By user
            user_result = await session.execute(
                select(ActivityLogModel.user_email, func.count(ActivityLogModel.id))
                .where(and_(
                    ActivityLogModel.user_email.isnot(None),
                    ActivityLogModel.company_id == company_id if company_id else True
                ))
                .group_by(ActivityLogModel.user_email)
            )
            by_user = {row[0]: row[1] for row in user_result.fetchall()}

            return ActivityLogStats(
                total=total,
                today=today_count,
                this_week=week_count,
                this_month=month_count,
                by_action=by_action,
                by_user=by_user
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting activity stats: {str(e)}")

    async def delete_old_activities(self, days_to_keep: int = 90) -> int:
        """Delete activity logs older than specified days"""
        try:
            session = get_db_session()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Get activities to delete
            result = await session.execute(
                select(ActivityLogModel).where(ActivityLogModel.created_at < cutoff_date)
            )
            activities_to_delete = result.scalars().all()

            # Delete activities
            for activity in activities_to_delete:
                await session.delete(activity)

            await session.commit()

            return len(activities_to_delete)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting old activities: {str(e)}")

    async def export_activities(self, filters: ActivityLogFilters) -> List[Dict[str, Any]]:
        """Export activity logs for synchronization"""
        try:
            activities = await self.get_activity_logs(filters)
            return [activity.model_dump() for activity in activities]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exporting activities: {str(e)}")
