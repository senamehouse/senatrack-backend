from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class Supplier(Base):
    """SQLAlchemy model for Supplier table (tenant-scoped)"""
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        details = self.details or {}
        return {
            "supplierCode": f"SUP-{self.id[:8].upper()}",
            "contactPerson": None,
            "city": None,
            "country": None,
            "postalCode": None,
            "taxNumber": None,
            "paymentTerms": "net_30",
            "currency": "XOF",
            "notes": None,
            **details,
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "date": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }




