from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.payroll_model import Payroll as PayrollModel
from app.schemas.payroll_schema import Payroll as PayrollSchema, PayrollCreate, PayrollUpdate
from app.utils.activity_logger import audit, ActivityActor


class PayrollService:
    async def get_all(self, company_id: str) -> List[PayrollSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PayrollModel).where(PayrollModel.company_id == company_id)
            )
            rows = result.scalars().all()
            return [PayrollSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving payroll: {str(e)}")

    async def get_by_id(self, payroll_id: str, company_id: str) -> Optional[PayrollSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PayrollModel).where(
                    PayrollModel.id == payroll_id,
                    PayrollModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return PayrollSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving payroll: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="payroll",
        details=lambda result, _a, kw: f"Paie créée pour employé {kw['payload'].employee_id}",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create(self, company_id: str, payload: PayrollCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            pr = PayrollModel(
                company_id=company_id,
                employee_id=payload.employee_id,
                period_year=payload.period_year,
                period_month=payload.period_month,
                net_salary=payload.net_salary,
                status=payload.status,
                payment_method=payload.payment_method,
                paid_date=payload.paid_date,
            )
            session.add(pr)
            await session.commit()
            await session.refresh(pr)
            return pr.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating payroll: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="payroll",
        details=lambda _r, _a, kw: f"Paie {kw['payroll_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["payroll_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, payroll_id: str, company_id: str, payload: PayrollUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PayrollModel).where(
                    PayrollModel.id == payroll_id,
                    PayrollModel.company_id == company_id,
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
            raise HTTPException(status_code=500, detail=f"Error updating payroll: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="payroll",
        details=lambda _r, _a, kw: f"Paie {kw['payroll_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["payroll_id"],
    )
    async def delete(self, payroll_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PayrollModel).where(
                    PayrollModel.id == payroll_id,
                    PayrollModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            await session.delete(pr)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting payroll: {str(e)}")

    async def get_stats(self, company_id: str) -> Dict:
        try:
            session = get_db_session()
            total = (await session.execute(
                select(func.count()).select_from(PayrollModel).where(PayrollModel.company_id == company_id)
            )).scalar() or 0

            async def c(status: str) -> int:
                return (await session.execute(
                    select(func.count()).select_from(PayrollModel).where(
                        PayrollModel.company_id == company_id,
                        PayrollModel.status == status,
                    )
                )).scalar() or 0

            paid = await c("paid")
            pending = await c("pending")
            failed = await c("failed")
            cancelled = await c("cancelled")

            total_amount = (await session.execute(
                select(func.coalesce(func.sum(PayrollModel.net_salary), 0)).where(PayrollModel.company_id == company_id)
            )).scalar() or 0

            return {
                "total": total,
                "paid": paid,
                "pending": pending,
                "failed": failed,
                "cancelled": cancelled,
                "totalAmount": float(total_amount),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing payroll stats: {str(e)}")