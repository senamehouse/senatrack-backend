from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.proforma_schema import (
    Proforma, ProformaCreate, ProformaUpdate, ProformaStats, ProformaFilter
)
from app.services.proforma_service import ProformaService
from app.utils.activity_logger import ActivityActor

router = APIRouter(prefix="/proformas", tags=["Proformas"])
proforma_service = ProformaService()

@router.post("/", response_model=Proforma, status_code=status.HTTP_201_CREATED)
async def create_proforma(
    proforma_data: ProformaCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Create a new proforma"""
    # enforce company id from header
    proforma_data.company_id = proforma_data.company_id
    return await proforma_service.create_proforma(proforma_data, actor=ActivityActor.from_user(current_user))

@router.get("/", response_model=List[Proforma])
async def get_company_proformas(
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit results"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get all proformas for a company"""
    filters = ProformaFilter(
        client_name=client_name,
        status=status,
        limit=limit
    )
    return await proforma_service.get_company_proformas(company_id, filters)

@router.get("/{proforma_id}", response_model=Proforma)
async def get_proforma(
    proforma_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Get a proforma by ID"""
    proforma = await proforma_service.get_proforma_by_id(proforma_id)
    if not proforma:
        raise HTTPException(status_code=404, detail="Proforma not found")
    return proforma

@router.put("/{proforma_id}", response_model=Proforma)
async def update_proforma(
    proforma_id: str,
    proforma_data: ProformaUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Update a proforma"""
    return await proforma_service.update_proforma(proforma_id=proforma_id, proforma_data=proforma_data, actor=ActivityActor.from_user(current_user))

@router.delete("/{proforma_id}")
async def delete_proforma(
    proforma_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    """Delete a proforma"""
    success = await proforma_service.delete_proforma(proforma_id=proforma_id, actor=ActivityActor.from_user(current_user))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete proforma")
    return {"message": "Proforma deleted successfully"}

@router.get("/stats/{company_id}", response_model=ProformaStats)
async def get_proforma_stats(
    company_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    header_company_id: str = Depends(get_company_id)
):
    """Get proforma statistics for a company"""
    return await proforma_service.get_proforma_stats(company_id)

@router.get("/client/{company_id}/{client_name}", response_model=List[Proforma])
async def get_proformas_by_client(
    company_id: str,
    client_name: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    header_company_id: str = Depends(get_company_id)
):
    """Get proformas by client name"""
    return await proforma_service.get_proformas_by_client(company_id, client_name)

@router.get("/recent/{company_id}", response_model=List[Proforma])
async def get_recent_proformas(
    company_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent proformas"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    header_company_id: str = Depends(get_company_id)
):
    """Get recent proformas for a company"""
    return await proforma_service.get_recent_proformas(company_id, limit)
