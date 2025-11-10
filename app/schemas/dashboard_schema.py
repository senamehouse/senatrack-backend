from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.schemas.product_schema import Product
from app.schemas.activity_schema import ActivityLog


class DailySales(BaseCamelModel):
    """Daily sales data for chart"""
    date: str = Field(..., description="Date in format DD/MM")
    sales: float = Field(..., description="Total sales amount for the day")
    count: int = Field(..., description="Number of sales for the day")
    profit: float = Field(default=0.0, description="Total profit for the day")
    revenue: float = Field(default=0.0, description="Total revenue for the day (alias for sales)")


class StockSummary(BaseCamelModel):
    """Stock summary data"""
    total_products: int = Field(..., alias="totalProducts")
    low_stock: int = Field(..., alias="lowStock")
    out_of_stock: int = Field(..., alias="outOfStock")
    total_stock_value: float = Field(..., alias="totalStockValue")
    low_stock_products: List[Product] = Field(default_factory=list, alias="lowStockProducts")


class SalesStats(BaseCamelModel):
    """Sales statistics"""
    today_sales_count: int = Field(..., alias="todaySalesCount")
    today_sales_amount: float = Field(..., alias="todaySalesAmount")
    total_revenue: float = Field(..., alias="totalRevenue")
    total_profit: float = Field(..., alias="totalProfit")
    average_margin: float = Field(..., alias="averageMargin")
    total_cost: float = Field(..., alias="totalCost")


class DashboardStats(BaseCamelModel):
    """Complete dashboard statistics"""
    # Entity counts
    products_count: int = Field(..., alias="productsCount")
    services_count: int = Field(..., alias="servicesCount")
    categories_count: int = Field(..., alias="categoriesCount")
    units_count: int = Field(..., alias="unitsCount")
    suppliers_count: int = Field(..., alias="suppliersCount")
    clients_count: int = Field(..., alias="clientsCount")
    
    # Sales statistics
    sales_stats: SalesStats = Field(..., alias="salesStats")
    
    # Stock summary
    stock_summary: StockSummary = Field(..., alias="stockSummary")
    
    # Recent activities
    recent_activities: List[ActivityLog] = Field(default_factory=list, alias="recentActivities")
    
    # Daily sales for chart (last 7 days)
    daily_sales: List[DailySales] = Field(default_factory=list, alias="dailySales")

