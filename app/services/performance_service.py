from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.performance_model import PerformanceReview as PerformanceModel
from app.schemas.performance_schema import PerformanceReview as PerformanceSchema, PerformanceReviewCreate, PerformanceReviewUpdate

class PerformanceService:
    async def get_all(self, company_id: str) -> List[PerformanceSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PerformanceModel).where(PerformanceModel.company_id == company_id)
            )
            rows = result.scalars().all()
            return [PerformanceSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving performance reviews: {str(e)}")

    async def get_by_id(self, review_id: str, company_id: str) -> Optional[PerformanceSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PerformanceModel).where(
                    PerformanceModel.id == review_id,
                    PerformanceModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return PerformanceSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving performance review: {str(e)}")

    async def create(self, company_id: str, payload: PerformanceReviewCreate) -> str:
        try:
            session = get_db_session()
            pr = PerformanceModel(
                company_id=company_id,
                employee_id=payload.employee_id,
                reviewer_id=payload.reviewer_id,
                status=payload.status,
                overall_rating=payload.overall_rating,
            )
            session.add(pr)
            await session.commit()
            await session.refresh(pr)
            return pr.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating performance review: {str(e)}")

    async def update(self, review_id: str, company_id: str, payload: PerformanceReviewUpdate) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PerformanceModel).where(
                    PerformanceModel.id == review_id,
                    PerformanceModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(pr, field, value)
            pr.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating performance review: {str(e)}")

    async def delete(self, review_id: str, company_id: str) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PerformanceModel).where(
                    PerformanceModel.id == review_id,
                    PerformanceModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            await session.delete(pr)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting performance review: {str(e)}")

    async def get_stats(self, company_id: str) -> Dict:
        try:
            session = get_db_session()
            total = (await session.execute(
                select(func.count()).select_from(PerformanceModel).where(PerformanceModel.company_id == company_id)
            )).scalar() or 0
            avg = (await session.execute(
                select(func.coalesce(func.avg(PerformanceModel.overall_rating), 0)).where(PerformanceModel.company_id == company_id)
            )).scalar() or 0
            return {"total": total, "averageRating": float(avg)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing performance stats: {str(e)}")
