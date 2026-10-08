from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.models.purchase_order_model import PurchaseOrder as PurchaseOrderModel
from app.schemas.purchase_order_schema import PurchaseOrder as PurchaseOrderSchema, PurchaseOrderCreate, PurchaseOrderUpdate
from app.utils.activity_logger import audit, ActivityActor


class PurchaseOrderService:
    async def _lock_number_scope(self, session: AsyncSession, company_id: str) -> None:
        # Serialize reference allocation across backend workers on PostgreSQL.
        # SQLite relies on the unique constraint added to new/migrated tables.
        if session.get_bind().dialect.name == "postgresql":
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
                {"lock_key": f"purchase-order:{company_id}"},
            )

    async def get_all(self, company_id: str) -> List[PurchaseOrderSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(PurchaseOrderModel)
                .where(PurchaseOrderModel.company_id == company_id)
                .order_by(PurchaseOrderModel.created_at.desc())
            )
            rows = result.scalars().all()
            return [PurchaseOrderSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving purchase orders: {str(e)}")

    async def get_by_id(self, order_id: str, company_id: str) -> Optional[PurchaseOrderSchema]:
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

    @audit(
        action="CREATE",
        entity_type="purchase_order",
        details=lambda result, _a, kw: f"Bon de commande créé",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(mode='json', exclude_none=True)},
    )
    async def create(self, company_id: str, payload: PurchaseOrderCreate, actor: ActivityActor | None = None) -> str:
        session = get_db_session()
        auto_number = not payload.order_number or not payload.order_number.strip()
        try:
            for attempt in range(3):
                await self._lock_number_scope(session, company_id)
                order_number = await self.generate_order_number(company_id) if auto_number else payload.order_number.strip()
                existing = await session.scalar(select(PurchaseOrderModel.id).where(
                    PurchaseOrderModel.company_id == company_id,
                    PurchaseOrderModel.order_number == order_number,
                ).limit(1))
                if existing:
                    if auto_number and attempt < 2:
                        continue
                    raise HTTPException(status_code=409, detail="Ce numéro de bon de commande existe déjà.")

                po = PurchaseOrderModel(
                    company_id=company_id,
                    order_number=order_number,
                    supplier_id=payload.supplier_id,
                    status=payload.status,
                    total_amount=payload.total_amount,
                    details={**payload.model_dump(mode="json", by_alias=True, exclude={"order_number", "supplier_id", "status", "total_amount"}),
                             "createdBy": actor.user_id if actor else None},
                    created_at=datetime.utcnow(),
                )
                session.add(po)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    conflicting_number = await session.scalar(select(PurchaseOrderModel.id).where(
                        PurchaseOrderModel.company_id == company_id,
                        PurchaseOrderModel.order_number == order_number,
                    ).limit(1))
                    if conflicting_number:
                        if auto_number and attempt < 2:
                            continue
                        raise HTTPException(status_code=409, detail="Ce numéro de bon de commande existe déjà.")
                    raise
                return po.id
            raise HTTPException(status_code=409, detail="Impossible d'attribuer un numéro de bon de commande unique. Réessayez.")
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Impossible d'enregistrer le bon de commande. Réessayez.")

    @audit(
        action="UPDATE",
        entity_type="purchase_order",
        details=lambda _r, _a, kw: f"Bon de commande {kw['order_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["order_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, order_id: str, company_id: str, payload: PurchaseOrderUpdate, actor: ActivityActor | None = None) -> bool:
        session = get_db_session()
        try:
            result = await session.execute(
                select(PurchaseOrderModel).where(
                    PurchaseOrderModel.id == order_id,
                    PurchaseOrderModel.company_id == company_id,
                )
            )
            po = result.scalar_one_or_none()
            if not po:
                return False
            changes = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
            next_number = changes.get("orderNumber")
            if "orderNumber" in changes and (not isinstance(next_number, str) or not next_number.strip()):
                raise HTTPException(status_code=422, detail="Le numéro du bon de commande est requis.")
            if next_number:
                next_number = next_number.strip()
                changes["orderNumber"] = next_number
            if next_number and next_number != po.order_number:
                await self._lock_number_scope(session, company_id)
                existing = await session.scalar(select(PurchaseOrderModel.id).where(
                    PurchaseOrderModel.company_id == company_id,
                    PurchaseOrderModel.order_number == next_number,
                    PurchaseOrderModel.id != order_id,
                ).limit(1))
                if existing:
                    raise HTTPException(status_code=409, detail="Ce numéro de bon de commande existe déjà.")
            core_fields = {"orderNumber": "order_number", "supplierId": "supplier_id",
                           "status": "status", "totalAmount": "total_amount"}
            for field, attribute in core_fields.items():
                if field in changes:
                    setattr(po, attribute, changes.pop(field))
            po.details = {**(po.details or {}), **changes}
            po.updated_at = datetime.now()
            await session.commit()
            return True
        except HTTPException:
            await session.rollback()
            raise
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Ce numéro de bon de commande existe déjà.")
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Impossible de modifier le bon de commande. Réessayez.")

    @audit(
        action="DELETE",
        entity_type="purchase_order",
        details=lambda _r, _a, kw: f"Bon de commande {kw['order_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["order_id"],
    )
    async def delete(self, order_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
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


