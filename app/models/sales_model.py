from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    reference: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    client_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seller_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    tva_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tva_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items: Mapped[List["SaleItem"]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
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
            "payment_status": self.payment_status,
            "amount_paid": self.amount_paid,
            "payment_reference": self.payment_reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    sale_id: Mapped[str] = mapped_column(String(20), ForeignKey("sales.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(20), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # product|service
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    sell_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_sell_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price_modified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_reference": self.product_reference,
            "item_type": self.item_type,
            "quantity": self.quantity,
            "sell_price": self.sell_price,
            "original_sell_price": self.original_sell_price,
            "total": self.total,
            "unit": self.unit,
            "price_modified": self.price_modified,
        }




