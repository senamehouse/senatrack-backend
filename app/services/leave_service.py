from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.leave_model import LeaveRequest as LeaveModel
from app.schemas.leave_schema import LeaveRequest as LeaveSchema, LeaveRequestCreate, LeaveRequestUpdate

class LeaveService:
    async def get_all(self, company_id: str) -> List[LeaveSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(LeaveModel.company_id == company_id)
            )
            rows = result.scalars().all()
            return [LeaveSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving leave requests: {str(e)}")

    async def get_by_id(self, leave_id: str, company_id: str) -> Optional[LeaveSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(
                    LeaveModel.id == leave_id,
                    LeaveModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return LeaveSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving leave request: {str(e)}")

    async def create(self, company_id: str, payload: LeaveRequestCreate) -> str:
        try:
            session = get_db_session()
            lv = LeaveModel(
                company_id=company_id,
                employee_id=payload.employee_id,
                leave_type=payload.leave_type,
                status=payload.status,
                start_date=payload.start_date,
                end_date=payload.end_date,
                days_requested=payload.days_requested,
                reason=payload.reason,
                approved_by=payload.approved_by,
                approved_date=payload.approved_date,
            )
            session.add(lv)
            await session.commit()
            await session.refresh(lv)
            return lv.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating leave request: {str(e)}")

    async def update(self, leave_id: str, company_id: str, payload: LeaveRequestUpdate) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(
                    LeaveModel.id == leave_id,
                    LeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(lv, field, value)
            lv.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating leave request: {str(e)}")

    async def delete(self, leave_id: str, company_id: str) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(
                    LeaveModel.id == leave_id,
                    LeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            await session.delete(lv)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting leave request: {str(e)}")

    async def get_stats(self, company_id: str) -> Dict:
        try:
            session = get_db_session()
            total = (await session.execute(
                select(func.count()).select_from(LeaveModel).where(LeaveModel.company_id == company_id)
            )).scalar() or 0

            async def c(status: str) -> int:
                return (await session.execute(
                    select(func.count()).select_from(LeaveModel).where(
                        LeaveModel.company_id == company_id,
                        LeaveModel.status == status,
                    )
                )).scalar() or 0

            return {
                "total": total,
                "pending": await c("pending"),
                "approved": await c("approved"),
                "rejected": await c("rejected"),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing leave stats: {str(e)}")

    async def approve(self, leave_id: str, company_id: str, approved_by: Optional[str] = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(
                    LeaveModel.id == leave_id,
                    LeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            lv.status = "approved"
            lv.approved_by = approved_by
            lv.approved_date = datetime.utcnow().isoformat()
            lv.updated_at = datetime.utcnow()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error approving leave request: {str(e)}")

    async def reject(self, leave_id: str, company_id: str, approved_by: Optional[str] = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(LeaveModel).where(
                    LeaveModel.id == leave_id,
                    LeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            lv.status = "rejected"
            lv.approved_by = approved_by
            lv.approved_date = datetime.utcnow().isoformat()
            lv.updated_at = datetime.utcnow()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error rejecting leave request: {str(e)}")
