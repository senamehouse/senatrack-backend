from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.product_schema import (
    Product, ProductCreate, ProductUpdate,
    ProductCategory, ProductCategoryCreate, ProductCategoryUpdate,
    Unit, UnitCreate, UnitUpdate,
    ProductStats, ProductCategoryStats, UnitStats
)
from app.services.product_service import ProductService
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.utils.activity_logger import ActivityActor

router = APIRouter(prefix="/products", tags=["Products"])
product_service = ProductService()

# Product Category Routes
@router.get("/categories", response_model=List[ProductCategory])
async def get_all_categories(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get all product categories"""
    return await product_service.get_all_categories(company_id)

@router.get("/categories/{category_id}", response_model=ProductCategory)
async def get_category(
    category_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get product category by ID"""
    category = await product_service.get_category_by_id(category_id, company_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/categories", response_model=dict)
async def create_category(
    category_data: ProductCategoryCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Create a new product category"""
    category_id = await product_service.create_category(category_data=category_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    return {"message": "Category created successfully", "category_id": category_id}

@router.put("/categories/{category_id}", response_model=dict)
async def update_category(
    category_id: str,
    category_data: ProductCategoryUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Update a product category"""
    success = await product_service.update_category(category_id=category_id, category_data=category_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated successfully"}

@router.delete("/categories/{category_id}", response_model=dict)
async def delete_category(
    category_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Delete a product category"""
    success = await product_service.delete_category(category_id=category_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Unit Routes
@router.get("/units", response_model=List[Unit])
async def get_all_units(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get all units"""
    return await product_service.get_all_units(company_id)

@router.get("/units/{unit_id}", response_model=Unit)
async def get_unit(
    unit_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get unit by ID"""
    unit = await product_service.get_unit_by_id(unit_id, company_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit

@router.post("/units", response_model=dict)
async def create_unit(
    unit_data: UnitCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Create a new unit"""
    unit_id = await product_service.create_unit(unit_data=unit_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    return {"message": "Unit created successfully", "unit_id": unit_id}

@router.put("/units/{unit_id}", response_model=dict)
async def update_unit(
    unit_id: str,
    unit_data: UnitUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Update a unit"""
    success = await product_service.update_unit(unit_id=unit_id, unit_data=unit_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"message": "Unit updated successfully"}

@router.delete("/units/{unit_id}", response_model=dict)
async def delete_unit(
    unit_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Delete a unit"""
    success = await product_service.delete_unit(unit_id=unit_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"message": "Unit deleted successfully"}

# Product Routes
@router.get("/", response_model=List[Product])
async def get_all_products(
    category_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get all products, optionally filtered by category"""
    if category_id:
        return await product_service.get_products_by_category(category_id, company_id)
    return await product_service.get_all_products(company_id)

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get product by ID"""
    product = await product_service.get_product_by_id(product_id, company_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=dict)
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Create a new product"""
    product_id = await product_service.create_product(product_data=product_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    return {"message": "Product created successfully", "product_id": product_id}

@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Update a product"""
    success = await product_service.update_product(product_id=product_id, product_data=product_data, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}

@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Delete a product"""
    success = await product_service.delete_product(product_id=product_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Statistics Routes
@router.get("/stats/products", response_model=ProductStats)
async def get_product_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get product statistics"""
    return await product_service.get_product_stats(company_id)

@router.get("/stats/categories", response_model=ProductCategoryStats)
async def get_category_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get product category statistics"""
    return await product_service.get_category_stats(company_id)

@router.get("/stats/units", response_model=UnitStats)
async def get_unit_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    """Get unit statistics"""
    return await product_service.get_unit_stats(company_id)

