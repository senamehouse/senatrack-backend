from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional, List


# Product Category Schemas
class ProductCategoryBase(BaseCamelModel):
    """Base product category schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    """Schema for creating a product category"""
    pass


class ProductCategoryUpdate(BaseCamelModel):
    """Schema for updating a product category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class ProductCategory(ProductCategoryBase):
    """Schema for product category response"""
    id: str
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Unit Schemas
class UnitBase(BaseCamelModel):
    """Base unit schema"""
    name: str = Field(..., min_length=1, max_length=100)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    description: Optional[str] = None


class UnitCreate(UnitBase):
    """Schema for creating a unit"""
    pass


class UnitUpdate(BaseCamelModel):
    """Schema for updating a unit"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    abbreviation: Optional[str] = Field(None, min_length=1, max_length=10)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")


class Unit(UnitBase):
    """Schema for unit response"""
    id: str
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Product Schemas
class ProductBase(BaseCamelModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    buy_price: float = Field(..., ge=0, alias="buyPrice")
    sell_price: float = Field(..., ge=0, alias="sellPrice")
    stock: int = Field(..., ge=0)
    image_url: Optional[str] = Field(None, max_length=500, alias="imageUrl")
    

class ProductCreate(ProductBase):
    """Schema for creating a product"""
    category_id: str = Field(..., alias="categoryId")
    unit_id: str = Field(..., alias="unitId")


class ProductUpdate(BaseCamelModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    buy_price: Optional[float] = Field(None, ge=0, alias="buyPrice")
    sell_price: Optional[float] = Field(None, ge=0, alias="sellPrice")
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500, alias="imageUrl")
    category_id: Optional[str] = Field(None, alias="categoryId")
    unit_id: Optional[str] = Field(None, alias="unitId")
    is_active: Optional[bool] = Field(None, alias="isActive")


class Product(ProductBase):
    """Schema for product response"""
    id: str
    category_id: str = Field(..., alias="categoryId")
    unit_id: str = Field(..., alias="unitId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


class ProductWithDetails(Product):
    """Schema for product with related data"""
    category: ProductCategory
    unit: Unit


# Bulk operations schemas
class BulkProductCreate(BaseCamelModel):
    """Schema for bulk product creation"""
    products: List[ProductCreate]


class BulkProductCategoryCreate(BaseCamelModel):
    """Schema for bulk product category creation"""
    categories: List[ProductCategoryCreate]


class BulkUnitCreate(BaseCamelModel):
    """Schema for bulk unit creation"""
    units: List[UnitCreate]


# Statistics schemas
class ProductStats(BaseCamelModel):
    """Schema for product statistics"""
    total: int
    active: int
    low_stock: int
    out_of_stock: int
    categories: int
    average_price: float


class ProductCategoryStats(BaseCamelModel):
    """Schema for product category statistics"""
    total: int
    active: int
    products_count: int


class UnitStats(BaseCamelModel):
    """Schema for unit statistics"""
    total: int
    active: int
    products_count: int

