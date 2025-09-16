import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.product import Product as ProductModel, ProductCategory as ProductCategoryModel, Unit as UnitModel
from app.models.sync import SyncLog
from app.schemas.product import (
    ProductCreate, ProductUpdate, Product as ProductSchema,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategory as ProductCategorySchema,
    UnitCreate, UnitUpdate, Unit as UnitSchema,
    ProductStats, ProductCategoryStats, UnitStats
)


class ProductService:
    """Service for product-related database operations"""
    
    # Product Category methods
    async def get_all_categories(self) -> List[ProductCategorySchema]:
        """Get all active product categories"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductCategoryModel).where(ProductCategoryModel.is_active == True)
                )
                categories = result.scalars().all()
                return [ProductCategorySchema(**category.to_dict()) for category in categories]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")
    
    async def get_category_by_id(self, category_id: int) -> Optional[ProductCategorySchema]:
        """Get a product category by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductCategoryModel).where(
                        ProductCategoryModel.id == category_id,
                        ProductCategoryModel.is_active == True
                    )
                )
                category = result.scalar_one_or_none()
                return ProductCategorySchema(**category.to_dict()) if category else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving category: {str(e)}")
    
    async def create_category(self, category_data: ProductCategoryCreate) -> int:
        """Create a new product category and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                category = ProductCategoryModel(
                    name=category_data.name,
                    description=category_data.description
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='product_categories',
                    record_id=category.id,
                    data=json.dumps(category.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return category.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")
    
    async def update_category(self, category_id: int, category_data: ProductCategoryUpdate) -> bool:
        """Update a product category by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductCategoryModel).where(ProductCategoryModel.id == category_id)
                )
                category = result.scalar_one_or_none()
                
                if not category:
                    return False
                
                # Update fields
                if category_data.name is not None:
                    category.name = category_data.name
                if category_data.description is not None:
                    category.description = category_data.description
                if category_data.is_active is not None:
                    category.is_active = category_data.is_active
                
                category.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='product_categories',
                    record_id=category.id,
                    data=json.dumps(category.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")
    
    async def delete_category(self, category_id: int) -> bool:
        """Delete a product category by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductCategoryModel).where(ProductCategoryModel.id == category_id)
                )
                category = result.scalar_one_or_none()
                
                if not category:
                    return False
                
                # Soft delete
                category.is_active = False
                category.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='product_categories',
                    record_id=category.id,
                    data=json.dumps(category.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting category: {str(e)}")
    
    # Unit methods
    async def get_all_units(self) -> List[UnitSchema]:
        """Get all active units"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UnitModel).where(UnitModel.is_active == True)
                )
                units = result.scalars().all()
                return [UnitSchema(**unit.to_dict()) for unit in units]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving units: {str(e)}")
    
    async def get_unit_by_id(self, unit_id: int) -> Optional[UnitSchema]:
        """Get a unit by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UnitModel).where(
                        UnitModel.id == unit_id,
                        UnitModel.is_active == True
                    )
                )
                unit = result.scalar_one_or_none()
                return UnitSchema(**unit.to_dict()) if unit else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving unit: {str(e)}")
    
    async def create_unit(self, unit_data: UnitCreate) -> int:
        """Create a new unit and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                unit = UnitModel(
                    name=unit_data.name,
                    abbreviation=unit_data.abbreviation,
                    description=unit_data.description
                )
                session.add(unit)
                await session.commit()
                await session.refresh(unit)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='units',
                    record_id=unit.id,
                    data=json.dumps(unit.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return unit.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating unit: {str(e)}")
    
    async def update_unit(self, unit_id: int, unit_data: UnitUpdate) -> bool:
        """Update a unit by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UnitModel).where(UnitModel.id == unit_id)
                )
                unit = result.scalar_one_or_none()
                
                if not unit:
                    return False
                
                # Update fields
                if unit_data.name is not None:
                    unit.name = unit_data.name
                if unit_data.abbreviation is not None:
                    unit.abbreviation = unit_data.abbreviation
                if unit_data.description is not None:
                    unit.description = unit_data.description
                if unit_data.is_active is not None:
                    unit.is_active = unit_data.is_active
                
                unit.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='units',
                    record_id=unit.id,
                    data=json.dumps(unit.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating unit: {str(e)}")
    
    async def delete_unit(self, unit_id: int) -> bool:
        """Delete a unit by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UnitModel).where(UnitModel.id == unit_id)
                )
                unit = result.scalar_one_or_none()
                
                if not unit:
                    return False
                
                # Soft delete
                unit.is_active = False
                unit.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='units',
                    record_id=unit.id,
                    data=json.dumps(unit.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting unit: {str(e)}")
    
    # Product methods
    async def get_all_products(self) -> List[ProductSchema]:
        """Get all active products"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductModel).where(ProductModel.is_active == True)
                )
                products = result.scalars().all()
                return [ProductSchema(**product.to_dict()) for product in products]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")
    
    async def get_product_by_id(self, product_id: int) -> Optional[ProductSchema]:
        """Get a product by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductModel).where(
                        ProductModel.id == product_id,
                        ProductModel.is_active == True
                    )
                )
                product = result.scalar_one_or_none()
                return ProductSchema(**product.to_dict()) if product else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")
    
    async def get_products_by_category(self, category_id: int) -> List[ProductSchema]:
        """Get products by category ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductModel).where(
                        and_(
                            ProductModel.category_id == category_id,
                            ProductModel.is_active == True
                        )
                    )
                )
                products = result.scalars().all()
                return [ProductSchema(**product.to_dict()) for product in products]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products by category: {str(e)}")
    
    async def create_product(self, product_data: ProductCreate) -> int:
        """Create a new product and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                product = ProductModel(
                    name=product_data.name,
                    description=product_data.description,
                    sku=product_data.sku,
                    buy_price=product_data.buy_price,
                    unit_price=product_data.unit_price,
                    stock=product_data.stock,
                    stock_alert_threshold=product_data.stock_alert_threshold,
                    image_url=product_data.image_url,
                    category_id=product_data.category_id,
                    unit_id=product_data.unit_id
                )
                session.add(product)
                await session.commit()
                await session.refresh(product)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='products',
                    record_id=product.id,
                    data=json.dumps(product.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return product.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")
    
    async def update_product(self, product_id: int, product_data: ProductUpdate) -> bool:
        """Update a product by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductModel).where(ProductModel.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False
                
                # Update fields
                if product_data.name is not None:
                    product.name = product_data.name
                if product_data.description is not None:
                    product.description = product_data.description
                if product_data.sku is not None:
                    product.sku = product_data.sku
                if product_data.buy_price is not None:
                    product.buy_price = product_data.buy_price
                if product_data.unit_price is not None:
                    product.unit_price = product_data.unit_price
                if product_data.stock is not None:
                    product.stock = product_data.stock
                if product_data.stock_alert_threshold is not None:
                    product.stock_alert_threshold = product_data.stock_alert_threshold
                if product_data.image_url is not None:
                    product.image_url = product_data.image_url
                if product_data.category_id is not None:
                    product.category_id = product_data.category_id
                if product_data.unit_id is not None:
                    product.unit_id = product_data.unit_id
                if product_data.is_active is not None:
                    product.is_active = product_data.is_active
                
                product.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='products',
                    record_id=product.id,
                    data=json.dumps(product.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")
    
    async def delete_product(self, product_id: int) -> bool:
        """Delete a product by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ProductModel).where(ProductModel.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False
                
                # Soft delete
                product.is_active = False
                product.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='products',
                    record_id=product.id,
                    data=json.dumps(product.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")
    
    # Statistics methods
    async def get_product_stats(self) -> ProductStats:
        """Get product statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total products
                total_result = await session.execute(
                    select(func.count(ProductModel.id))
                )
                total = total_result.scalar()
                
                # Active products
                active_result = await session.execute(
                    select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Low stock products
                low_stock_result = await session.execute(
                    select(func.count(ProductModel.id)).where(
                        and_(
                            ProductModel.is_active == True,
                            ProductModel.stock <= ProductModel.stock_alert_threshold,
                            ProductModel.stock > 0
                        )
                    )
                )
                low_stock = low_stock_result.scalar()
                
                # Out of stock products
                out_of_stock_result = await session.execute(
                    select(func.count(ProductModel.id)).where(
                        and_(
                            ProductModel.is_active == True,
                            ProductModel.stock == 0
                        )
                    )
                )
                out_of_stock = out_of_stock_result.scalar()
                
                # Categories count
                categories_result = await session.execute(
                    select(func.count(ProductCategoryModel.id)).where(ProductCategoryModel.is_active == True)
                )
                categories = categories_result.scalar()
                
                # Average price
                avg_price_result = await session.execute(
                    select(func.avg(ProductModel.unit_price)).where(ProductModel.is_active == True)
                )
                average_price = avg_price_result.scalar() or 0.0
                
                return ProductStats(
                    total=total,
                    active=active,
                    low_stock=low_stock,
                    out_of_stock=out_of_stock,
                    categories=categories,
                    average_price=round(average_price, 2)
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting product stats: {str(e)}")
    
    async def get_category_stats(self) -> ProductCategoryStats:
        """Get product category statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total categories
                total_result = await session.execute(
                    select(func.count(ProductCategoryModel.id))
                )
                total = total_result.scalar()
                
                # Active categories
                active_result = await session.execute(
                    select(func.count(ProductCategoryModel.id)).where(ProductCategoryModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Products count
                products_result = await session.execute(
                    select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
                )
                products_count = products_result.scalar()
                
                return ProductCategoryStats(
                    total=total,
                    active=active,
                    products_count=products_count
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting category stats: {str(e)}")
    
    async def get_unit_stats(self) -> UnitStats:
        """Get unit statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total units
                total_result = await session.execute(
                    select(func.count(UnitModel.id))
                )
                total = total_result.scalar()
                
                # Active units
                active_result = await session.execute(
                    select(func.count(UnitModel.id)).where(UnitModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Products count
                products_result = await session.execute(
                    select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
                )
                products_count = products_result.scalar()
                
                return UnitStats(
                    total=total,
                    active=active,
                    products_count=products_count
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting unit stats: {str(e)}")

