from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from . import SCHEMA_CONFIG


class LeaveRequestBase(BaseModel):
    model_config = SCHEMA_CONFIG

    employee_id: str = Field(..., alias="employeeId")
    leave_type: str = Field(..., alias="leaveType")
    status: str = Field("pending")
    start_date: str = Field(..., alias="startDate")
    end_date: str = Field(..., alias="endDate")
    days_requested: int = Field(..., ge=1, alias="daysRequested")
    reason: Optional[str] = None
    approved_by: Optional[str] = Field(None, alias="approvedBy")
    approved_date: Optional[str] = Field(None, alias="approvedDate")


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    model_config = SCHEMA_CONFIG

    leave_type: Optional[str] = Field(None, alias="leaveType")
    status: Optional[str] = None
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    days_requested: Optional[int] = Field(None, ge=1, alias="daysRequested")
    reason: Optional[str] = None
    approved_by: Optional[str] = Field(None, alias="approvedBy")
    approved_date: Optional[str] = Field(None, alias="approvedDate")


class LeaveRequest(LeaveRequestBase):
    model_config = SCHEMA_CONFIG

    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




