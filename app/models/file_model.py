from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class FileRecord(Base):
    """Comprehensive file storage tracking model"""
    __tablename__ = "file_records"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    remote_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Generic linkage to any entity field
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional company scoping for multi-tenant entities
    company_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    storage_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="hybrid")
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "remote_url": self.remote_url,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "file_hash": self.file_hash,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "company_id": self.company_id,
            "storage_mode": self.storage_mode,
            "sync_status": self.sync_status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }


