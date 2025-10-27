from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import Base
from app.utils.id_generator import generate_id

class CompanyInvitation(Base):
    """Company invitation model"""
    __tablename__ = "company_invitations"
    
    id = Column(String(20), primary_key=True, index=True, default=generate_id)
    company_id = Column(String(20), ForeignKey("companies.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, manager, operator, viewer
    invited_by = Column(String(20), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=True)
    token = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, accepted, declined, expired
    invited_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(String(20), ForeignKey("users.id"), nullable=True)
    declined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")
    inviter = relationship("User", foreign_keys=[invited_by])
    accepter = relationship("User", foreign_keys=[accepted_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "email": self.email,
            "role": self.role,
            "invited_by": self.invited_by,
            "message": self.message,
            "token": self.token,
            "status": self.status,
            "invited_at": self.invited_at.isoformat() if self.invited_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "accepted_by": self.accepted_by,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
