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
    EmployeeDepartment,
    EmployeeDepartmentCreate,
    EmployeeDepartmentUpdate,
    EmployeeLeaveRequest,
    EmployeeLeaveRequestCreate,
    EmployeeLeaveRequestUpdate,
    EmployeePayroll,
    EmployeePayrollCreate,
    EmployeePayrollUpdate,
    EmployeePerformanceReview,
    EmployeePerformanceReviewCreate,
    EmployeePerformanceReviewUpdate
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


# Department routes (must come before /{employee_id} to avoid conflicts)
@router.get("/departments", response_model=List[EmployeeDepartment])
async def get_departments(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_departments(company_id)


@router.get("/departments/{department_id}", response_model=EmployeeDepartment)
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
    payload: EmployeeDepartmentCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user), 
    company_id: str = Depends(get_company_id)
):
    dept_id = await svc.create_department(company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Department created", "department_id": dept_id}


@router.put("/departments/{department_id}", response_model=dict)
async def update_department(
    department_id: str,
    payload: EmployeeDepartmentUpdate,
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


# Company-wide Leave Request routes (before employee-specific routes)
@router.get("/leaves", response_model=List[EmployeeLeaveRequest])
async def get_all_leave_requests(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_leave_requests(company_id)

# Leave Request routes
@router.get("/{employee_id}/leaves", response_model=List[EmployeeLeaveRequest])
async def get_employee_leaves(
    employee_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_leave_requests(employee_id, company_id)


@router.get("/{employee_id}/leaves/{leave_id}", response_model=EmployeeLeaveRequest)
async def get_employee_leave(
    employee_id: str,
    leave_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    leave = await svc.get_leave_request_by_id(leave_id, employee_id, company_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave


@router.post("/{employee_id}/leaves", response_model=dict)
async def create_employee_leave(
    employee_id: str,
    payload: EmployeeLeaveRequestCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    leave_id = await svc.create_leave_request(employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Leave request created", "leave_id": leave_id}


@router.put("/{employee_id}/leaves/{leave_id}", response_model=dict)
async def update_employee_leave(
    employee_id: str,
    leave_id: str,
    payload: EmployeeLeaveRequestUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update_leave_request(leave_id=leave_id, employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request updated"}


@router.delete("/{employee_id}/leaves/{leave_id}", response_model=dict)
async def delete_employee_leave(
    employee_id: str,
    leave_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete_leave_request(leave_id=leave_id, employee_id=employee_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request deleted"}


@router.post("/{employee_id}/leaves/{leave_id}/approve", response_model=dict)
async def approve_employee_leave(
    employee_id: str,
    leave_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.approve_leave_request(leave_id=leave_id, employee_id=employee_id, company_id=company_id, approved_by=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request approved"}


@router.post("/{employee_id}/leaves/{leave_id}/reject", response_model=dict)
async def reject_employee_leave(
    employee_id: str,
    leave_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    rejection_reason = payload.get("rejectionReason")
    ok = await svc.reject_leave_request(leave_id=leave_id, employee_id=employee_id, company_id=company_id, approved_by=current_user.id, rejection_reason=rejection_reason)
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request rejected"}


# Company-wide Payroll routes (before employee-specific routes)
@router.get("/payrolls", response_model=List[EmployeePayroll])
async def get_all_payrolls(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_payrolls(company_id)

# Payroll routes
@router.get("/{employee_id}/payrolls", response_model=List[EmployeePayroll])
async def get_employee_payrolls(
    employee_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_payrolls(employee_id, company_id)


@router.get("/{employee_id}/payrolls/{payroll_id}", response_model=EmployeePayroll)
async def get_employee_payroll(
    employee_id: str,
    payroll_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    payroll = await svc.get_payroll_by_id(payroll_id, employee_id, company_id)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return payroll


@router.post("/{employee_id}/payrolls", response_model=dict)
async def create_employee_payroll(
    employee_id: str,
    payload: EmployeePayrollCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    payroll_id = await svc.create_payroll(employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Payroll created", "payroll_id": payroll_id}


@router.put("/{employee_id}/payrolls/{payroll_id}", response_model=dict)
async def update_employee_payroll(
    employee_id: str,
    payroll_id: str,
    payload: EmployeePayrollUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update_payroll(payroll_id=payroll_id, employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll updated"}


@router.delete("/{employee_id}/payrolls/{payroll_id}", response_model=dict)
async def delete_employee_payroll(
    employee_id: str,
    payroll_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete_payroll(payroll_id=payroll_id, employee_id=employee_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll deleted"}


# Company-wide Performance Review routes (before employee-specific routes)
@router.get("/reviews", response_model=List[EmployeePerformanceReview])
async def get_all_performance_reviews(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_all_performance_reviews(company_id)

# Performance Review routes
@router.get("/{employee_id}/reviews", response_model=List[EmployeePerformanceReview])
async def get_employee_reviews(
    employee_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    return await svc.get_performance_reviews(employee_id, company_id)


@router.get("/{employee_id}/reviews/{review_id}", response_model=EmployeePerformanceReview)
async def get_employee_review(
    employee_id: str,
    review_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    review = await svc.get_performance_review_by_id(review_id, employee_id, company_id)
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return review


@router.post("/{employee_id}/reviews", response_model=dict)
async def create_employee_review(
    employee_id: str,
    payload: EmployeePerformanceReviewCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    review_id = await svc.create_performance_review(employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    return {"message": "Performance review created", "review_id": review_id}


@router.put("/{employee_id}/reviews/{review_id}", response_model=dict)
async def update_employee_review(
    employee_id: str,
    review_id: str,
    payload: EmployeePerformanceReviewUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.update_performance_review(review_id=review_id, employee_id=employee_id, company_id=company_id, payload=payload, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return {"message": "Performance review updated"}


@router.delete("/{employee_id}/reviews/{review_id}", response_model=dict)
async def delete_employee_review(
    employee_id: str,
    review_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_company_id)
):
    ok = await svc.delete_performance_review(review_id=review_id, employee_id=employee_id, company_id=company_id, actor=ActivityActor(current_user.id, None))
    if not ok:
        raise HTTPException(status_code=404, detail="Performance review not found")
    return {"message": "Performance review deleted"}