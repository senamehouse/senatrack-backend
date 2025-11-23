from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.models.sales_model import Sale as SaleModel, SaleItem as SaleItemModel
from app.models.user_model import User as UserModel
from app.schemas.sales_schema import (
    Sale as SaleSchema,
    SaleResponse,
    SaleCreate, 
    SaleUpdate, 
    SaleProfit,
    PaymentStatus,
)
from app.utils.activity_logger import audit, ActivityActor
from app.schemas.stats_schema import (
    SalesReportStats,
    TopProductProfit,
    ClientSalesStats,
)


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
            
            # Get all sales, ordered by date descending (most recent first)
            sales_result = await session.execute(
                select(SaleModel)
                .where(SaleModel.company_id == company_id)
                .order_by(SaleModel.date.desc())
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
                # Create schema with backend enum values
                sale_schema = SaleSchema(**sale_dict)
                # Convert to dict (automatic camelCase via BaseCamelModel)
                sale_response = sale_schema.model_dump()
                sales_data.append(sale_response)
            
            return sales_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sales: {str(e)}")

    async def get_by_id(self, sale_id: str, company_id: str) -> Optional[SaleResponse]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(SaleModel).options(joinedload(SaleModel.items)).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id,
                )
            )
            sale = result.unique().scalar_one_or_none()
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
            
            # Include items - use SaleItemResponse schema for frontend format
            from app.schemas.sales_schema import SaleItemResponse, SaleProfitItem, SaleProfitItemInfo
            from app.models.product_model import Product as ProductModel
            
            items_data = []
            for item in sale.items:
                item_dict = item.to_dict()
                # Use SaleItemResponse schema to transform product_id -> item_id, etc.
                item_response = SaleItemResponse(
                    item_id=item_dict["product_id"],
                    item_name=item_dict["product_name"],
                    item_reference=item_dict.get("product_reference"),
                    item_type=item_dict.get("item_type", "product"),
                    quantity=item_dict["quantity"],
                    sell_price=item_dict["sell_price"],
                    original_sell_price=item_dict.get("original_sell_price"),
                    total=item_dict["total"],
                    unit=item_dict.get("unit"),
                    price_modified=item_dict.get("price_modified", False),
                )
                items_data.append(item_response)
            
            # Calculate profit
            total_cost = 0
            total_profit = 0
            items_profit = []
            
            for item in sale.items:
                item_cost = 0
                item_profit = 0
                
                if item.item_type == "product":
                    product_result = await session.execute(
                        select(ProductModel).where(ProductModel.id == item.product_id)
                    )
                    product = product_result.scalar_one_or_none()
                    if product:
                        item_cost = product.buy_price * item.quantity
                        item_profit = item.total - item_cost
                elif item.item_type == "service":
                    # For services, assume 30% cost
                    item_cost = item.total * 0.3
                    item_profit = item.total - item_cost
                
                total_cost += item_cost
                total_profit += item_profit
                
                # Create schema instances
                item_info = SaleProfitItemInfo(
                    item_id=item.product_id,
                    item_name=item.product_name,
                    quantity=item.quantity
                )
                profit_item = SaleProfitItem(
                    item=item_info,
                    cost=item_cost,
                    profit=item_profit,
                    margin=(item_profit / item.total * 100) if item.total > 0 else 0
                )
                items_profit.append(profit_item)
            
            average_margin = (total_profit / sale.total * 100) if sale.total > 0 else 0
            profit_schema = SaleProfit(
                totalCost=total_cost,
                totalProfit=total_profit,
                averageMargin=average_margin,
                items=items_profit
            )
            
            # Construct response using SaleResponse schema
            # Use model fields directly for datetime to avoid string conversion issues
            sale_response = SaleResponse(
                id=sale.id,
                company_id=sale.company_id,
                reference=sale.reference,
                date=sale.date,
                client_id=sale.client_id,
                client_name=sale.client_name,
                seller_id=sale.seller_id,
                seller_name=sale_dict.get("seller_name"),
                subtotal=sale.subtotal,
                discount=sale.discount or 0.0,
                tva_rate=sale.tva_rate or 0.0,
                tva_amount=sale.tva_amount or 0.0,
                total=sale.total,
                payment_status=PaymentStatus(sale.payment_status),
                amount_paid=sale.amount_paid or 0.0,
                payment_reference=sale.payment_reference,
                created_at=sale.created_at,
                updated_at=sale.updated_at,
                items=items_data,
                profit=profit_schema,
            )
            
            return sale_response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sale: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="sale",
        details=lambda result, _a, kw: f"Vente {kw['payload'].reference} créée",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(mode='json', exclude_none=True)},
    )
    async def create(self, company_id: str, payload: SaleCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            max_attempts = 5

            # Validate sufficient stock for product items before creating the sale
            from app.models.product_model import Product as ProductModel
            for item in payload.items:
                item_type = getattr(item, "item_type", "product") or "product"
                if item_type == "product":
                    product_result = await session.execute(
                        select(ProductModel).where(
                            ProductModel.id == item.product_id,
                            ProductModel.company_id == company_id
                        )
                    )
                    product = product_result.scalar_one_or_none()
                    if not product:
                        raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
                    current_stock = product.stock or 0
                    if current_stock < item.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for product '{product.name}' (available {current_stock}, requested {item.quantity})"
                        )

            sale: SaleModel | None = None
            for attempt in range(max_attempts):
                # Always assign a fresh unique reference on the backend scoped to company
                payload.reference = await self.generate_sale_reference(company_id, session=session)

                sale_candidate = SaleModel(
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
                    amount_paid=payload.amount_paid,
                    payment_reference=payload.payment_reference,
                )
                session.add(sale_candidate)
                try:
                    await session.commit()
                    await session.refresh(sale_candidate)
                    sale = sale_candidate
                    break
                except IntegrityError as exc:
                    await session.rollback()
                    if "ix_sales_reference" not in str(exc.orig) or attempt == max_attempts - 1:
                        raise
                    continue

            if sale is None:
                raise HTTPException(status_code=500, detail="Unable to reserve a unique sale reference")
            
            # Add sale items
            for item in payload.items:
                sale_item = SaleItemModel(
                    sale_id=sale.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_reference=getattr(item, 'product_reference', None),
                    item_type=getattr(item, 'item_type', 'product') or 'product',
                    quantity=item.quantity,
                    sell_price=item.sell_price,
                    original_sell_price=getattr(item, 'original_sell_price', None),
                    total=item.total_price,
                    unit=getattr(item, 'unit', None),
                    price_modified=getattr(item, 'price_modified', False),
                )
                session.add(sale_item)
            await session.commit()
            
            # Create stock movement (OUT) for product items in this sale
            try:
                from app.schemas.stock_movement_schema import (
                    StockMovementCreate, StockMovementItemCreate, MovementType
                )
                from app.services.stock_movement_service import StockMovementService

                out_items: list[StockMovementItemCreate] = []
                for item in payload.items:
                    # Only decrement stock for products
                    if getattr(item, "item_type", "product") == "product":
                        out_items.append(StockMovementItemCreate(
                            product_id=item.product_id,
                            product_name=item.product_name,
                            quantity=item.quantity,
                            price=item.sell_price,
                            total=item.total_price,
                            unit=getattr(item, "unit", "") or ""
                        ))

                if out_items:
                    stock_mvt_payload = StockMovementCreate(
                        date=datetime.utcnow(),
                        movement_type=MovementType.OUT,
                        label="Vente",
                        supplier_id=None,
                        customer_id=payload.client_id,
                        reason="Sale deduction",
                        author=sale.seller_id or "system",
                        details=None,
                        document_reference=sale.reference,
                        total_value=payload.total,
                        items=out_items,
                    )
                    stock_svc = StockMovementService()
                    await stock_svc.create(company_id, stock_mvt_payload)
            except Exception:
                # Do not fail the sale if movement creation fails
                pass

            return sale.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating sale: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="sale",
        details=lambda _r, _a, kw: f"Vente {kw['sale_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["sale_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, sale_id: str, company_id: str, payload: SaleUpdate, actor: ActivityActor | None = None) -> bool:
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
                else:
                    setattr(sale, field, value)
            sale.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating sale: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="sale",
        details=lambda _r, _a, kw: f"Vente {kw['sale_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["sale_id"],
    )
    async def delete(self, sale_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
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

    async def generate_sale_reference(self, company_id: str, session: AsyncSession | None = None) -> str:
        """Generate a unique sale reference like VNT-YYYY-0001 scoped to company."""
        try:
            session = session or get_db_session()
            year = datetime.utcnow().year
            prefix = f"VNT-{year}-"
            result = await session.execute(
                select(SaleModel.reference)
                .where(
                    SaleModel.company_id == company_id,
                    SaleModel.reference.like(f"{prefix}%")
                )
                .order_by(SaleModel.reference.desc())
                .with_for_update()
            )
            last_ref = result.scalars().first()
            counter = int(last_ref.split("-")[-1]) if last_ref else 0
            return f"{prefix}{counter + 1:04d}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating sale reference: {str(e)}")

    async def calculate_sale_profit(self, sale_id: str, company_id: str) -> SaleProfit:
        """Calculate profit for a sale based on product costs and sale prices"""
        try:
            session = get_db_session()
            # Get the sale with items
            result = await session.execute(
                select(SaleModel).options(joinedload(SaleModel.items)).where(
                    SaleModel.id == sale_id,
                    SaleModel.company_id == company_id
                )
            )
            sale = result.unique().scalar_one_or_none()
            if not sale:
                raise HTTPException(status_code=404, detail="Sale not found")
            
            from app.models.product_model import Product as ProductModel
            from app.schemas.sales_schema import SaleProfit, SaleProfitItem, SaleProfitItemInfo
            
            total_cost = 0
            total_profit = 0
            items_profit = []
            
            # Calculate profit for each item
            for item in sale.items:
                item_cost = 0
                item_profit = 0
                
                if item.item_type == "product":
                    product_result = await session.execute(
                        select(ProductModel).where(ProductModel.id == item.product_id)
                    )
                    product = product_result.scalar_one_or_none()
                    if product:
                        item_cost = product.buy_price * item.quantity
                        item_profit = item.total - item_cost
                elif item.item_type == "service":
                    # For services, assume 30% cost
                    item_cost = item.total * 0.3
                    item_profit = item.total - item_cost
                
                total_cost += item_cost
                total_profit += item_profit
                
                # Create schema instances
                item_info = SaleProfitItemInfo(
                    item_id=item.product_id,
                    item_name=item.product_name,
                    quantity=item.quantity
                )
                profit_item = SaleProfitItem(
                    item=item_info,
                    cost=item_cost,
                    profit=item_profit,
                    margin=(item_profit / item.total * 100) if item.total > 0 else 0
                )
                items_profit.append(profit_item)
            
            average_margin = (total_profit / sale.total * 100) if sale.total > 0 else 0
            
            return SaleProfit(
                totalCost=total_cost,
                totalProfit=total_profit,
                averageMargin=average_margin,
                items=items_profit
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating sale profit: {str(e)}")

    async def get_sales_report_stats(
        self,
        company_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> SalesReportStats:
        """Get detailed report statistics with filters"""
        try:
            session = get_db_session()
            
            # Build query
            query = select(SaleModel).options(joinedload(SaleModel.items)).where(
                SaleModel.company_id == company_id
            )
            
            if start_date:
                query = query.where(SaleModel.date >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(SaleModel.date <= datetime.fromisoformat(end_date))
            if client_id:
                query = query.where(SaleModel.client_id == client_id)
            
            result = await session.execute(query)
            sales = result.unique().scalars().all()
            
            # Calculate stats from sales with profit data
            total_revenue = 0.0
            total_cost = 0.0
            total_profit = 0.0
            total_quantity = 0
            unique_clients = set()
            all_items = []
            product_stats = {}
            modified_items_count = 0
            total_price_difference = 0.0
            
            for sale in sales:
                total_revenue += sale.total or 0.0
                if sale.client_id:
                    unique_clients.add(sale.client_id)
                
                # Calculate profit for this sale
                profit_data = await self.calculate_sale_profit(sale.id, company_id)
                total_cost += profit_data.totalCost
                total_profit += profit_data.totalProfit
                
                # Process items
                for item in sale.items:
                    total_quantity += item.quantity
                    all_items.append(item)
                    
                    if item.price_modified:
                        modified_items_count += 1
                        original_total = (item.original_sell_price or item.sell_price) * item.quantity
                        total_price_difference += (item.total - original_total)
                    
                    # Aggregate product stats
                    if item.item_type == "product":
                        product_id = item.product_id
                        if product_id not in product_stats:
                            product_stats[product_id] = {
                                "product_name": item.product_name,
                                "total_quantity": 0,
                                "total_revenue": 0.0,
                                "total_cost": 0.0,
                                "total_profit": 0.0,
                            }
                        
                        product_stats[product_id]["total_quantity"] += item.quantity
                        product_stats[product_id]["total_revenue"] += item.total
                        
                        # Get cost from profit data
                        for profit_item in profit_data.items:
                            if profit_item.item.item_id == product_id:
                                product_stats[product_id]["total_cost"] += profit_item.cost
                                product_stats[product_id]["total_profit"] += profit_item.profit
                                break
            
            # Calculate averages
            total_sales = len(sales)
            average_sale = total_revenue / total_sales if total_sales > 0 else 0.0
            average_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
            price_modification_rate = (modified_items_count / len(all_items) * 100) if all_items else 0.0
            
            # Build top products list
            top_products = []
            for product_id, stats in product_stats.items():
                avg_margin = (stats["total_profit"] / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0.0
                top_products.append(TopProductProfit(
                    product_id=product_id,
                    product_name=stats["product_name"],
                    total_quantity=stats["total_quantity"],
                    total_revenue=stats["total_revenue"],
                    total_cost=stats["total_cost"],
                    total_profit=stats["total_profit"],
                    average_margin=avg_margin
                ))
            
            # Sort by profit and take top 10
            top_products.sort(key=lambda x: x.total_profit, reverse=True)
            top_products = top_products[:10]
            
            return SalesReportStats(
                total_revenue=total_revenue,
                total_cost=total_cost,
                total_profit=total_profit,
                average_margin=average_margin,
                total_sales=total_sales,
                total_quantity=total_quantity,
                average_sale=average_sale,
                unique_clients=len(unique_clients),
                top_products=top_products,
                price_modification_rate=price_modification_rate,
                total_price_difference=total_price_difference
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating sales report stats: {str(e)}")

    async def get_client_sales_stats(
        self,
        company_id: str,
        client_id: str
    ) -> ClientSalesStats:
        """Get statistics for a specific client"""
        try:
            session = get_db_session()
            
            # Get all sales for this client
            result = await session.execute(
                select(SaleModel).options(joinedload(SaleModel.items)).where(
                    SaleModel.company_id == company_id,
                    SaleModel.client_id == client_id
                )
            )
            sales = result.unique().scalars().all()
            
            if not sales:
                # Get client name
                from app.models.client_model import Client as ClientModel
                client_result = await session.execute(
                    select(ClientModel).where(
                        ClientModel.id == client_id,
                        ClientModel.company_id == company_id
                    )
                )
                client = client_result.scalar_one_or_none()
                client_name = client.name if client else "Unknown"
                
                return ClientSalesStats(
                    client_id=client_id,
                    client_name=client_name,
                    total_sales=0,
                    total_sold=0.0,
                    total_paid=0.0,
                    total_debt=0.0,
                    total_profit=0.0,
                    average_margin=0.0,
                    paid_sales=0,
                    partial_sales=0,
                    unpaid_sales=0
                )
            
            # Get client name from first sale
            client_name = sales[0].client_name or "Unknown"
            
            # Calculate stats
            total_sold = sum(sale.total or 0.0 for sale in sales)
            total_paid = sum(sale.amount_paid or 0.0 for sale in sales)
            total_debt = total_sold - total_paid
            total_profit = 0.0
            total_cost = 0.0
            
            paid_sales = 0
            partial_sales = 0
            unpaid_sales = 0
            
            for sale in sales:
                # Calculate profit for this sale
                profit_data = await self.calculate_sale_profit(sale.id, company_id)
                total_profit += profit_data.totalProfit
                total_cost += profit_data.totalCost
                
                # Count payment status
                if sale.payment_status == "paid" and sale.amount_paid >= sale.total:
                    paid_sales += 1
                elif sale.payment_status == "partial" or (sale.amount_paid > 0 and sale.amount_paid < sale.total):
                    partial_sales += 1
                else:
                    unpaid_sales += 1
            
            total_revenue = total_sold
            average_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
            
            return ClientSalesStats(
                client_id=client_id,
                client_name=client_name,
                total_sales=len(sales),
                total_sold=total_sold,
                total_paid=total_paid,
                total_debt=total_debt,
                total_profit=total_profit,
                average_margin=average_margin,
                paid_sales=paid_sales,
                partial_sales=partial_sales,
                unpaid_sales=unpaid_sales
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calculating client sales stats: {str(e)}")

    async def get_top_profitable_products(
        self,
        company_id: str,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[TopProductProfit]:
        """Get top profitable products"""
        try:
            session = get_db_session()
            
            # Build query
            query = select(SaleModel).options(joinedload(SaleModel.items)).where(
                SaleModel.company_id == company_id
            )
            
            if start_date:
                query = query.where(SaleModel.date >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(SaleModel.date <= datetime.fromisoformat(end_date))
            
            result = await session.execute(query)
            sales = result.unique().scalars().all()
            
            # Aggregate product stats
            product_stats = {}
            
            for sale in sales:
                # Calculate profit data for this sale
                profit_data = await self.calculate_sale_profit(sale.id, company_id)
                
                # Map profit items by product_id
                profit_by_product = {}
                for profit_item in profit_data.items:
                    profit_by_product[profit_item.item.item_id] = profit_item
                
                # Process sale items
                for item in sale.items:
                    if item.item_type == "product":
                        product_id = item.product_id
                        if product_id not in product_stats:
                            product_stats[product_id] = {
                                "product_name": item.product_name,
                                "total_quantity": 0,
                                "total_revenue": 0.0,
                                "total_cost": 0.0,
                                "total_profit": 0.0,
                            }
                        
                        product_stats[product_id]["total_quantity"] += item.quantity
                        product_stats[product_id]["total_revenue"] += item.total
                        
                        # Get cost and profit from profit data
                        if product_id in profit_by_product:
                            profit_item = profit_by_product[product_id]
                            product_stats[product_id]["total_cost"] += profit_item.cost
                            product_stats[product_id]["total_profit"] += profit_item.profit
            
            # Build and sort results
            top_products = []
            for product_id, stats in product_stats.items():
                avg_margin = (stats["total_profit"] / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0.0
                top_products.append(TopProductProfit(
                    product_id=product_id,
                    product_name=stats["product_name"],
                    total_quantity=stats["total_quantity"],
                    total_revenue=stats["total_revenue"],
                    total_cost=stats["total_cost"],
                    total_profit=stats["total_profit"],
                    average_margin=avg_margin
                ))
            
            # Sort by profit and return top N
            top_products.sort(key=lambda x: x.total_profit, reverse=True)
            return top_products[:limit]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting top profitable products: {str(e)}")


