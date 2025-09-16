from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import Base

class ActivationKey(Base):
    """Activation key model"""
    __tablename__ = "activation_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False)  # free_trial, basic, premium, enterprise
    duration = Column(Integer, nullable=False)  # Duration in days
    status = Column(String(50), nullable=False, default="active")  # active, used, expired, cancelled
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by = Column(Integer, ForeignKey("companies.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    used_company = relationship("Company", foreign_keys=[used_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "key": self.key,
            "plan": self.plan,
            "duration": self.duration,
            "status": self.status,
            "created_by": self.created_by,
            "used_by": self.used_by,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
