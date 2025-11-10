from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.payroll_schema import Payroll, PayrollCreate, PayrollUpdate
from app.services.payroll_service import PayrollService


router = APIRouter(prefix="/payroll", tags=["Payroll"])
svc = PayrollService()


@router.get("/", response_model=List[Payroll])
async def get_payroll(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/{payroll_id}", response_model=Payroll)
async def get_payroll_row(
    payroll_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    row = await svc.get_by_id(payroll_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return row


@router.post("/", response_model=dict)
async def create_payroll(
    payload: PayrollCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    payroll_id = await svc.create(company_id, payload)
    return {"message": "Payroll created", "payroll_id": payroll_id}


@router.put("/{payroll_id}", response_model=dict)
async def update_payroll(
    payroll_id: int,
    payload: PayrollUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(payroll_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll updated"}


@router.delete("/{payroll_id}", response_model=dict)
async def delete_payroll(
    payroll_id: int,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(payroll_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll deleted"}

@router.get("/stats", response_model=dict)
async def get_payroll_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_stats(company_id)