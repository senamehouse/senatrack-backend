from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List


class ActivityLogBase(BaseModel):
    """Base activity log schema"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, serialize_by_alias=True)
    
    action: str = Field(..., min_length=1, max_length=255)
    details: str = Field(..., min_length=1)
    user_id: Optional[int] = Field(None, alias="userId")
    user_email: Optional[str] = Field(None, max_length=255, alias="userEmail")
    company_id: Optional[int] = Field(None, alias="companyId")
    entity_type: Optional[str] = Field(None, max_length=100, alias="entityType")
    entity_id: Optional[str] = Field(None, max_length=100, alias="entityId")
    extra_data: Optional[Dict[str, Any]] = Field(None, alias="extraData")


class ActivityLogCreate(ActivityLogBase):
    """Schema for creating an activity log"""
    pass


class ActivityLog(ActivityLogBase):
    """Schema for activity log response"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, serialize_by_alias=True)
    
    id: int
    created_at: datetime = Field(..., alias="createdAt")


class ActivityLogFilters(BaseModel):
    """Schema for activity log filters"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, serialize_by_alias=True)
    
    user_id: Optional[int] = Field(None, alias="userId")
    company_id: Optional[int] = Field(None, alias="companyId")
    entity_type: Optional[str] = Field(None, alias="entityType")
    entity_id: Optional[str] = Field(None, alias="entityId")
    start_date: Optional[datetime] = Field(None, alias="startDate")
    end_date: Optional[datetime] = Field(None, alias="endDate")
    actions: Optional[List[str]] = None
    limit: Optional[int] = Field(100, ge=1, le=1000)


class ActivityLogStats(BaseModel):
    """Schema for activity log statistics"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, serialize_by_alias=True)
    
    total: int
    today: int
    this_week: int = Field(..., alias="thisWeek")
    this_month: int = Field(..., alias="thisMonth")
    by_action: Dict[str, int] = Field(..., alias="byAction")
    by_user: Dict[str, int] = Field(..., alias="byUser")
