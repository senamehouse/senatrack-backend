from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# Product Category Schemas
class ProductCategoryBase(BaseModel):
    """Base product category schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    """Schema for creating a product category"""
    pass


class ProductCategoryUpdate(BaseModel):
    """Schema for updating a product category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


class ProductCategory(ProductCategoryBase):
    """Schema for product category response"""
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


# Unit Schemas
class UnitBase(BaseModel):
    """Base unit schema"""
    name: str = Field(..., min_length=1, max_length=100)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    description: Optional[str] = None


class UnitCreate(UnitBase):
    """Schema for creating a unit"""
    pass


class UnitUpdate(BaseModel):
    """Schema for updating a unit"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    abbreviation: Optional[str] = Field(None, min_length=1, max_length=10)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


class Unit(UnitBase):
    """Schema for unit response"""
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    buy_price: float = Field(..., ge=0, alias="buyPrice")
    unit_price: float = Field(..., ge=0, alias="unitPrice")
    stock: int = Field(..., ge=0)
    stock_alert_threshold: int = Field(..., ge=0, alias="stockAlertThreshold")
    image_url: Optional[str] = Field(None, max_length=500, alias="imageUrl")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    category_id: int = Field(..., alias="categoryId")
    unit_id: int = Field(..., alias="unitId")


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    buy_price: Optional[float] = Field(None, ge=0, alias="buyPrice")
    unit_price: Optional[float] = Field(None, ge=0, alias="unitPrice")
    stock: Optional[int] = Field(None, ge=0)
    stock_alert_threshold: Optional[int] = Field(None, ge=0, alias="stockAlertThreshold")
    image_url: Optional[str] = Field(None, max_length=500, alias="imageUrl")
    category_id: Optional[int] = Field(None, alias="categoryId")
    unit_id: Optional[int] = Field(None, alias="unitId")
    is_active: Optional[bool] = Field(None, alias="isActive")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        serialize_by_alias = True


class Product(ProductBase):
    """Schema for product response"""
    id: int
    category_id: int = Field(..., alias="categoryId")
    unit_id: int = Field(..., alias="unitId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True


class ProductWithDetails(Product):
    """Schema for product with related data"""
    category: ProductCategory
    unit: Unit


# Bulk operations schemas
class BulkProductCreate(BaseModel):
    """Schema for bulk product creation"""
    products: List[ProductCreate]


class BulkProductCategoryCreate(BaseModel):
    """Schema for bulk product category creation"""
    categories: List[ProductCategoryCreate]


class BulkUnitCreate(BaseModel):
    """Schema for bulk unit creation"""
    units: List[UnitCreate]


# Statistics schemas
class ProductStats(BaseModel):
    """Schema for product statistics"""
    total: int
    active: int
    low_stock: int
    out_of_stock: int
    categories: int
    average_price: float


class ProductCategoryStats(BaseModel):
    """Schema for product category statistics"""
    total: int
    active: int
    products_count: int


class UnitStats(BaseModel):
    """Schema for unit statistics"""
    total: int
    active: int
    products_count: int

