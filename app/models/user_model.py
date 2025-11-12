from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class User(Base):
    """Async SQLAlchemy model for User table"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    current_company_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("companies.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owned_companies = relationship("Company", back_populates="owner", foreign_keys="Company.owner_id")
    current_company = relationship("Company", foreign_keys=[current_company_id])
    
    # New role system relationships
    role_assignments: Mapped[list["UserRoleAssignmentModel"]] = relationship("UserRoleAssignmentModel", back_populates="user", foreign_keys="UserRoleAssignmentModel.user_id", cascade="all, delete-orphan")
    company_role_assignments: Mapped[list["UserCompanyRoleAssignmentModel"]] = relationship("UserCompanyRoleAssignmentModel", back_populates="user", foreign_keys="UserCompanyRoleAssignmentModel.user_id", cascade="all, delete-orphan")
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "current_company_id": self.current_company_id,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
        if include_password:
            data["hashed_password"] = self.hashed_password
        return data


class UserRoleModel(Base):
    """Platform-level roles for system access control"""
    __tablename__ = "user_roles"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Cannot be deleted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignments: Mapped[list["UserRoleAssignmentModel"]] = relationship("UserRoleAssignmentModel", back_populates="role", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "isPreset": self.is_preset,
            "isSystem": self.is_system,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }


class UserRoleAssignmentModel(Base):
    """Links users to platform roles"""
    __tablename__ = "user_role_assignments"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[str] = mapped_column(String(20), ForeignKey("user_roles.id"), nullable=False, index=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="role_assignments")
    role: Mapped["UserRoleModel"] = relationship("UserRoleModel", back_populates="assignments")
    assigned_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "userId": self.user_id,
            "roleId": self.role_id,
            "assignedBy": self.assigned_by,
            "assignedAt": self.assigned_at.isoformat() if self.assigned_at else None
        }
