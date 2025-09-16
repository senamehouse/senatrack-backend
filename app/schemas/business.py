from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from . import SCHEMA_CONFIG


# Enums
class PaymentStatus(str, Enum):
    PAYE_TOTALITE = "paye_totalite"
    PAYE_PARTIEL = "paye_partiel"
    NON_PAYE = "non_paye"


class PaymentMethod(str, Enum):
    ESPECES = "especes"
    CHEQUE = "cheque"
    VIREMENT = "virement"
    CARTE_BANCAIRE = "carte_bancaire"
    MOBILE_MONEY = "mobile_money"


class StockMovementType(str, Enum):
    ENTREE = "entree"
    SORTIE = "sortie"
    AJUSTEMENT = "ajustement"


# Supplier Schemas
class SupplierBase(BaseModel):
    """Base supplier schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier"""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Supplier(SupplierBase):
    """Schema for supplier response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Client Schemas
class ClientBase(BaseModel):
    """Base client schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    invoices: Optional[int] = Field(0, ge=0)


class ClientCreate(ClientBase):
    """Schema for creating a client"""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    invoices: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = Field(None, alias="isActive")


class Client(ClientBase):
    """Schema for client response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Service Schemas
class ServiceBase(BaseModel):
    """Base service schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., ge=0)
    description: Optional[str] = None


class ServiceCreate(ServiceBase):
    """Schema for creating a service"""
    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a service"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Service(ServiceBase):
    """Schema for service response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# TVA Schemas
class TvaBase(BaseModel):
    """Base TVA schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=100)
    rate: float = Field(..., ge=0, le=100)
    description: Optional[str] = None


class TvaCreate(TvaBase):
    """Schema for creating a TVA"""
    pass


class TvaUpdate(BaseModel):
    """Schema for updating a TVA"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Tva(TvaBase):
    """Schema for TVA response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# ABIC Schemas
class AbicBase(BaseModel):
    """Base ABIC schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=100)
    rate: float = Field(..., ge=0, le=100)
    description: Optional[str] = None


class AbicCreate(AbicBase):
    """Schema for creating an ABIC"""
    pass


class AbicUpdate(BaseModel):
    """Schema for updating an ABIC"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Abic(AbicBase):
    """Schema for ABIC response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Stock Movement Item Schemas
class StockMovementItemBase(BaseModel):
    """Base stock movement item schema"""
    model_config = SCHEMA_CONFIG
    
    product_id: int = Field(..., alias="productId")
    product_name: str = Field(..., min_length=1, max_length=255, alias="productName")
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0, alias="unitPrice")
    total: float = Field(..., ge=0)
    unit: str = Field(..., min_length=1, max_length=50)


class StockMovementItemCreate(StockMovementItemBase):
    """Schema for creating a stock movement item"""
    pass


class StockMovementItem(StockMovementItemBase):
    """Schema for stock movement item response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    stock_movement_id: int = Field(..., alias="stockMovementId")


# Stock Movement Schemas
class StockMovementBase(BaseModel):
    """Base stock movement schema"""
    model_config = SCHEMA_CONFIG
    
    date: datetime
    movement_type: StockMovementType = Field(..., alias="movementType")
    label: str = Field(..., min_length=1, max_length=255)
    supplier_id: Optional[int] = Field(None, alias="supplierId")
    customer_id: Optional[int] = Field(None, alias="customerId")
    reason: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    details: Optional[str] = None
    document_reference: Optional[str] = Field(None, max_length=255, alias="documentReference")
    total_value: float = Field(0.0, ge=0, alias="totalValue")


class StockMovementCreate(StockMovementBase):
    """Schema for creating a stock movement"""
    items: List[StockMovementItemCreate] = Field(..., min_items=1)


class StockMovementUpdate(BaseModel):
    """Schema for updating a stock movement"""
    model_config = SCHEMA_CONFIG
    
    date: Optional[datetime] = None
    movement_type: Optional[StockMovementType] = Field(None, alias="movementType")
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_id: Optional[int] = Field(None, alias="supplierId")
    customer_id: Optional[int] = Field(None, alias="customerId")
    reason: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    details: Optional[str] = None
    document_reference: Optional[str] = Field(None, max_length=255, alias="documentReference")
    total_value: Optional[float] = Field(None, ge=0, alias="totalValue")


class StockMovement(StockMovementBase):
    """Schema for stock movement response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    items: List[StockMovementItem] = []
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Sale Item Schemas
class SaleItemBase(BaseModel):
    """Base sale item schema"""
    model_config = SCHEMA_CONFIG
    
    item_id: int = Field(..., alias="itemId")
    item_name: str = Field(..., min_length=1, max_length=255, alias="itemName")
    item_reference: Optional[str] = Field(None, max_length=100, alias="itemReference")
    item_type: str = Field(..., pattern="^(product|service)$", alias="itemType")
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0, alias="unitPrice")
    total: float = Field(..., ge=0)
    unit: Optional[str] = Field(None, max_length=50)


class SaleItemCreate(SaleItemBase):
    """Schema for creating a sale item"""
    pass


class SaleItem(SaleItemBase):
    """Schema for sale item response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    sale_id: int = Field(..., alias="saleId")


# Sale Schemas
class SaleBase(BaseModel):
    """Base sale schema"""
    model_config = SCHEMA_CONFIG
    
    reference: str = Field(..., min_length=1, max_length=100)
    date: datetime
    client_id: int = Field(..., alias="clientId")
    client_name: Optional[str] = Field(None, max_length=255, alias="clientName")
    seller_id: Optional[int] = Field(None, alias="sellerId")
    subtotal: float = Field(0.0, ge=0)
    discount: Optional[float] = Field(0.0, ge=0)
    tva_rate: Optional[float] = Field(None, ge=0, le=100, alias="tvaRate")
    tva_amount: Optional[float] = Field(None, ge=0, alias="tvaAmount")
    total: float = Field(0.0, ge=0)
    payment_status: PaymentStatus = Field(..., alias="paymentStatus")
    payment_method: Optional[PaymentMethod] = Field(None, alias="paymentMethod")
    amount_paid: float = Field(0.0, ge=0, alias="amountPaid")
    payment_reference: Optional[str] = Field(None, max_length=255, alias="paymentReference")
    notes: Optional[str] = None
    print_after_creation: bool = Field(False, alias="printAfterCreation")


class SaleCreate(SaleBase):
    """Schema for creating a sale"""
    items: List[SaleItemCreate] = Field(..., min_items=1)


class SaleUpdate(BaseModel):
    """Schema for updating a sale"""
    model_config = SCHEMA_CONFIG
    
    reference: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[datetime] = None
    client_id: Optional[int] = Field(None, alias="clientId")
    client_name: Optional[str] = Field(None, max_length=255, alias="clientName")
    seller_id: Optional[int] = Field(None, alias="sellerId")
    subtotal: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)
    tva_rate: Optional[float] = Field(None, ge=0, le=100, alias="tvaRate")
    tva_amount: Optional[float] = Field(None, ge=0, alias="tvaAmount")
    total: Optional[float] = Field(None, ge=0)
    payment_status: Optional[PaymentStatus] = Field(None, alias="paymentStatus")
    payment_method: Optional[PaymentMethod] = Field(None, alias="paymentMethod")
    amount_paid: Optional[float] = Field(None, ge=0, alias="amountPaid")
    payment_reference: Optional[str] = Field(None, max_length=255, alias="paymentReference")
    notes: Optional[str] = None
    print_after_creation: Optional[bool] = Field(None, alias="printAfterCreation")


class Sale(SaleBase):
    """Schema for sale response"""
    model_config = SCHEMA_CONFIG
    
    id: int
    items: List[SaleItem] = []
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Statistics Schemas
class SupplierStats(BaseModel):
    """Schema for supplier statistics"""
    model_config = SCHEMA_CONFIG
    
    total: int
    active: int
    with_movements: int = Field(..., alias="withMovements")


class ClientStats(BaseModel):
    """Schema for client statistics"""
    model_config = SCHEMA_CONFIG
    
    total: int
    active: int
    with_sales: int = Field(..., alias="withSales")
    total_sales_value: float = Field(..., alias="totalSalesValue")


class ServiceStats(BaseModel):
    """Schema for service statistics"""
    model_config = SCHEMA_CONFIG
    
    total: int
    active: int
    average_price: float = Field(..., alias="averagePrice")


class SaleStats(BaseModel):
    """Schema for sale statistics"""
    model_config = SCHEMA_CONFIG
    
    total: int
    total_value: float = Field(..., alias="totalValue")
    by_status: Dict[str, int] = Field(..., alias="byStatus")
    by_payment_method: Dict[str, int] = Field(..., alias="byPaymentMethod")


class StockMovementStats(BaseModel):
    """Schema for stock movement statistics"""
    model_config = SCHEMA_CONFIG
    
    total: int
    by_type: Dict[str, int] = Field(..., alias="byType")
    total_value: float = Field(..., alias="totalValue")
    recent_movements: int = Field(..., alias="recentMovements")

