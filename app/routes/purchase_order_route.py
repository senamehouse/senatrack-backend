from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.dependencies import get_current_user, get_company_id
from app.schemas.user_schema import User
from app.services.purchase_order_service import PurchaseOrderService


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])
svc = PurchaseOrderService()


@router.get("/")
async def get_purchase_orders(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    return await svc.get_all(company_id)


@router.get("/{order_id}")
async def get_purchase_order(order_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    row = await svc.get_by_id(order_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return row


@router.post("/")
async def create_purchase_order(payload: dict, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    order_id = await svc.create(company_id, payload)
    return {"message": "Purchase order created", "order_id": order_id}


@router.put("/{order_id}")
async def update_purchase_order(order_id: int, payload: dict, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.update(order_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"message": "Purchase order updated"}


@router.delete("/{order_id}")
async def delete_purchase_order(order_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.delete(order_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"message": "Purchase order deleted"}


@router.post("/generate-number")
async def generate_purchase_order_number(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    number = await svc.generate_order_number(company_id)
    return {"number": number}


@router.get("/stats")
async def get_purchase_order_stats(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    return await svc.get_stats(company_id)


