from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class UserRole(Base):
    """Platform-level roles for system access control"""
    __tablename__ = "user_roles"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Cannot be deleted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignments = relationship("UserRoleAssignment", back_populates="role", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "is_preset": self.is_preset,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserRoleAssignment(Base):
    """Links users to platform roles"""
    __tablename__ = "user_role_assignments"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[str] = mapped_column(String(20), ForeignKey("user_roles.id"), nullable=False, index=True)
    assigned_by: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="role_assignments")
    role = relationship("UserRole", back_populates="assignments")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None
        }

