from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.core.database import get_db_session
from app.models.sales_model import Sale as SaleModel
from app.models.user_model import User as UserModel
from app.schemas.sales_schema import Sale as SaleSchema, SaleCreate, SaleUpdate


class SalesService:
    async def get_all(self, company_id: str) -> List[SaleSchema]:
        try:
            session = get_db_session()
            # Get all unique seller IDs from sales
            result = await session.execute(
                select(SaleModel.seller_id).where(
                    SaleModel.company_id == company_id,
                    SaleModel.seller_id.isnot(None)
                ).distinct()
            )
            seller_ids = [row[0] for row in result.fetchall() if row[0]]
            
            # Fetch all sellers in one query
            sellers_dict = {}
            if seller_ids:
                sellers_result = await session.execute(
                    select(UserModel).where(UserModel.id.in_(seller_ids))
                )
                sellers = sellers_result.scalars().all()
                sellers_dict = {seller.id: seller.name for seller in sellers}
            
            # Get all sales
            sales_result = await session.execute(
                select(SaleModel).where(SaleModel.company_id == company_id)
            )
            sales = sales_result.scalars().all()
            
            # Build response with seller names
            sales_data = []
            for sale in sales:
                sale_dict = sale.to_dict()
                if sale.seller_id and sale.seller_id in sellers_dict:
                    sale_dict["seller_name"] = sellers_dict[sale.seller_id]
                else:
                    sale_dict["seller_name"] = None
                sales_data.append(SaleSchema(**sale_dict))
            
            return sales_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sales: {str(e)}")

    async def get_by_id(self, sale_id: int, company_id: str) -> Optional[SaleSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SaleModel).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id,
                )
            )
            sale = result.scalar_one_or_none()
            if not sale:
                return None
            
            # Get seller name if seller_id exists
            sale_dict = sale.to_dict()
            if sale.seller_id:
                seller_result = await session.execute(
                    select(UserModel).where(UserModel.id == sale.seller_id)
                )
                seller = seller_result.scalar_one_or_none()
                sale_dict["seller_name"] = seller.name if seller else None
            else:
                sale_dict["seller_name"] = None
            
            return SaleSchema(**sale_dict)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sale: {str(e)}")

    async def create(self, company_id: str, payload: SaleCreate) -> int:
        try:
            session = get_db_session()
            sale = SaleModel(
                company_id=company_id,
                reference=payload.reference,
                date=payload.date,
                client_id=payload.client_id if payload.client_id else None,
                client_name=payload.client_name if payload.client_name else None,
                seller_id=payload.seller_id,
                subtotal=payload.subtotal,
                discount=payload.discount,
                tva_rate=payload.tva_rate,
                tva_amount=payload.tva_amount,
                total=payload.total,
                payment_status=payload.payment_status.value,
                payment_method=payload.payment_method.value if payload.payment_method else None,
                amount_paid=payload.amount_paid,
                payment_reference=payload.payment_reference,
                notes=payload.notes,
                print_after_creation=payload.print_after_creation,
            )
            session.add(sale)
            await session.commit()
            await session.refresh(sale)
            return sale.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating sale: {str(e)}")

    async def update(self, sale_id: int, company_id: str, payload: SaleUpdate) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SaleModel).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id,
                )
            )
            sale = result.scalar_one_or_none()
            if not sale:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                if field == 'payment_status' and value is not None:
                    setattr(sale, 'payment_status', value.value)
                elif field == 'payment_method' and value is not None:
                    setattr(sale, 'payment_method', value.value)
                else:
                    setattr(sale, field, value)
            sale.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating sale: {str(e)}")

    async def delete(self, sale_id: int, company_id: str) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SaleModel).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id,
                )
            )
            sale = result.scalar_one_or_none()
            if not sale:
                return False
            await session.delete(sale)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting sale: {str(e)}")

    async def generate_sale_reference(self, company_id: str) -> str:
        """Generate a unique sale reference like VNT-YYYY-0001 scoped to company."""
        try:
            session = get_db_session()
            year = datetime.utcnow().year
            prefix = f"VNT-{year}-"
            result = await session.execute(
                select(SaleModel.reference).where(
                    SaleModel.company_id == company_id,
                    SaleModel.reference.like(f"{prefix}%")
                )
            )
            refs = [row[0] for row in result.fetchall()]
            existing = set(refs)
            counter = 1
            ref = f"{prefix}{counter:04d}"
            while ref in existing:
                counter += 1
                ref = f"{prefix}{counter:04d}"
            return ref
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating sale reference: {str(e)}")

    async def calculate_sale_profit(self, sale_id: int, company_id: str) -> dict:
        """Calculate profit for a sale based on product costs and sale prices"""
        try:
            session = get_db_session()
            # Get the sale with items
            result = await session.execute(
                select(SaleModel).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id
                )
            )
            sale = result.scalar_one_or_none()
            if not sale:
                raise HTTPException(status_code=404, detail="Sale not found")
            
            # Import here to avoid circular imports
            from app.models.product_model import Product as ProductModel
            
            total_cost = 0
            total_profit = 0
            items_profit = []
            
            # Calculate profit for each item
            for item in sale.items:
                # Get product cost
                product_result = await session.execute(
                    select(ProductModel).where(ProductModel.id == item.item_id)
                )
                product = product_result.scalar_one_or_none()
                
                if product:
                    item_cost = product.buy_price * item.quantity
                    item_profit = item.total - item_cost
                    total_cost += item_cost
                    total_profit += item_profit
                    
                    items_profit.append({
                        "item": {
                            "itemId": item.item_id,
                            "itemName": item.item_name,
                            "quantity": item.quantity
                        },
                        "cost": item_cost,
                        "profit": item_profit,
                        "margin": (item_profit / item.total * 100) if item.total > 0 else 0
                    })
            
            average_margin = (total_profit / sale.total * 100) if sale.total > 0 else 0
            
            return {
                "totalCost": total_cost,
                "totalProfit": total_profit,
                "averageMargin": average_margin,
                "items": items_profit
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating sale profit: {str(e)}")


