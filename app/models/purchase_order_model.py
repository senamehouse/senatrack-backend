from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("company_id", "order_number", name="uq_purchase_orders_company_order_number"),)

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    order_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        details = self.details or {}
        return {
            "supplierName": "",
            "orderDate": self.created_at.isoformat() if self.created_at else "",
            "items": [],
            "subtotal": self.total_amount,
            "taxRate": 0,
            "taxAmount": 0,
            "currency": "FCFA",
            **details,
            "id": self.id,
            "companyId": self.company_id,
            "orderNumber": self.order_number,
            "supplierId": self.supplier_id or "",
            "status": self.status,
            "totalAmount": self.total_amount,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }




