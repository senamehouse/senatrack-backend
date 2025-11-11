from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.services.reception_service import ReceptionService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/receptions", tags=["Receptions"])
svc = ReceptionService()


@router.get("/")
async def get_receptions(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/{reception_id}")
async def get_reception(
    reception_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    row = await svc.get_by_id(reception_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Reception not found")
    return row


@router.post("/")
async def create_reception(
    payload: dict,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    reception_id = await svc.create(company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Reception created", "reception_id": reception_id}


@router.put("/{reception_id}")
async def update_reception(
    reception_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(reception_id=reception_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Reception not found")
    return {"message": "Reception updated"}


@router.delete("/{reception_id}")
async def delete_reception(
    reception_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(reception_id=reception_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Reception not found")
    return {"message": "Reception deleted"}




