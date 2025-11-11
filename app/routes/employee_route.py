from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.employee_schema import Employee, EmployeeCreate, EmployeeUpdate
from app.services.employee_service import EmployeeService


router = APIRouter(prefix="/employees", tags=["Employees"])
svc = EmployeeService()


@router.get("/", response_model=List[Employee])
async def get_employees(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(
    employee_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    emp = await svc.get_by_id(employee_id, company_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("/", response_model=dict)
async def create_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    emp_id = await svc.create(company_id, payload)
    return {"message": "Employee created", "employee_id": emp_id}


@router.put("/{employee_id}", response_model=dict)
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(employee_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated"}


@router.delete("/{employee_id}", response_model=dict)
async def delete_employee(
    employee_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete(employee_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted"}

@router.get("/stats", response_model=dict)
async def get_employee_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_stats(company_id)


@router.get("/next-number", response_model=dict)
async def get_next_employee_number(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    number = await svc.generate_employee_number(company_id)
    return {"employeeNumber": number}