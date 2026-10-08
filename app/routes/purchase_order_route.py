from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.services.purchase_order_service import PurchaseOrderService
from app.schemas.purchase_order_schema import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])
svc = PurchaseOrderService()


@router.get("/")
async def get_purchase_orders(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/stats")
async def get_purchase_order_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_stats(company_id)


@router.get("/{order_id}")
async def get_purchase_order(
    order_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    row = await svc.get_by_id(order_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return row


@router.post("/", response_model=PurchaseOrder)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    order_id = await svc.create(company_id=company_id, payload=payload, actor=ActivityActor.from_user(current_user))
    return await svc.get_by_id(order_id, company_id)


@router.put("/{order_id}", response_model=PurchaseOrder)
async def update_purchase_order(
    order_id: str,
    payload: PurchaseOrderUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(order_id=order_id, company_id=company_id, payload=payload, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return await svc.get_by_id(order_id, company_id)


@router.delete("/{order_id}")
async def delete_purchase_order(
    order_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(order_id=order_id, company_id=company_id, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"message": "Purchase order deleted"}

