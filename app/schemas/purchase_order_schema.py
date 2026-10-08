from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field

from app.utils.casing import BaseCamelModel


PurchaseOrderStatus = Literal["draft", "pending", "approved", "ordered", "received", "cancelled"]


class PurchaseOrderItem(BaseCamelModel):
    id: str
    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    product_code: Optional[str] = Field(None, alias="productCode")
    description: Optional[str] = None
    quantity: int = Field(..., gt=0)
    buy_price: float = Field(..., ge=0, alias="buyPrice")
    total_price: float = Field(..., ge=0, alias="totalPrice")
    unit: str = "unité"
    received_quantity: Optional[int] = Field(None, ge=0, alias="receivedQuantity")
    pending_quantity: Optional[int] = Field(None, ge=0, alias="pendingQuantity")


class PurchaseOrderCreate(BaseCamelModel):
    order_number: Optional[str] = Field(None, alias="orderNumber")
    supplier_id: str = Field(..., alias="supplierId")
    supplier_name: str = Field(..., alias="supplierName")
    supplier_contact: Optional[str] = Field(None, alias="supplierContact")
    supplier_email: Optional[str] = Field(None, alias="supplierEmail")
    supplier_phone: Optional[str] = Field(None, alias="supplierPhone")
    supplier_address: Optional[str] = Field(None, alias="supplierAddress")
    status: PurchaseOrderStatus = "draft"
    order_date: str = Field(..., alias="orderDate")
    expected_delivery_date: Optional[str] = Field(None, alias="expectedDeliveryDate")
    actual_delivery_date: Optional[str] = Field(None, alias="actualDeliveryDate")
    items: List[PurchaseOrderItem] = Field(..., min_length=1)
    subtotal: float = Field(..., ge=0)
    tax_rate: float = Field(0, ge=0, le=100, alias="taxRate")
    tax_amount: float = Field(0, ge=0, alias="taxAmount")
    total_amount: float = Field(..., ge=0, alias="totalAmount")
    currency: str = "FCFA"
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = Field(None, alias="termsAndConditions")
    payment_terms: Optional[str] = Field(None, alias="paymentTerms")


class PurchaseOrderUpdate(BaseCamelModel):
    order_number: Optional[str] = Field(None, alias="orderNumber")
    supplier_id: Optional[str] = Field(None, alias="supplierId")
    supplier_name: Optional[str] = Field(None, alias="supplierName")
    supplier_contact: Optional[str] = Field(None, alias="supplierContact")
    supplier_email: Optional[str] = Field(None, alias="supplierEmail")
    supplier_phone: Optional[str] = Field(None, alias="supplierPhone")
    supplier_address: Optional[str] = Field(None, alias="supplierAddress")
    status: Optional[PurchaseOrderStatus] = None
    order_date: Optional[str] = Field(None, alias="orderDate")
    expected_delivery_date: Optional[str] = Field(None, alias="expectedDeliveryDate")
    actual_delivery_date: Optional[str] = Field(None, alias="actualDeliveryDate")
    items: Optional[List[PurchaseOrderItem]] = None
    subtotal: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100, alias="taxRate")
    tax_amount: Optional[float] = Field(None, ge=0, alias="taxAmount")
    total_amount: Optional[float] = Field(None, ge=0, alias="totalAmount")
    currency: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = Field(None, alias="termsAndConditions")
    payment_terms: Optional[str] = Field(None, alias="paymentTerms")


class PurchaseOrder(BaseCamelModel):
    id: str
    order_number: str = Field(..., alias="orderNumber")
    supplier_id: str = Field("", alias="supplierId")
    supplier_name: str = Field("", alias="supplierName")
    supplier_contact: Optional[str] = Field(None, alias="supplierContact")
    supplier_email: Optional[str] = Field(None, alias="supplierEmail")
    supplier_phone: Optional[str] = Field(None, alias="supplierPhone")
    supplier_address: Optional[str] = Field(None, alias="supplierAddress")
    status: PurchaseOrderStatus = "draft"
    order_date: str = Field(..., alias="orderDate")
    expected_delivery_date: Optional[str] = Field(None, alias="expectedDeliveryDate")
    actual_delivery_date: Optional[str] = Field(None, alias="actualDeliveryDate")
    items: List[PurchaseOrderItem] = Field(default_factory=list)
    subtotal: float = 0
    tax_rate: float = Field(0, alias="taxRate")
    tax_amount: float = Field(0, alias="taxAmount")
    total_amount: float = Field(..., alias="totalAmount")
    currency: str = "FCFA"
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = Field(None, alias="termsAndConditions")
    payment_terms: Optional[str] = Field(None, alias="paymentTerms")
    created_by: Optional[str] = Field(None, alias="createdBy")
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
