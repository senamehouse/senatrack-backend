from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.dependencies import get_current_user, get_company_id
from app.schemas.user_schema import User
from app.services.reception_service import ReceptionService


router = APIRouter(prefix="/receptions", tags=["Receptions"])
svc = ReceptionService()


@router.get("/")
async def get_receptions(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    return await svc.get_all(company_id)


@router.get("/{reception_id}")
async def get_reception(reception_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    row = await svc.get_by_id(reception_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Reception not found")
    return row


@router.post("/")
async def create_reception(payload: dict, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    reception_id = await svc.create(company_id, payload)
    return {"message": "Reception created", "reception_id": reception_id}


@router.put("/{reception_id}")
async def update_reception(reception_id: int, payload: dict, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.update(reception_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Reception not found")
    return {"message": "Reception updated"}


@router.delete("/{reception_id}")
async def delete_reception(reception_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.delete(reception_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Reception not found")
    return {"message": "Reception deleted"}




