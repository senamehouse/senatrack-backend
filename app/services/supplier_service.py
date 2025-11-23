from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.supplier_model import Supplier as SupplierModel
from app.schemas.supplier_schema import Supplier as SupplierSchema, SupplierCreate, SupplierUpdate
from app.utils.activity_logger import audit, ActivityActor


class SupplierService:
    async def get_all_suppliers(self, company_id: str) -> List[SupplierSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SupplierModel)
                .where(
                    SupplierModel.company_id == company_id,
                    SupplierModel.is_active == True,
                )
                .order_by(SupplierModel.created_at.desc())
            )
            suppliers = result.scalars().all()
            return [SupplierSchema(**s.to_dict()) for s in suppliers]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving suppliers: {str(e)}")

    async def get_supplier_by_id(self, supplier_id: str, company_id: str) -> Optional[SupplierSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SupplierModel).where(
                    SupplierModel.id == supplier_id,
                    SupplierModel.company_id == company_id,
                    SupplierModel.is_active == True,
                )
            )
            supplier = result.scalar_one_or_none()
            return SupplierSchema(**supplier.to_dict()) if supplier else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving supplier: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="supplier",
        details=lambda result, _a, kw: f"Fournisseur {kw['supplier_data'].name} créé",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["supplier_data"].model_dump(exclude_none=True)},
    )
    async def create_supplier(self, company_id: str, supplier_data: SupplierCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            supplier = SupplierModel(
                company_id=company_id,
                name=supplier_data.name,
                email=supplier_data.email,
                phone=supplier_data.phone,
                address=supplier_data.address,
            )
            session.add(supplier)
            await session.commit()
            await session.refresh(supplier)
            return supplier.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating supplier: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="supplier",
        details=lambda _r, _a, kw: f"Fournisseur {kw['supplier_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["supplier_id"],
        extra=lambda _r, _a, kw: kw["supplier_data"].model_dump(exclude_unset=True),
    )
    async def update_supplier(self, supplier_id: str, company_id: str, supplier_data: SupplierUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SupplierModel).where(
                    SupplierModel.id == supplier_id,
                    SupplierModel.company_id == company_id,
                )
            )
            supplier = result.scalar_one_or_none()
            if not supplier:
                return False
            if supplier_data.name is not None:
                supplier.name = supplier_data.name
            if supplier_data.email is not None:
                supplier.email = supplier_data.email
            if supplier_data.phone is not None:
                supplier.phone = supplier_data.phone
            if supplier_data.address is not None:
                supplier.address = supplier_data.address
            if supplier_data.is_active is not None:
                supplier.is_active = supplier_data.is_active
            supplier.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating supplier: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="supplier",
        details=lambda _r, _a, kw: f"Fournisseur {kw['supplier_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["supplier_id"],
    )
    async def delete_supplier(self, supplier_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SupplierModel).where(
                    SupplierModel.id == supplier_id,
                    SupplierModel.company_id == company_id,
                )
            )
            supplier = result.scalar_one_or_none()
            if not supplier:
                return False
            supplier.is_active = False
            supplier.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting supplier: {str(e)}")

    async def generate_supplier_code(self, company_id: str) -> str:
        """Generate supplier code like SUP-YYYY-0001 per company."""
        try:
            session = get_db_session()
            year = datetime.utcnow().year
            prefix = f"SUP-{year}-"
            rows = await session.execute(
                select(SupplierModel.name)  # we don't have code column yet; fallback to count
                .where(SupplierModel.company_id == company_id)
            )
            count = len(rows.fetchall())
            return f"{prefix}{count + 1:04d}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating supplier code: {str(e)}")