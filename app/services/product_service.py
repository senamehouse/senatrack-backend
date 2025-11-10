import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func, and_
from app.core.database import get_db_session
from app.models.product_model import Product as ProductModel, ProductCategory as ProductCategoryModel, ProductUnit as UnitModel
from app.models.sync_model import SyncLog
from app.schemas.product_schema import (
    ProductCreate, ProductUpdate, Product as ProductSchema,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategory as ProductCategorySchema,
    UnitCreate, UnitUpdate, Unit as UnitSchema,
    ProductStats, ProductCategoryStats, UnitStats
)


class ProductService:
    """Service for product-related database operations"""
    
    # Product Category methods
    async def get_all_categories(self, company_id: str | None = None) -> List[ProductCategorySchema]:
        """Get all active product categories"""
        try:
            session = get_db_session()
            query = select(ProductCategoryModel).where(ProductCategoryModel.is_active == True)
            if company_id:
                query = query.where(ProductCategoryModel.company_id == company_id)
            result = await session.execute(query)
            categories = result.scalars().all()
            return [ProductCategorySchema(**category.to_dict()) for category in categories]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")
    
    async def get_category_by_id(self, category_id: str, company_id: str | None = None) -> Optional[ProductCategorySchema]:
        """Get a product category by ID"""
        try:
            session = get_db_session()
            query = select(ProductCategoryModel).where(
                ProductCategoryModel.id == category_id,
                ProductCategoryModel.is_active == True
            )
            if company_id:
                query = query.where(ProductCategoryModel.company_id == company_id)
            result = await session.execute(query)
            category = result.scalar_one_or_none()
            return ProductCategorySchema(**category.to_dict()) if category else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving category: {str(e)}")
    
    async def create_category(self, category_data: ProductCategoryCreate, company_id: str | None = None) -> str:
        """Create a new product category and return the ID"""
        try:
            session = get_db_session()
            category = ProductCategoryModel(
                name=category_data.name,
                description=category_data.description,
                company_id=company_id
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
    
    async def update_category(self, category_id: str, category_data: ProductCategoryUpdate, company_id: str | None = None) -> bool:
        """Update a product category by ID"""
        try:
            session = get_db_session()
            query = select(ProductCategoryModel).where(ProductCategoryModel.id == category_id)
            if company_id:
                query = query.where(ProductCategoryModel.company_id == company_id)
            result = await session.execute(query)
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
    
    async def delete_category(self, category_id: str, company_id: str | None = None) -> bool:
        """Delete a product category by ID (soft delete)"""
        try:
            session = get_db_session()
            query = select(ProductCategoryModel).where(ProductCategoryModel.id == category_id)
            if company_id:
                query = query.where(ProductCategoryModel.company_id == company_id)
            result = await session.execute(query)
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
    async def get_all_units(self, company_id: str | None = None) -> List[UnitSchema]:
        """Get all active units"""
        try:
            session = get_db_session()
            query = select(UnitModel).where(UnitModel.is_active == True)
            if company_id:
                query = query.where(UnitModel.company_id == company_id)
            result = await session.execute(query)
            units = result.scalars().all()
            return [UnitSchema(**unit.to_dict()) for unit in units]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving units: {str(e)}")
    
    async def get_unit_by_id(self, unit_id: str, company_id: str | None = None) -> Optional[UnitSchema]:
        """Get a unit by ID"""
        try:
            session = get_db_session()
            query = select(UnitModel).where(UnitModel.id == unit_id, UnitModel.is_active == True)
            if company_id:
                query = query.where(UnitModel.company_id == company_id)
            result = await session.execute(query)
            unit = result.scalar_one_or_none()
            return UnitSchema(**unit.to_dict()) if unit else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving unit: {str(e)}")
    
    async def create_unit(self, unit_data: UnitCreate, company_id: str | None = None) -> str:
        """Create a new unit and return the ID"""
        try:
            session = get_db_session()
            unit = UnitModel(
                name=unit_data.name,
                abbreviation=unit_data.abbreviation,
                description=unit_data.description,
                company_id=company_id
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
    
    async def update_unit(self, unit_id: str, unit_data: UnitUpdate, company_id: str | None = None) -> bool:
        """Update a unit by ID"""
        try:
            session = get_db_session()
            query = select(UnitModel).where(UnitModel.id == unit_id)
            if company_id:
                query = query.where(UnitModel.company_id == company_id)
            result = await session.execute(query)
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
    
    async def delete_unit(self, unit_id: str, company_id: str | None = None) -> bool:
        """Delete a unit by ID (soft delete)"""
        try:
            session = get_db_session()
            query = select(UnitModel).where(UnitModel.id == unit_id)
            if company_id:
                query = query.where(UnitModel.company_id == company_id)
            result = await session.execute(query)
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
    async def get_all_products(self, company_id: str | None = None) -> List[ProductSchema]:
        """Get all active products"""
        try:
            session = get_db_session()
            query = select(ProductModel).where(ProductModel.is_active == True)
            if company_id:
                query = query.where(ProductModel.company_id == company_id)
            result = await session.execute(query)
            products = result.scalars().all()
            return [ProductSchema(**product.to_dict()) for product in products]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")
    
    async def get_product_by_id(self, product_id: str, company_id: str | None = None) -> Optional[ProductSchema]:
        """Get a product by ID"""
        try:
            session = get_db_session()
            query = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
            if company_id:
                query = query.where(ProductModel.company_id == company_id)
            result = await session.execute(query)
            product = result.scalar_one_or_none()
            return ProductSchema(**product.to_dict()) if product else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")
    
    async def get_products_by_category(self, category_id: str, company_id: str | None = None) -> List[ProductSchema]:
        """Get products by category ID"""
        try:
            session = get_db_session()
            query = select(ProductModel).where(
                and_(
                    ProductModel.category_id == category_id,
                    ProductModel.is_active == True,
                )
            )
            if company_id:
                query = query.where(ProductModel.company_id == company_id)
            result = await session.execute(query)
            products = result.scalars().all()
            return [ProductSchema(**product.to_dict()) for product in products]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products by category: {str(e)}")
    
    async def create_product(self, product_data: ProductCreate, company_id: str | None = None) -> str:
        """Create a new product and return the ID"""
        try:
            session = get_db_session()
            product = ProductModel(
                name=product_data.name,
                description=product_data.description,
                sku=product_data.sku,
                buy_price=product_data.buy_price,
                unit_price=product_data.unit_price,
                stock=product_data.stock,
                image_url=product_data.image_url,
                category_id=product_data.category_id,
                unit_id=product_data.unit_id,
                company_id=company_id
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
    
    async def update_product(self, product_id: str, product_data: ProductUpdate, company_id: str | None = None) -> bool:
        """Update a product by ID"""
        try:
            session = get_db_session()
            query = select(ProductModel).where(ProductModel.id == product_id)
            if company_id:
                query = query.where(ProductModel.company_id == company_id)
            result = await session.execute(query)
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
    
    async def delete_product(self, product_id: str, company_id: str | None = None) -> bool:
        """Delete a product by ID (soft delete)"""
        try:
            session = get_db_session()
            query = select(ProductModel).where(ProductModel.id == product_id)
            if company_id:
                query = query.where(ProductModel.company_id == company_id)
            result = await session.execute(query)
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
    async def get_product_stats(self, company_id: str | None = None) -> ProductStats:
        """Get product statistics"""
        try:
            session = get_db_session()
            # Total products
            q_total = select(func.count(ProductModel.id))
            if company_id:
                q_total = q_total.where(ProductModel.company_id == company_id)
            total_result = await session.execute(q_total)
            total = total_result.scalar()
            
            # Active products
            q_active = select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
            if company_id:
                q_active = q_active.where(ProductModel.company_id == company_id)
            active_result = await session.execute(q_active)
            active = active_result.scalar()
            
            # Low stock products
            q_low = select(func.count(ProductModel.id)).where(
                and_(
                    ProductModel.is_active == True,
                    ProductModel.stock <= 5,  # Default threshold
                    ProductModel.stock > 0,
                )
            )
            if company_id:
                q_low = q_low.where(ProductModel.company_id == company_id)
            low_stock_result = await session.execute(q_low)
            low_stock = low_stock_result.scalar()
            
            # Out of stock products
            q_oos = select(func.count(ProductModel.id)).where(
                and_(ProductModel.is_active == True, ProductModel.stock == 0)
            )
            if company_id:
                q_oos = q_oos.where(ProductModel.company_id == company_id)
            out_of_stock_result = await session.execute(q_oos)
            out_of_stock = out_of_stock_result.scalar()
            
            # Categories count
            q_cat = select(func.count(ProductCategoryModel.id)).where(ProductCategoryModel.is_active == True)
            if company_id:
                q_cat = q_cat.where(ProductCategoryModel.company_id == company_id)
            categories_result = await session.execute(q_cat)
            categories = categories_result.scalar()
            
            # Average price
            q_avg = select(func.avg(ProductModel.unit_price)).where(ProductModel.is_active == True)
            if company_id:
                q_avg = q_avg.where(ProductModel.company_id == company_id)
            avg_price_result = await session.execute(q_avg)
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
    
    async def get_category_stats(self, company_id: str | None = None) -> ProductCategoryStats:
        """Get product category statistics"""
        try:
            session = get_db_session()
            # Total categories
            q_total = select(func.count(ProductCategoryModel.id))
            if company_id:
                q_total = q_total.where(ProductCategoryModel.company_id == company_id)
            total_result = await session.execute(q_total)
            total = total_result.scalar()
            
            # Active categories
            q_active = select(func.count(ProductCategoryModel.id)).where(ProductCategoryModel.is_active == True)
            if company_id:
                q_active = q_active.where(ProductCategoryModel.company_id == company_id)
            active_result = await session.execute(q_active)
            active = active_result.scalar()
            
            # Products count
            q_products = select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
            if company_id:
                q_products = q_products.where(ProductModel.company_id == company_id)
            products_result = await session.execute(q_products)
            products_count = products_result.scalar()
            
            return ProductCategoryStats(
                total=total,
                active=active,
                products_count=products_count
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting category stats: {str(e)}")
    
    async def get_unit_stats(self, company_id: str | None = None) -> UnitStats:
        """Get unit statistics"""
        try:
            session = get_db_session()
            # Total units
            q_total = select(func.count(UnitModel.id))
            if company_id:
                q_total = q_total.where(UnitModel.company_id == company_id)
            total_result = await session.execute(q_total)
            total = total_result.scalar()
            
            # Active units
            q_active = select(func.count(UnitModel.id)).where(UnitModel.is_active == True)
            if company_id:
                q_active = q_active.where(UnitModel.company_id == company_id)
            active_result = await session.execute(q_active)
            active = active_result.scalar()
            
            # Products count
            q_products = select(func.count(ProductModel.id)).where(ProductModel.is_active == True)
            if company_id:
                q_products = q_products.where(ProductModel.company_id == company_id)
            products_result = await session.execute(q_products)
            products_count = products_result.scalar()
            
            return UnitStats(
                total=total,
                active=active,
                products_count=products_count
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting unit stats: {str(e)}")

