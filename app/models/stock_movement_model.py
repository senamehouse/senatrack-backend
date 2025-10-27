from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # entree|sortie|ajustement
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "date": self.date.isoformat() if self.date else None,
            "movement_type": self.movement_type,
            "label": self.label,
            "supplier_id": self.supplier_id,
            "customer_id": self.customer_id,
            "reason": self.reason,
            "author": self.author,
            "details": self.details,
            "document_reference": self.document_reference,
            "total_value": self.total_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockMovementItem(Base):
    __tablename__ = "stock_movement_items"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    stock_movement_id: Mapped[str] = mapped_column(String(20), ForeignKey("stock_movements.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(20), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "stock_movement_id": self.stock_movement_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
            "unit": self.unit,
        }




