from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.schemas.product import (
    Product, ProductCreate, ProductUpdate,
    ProductCategory, ProductCategoryCreate, ProductCategoryUpdate,
    Unit, UnitCreate, UnitUpdate,
    ProductStats, ProductCategoryStats, UnitStats
)
from app.services.product import ProductService
from app.core.dependencies import get_current_user
from app.schemas.user import User

router = APIRouter(prefix="/products", tags=["Products"])
product_service = ProductService()

# Product Category Routes
@router.get("/categories", response_model=List[ProductCategory])
async def get_all_categories(current_user: User = Depends(get_current_user)):
    """Get all product categories"""
    return await product_service.get_all_categories()

@router.get("/categories/{category_id}", response_model=ProductCategory)
async def get_category(
    category_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get product category by ID"""
    category = await product_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/categories", response_model=dict)
async def create_category(
    category_data: ProductCategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new product category"""
    category_id = await product_service.create_category(category_data)
    return {"message": "Category created successfully", "category_id": category_id}

@router.put("/categories/{category_id}", response_model=dict)
async def update_category(
    category_id: int,
    category_data: ProductCategoryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a product category"""
    success = await product_service.update_category(category_id, category_data)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated successfully"}

@router.delete("/categories/{category_id}", response_model=dict)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a product category"""
    success = await product_service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Unit Routes
@router.get("/units", response_model=List[Unit])
async def get_all_units(current_user: User = Depends(get_current_user)):
    """Get all units"""
    return await product_service.get_all_units()

@router.get("/units/{unit_id}", response_model=Unit)
async def get_unit(
    unit_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get unit by ID"""
    unit = await product_service.get_unit_by_id(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit

@router.post("/units", response_model=dict)
async def create_unit(
    unit_data: UnitCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new unit"""
    unit_id = await product_service.create_unit(unit_data)
    return {"message": "Unit created successfully", "unit_id": unit_id}

@router.put("/units/{unit_id}", response_model=dict)
async def update_unit(
    unit_id: int,
    unit_data: UnitUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a unit"""
    success = await product_service.update_unit(unit_id, unit_data)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"message": "Unit updated successfully"}

@router.delete("/units/{unit_id}", response_model=dict)
async def delete_unit(
    unit_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a unit"""
    success = await product_service.delete_unit(unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"message": "Unit deleted successfully"}

# Product Routes
@router.get("/", response_model=List[Product])
async def get_all_products(
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get all products, optionally filtered by category"""
    if category_id:
        return await product_service.get_products_by_category(category_id)
    return await product_service.get_all_products()

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get product by ID"""
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=dict)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new product"""
    product_id = await product_service.create_product(product_data)
    return {"message": "Product created successfully", "product_id": product_id}

@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    success = await product_service.update_product(product_id, product_data)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}

@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a product"""
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Statistics Routes
@router.get("/stats/products", response_model=ProductStats)
async def get_product_stats(current_user: User = Depends(get_current_user)):
    """Get product statistics"""
    return await product_service.get_product_stats()

@router.get("/stats/categories", response_model=ProductCategoryStats)
async def get_category_stats(current_user: User = Depends(get_current_user)):
    """Get product category statistics"""
    return await product_service.get_category_stats()

@router.get("/stats/units", response_model=UnitStats)
async def get_unit_stats(current_user: User = Depends(get_current_user)):
    """Get unit statistics"""
    return await product_service.get_unit_stats()

