from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.core.database import get_db_session
from app.schemas.stats_schema import DashboardStats, SalesStats, StockSummary, DailySales
from app.models.product_model import Product as ProductModel
from app.models.sales_model import Sale as SaleModel
from app.services.sales_service import SalesService


class StatsService:
    async def get_dashboard_stats(self, company_id: str, time_range: str = "7d") -> DashboardStats:
        try:
            session = get_db_session()

            # Counts (basic entity counts)
            products_count = await self._count_where(session, ProductModel, company_id)
            # For simplicity, set to 0 if not available in this context
            services_count = 0
            categories_count = 0
            units_count = 0
            suppliers_count = 0
            clients_count = 0

            # Sales stats with profit
            sales_stats = await self._get_sales_stats(session, company_id, time_range)

            # Stock summary
            stock_summary = await self._get_stock_summary(session, company_id)

            # Daily sales
            daily_sales = await self._get_daily_sales(session, company_id, time_range)

            return DashboardStats(
                productsCount=products_count,
                servicesCount=services_count,
                categoriesCount=categories_count,
                unitsCount=units_count,
                suppliersCount=suppliers_count,
                clientsCount=clients_count,
                salesStats=sales_stats,
                stockSummary=stock_summary,
                recentActivities=[],  # can be filled from activity logs service
                dailySales=daily_sales,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving dashboard stats: {str(e)}")

    async def _count_where(self, session, model, company_id: str) -> int:
        result = await session.execute(
            select(func.count(model.id)).where(getattr(model, "company_id") == company_id)
        )
        return int(result.scalar() or 0)

    async def _get_sales_stats(self, session, company_id: str, time_range: str) -> SalesStats:
        # Use SalesService to leverage existing profit logic
        sales_service = SalesService()

        # Determine date range
        end_date = datetime.utcnow()
        if time_range == "90d":
            start_date = end_date - timedelta(days=90)
        elif time_range == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        # Get sales in range
        result = await session.execute(
            select(SaleModel).options(joinedload(SaleModel.items)).where(
                SaleModel.company_id == company_id,
                SaleModel.date >= start_date,
                SaleModel.date <= end_date,
            )
        )
        sales = result.unique().scalars().all()

        total_revenue = 0.0
        total_cost = 0.0
        total_profit = 0.0
        today = datetime.utcnow().date()
        today_sales_amount = 0.0
        today_sales_count = 0

        for sale in sales:
            total_revenue += sale.total or 0.0
            if sale.date.date() == today:
                today_sales_count += 1
                today_sales_amount += sale.total or 0.0

            profit = await sales_service.calculate_sale_profit(sale.id, company_id)
            total_cost += profit.totalCost
            total_profit += profit.totalProfit

        average_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

        return SalesStats(
            todaySalesCount=today_sales_count,
            todaySalesAmount=today_sales_amount,
            totalRevenue=total_revenue,
            totalProfit=total_profit,
            averageMargin=average_margin,
            totalCost=total_cost,
        )

    async def _get_stock_summary(self, session, company_id: str) -> StockSummary:
        # Total products
        total_result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
            )
        )
        total_products = int(total_result.scalar() or 0)

        # Low stock and out of stock
        low_stock_result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
                ProductModel.stock <= 10,
            )
        )
        low_stock = int(low_stock_result.scalar() or 0)

        out_stock_result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
                ProductModel.stock <= 0,
            )
        )
        out_of_stock = int(out_stock_result.scalar() or 0)

        # Total stock value
        value_result = await session.execute(
            select(func.sum(ProductModel.stock * ProductModel.buy_price)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
            )
        )
        total_stock_value = float(value_result.scalar() or 0.0)

        return StockSummary(
            totalProducts=total_products,
            lowStock=low_stock,
            outOfStock=out_of_stock,
            totalStockValue=total_stock_value,
            lowStockProducts=[],
        )

    async def _get_daily_sales(self, session, company_id: str, time_range: str) -> list[DailySales]:
        # For now, simple last N days aggregation
        days = 7 if time_range == "7d" else 30 if time_range == "30d" else 90
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)

        # Fetch sales
        result = await session.execute(
            select(SaleModel).where(
                SaleModel.company_id == company_id,
                SaleModel.date >= datetime.combine(start_date, datetime.min.time()),
                SaleModel.date <= datetime.combine(end_date, datetime.max.time()),
            )
        )
        sales = result.scalars().all()

        # Group by date
        buckets = {}
        for i in range(days):
            d = start_date + timedelta(days=i)
            buckets[d] = {"sales": 0.0, "count": 0, "profit": 0.0}

        sales_service = SalesService()
        for sale in sales:
            d = sale.date.date()
            if d in buckets:
                buckets[d]["sales"] += sale.total or 0.0
                buckets[d]["count"] += 1
                profit = await sales_service.calculate_sale_profit(sale.id, company_id)
                buckets[d]["profit"] += profit.totalProfit

        def fmt_day(d: datetime.date) -> str:
            return d.strftime("%d/%m")

        return [
            DailySales(
                date=fmt_day(day),
                sales=data["sales"],
                count=data["count"],
                profit=data["profit"],
                revenue=data["sales"],
            )
            for day, data in buckets.items()
        ]


