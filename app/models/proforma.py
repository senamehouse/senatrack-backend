from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import Base

class Proforma(Base):
    """Proforma model"""
    __tablename__ = "proformas"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(100), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    client = Column(JSON, nullable=False)  # Store client info as JSON
    items = Column(JSON, nullable=False)  # Store items as JSON array
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")  # draft, sent, accepted, rejected
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")
    creator = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "number": self.number,
            "date": self.date.isoformat() if self.date else None,
            "client": self.client,
            "items": self.items,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "total": self.total,
            "notes": self.notes,
            "status": self.status,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
