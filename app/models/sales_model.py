from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text
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
    payment_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    print_after_creation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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
            "payment_method": self.payment_method,
            "amount_paid": self.amount_paid,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "print_after_creation": self.print_after_creation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }




