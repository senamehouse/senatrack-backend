from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class SyncLog(Base):
    """Async SQLAlchemy model for sync operations tracking"""
    __tablename__ = "sync_log"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[str] = mapped_column(String(20), nullable=False)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON data
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "operation": self.operation,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "data": self.data,
            "synced": self.synced,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None
        }
