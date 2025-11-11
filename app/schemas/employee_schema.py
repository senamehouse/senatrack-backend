from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class EmployeeBase(BaseCamelModel):

    employee_number: Optional[str] = Field(None, max_length=50, alias="employeeNumber")
    first_name: str = Field(..., min_length=1, max_length=100, alias="firstName")
    last_name: str = Field(..., min_length=1, max_length=100, alias="lastName")
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employment_status: str = Field("active", alias="employmentStatus")
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
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employment_status: Optional[str] = Field(None, alias="employmentStatus")
    salary_amount: Optional[float] = Field(None, ge=0, alias="salaryAmount")
    salary_currency: Optional[str] = Field(None, max_length=10, alias="salaryCurrency")
    is_active: Optional[bool] = Field(None, alias="isActive")


class Employee(EmployeeBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


# Department schemas
class DepartmentBase(BaseCamelModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[str] = Field(None, alias="managerId")
    budget: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseCamelModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[str] = Field(None, alias="managerId")
    budget: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None, alias="isActive")


class Department(DepartmentBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




