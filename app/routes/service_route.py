from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.service_schema import Service as ServiceSchema, ServiceCreate, ServiceUpdate
from app.services.service_service import ServiceService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/services", tags=["Services"])
svc = ServiceService()


@router.get("/", response_model=List[ServiceSchema])
async def get_services(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_services(company_id)


@router.get("/{service_id}", response_model=ServiceSchema)
async def get_service(
    service_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    service = await svc.get_service_by_id(service_id, company_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/", response_model=ServiceSchema)
async def create_service(
    payload: ServiceCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    service_id = await svc.create_service(company_id=company_id, service_data=payload, actor=ActivityActor.from_user(current_user))
    return await svc.get_service_by_id(service_id, company_id)


@router.put("/{service_id}", response_model=ServiceSchema)
async def update_service(
    service_id: str,
    payload: ServiceUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update_service(service_id=service_id, company_id=company_id, service_data=payload, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Service not found")
    return await svc.get_service_by_id(service_id, company_id, include_inactive=True)


@router.delete("/{service_id}", response_model=dict)
async def delete_service(
    service_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete_service(service_id=service_id, company_id=company_id, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted"}


