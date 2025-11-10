from app.utils.casing import BaseCamelModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    MOBILE_MONEY = "mobile_money"


class SaleItemBase(BaseCamelModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float


class SaleItemCreate(SaleItemBase):
    pass


class SaleItem(SaleItemBase):
    id: str
    sale_id: str


class SaleBase(BaseCamelModel):
    reference: str
    date: datetime
    client_id: Optional[int] = None
    client_name: str
    seller_id: Optional[int] = None
    subtotal: float
    discount: float = 0.0
    tva_rate: float = 0.0
    tva_amount: float = 0.0
    total: float
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    amount_paid: float = 0.0
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    print_after_creation: bool = False


class SaleCreate(SaleBase):
    items: List[SaleItemCreate] = []


class SaleUpdate(BaseCamelModel):
    reference: Optional[str] = None
    date: Optional[datetime] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    seller_id: Optional[int] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tva_rate: Optional[float] = None
    tva_amount: Optional[float] = None
    total: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    amount_paid: Optional[float] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    print_after_creation: Optional[bool] = None


class Sale(SaleBase):
    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    items: List[SaleItem] = []
