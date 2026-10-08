from typing import List, Optional
from datetime import datetime
import re
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db_session
from app.models.stock_movement_model import StockMovement as StockMovementModel, StockMovementItem as StockMovementItemModel
from app.schemas.stock_movement_schema import StockMovement as StockMovementSchema, StockMovementCreate, StockMovementUpdate, MovementType
from app.utils.activity_logger import audit, ActivityActor
from app.utils.stock_alerts import stock_alert_threshold

class StockMovementService:
    async def get_all(self, company_id: str) -> List[StockMovementSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(StockMovementModel)
                .options(selectinload(StockMovementModel.items))
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
                select(StockMovementModel).options(selectinload(StockMovementModel.items)).where(
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
            from app.models.product_model import Product as ProductModel
            if not payload.items:
                raise HTTPException(status_code=400, detail="At least one product is required")
            quantities: dict[str, int] = {}
            for item in payload.items:
                if item.quantity == 0 or item.price < 0 or (payload.movement_type != MovementType.ADJUSTMENT and item.quantity < 0):
                    raise HTTPException(status_code=400, detail="Invalid item quantity or price")
                quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
            products_result = await session.execute(
                select(ProductModel).where(
                    ProductModel.company_id == company_id,
                    ProductModel.id.in_(quantities),
                ).with_for_update()
            )
            products = {product.id: product for product in products_result.scalars()}
            if len(products) != len(quantities):
                raise HTTPException(status_code=400, detail="A product does not belong to this company")
            if payload.movement_type in (MovementType.OUT, MovementType.ADJUSTMENT):
                for product_id, quantity in quantities.items():
                    delta = -quantity if payload.movement_type == MovementType.OUT else quantity
                    if (products[product_id].stock or 0) + delta < 0:
                        raise HTTPException(status_code=409, detail="Insufficient product stock")
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
            for item in payload.items:
                movement.items.append(StockMovementItemModel(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    unit=item.unit,
                ))
            if payload.document_reference and "/files/" in payload.document_reference:
                from app.models.file_model import FileRecord
                file_match = re.search(r"/files/([A-Za-z0-9]{15})(?:\?.*)?$", payload.document_reference)
                if not file_match:
                    raise HTTPException(status_code=400, detail="Invalid document reference")
                pending_file = await session.scalar(select(FileRecord).where(
                    FileRecord.id == file_match.group(1),
                    FileRecord.company_id == company_id,
                    FileRecord.entity_type == "stock_movement",
                    FileRecord.entity_id.like("temp-stock-%"),
                    FileRecord.field_name == "document_url",
                    FileRecord.is_active == True,
                ))
                if not pending_file:
                    raise HTTPException(status_code=400, detail="Stock document not found")
                await session.flush()
                pending_file.entity_id = movement.id
            for product_id, quantity in quantities.items():
                product = products[product_id]
                delta = -quantity if payload.movement_type == MovementType.OUT else quantity
                product.stock = (product.stock or 0) + delta
                product.updated_at = datetime.now()
            await session.commit()
            return movement.id
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
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
                select(StockMovementModel).options(selectinload(StockMovementModel.items)).where(
                    StockMovementModel.id == movement_id,
                    StockMovementModel.company_id == company_id,
                )
            )
            movement = result.scalar_one_or_none()
            if not movement:
                return False
            if movement.reason == "Sale deduction":
                from app.models.sales_model import Sale as SaleModel
                sale_result = await session.execute(
                    select(SaleModel.id).where(
                        SaleModel.company_id == company_id,
                        SaleModel.reference == movement.document_reference,
                    )
                )
                if sale_result.scalar_one_or_none():
                    raise HTTPException(status_code=409, detail="Delete the sale to reverse its stock movement")

            if payload.date is not None:
                movement.date = payload.date
            if payload.movement_type is not None and payload.movement_type != MovementType(movement.movement_type):
                raise HTTPException(status_code=400, detail="Movement type cannot be changed after stock is recorded")
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
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
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
                select(StockMovementModel).options(selectinload(StockMovementModel.items)).where(
                    StockMovementModel.id == movement_id,
                    StockMovementModel.company_id == company_id,
                )
            )
            movement = result.scalar_one_or_none()
            if not movement:
                return False
            if movement.reason == "Sale deduction":
                from app.models.sales_model import Sale as SaleModel
                sale_result = await session.execute(
                    select(SaleModel.id).where(
                        SaleModel.company_id == company_id,
                        SaleModel.reference == movement.document_reference,
                    )
                )
                if sale_result.scalar_one_or_none():
                    raise HTTPException(status_code=409, detail="Delete the sale to reverse its stock movement")

            from app.models.product_model import Product as ProductModel
            movement_type = MovementType(movement.movement_type)
            quantities: dict[str, int] = {}
            for item in movement.items:
                quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
            products_result = await session.execute(
                select(ProductModel).where(
                    ProductModel.company_id == company_id,
                    ProductModel.id.in_(quantities),
                ).with_for_update()
            )
            products = {product.id: product for product in products_result.scalars()}
            if len(products) != len(quantities):
                raise HTTPException(status_code=409, detail="A movement product no longer exists")
            for product_id, quantity in quantities.items():
                product = products[product_id]
                reversal = quantity if movement_type == MovementType.OUT else -quantity
                if (product.stock or 0) + reversal < 0:
                    raise HTTPException(status_code=409, detail="Cannot reverse movement: insufficient stock")
                product.stock = (product.stock or 0) + reversal
                product.updated_at = datetime.now()
            if movement.document_reference:
                file_match = re.search(r"/files/([A-Za-z0-9]{15})(?:\?.*)?$", movement.document_reference)
                if file_match:
                    from app.models.file_model import FileRecord
                    attachment = await session.scalar(select(FileRecord).where(
                        FileRecord.id == file_match.group(1),
                        FileRecord.company_id == company_id,
                        FileRecord.entity_type == "stock_movement",
                        FileRecord.entity_id == movement.id,
                    ))
                    if attachment:
                        attachment.is_active = False
            await session.delete(movement)
            await session.commit()
            return True
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
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
                .options(selectinload(StockMovementModel.items))
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
            from app.models.company_model import Company as CompanyModel
            from sqlalchemy import func

            company_settings = await session.scalar(select(CompanyModel.settings).where(CompanyModel.id == company_id))
            threshold = stock_alert_threshold(company_settings)

            total_result = await session.execute(
                select(func.count(ProductModel.id)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.is_active == True,
                )
            )
            total_products = total_result.scalar() or 0

            low_stock_result = await session.execute(
                select(func.count(ProductModel.id)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.is_active == True,
                    ProductModel.stock <= threshold,
                )
            )
            low_stock = low_stock_result.scalar() or 0

            out_of_stock_result = await session.execute(
                select(func.count(ProductModel.id)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.is_active == True,
                    ProductModel.stock <= 0,
                )
            )
            out_of_stock = out_of_stock_result.scalar() or 0

            value_result = await session.execute(
                select(func.coalesce(func.sum(ProductModel.stock * ProductModel.buy_price), 0)).where(
                    ProductModel.company_id == company_id,
                    ProductModel.is_active == True,
                )
            )
            total_stock_value = value_result.scalar() or 0

            return {
                "totalProducts": total_products,
                "lowStock": low_stock,
                "outOfStock": out_of_stock,
                "totalStockValue": total_stock_value,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting stock stats: {str(e)}")
