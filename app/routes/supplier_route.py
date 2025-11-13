from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.supplier_schema import Supplier, SupplierCreate, SupplierUpdate
from app.services.supplier_service import SupplierService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
service = SupplierService()


@router.get("/", response_model=List[Supplier])
async def get_suppliers(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await service.get_all_suppliers(company_id)


@router.get("/{supplier_id}", response_model=Supplier)
async def get_supplier(
    supplier_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    supplier = await service.get_supplier_by_id(supplier_id, company_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("/", response_model=dict)
async def create_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    supplier_id = await service.create_supplier(company_id=company_id, supplier_data=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Supplier created", "supplier_id": supplier_id}


@router.put("/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await service.update_supplier(supplier_id=supplier_id, company_id=company_id, supplier_data=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier updated"}


@router.delete("/{supplier_id}", response_model=dict)
async def delete_supplier(
    supplier_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await service.delete_supplier(supplier_id=supplier_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted"}