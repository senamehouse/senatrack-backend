from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any


class EmployeeSalary(BaseCamelModel):
    type: str = Field(..., alias="type")
    amount: float = Field(..., ge=0, alias="amount")
    currency: str = Field(..., alias="currency")
    payment_frequency: str = Field(..., alias="paymentFrequency")


class EmployeeBase(BaseCamelModel):

    employee_number: Optional[str] = Field(None, max_length=50, alias="employeeNumber")
    first_name: str = Field(..., min_length=1, max_length=100, alias="firstName")
    last_name: str = Field(..., min_length=1, max_length=100, alias="lastName")
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, alias="address")
    department_id: Optional[str] = Field(None, alias="departmentId")
    position: Optional[str] = Field(None, max_length=100)
    employment_type: str = Field("full_time", alias="employmentType")
    is_active: bool = Field(True, alias="isActive")
    hire_date: Optional[str] = Field(None, alias="hireDate")
    salary: Optional[EmployeeSalary] = Field(None, alias="salary")
    # Legacy fields for backward compatibility
    salary_amount: Optional[float] = Field(None, ge=0, alias="salaryAmount")
    salary_currency: Optional[str] = Field(None, max_length=10, alias="salaryCurrency")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseCamelModel):

    employee_number: Optional[str] = Field(None, max_length=50, alias="employeeNumber")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, alias="firstName")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, alias="lastName")
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, alias="address")
    department_id: Optional[str] = Field(None, alias="departmentId")
    position: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, alias="employmentType")
    is_active: Optional[bool] = Field(None, alias="isActive")
    hire_date: Optional[str] = Field(None, alias="hireDate")
    salary: Optional[EmployeeSalary] = Field(None, alias="salary")
    # Legacy fields for backward compatibility
    salary_amount: Optional[float] = Field(None, ge=0, alias="salaryAmount")
    salary_currency: Optional[str] = Field(None, max_length=10, alias="salaryCurrency")


class Employee(EmployeeBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    department: Optional[str] = None  # Department name for backward compatibility
    department_info: Optional[Dict[str, Any]] = Field(None, alias="departmentInfo")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Employee Department schemas
class EmployeeDepartmentBase(BaseCamelModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[str] = Field(None, alias="managerId")
    budget: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)


class EmployeeDepartmentCreate(EmployeeDepartmentBase):
    pass


class EmployeeDepartmentUpdate(BaseCamelModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[str] = Field(None, alias="managerId")
    budget: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None, alias="isActive")


class EmployeeDepartment(EmployeeDepartmentBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Employee Leave Request schemas
class EmployeeLeaveRequestBase(BaseCamelModel):
    employee_id: str = Field(..., alias="employeeId")
    leave_type: str = Field(..., alias="leaveType")
    status: str = Field("pending")
    start_date: str = Field(..., alias="startDate")
    end_date: str = Field(..., alias="endDate")
    days_requested: int = Field(..., ge=1, alias="daysRequested")
    reason: Optional[str] = None
    approved_by: Optional[str] = Field(None, alias="approvedBy")
    approved_date: Optional[str] = Field(None, alias="approvedDate")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")
    requested_date: Optional[str] = Field(None, alias="requestedDate")


class EmployeeLeaveRequestCreate(EmployeeLeaveRequestBase):
    pass


class EmployeeLeaveRequestUpdate(BaseCamelModel):
    leave_type: Optional[str] = Field(None, alias="leaveType")
    status: Optional[str] = None
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    days_requested: Optional[int] = Field(None, ge=1, alias="daysRequested")
    reason: Optional[str] = None
    approved_by: Optional[str] = Field(None, alias="approvedBy")
    approved_date: Optional[str] = Field(None, alias="approvedDate")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")


class EmployeeLeaveRequest(EmployeeLeaveRequestBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    employee_name: Optional[str] = Field(None, alias="employeeName")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Employee Payroll schemas - simplified
class EmployeePayrollBase(BaseCamelModel):
    employee_id: str = Field(..., alias="employeeId")
    period_year: int = Field(..., ge=2000, le=9999, alias="periodYear")
    period_month: int = Field(..., ge=1, le=12, alias="periodMonth")
    net_salary: float = Field(..., ge=0, alias="netSalary")
    status: str = Field("pending")
    payment_method: Optional[str] = Field(None, alias="paymentMethod")
    paid_date: Optional[str] = Field(None, alias="paidDate")
    notes: Optional[str] = Field(None, alias="notes")


class EmployeePayrollCreate(EmployeePayrollBase):
    pass


class EmployeePayrollUpdate(BaseCamelModel):
    period_year: Optional[int] = Field(None, ge=2000, le=9999, alias="periodYear")
    period_month: Optional[int] = Field(None, ge=1, le=12, alias="periodMonth")
    net_salary: Optional[float] = Field(None, ge=0, alias="netSalary")
    status: Optional[str] = None
    payment_method: Optional[str] = Field(None, alias="paymentMethod")
    paid_date: Optional[str] = Field(None, alias="paidDate")
    notes: Optional[str] = Field(None, alias="notes")


class EmployeePayroll(EmployeePayrollBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    employee_name: Optional[str] = Field(None, alias="employeeName")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")






