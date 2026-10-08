from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.client_schema import Client, ClientCreate, ClientUpdate
from app.services.client_service import ClientService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/clients", tags=["Clients"])
service = ClientService()


@router.get("/", response_model=List[Client])
async def get_clients(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await service.get_all_clients(company_id)


@router.get("/{client_id}", response_model=Client)
async def get_client(
    client_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    client = await service.get_client_by_id(client_id, company_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=Client)
async def create_client(
    payload: ClientCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    client_id = await service.create_client(company_id=company_id, client_data=payload, actor=ActivityActor.from_user(current_user))
    return await service.get_client_by_id(client_id, company_id)


@router.put("/{client_id}", response_model=Client)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await service.update_client(client_id=client_id, company_id=company_id, client_data=payload, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Client not found")
    return await service.get_client_by_id(client_id, company_id, include_inactive=True)


@router.delete("/{client_id}", response_model=dict)
async def delete_client(
    client_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await service.delete_client(client_id=client_id, company_id=company_id, actor=ActivityActor.from_user(current_user))
    if not ok:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted"}




