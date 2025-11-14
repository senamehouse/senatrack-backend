from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id

if TYPE_CHECKING:
    from app.models.company_model import Company


class TvaRateModel(Base):
    """SQLAlchemy model for TVA Rate table"""
    __tablename__ = "tva_rates"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[str] = mapped_column(String(20), ForeignKey("companies.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", foreign_keys=[company_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companyId": self.company_id,
            "name": self.name,
            "rate": self.rate,
            "isDefault": self.is_default,
            "isActive": self.is_active,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }

