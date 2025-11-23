from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.stock_movement_model import StockMovement as StockMovementModel, StockMovementItem as StockMovementItemModel
from app.schemas.stock_movement_schema import StockMovement as StockMovementSchema, StockMovementCreate, StockMovementUpdate, StockMovementItemCreate
from app.utils.activity_logger import audit, ActivityActor

class StockMovementService:
    async def get_all(self, company_id: str) -> List[StockMovementSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(StockMovementModel)
                .where(StockMovementModel.company_id == company_id)
                .order_by(StockMovementModel.date.desc())
            )
            movements = result.scalars().all()
            return [StockMovementSchema(**m.to_dict()) for m in movements]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving stock movements: {str(e)}")

    async def get_by_id(self, movement_id: str, company_id: str) -> Optional[StockMovementSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(StockMovementModel).where(
                    StockMovementModel.id == movement_id,
                    StockMovementModel.company_id == company_id,
                )
            )
            movement = result.scalar_one_or_none()
            return StockMovementSchema(**movement.to_dict()) if movement else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving stock movement: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="stock_movement",
        details=lambda result, _a, kw: f"Mouvement de stock {result} enregistré ({kw['payload'].movement_type.value})",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(mode='json', exclude_none=True)},
    )
    async def create(self, company_id: str, payload: StockMovementCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            movement = StockMovementModel(
                company_id=company_id,
                date=payload.date,
                movement_type=payload.movement_type.value,
                label=payload.label,
                supplier_id=payload.supplier_id,
                customer_id=payload.customer_id,
                reason=payload.reason,
                author=payload.author,
                details=payload.details,
                document_reference=payload.document_reference,
                total_value=payload.total_value,
            )
            session.add(movement)
            await session.commit()
            await session.refresh(movement)

            # Add items
            for item in payload.items:
                session.add(StockMovementItemModel(
                    stock_movement_id=movement.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    unit=item.unit,
                ))
            await session.commit()

            # Update product stock based on movement type
            from app.models.product_model import Product as ProductModel
            # OUT = decrement, IN = increment, ADJUSTMENT = apply delta (+/-)
            for item in payload.items:
                product_result = await session.execute(
                    select(ProductModel).where(
                        ProductModel.id == item.product_id,
                        ProductModel.company_id == company_id
                    )
                )
                product = product_result.scalar_one_or_none()
                if not product:
                    continue

                if payload.movement_type.value == "out":
                    product.stock = max(0, (product.stock or 0) - item.quantity)
                elif payload.movement_type.value == "in":
                    product.stock = (product.stock or 0) + item.quantity
                elif payload.movement_type.value == "adjustment":
                    product.stock = max(0, (product.stock or 0) + item.quantity)

                product.updated_at = datetime.now()

            await session.commit()
            return movement.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating stock movement: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="stock_movement",
        details=lambda _r, _a, kw: f"Mouvement de stock {kw['movement_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["movement_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, movement_id: str, company_id: str, payload: StockMovementUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(StockMovementModel).where(
                    StockMovementModel.id == movement_id,
                    StockMovementModel.company_id == company_id,
                )
            )
            movement = result.scalar_one_or_none()
            if not movement:
                return False

            if payload.date is not None:
                movement.date = payload.date
            if payload.movement_type is not None:
                movement.movement_type = payload.movement_type.value
            if payload.label is not None:
                movement.label = payload.label
            if payload.supplier_id is not None:
                movement.supplier_id = payload.supplier_id
            if payload.customer_id is not None:
                movement.customer_id = payload.customer_id
            if payload.reason is not None:
                movement.reason = payload.reason
            if payload.author is not None:
                movement.author = payload.author
            if payload.details is not None:
                movement.details = payload.details
            if payload.document_reference is not None:
                movement.document_reference = payload.document_reference
            if payload.total_value is not None:
                movement.total_value = payload.total_value

            movement.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating stock movement: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="stock_movement",
        details=lambda _r, _a, kw: f"Mouvement de stock {kw['movement_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["movement_id"],
    )
    async def delete(self, movement_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(StockMovementModel).where(
                    StockMovementModel.id == movement_id,
                    StockMovementModel.company_id == company_id,
                )
            )
            movement = result.scalar_one_or_none()
            if not movement:
                return False

            await session.delete(movement)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting stock movement: {str(e)}")

    async def get_product_stock(self, product_id: str, company_id: str) -> int:
        """Get current stock for a product"""
        try:
            session = get_db_session()
            from app.models.product_model import Product as ProductModel
            result = await session.execute(
                select(ProductModel.stock).where(
                    ProductModel.id == product_id,
                    ProductModel.company_id == company_id
                )
            )
            stock = result.scalar_one_or_none()
            return stock or 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting product stock: {str(e)}")

    async def get_movements_by_sale_id(self, sale_id: str, company_id: str) -> List[StockMovementSchema]:
        """Get stock movements by sale ID"""
        try:
            session = get_db_session()
            from app.models.sales_model import Sale as SaleModel
            sale_result = await session.execute(
                select(SaleModel.reference).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id
                )
            )
            sale_reference = sale_result.scalar_one_or_none()
            if not sale_reference:
                return []

            result = await session.execute(
                select(StockMovementModel)
                .where(
                    StockMovementModel.company_id == company_id,
                    StockMovementModel.document_reference == sale_reference
                )
                .order_by(StockMovementModel.date.desc())
            )
            movements = result.scalars().all()
            return [StockMovementSchema(**m.to_dict()) for m in movements]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving stock movements by sale ID: {str(e)}")

    async def get_stock_summary(self, company_id: str) -> dict:
        """Get stock summary statistics"""
        try:
            session = get_db_session()
            from app.models.product_model import Product as ProductModel
            from sqlalchemy import func

            total_result = await session.execute(
                select(func.count(ProductModel.id)).where(ProductModel.company_id == company_id)
            )
            total_products = total_result.scalar() or 0

            # Use default threshold of 10 for low stock detection
            low_stock_result = await session.execute(
                select(func.count(ProductModel.id)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.stock <= 10,  # Default threshold
                    ProductModel.stock > 0
                )
            )
            low_stock = low_stock_result.scalar() or 0

            out_of_stock_result = await session.execute(
                select(func.count(ProductModel.id)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.stock == 0
                )
            )
            out_of_stock = out_of_stock_result.scalar() or 0

            return {
                "totalProducts": total_products,
                "lowStock": low_stock,
                "outOfStock": out_of_stock
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting stock stats: {str(e)}")
