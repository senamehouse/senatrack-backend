from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.stock_movement_schema import StockMovement as StockMovementSchema, StockMovementCreate, StockMovementUpdate
from app.services.stock_movement_service import StockMovementService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])
svc = StockMovementService()


@router.get("/", response_model=List[StockMovementSchema])
async def get_movements(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get all stock movements for the company"""
    return await svc.get_all(company_id)


@router.get("/summary")
async def get_stock_summary(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get stock summary statistics"""
    summary = await svc.get_stock_summary(company_id)
    return summary


@router.get("/{movement_id}", response_model=StockMovementSchema)
async def get_movement(
    movement_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    mv = await svc.get_by_id(movement_id, company_id)
    if not mv:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    return mv


@router.post("/", response_model=StockMovementSchema)
async def create_movement(
    payload: StockMovementCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    movement_id = await svc.create(company_id=company_id, payload=payload, actor=ActivityActor.from_user(current_user))
    return await svc.get_by_id(movement_id, company_id)


@router.put("/{movement_id}", response_model=StockMovementSchema)
async def update_movement(
    movement_id: str,
    payload: StockMovementUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(movement_id=movement_id, company_id=company_id, payload=payload, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    return await svc.get_by_id(movement_id, company_id)


@router.delete("/{movement_id}", response_model=dict)
async def delete_movement(
    movement_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(movement_id=movement_id, company_id=company_id, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    return {"message": "Stock movement deleted"}


@router.get("/product/{product_id}/stock")
async def get_product_stock(
    product_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get current stock quantity for a product"""
    stock = await svc.get_product_stock(product_id, company_id)
    return {"stock": stock}


@router.get("/by-sale/{sale_id}")
async def get_movements_by_sale(
    sale_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get stock movements by sale ID"""
    movements = await svc.get_movements_by_sale_id(sale_id, company_id)
    return movements


 


