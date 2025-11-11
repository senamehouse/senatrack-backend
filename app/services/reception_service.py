from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.reception_model import Reception as ReceptionModel
from app.schemas.reception_schema import Reception as ReceptionSchema, ReceptionCreate, ReceptionUpdate
from app.utils.activity_logger import audit, ActivityActor


class ReceptionService:
    async def get_all(self, company_id: str) -> List[ReceptionSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ReceptionModel).where(ReceptionModel.company_id == company_id)
            )
            rows = result.scalars().all()
            return [ReceptionSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving receptions: {str(e)}")

    async def get_by_id(self, reception_id: str, company_id: str) -> Optional[ReceptionSchema]:
        try:
            session = get_db_session()
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

    @audit(
        action="CREATE",
        entity_type="reception",
        details=lambda result, _a, kw: f"Réception {kw['payload'].reception_number} créée",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create(self, company_id: str, payload: ReceptionCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
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

    @audit(
        action="UPDATE",
        entity_type="reception",
        details=lambda _r, _a, kw: f"Réception {kw['reception_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["reception_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, reception_id: str, company_id: str, payload: ReceptionUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
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

    @audit(
        action="DELETE",
        entity_type="reception",
        details=lambda _r, _a, kw: f"Réception {kw['reception_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["reception_id"],
    )
    async def delete(self, reception_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
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


