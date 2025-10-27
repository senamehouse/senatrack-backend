from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import Base
from app.utils.id_generator import generate_id

class Company(Base):
    """Company model"""
    __tablename__ = "companies"
    
    id = Column(String(20), primary_key=True, index=True, default=generate_id)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    currency = Column(String(10), nullable=False, default="XOF")
    language = Column(String(10), nullable=False, default="fr")
    timezone = Column(String(50), nullable=False, default="Africa/Dakar")
    tax_id = Column(String(100), nullable=True)
    registration_number = Column(String(100), nullable=True)
    owner_id = Column(String(20), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, nullable=True)
    subscription = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="owned_companies", foreign_keys=[owner_id])
    members = relationship("CompanyMember", back_populates="company", cascade="all, delete-orphan")
    
    # New role system relationships
    company_roles = relationship("UserCompanyRole", back_populates="company", foreign_keys="UserCompanyRole.company_id", cascade="all, delete-orphan")
    company_role_assignments = relationship("UserCompanyRoleAssignment", back_populates="company", foreign_keys="UserCompanyRoleAssignment.company_id", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "website": self.website,
            "logo_url": self.logo_url,
            "currency": self.currency,
            "language": self.language,
            "timezone": self.timezone,
            "tax_id": self.tax_id,
            "registration_number": self.registration_number,
            "owner_id": self.owner_id,
            "settings": self.settings,
            "subscription": self.subscription,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class CompanyMember(Base):
    """Company member model"""
    __tablename__ = "company_members"
    
    id = Column(String(20), primary_key=True, index=True, default=generate_id)
    company_id = Column(String(20), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(20), ForeignKey("users.id"), nullable=False)
    invited_by = Column(String(20), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow)
    joined_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "invited_by": self.invited_by,
            "invited_at": self.invited_at.isoformat() if self.invited_at else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
