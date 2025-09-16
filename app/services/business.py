import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.business import (
    Supplier as SupplierModel, Client as ClientModel, Service as ServiceModel,
    Tva as TvaModel, Abic as AbicModel, StockMovement as StockMovementModel,
    StockMovementItem as StockMovementItemModel, Sale as SaleModel, SaleItem as SaleItemModel
)
from app.models.sync import SyncLog
from app.schemas.business import (
    SupplierCreate, SupplierUpdate, Supplier as SupplierSchema,
    ClientCreate, ClientUpdate, Client as ClientSchema,
    ServiceCreate, ServiceUpdate, Service as ServiceSchema,
    TvaCreate, TvaUpdate, Tva as TvaSchema,
    AbicCreate, AbicUpdate, Abic as AbicSchema,
    StockMovementCreate, StockMovementUpdate, StockMovement as StockMovementSchema,
    SaleCreate, SaleUpdate, Sale as SaleSchema,
    SupplierStats, ClientStats, ServiceStats, SaleStats, StockMovementStats
)


class BusinessService:
    """Service for business-related database operations"""
    
    # Supplier methods
    async def get_all_suppliers(self) -> List[SupplierSchema]:
        """Get all active suppliers"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SupplierModel).where(SupplierModel.is_active == True)
                )
                suppliers = result.scalars().all()
                return [SupplierSchema(**supplier.to_dict()) for supplier in suppliers]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving suppliers: {str(e)}")
    
    async def get_supplier_by_id(self, supplier_id: int) -> Optional[SupplierSchema]:
        """Get a supplier by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SupplierModel).where(
                        SupplierModel.id == supplier_id,
                        SupplierModel.is_active == True
                    )
                )
                supplier = result.scalar_one_or_none()
                return SupplierSchema(**supplier.to_dict()) if supplier else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving supplier: {str(e)}")
    
    async def create_supplier(self, supplier_data: SupplierCreate) -> int:
        """Create a new supplier and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                supplier = SupplierModel(
                    name=supplier_data.name,
                    email=supplier_data.email,
                    phone=supplier_data.phone,
                    address=supplier_data.address
                )
                session.add(supplier)
                await session.commit()
                await session.refresh(supplier)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='suppliers',
                    record_id=supplier.id,
                    data=json.dumps(supplier.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return supplier.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating supplier: {str(e)}")
    
    async def update_supplier(self, supplier_id: int, supplier_data: SupplierUpdate) -> bool:
        """Update a supplier by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SupplierModel).where(SupplierModel.id == supplier_id)
                )
                supplier = result.scalar_one_or_none()
                
                if not supplier:
                    return False
                
                # Update fields
                if supplier_data.name is not None:
                    supplier.name = supplier_data.name
                if supplier_data.email is not None:
                    supplier.email = supplier_data.email
                if supplier_data.phone is not None:
                    supplier.phone = supplier_data.phone
                if supplier_data.address is not None:
                    supplier.address = supplier_data.address
                if supplier_data.is_active is not None:
                    supplier.is_active = supplier_data.is_active
                
                supplier.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='suppliers',
                    record_id=supplier.id,
                    data=json.dumps(supplier.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating supplier: {str(e)}")
    
    async def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SupplierModel).where(SupplierModel.id == supplier_id)
                )
                supplier = result.scalar_one_or_none()
                
                if not supplier:
                    return False
                
                # Soft delete
                supplier.is_active = False
                supplier.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='suppliers',
                    record_id=supplier.id,
                    data=json.dumps(supplier.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting supplier: {str(e)}")
    
    # Client methods
    async def get_all_clients(self) -> List[ClientSchema]:
        """Get all active clients"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ClientModel).where(ClientModel.is_active == True)
                )
                clients = result.scalars().all()
                return [ClientSchema(**client.to_dict()) for client in clients]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving clients: {str(e)}")
    
    async def get_client_by_id(self, client_id: int) -> Optional[ClientSchema]:
        """Get a client by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ClientModel).where(
                        ClientModel.id == client_id,
                        ClientModel.is_active == True
                    )
                )
                client = result.scalar_one_or_none()
                return ClientSchema(**client.to_dict()) if client else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving client: {str(e)}")
    
    async def create_client(self, client_data: ClientCreate) -> int:
        """Create a new client and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                client = ClientModel(
                    name=client_data.name,
                    email=client_data.email,
                    phone=client_data.phone,
                    address=client_data.address,
                    invoices=client_data.invoices or 0
                )
                session.add(client)
                await session.commit()
                await session.refresh(client)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='clients',
                    record_id=client.id,
                    data=json.dumps(client.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return client.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating client: {str(e)}")
    
    async def update_client(self, client_id: int, client_data: ClientUpdate) -> bool:
        """Update a client by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ClientModel).where(ClientModel.id == client_id)
                )
                client = result.scalar_one_or_none()
                
                if not client:
                    return False
                
                # Update fields
                if client_data.name is not None:
                    client.name = client_data.name
                if client_data.email is not None:
                    client.email = client_data.email
                if client_data.phone is not None:
                    client.phone = client_data.phone
                if client_data.address is not None:
                    client.address = client_data.address
                if client_data.invoices is not None:
                    client.invoices = client_data.invoices
                if client_data.is_active is not None:
                    client.is_active = client_data.is_active
                
                client.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='clients',
                    record_id=client.id,
                    data=json.dumps(client.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating client: {str(e)}")
    
    async def delete_client(self, client_id: int) -> bool:
        """Delete a client by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ClientModel).where(ClientModel.id == client_id)
                )
                client = result.scalar_one_or_none()
                
                if not client:
                    return False
                
                # Soft delete
                client.is_active = False
                client.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='clients',
                    record_id=client.id,
                    data=json.dumps(client.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting client: {str(e)}")
    
    # Service methods
    async def get_all_services(self) -> List[ServiceSchema]:
        """Get all active services"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ServiceModel).where(ServiceModel.is_active == True)
                )
                services = result.scalars().all()
                return [ServiceSchema(**service.to_dict()) for service in services]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving services: {str(e)}")
    
    async def get_service_by_id(self, service_id: int) -> Optional[ServiceSchema]:
        """Get a service by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ServiceModel).where(
                        ServiceModel.id == service_id,
                        ServiceModel.is_active == True
                    )
                )
                service = result.scalar_one_or_none()
                return ServiceSchema(**service.to_dict()) if service else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving service: {str(e)}")
    
    async def create_service(self, service_data: ServiceCreate) -> int:
        """Create a new service and return the ID"""
        try:
            async with AsyncSessionLocal() as session:
                service = ServiceModel(
                    name=service_data.name,
                    unit=service_data.unit,
                    price=service_data.price,
                    description=service_data.description
                )
                session.add(service)
                await session.commit()
                await session.refresh(service)
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='CREATE',
                    table_name='services',
                    record_id=service.id,
                    data=json.dumps(service.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return service.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating service: {str(e)}")
    
    async def update_service(self, service_id: int, service_data: ServiceUpdate) -> bool:
        """Update a service by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ServiceModel).where(ServiceModel.id == service_id)
                )
                service = result.scalar_one_or_none()
                
                if not service:
                    return False
                
                # Update fields
                if service_data.name is not None:
                    service.name = service_data.name
                if service_data.unit is not None:
                    service.unit = service_data.unit
                if service_data.price is not None:
                    service.price = service_data.price
                if service_data.description is not None:
                    service.description = service_data.description
                if service_data.is_active is not None:
                    service.is_active = service_data.is_active
                
                service.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='UPDATE',
                    table_name='services',
                    record_id=service.id,
                    data=json.dumps(service.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating service: {str(e)}")
    
    async def delete_service(self, service_id: int) -> bool:
        """Delete a service by ID (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ServiceModel).where(ServiceModel.id == service_id)
                )
                service = result.scalar_one_or_none()
                
                if not service:
                    return False
                
                # Soft delete
                service.is_active = False
                service.updated_at = datetime.now()
                await session.commit()
                
                # Log sync operation
                sync_log = SyncLog(
                    operation='DELETE',
                    table_name='services',
                    record_id=service.id,
                    data=json.dumps(service.to_dict())
                )
                session.add(sync_log)
                await session.commit()
                
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting service: {str(e)}")
    
    # Statistics methods
    async def get_supplier_stats(self) -> SupplierStats:
        """Get supplier statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total suppliers
                total_result = await session.execute(
                    select(func.count(SupplierModel.id))
                )
                total = total_result.scalar()
                
                # Active suppliers
                active_result = await session.execute(
                    select(func.count(SupplierModel.id)).where(SupplierModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Suppliers with movements
                with_movements_result = await session.execute(
                    select(func.count(func.distinct(StockMovementModel.supplier_id)))
                    .where(StockMovementModel.supplier_id.isnot(None))
                )
                with_movements = with_movements_result.scalar()
                
                return SupplierStats(
                    total=total,
                    active=active,
                    with_movements=with_movements
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting supplier stats: {str(e)}")
    
    async def get_client_stats(self) -> ClientStats:
        """Get client statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total clients
                total_result = await session.execute(
                    select(func.count(ClientModel.id))
                )
                total = total_result.scalar()
                
                # Active clients
                active_result = await session.execute(
                    select(func.count(ClientModel.id)).where(ClientModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Clients with sales
                with_sales_result = await session.execute(
                    select(func.count(func.distinct(SaleModel.client_id)))
                )
                with_sales = with_sales_result.scalar()
                
                # Total sales value
                total_sales_result = await session.execute(
                    select(func.sum(SaleModel.total))
                )
                total_sales_value = total_sales_result.scalar() or 0.0
                
                return ClientStats(
                    total=total,
                    active=active,
                    with_sales=with_sales,
                    total_sales_value=total_sales_value
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting client stats: {str(e)}")
    
    async def get_service_stats(self) -> ServiceStats:
        """Get service statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total services
                total_result = await session.execute(
                    select(func.count(ServiceModel.id))
                )
                total = total_result.scalar()
                
                # Active services
                active_result = await session.execute(
                    select(func.count(ServiceModel.id)).where(ServiceModel.is_active == True)
                )
                active = active_result.scalar()
                
                # Average price
                avg_price_result = await session.execute(
                    select(func.avg(ServiceModel.price)).where(ServiceModel.is_active == True)
                )
                average_price = avg_price_result.scalar() or 0.0
                
                return ServiceStats(
                    total=total,
                    active=active,
                    average_price=round(average_price, 2)
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting service stats: {str(e)}")

