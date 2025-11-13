from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.sales_schema import (
    Sale as SaleSchema, 
    SaleCreate, 
    SaleUpdate, 
    SaleProfit,
)
from app.schemas.stats_schema import (
    SalesReportStats,
    TopProductProfit,
    ClientSalesStats,
)
from app.services.sales_service import SalesService
from app.utils.activity_logger import ActivityActor


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
    sale_id: str,
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
    sale_id = await svc.create(company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Sale created", "sale_id": sale_id}


@router.put("/{sale_id}", response_model=dict)
async def update_sale(
    sale_id: str,
    payload: SaleUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(sale_id=sale_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": "Sale updated"}


@router.delete("/{sale_id}", response_model=dict)
async def delete_sale(
    sale_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(sale_id=sale_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": "Sale deleted"}


@router.get("/{sale_id}/profit", response_model=SaleProfit)
async def get_sale_profit(
    sale_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    profit_data = await svc.calculate_sale_profit(sale_id, company_id)
    return profit_data


@router.get("/{sale_id}/stock-movements")
async def get_sale_stock_movements(
    sale_id: str,
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


@router.get("/stats/report", response_model=SalesReportStats)
async def get_sales_report_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client_id: Optional[str] = None,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get detailed sales report statistics with filters"""
    return await svc.get_sales_report_stats(company_id, start_date, end_date, client_id)


@router.get("/stats/clients/{client_id}", response_model=ClientSalesStats)
async def get_client_sales_stats(
    client_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get sales statistics for a specific client"""
    return await svc.get_client_sales_stats(company_id, client_id)


@router.get("/stats/top-products", response_model=List[TopProductProfit])
async def get_top_profitable_products(
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get top profitable products"""
    return await svc.get_top_profitable_products(company_id, limit, start_date, end_date)


