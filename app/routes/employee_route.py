from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_company_id
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.employee_schema import (
    Employee, 
    EmployeeCreate, 
    EmployeeUpdate,
    Department,
    DepartmentCreate,
    DepartmentUpdate
)
from app.services.employee_service import EmployeeService
from app.utils.activity_logger import ActivityActor


router = APIRouter(prefix="/employees", tags=["Employees"])
svc = EmployeeService()


@router.get("/", response_model=List[Employee])
async def get_employees(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all(company_id)


# Specific routes must come BEFORE parameterized routes to avoid conflicts
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


# Department routes (must come before /{employee_id} to avoid conflicts)
@router.get("/departments", response_model=List[Department])
async def get_departments(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_departments(company_id)


@router.get("/departments/{department_id}", response_model=Department)
async def get_department(
    department_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    dept = await svc.get_department_by_id(department_id, company_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.post("/departments", response_model=dict)
async def create_department(
    payload: DepartmentCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    dept_id = await svc.create_department(company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Department created", "department_id": dept_id}


@router.put("/departments/{department_id}", response_model=dict)
async def update_department(
    department_id: str,
    payload: DepartmentUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update_department(department_id=department_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department updated"}


@router.delete("/departments/{department_id}", response_model=dict)
async def delete_department(
    department_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete_department(department_id=department_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department deleted"}


# Parameterized routes must come AFTER specific routes
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
    emp_id = await svc.create(company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Employee created", "employee_id": emp_id}


@router.put("/{employee_id}", response_model=dict)
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update(employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
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
    ok = await svc.delete(employee_id=employee_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted"}