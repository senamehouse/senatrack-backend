from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class ActivityLog(Base):
    """SQLAlchemy model for Activity Log table"""
    __tablename__ = "activity_logs"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "action": self.action,
            "details": self.details,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "company_id": self.company_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
