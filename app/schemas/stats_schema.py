from typing import List
from pydantic import Field
from app.utils.casing import BaseCamelModel


class DailySales(BaseCamelModel):
    date: str = Field(..., description="Date in format DD/MM")
    sales: float = Field(..., description="Total sales amount for the day")
    count: int = Field(..., description="Number of sales for the day")
    profit: float = Field(default=0.0, description="Total profit for the day")
    revenue: float = Field(default=0.0, description="Total revenue for the day (alias for sales)")


class StockSummary(BaseCamelModel):
    total_products: int = Field(..., alias="totalProducts")
    low_stock: int = Field(..., alias="lowStock")
    out_of_stock: int = Field(..., alias="outOfStock")
    total_stock_value: float = Field(..., alias="totalStockValue")
    low_stock_products: List[dict] = Field(default_factory=list, alias="lowStockProducts")


class SalesStats(BaseCamelModel):
    today_sales_count: int = Field(..., alias="todaySalesCount")
    today_sales_amount: float = Field(..., alias="todaySalesAmount")
    total_revenue: float = Field(..., alias="totalRevenue")
    total_profit: float = Field(..., alias="totalProfit")
    average_margin: float = Field(..., alias="averageMargin")
    total_cost: float = Field(..., alias="totalCost")


class DashboardStats(BaseCamelModel):
    products_count: int = Field(..., alias="productsCount")
    services_count: int = Field(..., alias="servicesCount")
    categories_count: int = Field(..., alias="categoriesCount")
    units_count: int = Field(..., alias="unitsCount")
    suppliers_count: int = Field(..., alias="suppliersCount")
    clients_count: int = Field(..., alias="clientsCount")

    sales_stats: SalesStats = Field(..., alias="salesStats")
    stock_summary: StockSummary = Field(..., alias="stockSummary")
    recent_activities: List[dict] = Field(default_factory=list, alias="recentActivities")
    daily_sales: List[DailySales] = Field(default_factory=list, alias="dailySales")


class TopProductProfit(BaseCamelModel):
    """Top profitable product statistics"""
    product_id: str
    product_name: str
    total_quantity: int
    total_revenue: float
    total_cost: float
    total_profit: float
    average_margin: float


class SalesReportStats(BaseCamelModel):
    """Extended stats for reports with date range support"""
    total_revenue: float
    total_cost: float
    total_profit: float
    average_margin: float
    total_sales: int
    total_quantity: int
    average_sale: float
    unique_clients: int
    top_products: List[TopProductProfit] = []
    price_modification_rate: float
    total_price_difference: float


class ClientSalesStats(BaseCamelModel):
    """Client-specific sales statistics"""
    client_id: str
    client_name: str
    total_sales: int
    total_sold: float
    total_paid: float
    total_debt: float
    total_profit: float
    average_margin: float
    paid_sales: int
    partial_sales: int
    unpaid_sales: int


