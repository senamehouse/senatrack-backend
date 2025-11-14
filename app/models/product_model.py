from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class ProductCategory(Base):
    """SQLAlchemy model for Product Category table"""
    __tablename__ = "product_categories"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ProductUnit(Base):
    """SQLAlchemy model for Unit table"""
    __tablename__ = "units"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="unit")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Product(Base):
    """SQLAlchemy model for Product table"""
    __tablename__ = "products"
    
    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    buy_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sell_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Foreign keys
    category_id: Mapped[str] = mapped_column(String(20), ForeignKey("product_categories.id"), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(20), ForeignKey("units.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category: Mapped["ProductCategory"] = relationship("ProductCategory", back_populates="products")
    unit: Mapped["ProductUnit"] = relationship("ProductUnit", back_populates="products")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sku": self.sku,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "stock": self.stock,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "category_id": self.category_id,
            "unit_id": self.unit_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

