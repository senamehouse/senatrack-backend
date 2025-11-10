from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class PayrollBase(BaseCamelModel):

    employee_id: str = Field(..., alias="employeeId")
    period_year: int = Field(..., ge=2000, le=9999, alias="periodYear")
    period_month: int = Field(..., ge=1, le=12, alias="periodMonth")
    net_salary: float = Field(..., ge=0, alias="netSalary")
    status: str = Field("pending")
    payment_method: Optional[str] = Field(None, alias="paymentMethod")
    paid_date: Optional[str] = Field(None, alias="paidDate")


class PayrollCreate(PayrollBase):
    pass


class PayrollUpdate(BaseCamelModel):

    period_year: Optional[int] = Field(None, ge=2000, le=9999, alias="periodYear")
    period_month: Optional[int] = Field(None, ge=1, le=12, alias="periodMonth")
    net_salary: Optional[float] = Field(None, ge=0, alias="netSalary")
    status: Optional[str] = None
    payment_method: Optional[str] = Field(None, alias="paymentMethod")
    paid_date: Optional[str] = Field(None, alias="paidDate")


class Payroll(PayrollBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




