from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PAYE_TOTALITE = "paye_totalite"
    PAYE_PARTIEL = "paye_partiel"
    NON_PAYE = "non_paye"


class PaymentMethod(str, enum.Enum):
    ESPECES = "especes"
    CHEQUE = "cheque"
    VIREMENT = "virement"
    CARTE_BANCAIRE = "carte_bancaire"
    MOBILE_MONEY = "mobile_money"


class StockMovementType(str, enum.Enum):
    ENTREE = "entree"
    SORTIE = "sortie"
    AJUSTEMENT = "ajustement"


# Supplier Model
class Supplier(Base):
    """SQLAlchemy model for Supplier table"""
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    stock_movements: Mapped[List["StockMovement"]] = relationship("StockMovement", back_populates="supplier")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Client Model
class Client(Base):
    """SQLAlchemy model for Client table"""
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoices: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sales: Mapped[List["Sale"]] = relationship("Sale", back_populates="client")
    stock_movements: Mapped[List["StockMovement"]] = relationship("StockMovement", back_populates="customer")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "invoices": self.invoices,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Service Model
class Service(Base):
    """SQLAlchemy model for Service table"""
    __tablename__ = "services"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit,
            "price": self.price,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# TVA Model
class Tva(Base):
    """SQLAlchemy model for TVA table"""
    __tablename__ = "tva"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "rate": self.rate,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ABIC Model
class Abic(Base):
    """SQLAlchemy model for ABIC table"""
    __tablename__ = "abic"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "rate": self.rate,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Stock Movement Item (JSON field in StockMovement)
class StockMovementItem(Base):
    """SQLAlchemy model for Stock Movement Items (separate table for better querying)"""
    __tablename__ = "stock_movement_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stock_movement_id: Mapped[int] = mapped_column(Integer, ForeignKey("stock_movements.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    stock_movement: Mapped["StockMovement"] = relationship("StockMovement", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "stock_movement_id": self.stock_movement_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
            "unit": self.unit
        }


# Stock Movement Model
class StockMovement(Base):
    """SQLAlchemy model for Stock Movement table"""
    __tablename__ = "stock_movements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    movement_type: Mapped[StockMovementType] = mapped_column(Enum(StockMovementType), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clients.id"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="stock_movements")
    customer: Mapped[Optional["Client"]] = relationship("Client", back_populates="stock_movements")
    items: Mapped[List["StockMovementItem"]] = relationship("StockMovementItem", back_populates="stock_movement")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "movement_type": self.movement_type.value,
            "label": self.label,
            "supplier_id": self.supplier_id,
            "customer_id": self.customer_id,
            "reason": self.reason,
            "author": self.author,
            "details": self.details,
            "document_reference": self.document_reference,
            "total_value": self.total_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Sale Item (JSON field in Sale)
class SaleItem(Base):
    """SQLAlchemy model for Sale Items (separate table for better querying)"""
    __tablename__ = "sale_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Can be product_id or service_id
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "product" or "service"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "item_reference": self.item_reference,
            "item_type": self.item_type,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
            "unit": self.unit
        }


# Sale Model
class Sale(Base):
    """SQLAlchemy model for Sale table"""
    __tablename__ = "sales"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seller_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    tva_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tva_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(Enum(PaymentMethod), nullable=True)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    print_after_creation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="sales")
    items: Mapped[List["SaleItem"]] = relationship("SaleItem", back_populates="sale")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "reference": self.reference,
            "date": self.date.isoformat() if self.date else None,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "seller_id": self.seller_id,
            "subtotal": self.subtotal,
            "discount": self.discount,
            "tva_rate": self.tva_rate,
            "tva_amount": self.tva_amount,
            "total": self.total,
            "payment_status": self.payment_status.value,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "amount_paid": self.amount_paid,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "print_after_creation": self.print_after_creation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
