from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.business import (
    Supplier, SupplierCreate, SupplierUpdate,
    Client, ClientCreate, ClientUpdate,
    Service, ServiceCreate, ServiceUpdate,
    Tva, TvaCreate, TvaUpdate,
    Abic, AbicCreate, AbicUpdate,
    SupplierStats, ClientStats, ServiceStats
)
from app.services.business import BusinessService
from app.core.dependencies import get_current_user
from app.schemas.user import User

router = APIRouter(prefix="/business", tags=["Business"])
business_service = BusinessService()

# Supplier Routes
@router.get("/suppliers", response_model=List[Supplier])
async def get_all_suppliers(current_user: User = Depends(get_current_user)):
    """Get all suppliers"""
    return await business_service.get_all_suppliers()

@router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(
    supplier_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get supplier by ID"""
    supplier = await business_service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.post("/suppliers", response_model=dict)
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier"""
    supplier_id = await business_service.create_supplier(supplier_data)
    return {"message": "Supplier created successfully", "supplier_id": supplier_id}

@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a supplier"""
    success = await business_service.update_supplier(supplier_id, supplier_data)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier updated successfully"}

@router.delete("/suppliers/{supplier_id}", response_model=dict)
async def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a supplier"""
    success = await business_service.delete_supplier(supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted successfully"}

# Client Routes
@router.get("/clients", response_model=List[Client])
async def get_all_clients(current_user: User = Depends(get_current_user)):
    """Get all clients"""
    return await business_service.get_all_clients()

@router.get("/clients/{client_id}", response_model=Client)
async def get_client(
    client_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get client by ID"""
    client = await business_service.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.post("/clients", response_model=dict)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new client"""
    client_id = await business_service.create_client(client_data)
    return {"message": "Client created successfully", "client_id": client_id}

@router.put("/clients/{client_id}", response_model=dict)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a client"""
    success = await business_service.update_client(client_id, client_data)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client updated successfully"}

@router.delete("/clients/{client_id}", response_model=dict)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a client"""
    success = await business_service.delete_client(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Service Routes
@router.get("/services", response_model=List[Service])
async def get_all_services(current_user: User = Depends(get_current_user)):
    """Get all services"""
    return await business_service.get_all_services()

@router.get("/services/{service_id}", response_model=Service)
async def get_service(
    service_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Get service by ID"""
    service = await business_service.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.post("/services", response_model=dict)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new service"""
    service_id = await business_service.create_service(service_data)
    return {"message": "Service created successfully", "service_id": service_id}

@router.put("/services/{service_id}", response_model=dict)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a service"""
    success = await business_service.update_service(service_id, service_data)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service updated successfully"}

@router.delete("/services/{service_id}", response_model=dict)
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a service"""
    success = await business_service.delete_service(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted successfully"}

# Statistics Routes
@router.get("/stats/suppliers", response_model=SupplierStats)
async def get_supplier_stats(current_user: User = Depends(get_current_user)):
    """Get supplier statistics"""
    return await business_service.get_supplier_stats()

@router.get("/stats/clients", response_model=ClientStats)
async def get_client_stats(current_user: User = Depends(get_current_user)):
    """Get client statistics"""
    return await business_service.get_client_stats()

@router.get("/stats/services", response_model=ServiceStats)
async def get_service_stats(current_user: User = Depends(get_current_user)):
    """Get service statistics"""
    return await business_service.get_service_stats()

