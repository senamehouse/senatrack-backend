from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.sales_schema import Sale as SaleSchema, SaleCreate, SaleUpdate
from app.services.sales_service import SalesService


router = APIRouter(prefix="/sales", tags=["Sales"])
svc = SalesService()


@router.get("/", response_model=List[SaleSchema])
async def get_sales(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/{sale_id}", response_model=SaleSchema)
async def get_sale(
    sale_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    sale = await svc.get_by_id(sale_id, company_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.post("/", response_model=dict)
async def create_sale(
    payload: SaleCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    sale_id = await svc.create(company_id, payload)
    return {"message": "Sale created", "sale_id": sale_id}


@router.put("/{sale_id}", response_model=dict)
async def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(sale_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": "Sale updated"}


@router.delete("/{sale_id}", response_model=dict)
async def delete_sale(
    sale_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(sale_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": "Sale deleted"}


@router.post("/generate-number")
async def generate_sale_number(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    number = await svc.generate_sale_reference(company_id)
    return {"number": number}


@router.get("/{sale_id}/profit")
async def get_sale_profit(
    sale_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    profit_data = await svc.calculate_sale_profit(sale_id, company_id)
    return profit_data


@router.get("/{sale_id}/stock-movements")
async def get_sale_stock_movements(
    sale_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    # Get the sale to get its reference
    sale = await svc.get_by_id(sale_id, company_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get stock movements by sale reference
    from app.services.stock_movement_service import StockMovementService
    stock_svc = StockMovementService()
    movements = await stock_svc.get_movements_by_sale_id(sale_id, company_id)
    return movements


