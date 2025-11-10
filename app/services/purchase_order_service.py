from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.purchase_order_model import PurchaseOrder as PurchaseOrderModel
from app.schemas.purchase_order_schema import PurchaseOrder as PurchaseOrderSchema, PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    async def get_all(self, company_id: str) -> List[PurchaseOrderSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PurchaseOrderModel).where(PurchaseOrderModel.company_id == company_id)
            )
            rows = result.scalars().all()
            return [PurchaseOrderSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving purchase orders: {str(e)}")

    async def get_by_id(self, order_id: int, company_id: str) -> Optional[PurchaseOrderSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PurchaseOrderModel).where(
                    PurchaseOrderModel.id == order_id,
                    PurchaseOrderModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return PurchaseOrderSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving purchase order: {str(e)}")

    async def create(self, company_id: str, payload: PurchaseOrderCreate) -> int:
        try:
            session = get_db_session()
            po = PurchaseOrderModel(
                company_id=company_id,
                order_number=payload.order_number,
                supplier_id=payload.supplier_id,
                status=payload.status,
                total_amount=payload.total_amount,
            )
            session.add(po)
            await session.commit()
            await session.refresh(po)
            return po.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating purchase order: {str(e)}")

    async def update(self, order_id: int, company_id: str, payload: PurchaseOrderUpdate) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PurchaseOrderModel).where(
                    PurchaseOrderModel.id == order_id,
                    PurchaseOrderModel.company_id == company_id,
                )
            )
            po = result.scalar_one_or_none()
            if not po:
                return False
            for k, v in payload.model_dump(exclude_unset=True).items():
                if hasattr(po, k):
                    setattr(po, k, v)
            po.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating purchase order: {str(e)}")

    async def delete(self, order_id: int, company_id: str) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PurchaseOrderModel).where(
                    PurchaseOrderModel.id == order_id,
                    PurchaseOrderModel.company_id == company_id,
                )
            )
            po = result.scalar_one_or_none()
            if not po:
                return False
            await session.delete(po)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting purchase order: {str(e)}")

    async def generate_order_number(self, company_id: str) -> str:
        """Generate a strict purchase order number like BC-YYYY-0001 scoped to company."""
        try:
            session = get_db_session()
            year = datetime.utcnow().year
            prefix = f"BC-{year}-"
            result = await session.execute(
                select(PurchaseOrderModel.order_number).where(
                    PurchaseOrderModel.company_id == company_id,
                    PurchaseOrderModel.order_number.like(f"{prefix}%")
                )
            )
            refs = [row[0] for row in result.fetchall()]
            existing = set(refs)
            counter = 1
            ref = f"{prefix}{counter:04d}"
            while ref in existing:
                counter += 1
                ref = f"{prefix}{counter:04d}"
            return ref
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating purchase order number: {str(e)}")

    async def get_stats(self, company_id: str) -> Dict:
        try:
            session = get_db_session()
            total = (await session.execute(
                select(func.count()).select_from(PurchaseOrderModel).where(PurchaseOrderModel.company_id == company_id)
            )).scalar() or 0

            async def c(status: str) -> int:
                return (await session.execute(
                    select(func.count()).select_from(PurchaseOrderModel).where(
                        PurchaseOrderModel.company_id == company_id,
                        PurchaseOrderModel.status == status,
                    )
                )).scalar() or 0

            total_value = (await session.execute(
                select(func.coalesce(func.sum(PurchaseOrderModel.total_amount), 0)).where(PurchaseOrderModel.company_id == company_id)
            )).scalar() or 0

            avg_value = float(total_value) / total if total > 0 else 0.0

            return {
                "total": total,
                "pending": await c("pending"),
                "approved": await c("approved"),
                "ordered": await c("ordered"),
                "received": await c("received"),
                "cancelled": await c("cancelled"),
                "totalValue": float(total_value),
                "averageValue": float(avg_value),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing purchase order stats: {str(e)}")


