from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, Float, Text
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class Department(Base):
    """SQLAlchemy model for Department (tenant-scoped)"""
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "manager_id": self.manager_id,
            "budget": self.budget,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

