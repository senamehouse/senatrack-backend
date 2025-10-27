from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_sessionmaker
from app.models.reception_model import Reception as ReceptionModel
from app.schemas.reception_schema import Reception as ReceptionSchema, ReceptionCreate, ReceptionUpdate


class ReceptionService:
    async def get_all(self, company_id: str) -> List[ReceptionSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ReceptionModel).where(ReceptionModel.company_id == company_id)
                )
                rows = result.scalars().all()
                return [ReceptionSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving receptions: {str(e)}")

    async def get_by_id(self, reception_id: int, company_id: str) -> Optional[ReceptionSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ReceptionModel).where(
                        ReceptionModel.id == reception_id,
                        ReceptionModel.company_id == company_id,
                    )
                )
                row = result.scalar_one_or_none()
                return ReceptionSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving reception: {str(e)}")

    async def create(self, company_id: str, payload: ReceptionCreate) -> int:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                rec = ReceptionModel(
                    company_id=company_id,
                    reception_number=payload.reception_number,
                    purchase_order_id=payload.purchase_order_id,
                    status=payload.status,
                )
                session.add(rec)
                await session.commit()
                await session.refresh(rec)
                return rec.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating reception: {str(e)}")

    async def update(self, reception_id: int, company_id: str, payload: ReceptionUpdate) -> bool:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ReceptionModel).where(
                        ReceptionModel.id == reception_id,
                        ReceptionModel.company_id == company_id,
                    )
                )
                rec = result.scalar_one_or_none()
                if not rec:
                    return False
                for k, v in payload.model_dump(exclude_unset=True).items():
                    if hasattr(rec, k):
                        setattr(rec, k, v)
                rec.updated_at = datetime.now()
                await session.commit()
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating reception: {str(e)}")

    async def delete(self, reception_id: int, company_id: str) -> bool:
        try:
            async with LocalAsyncSession() as session:
                result = await session.execute(
                    select(ReceptionModel).where(
                        ReceptionModel.id == reception_id,
                        ReceptionModel.company_id == company_id,
                    )
                )
                rec = result.scalar_one_or_none()
                if not rec:
                    return False
                await session.delete(rec)
                await session.commit()
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting reception: {str(e)}")


