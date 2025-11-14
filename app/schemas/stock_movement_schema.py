from app.utils.casing import BaseCamelModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"


class StockMovementItemBase(BaseCamelModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    total: float
    unit: str


class StockMovementItemCreate(StockMovementItemBase):
    pass


class StockMovementItem(StockMovementItemBase):
    id: str
    stock_movement_id: str


class StockMovementBase(BaseCamelModel):
    date: datetime
    movement_type: MovementType
    label: str
    supplier_id: Optional[str] = None
    customer_id: Optional[str] = None
    reason: Optional[str] = None
    author: str
    details: Optional[str] = None
    document_reference: Optional[str] = None
    total_value: float


class StockMovementCreate(StockMovementBase):
    items: List[StockMovementItemCreate] = []


class StockMovementUpdate(BaseCamelModel):
    date: Optional[datetime] = None
    movement_type: Optional[MovementType] = None
    label: Optional[str] = None
    supplier_id: Optional[str] = None
    customer_id: Optional[str] = None
    reason: Optional[str] = None
    author: Optional[str] = None
    details: Optional[str] = None
    document_reference: Optional[str] = None
    total_value: Optional[float] = None


class StockMovement(StockMovementBase):
    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    items: List[StockMovementItem] = []
