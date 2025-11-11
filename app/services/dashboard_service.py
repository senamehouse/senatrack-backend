from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func, and_
from app.core.database import get_db_session
from app.schemas.dashboard_schema import (
    DashboardStats, SalesStats, StockSummary, DailySales
)
from app.schemas.product_schema import Product as ProductSchema
from app.schemas.activity_schema import ActivityLog as ActivityLogSchema
from app.models.product_model import Product as ProductModel
from app.models.sales_model import Sale as SaleModel

class DashboardService:
    """Service for dashboard statistics aggregation"""

    async def get_dashboard_stats(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> DashboardStats:
        """Get aggregated dashboard statistics with optional date range"""
        try:
            # Calculate date range if time_range is provided
            if time_range:
                end_date = datetime.utcnow()
                if time_range == "7d":
                    start_date = end_date - timedelta(days=7)
                elif time_range == "30d":
                    start_date = end_date - timedelta(days=30)
                elif time_range == "90d":
                    start_date = end_date - timedelta(days=90)

            # Default to last 7 days if no range specified
            if not start_date and not end_date:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)

            session = get_db_session()
            # Get entity counts
            products_count = await self._get_products_count(session, company_id)
            services_count = await self._get_services_count(session, company_id)
            categories_count = await self._get_categories_count(session, company_id)
            units_count = await self._get_units_count(session, company_id)
            suppliers_count = await self._get_suppliers_count(session, company_id)
            clients_count = await self._get_clients_count(session, company_id)

            # Get sales stats with date range
            sales_stats = await self._get_sales_stats(session, company_id, start_date, end_date)

            # Get stock summary
            stock_summary = await self._get_stock_summary(session, company_id)

            # Get recent activities
            recent_activities = await self._get_recent_activities(session, company_id)

            # Get daily sales for date range
            daily_sales = await self._get_daily_sales(session, company_id, start_date, end_date)

            return DashboardStats(
                products_count=products_count,
                services_count=services_count,
                categories_count=categories_count,
                units_count=units_count,
                suppliers_count=suppliers_count,
                clients_count=clients_count,
                sales_stats=sales_stats,
                stock_summary=stock_summary,
                recent_activities=recent_activities,
                daily_sales=daily_sales
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

    async def _get_products_count(self, session, company_id: str) -> int:
        """Get products count"""
        result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_services_count(self, session, company_id: str) -> int:
        """Get services count"""
        from app.models.service_model import Service as ServiceModel
        result = await session.execute(
            select(func.count(ServiceModel.id)).where(
                ServiceModel.company_id == company_id,
                ServiceModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_categories_count(self, session, company_id: str) -> int:
        """Get categories count"""
        from app.models.product_model import ProductCategory as ProductCategoryModel
        result = await session.execute(
            select(func.count(ProductCategoryModel.id)).where(
                ProductCategoryModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_units_count(self, session, company_id: str) -> int:
        """Get units count"""
        from app.models.product_model import ProductUnit as UnitModel
        result = await session.execute(
            select(func.count(UnitModel.id)).where(
                UnitModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_suppliers_count(self, session, company_id: str) -> int:
        """Get suppliers count"""
        from app.models.supplier_model import Supplier as SupplierModel
        result = await session.execute(
            select(func.count(SupplierModel.id)).where(
                SupplierModel.company_id == company_id,
                SupplierModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_clients_count(self, session, company_id: str) -> int:
        """Get clients count"""
        from app.models.client_model import Client as ClientModel
        result = await session.execute(
            select(func.count(ClientModel.id)).where(
                ClientModel.company_id == company_id,
                ClientModel.is_active == True
            )
        )
        return result.scalar() or 0

    async def _get_sales_stats(
        self,
        session,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SalesStats:
        """Get sales statistics including profit calculations with date range"""
        # Use sales service to get all sales (which includes items)
        from app.services.sales_service import SalesService
        sales_service = SalesService()
        all_sales = await sales_service.get_all(company_id)

        # Filter sales by date range if provided
        sales = all_sales
        if start_date or end_date:
            filtered_sales = []
            for sale in all_sales:
                sale_date = self._get_sale_date(sale)
                if sale_date:
                    if start_date and sale_date < start_date.date():
                        continue
                    if end_date and sale_date > end_date.date():
                        continue
                    filtered_sales.append(sale)
            sales = filtered_sales

        # Get all products for profit calculation
        products_result = await session.execute(
            select(ProductModel).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True
            )
        )
        products = products_result.scalars().all()
        products_dict = {p.id: p for p in products}

        # Get today's date
        today = datetime.utcnow().date()

        # Filter today's sales
        today_sales = [s for s in sales if self._get_sale_date(s) == today]
        today_sales_count = len(today_sales)
        today_sales_amount = sum(s.total or 0 for s in today_sales)

        # Calculate total revenue
        total_revenue = sum(s.total or 0 for s in sales)

        # Calculate profit from sale items
        total_cost = 0.0
        total_profit = 0.0

        for sale in sales:
            if hasattr(sale, 'items') and sale.items:
                for item in sale.items:
                    # Get product to find buy_price
                    product = products_dict.get(item.item_id or item.product_id)

                    if product:
                        item_cost = (product.buy_price or 0) * (item.quantity or 0)
                        item_revenue = item.total_price or item.total or 0
                        total_cost += item_cost
                        total_profit += (item_revenue - item_cost)
                    elif hasattr(item, 'item_type') and item.item_type == 'service':
                        # For services, assume 30% cost
                        item_revenue = item.total_price or item.total or 0
                        item_cost = item_revenue * 0.3
                        total_cost += item_cost
                        total_profit += (item_revenue - item_cost)

        average_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

        return SalesStats(
            today_sales_count=today_sales_count,
            today_sales_amount=today_sales_amount,
            total_revenue=total_revenue,
            total_profit=total_profit,
            average_margin=average_margin,
            total_cost=total_cost
        )

    def _get_sale_date(self, sale):
        """Helper to extract date from sale (handles both datetime and string)"""
        if isinstance(sale.date, datetime):
            return sale.date.date()
        elif isinstance(sale.date, str):
            try:
                return datetime.fromisoformat(sale.date.replace('Z', '+00:00')).date()
            except:
                return None
        return None

    async def _get_stock_summary(self, session, company_id: str) -> StockSummary:
        """Get stock summary with low stock products"""
        # Get total products
        total_result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True
            )
        )
        total_products = total_result.scalar() or 0

        # Get low stock products (stock <= threshold and stock > 0)
        # Use default threshold of 10 for low stock detection
        low_stock_result = await session.execute(
            select(ProductModel).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
                ProductModel.stock <= 10,  # Default threshold
                ProductModel.stock > 0
            )
        )
        low_stock_models = low_stock_result.scalars().all()
        low_stock = len(low_stock_models)

        # Convert to schemas
        low_stock_products = [ProductSchema(**p.to_dict()) for p in low_stock_models]

        # Get out of stock products
        out_of_stock_result = await session.execute(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True,
                ProductModel.stock == 0
            )
        )
        out_of_stock = out_of_stock_result.scalar() or 0

        # Calculate total stock value
        all_products_result = await session.execute(
            select(ProductModel).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True
            )
        )
        all_products = all_products_result.scalars().all()
        total_stock_value = sum((p.stock or 0) * (p.buy_price or 0) for p in all_products)

        return StockSummary(
            total_products=total_products,
            low_stock=low_stock,
            out_of_stock=out_of_stock,
            total_stock_value=total_stock_value,
            low_stock_products=low_stock_products
        )

    async def _get_recent_activities(self, session, company_id: str) -> list[ActivityLogSchema]:
        """Get recent activities (last 10)"""
        from app.models.activity_model import ActivityLog as ActivityLogModel
        result = await session.execute(
            select(ActivityLogModel)
            .where(ActivityLogModel.company_id == company_id)
            .order_by(ActivityLogModel.created_at.desc())
            .limit(10)
        )
        activities = result.scalars().all()
        # Convert to schemas - ActivityLogSchema will handle created_at -> createdAt alias
        return [ActivityLogSchema(**a.to_dict()) for a in activities]

    async def _get_daily_sales(
        self,
        session,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[DailySales]:
        """Get daily sales for date range"""
        # Use sales service to get all sales
        from app.services.sales_service import SalesService
        sales_service = SalesService()
        all_sales = await sales_service.get_all(company_id)

        # Filter sales by date range if provided
        sales = all_sales
        if start_date or end_date:
            filtered_sales = []
            for sale in all_sales:
                sale_date = self._get_sale_date(sale)
                if sale_date:
                    if start_date and sale_date < start_date.date():
                        continue
                    if end_date and sale_date > end_date.date():
                        continue
                    filtered_sales.append(sale)
            sales = filtered_sales

        # Calculate date range
        if start_date and end_date:
            start = start_date.date()
            end = end_date.date()
        else:
            # Default to last 7 days
            end = datetime.utcnow().date()
            start = end - timedelta(days=6)

        # Generate list of days in range
        days = []
        current = start
        while current <= end:
            days.append(current)
            current += timedelta(days=1)

        daily_sales_list = []
        # Get products for profit calculation
        products_result = await session.execute(
            select(ProductModel).where(
                ProductModel.company_id == company_id,
                ProductModel.is_active == True
            )
        )
        products = products_result.scalars().all()
        products_dict = {p.id: p for p in products}

        for date in days:
            day_sales = [s for s in sales if self._get_sale_date(s) == date]
            total_sales = sum(s.total or 0 for s in day_sales)
            sales_count = len(day_sales)

            # Calculate profit for the day
            day_profit = 0.0
            for sale in day_sales:
                if hasattr(sale, 'items') and sale.items:
                    for item in sale.items:
                        product = products_dict.get(item.item_id or item.product_id)
                        if product:
                            item_cost = (product.buy_price or 0) * (item.quantity or 0)
                            item_revenue = item.total_price or item.total or 0
                            day_profit += (item_revenue - item_cost)
                        elif hasattr(item, 'item_type') and item.item_type == 'service':
                            item_revenue = item.total_price or item.total or 0
                            item_cost = item_revenue * 0.3
                            day_profit += (item_revenue - item_cost)

            daily_sales_list.append(DailySales(
                date=date.strftime('%d/%m'),
                sales=total_sales,
                count=sales_count,
                profit=day_profit,
                revenue=total_sales
            ))

        return daily_sales_list
