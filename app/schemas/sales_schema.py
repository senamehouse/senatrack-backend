from app.utils.casing import BaseCamelModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


class SaleItemBase(BaseCamelModel):
    product_id: str
    product_name: str
    quantity: int
    sell_price: float
    total_price: float
    item_type: Optional[str] = "product"  # product|service
    product_reference: Optional[str] = None
    unit: Optional[str] = None
    original_sell_price: Optional[float] = None
    price_modified: Optional[bool] = False


class SaleItemCreate(SaleItemBase):
    pass


class SaleItem(SaleItemBase):
    id: str
    sale_id: str


class SaleItemResponse(BaseCamelModel):
    """Response schema for sale items with frontend field names"""
    item_id: str
    item_name: str
    item_reference: Optional[str] = None
    item_type: str
    quantity: int
    sell_price: float
    original_sell_price: Optional[float] = None
    total: float
    unit: Optional[str] = None
    price_modified: bool = False


class SaleBase(BaseCamelModel):
    reference: str
    date: datetime
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    seller_id: Optional[str] = None
    seller_name: Optional[str] = None
    subtotal: float
    discount: float = 0.0
    tva_rate: float = 0.0
    tva_amount: float = 0.0
    total: float
    payment_status: PaymentStatus
    amount_paid: float = 0.0
    payment_reference: Optional[str] = None


class SaleCreate(SaleBase):
    reference: Optional[str] = None
    items: List[SaleItemCreate] = []


class SaleUpdate(BaseCamelModel):
    reference: Optional[str] = None
    date: Optional[datetime] = None
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    seller_id: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tva_rate: Optional[float] = None
    tva_amount: Optional[float] = None
    total: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    amount_paid: Optional[float] = None
    payment_reference: Optional[str] = None


class SaleProfitItemInfo(BaseCamelModel):
    item_id: str
    item_name: str
    quantity: int


class SaleProfitItem(BaseCamelModel):
    item: SaleProfitItemInfo
    cost: float
    profit: float
    margin: float


class SaleProfit(BaseCamelModel):
    totalCost: float
    totalProfit: float
    averageMargin: float
    items: List[SaleProfitItem] = []


class Sale(SaleBase):
    id: str
    company_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[SaleItem] = []
    profit: Optional[SaleProfit] = None

