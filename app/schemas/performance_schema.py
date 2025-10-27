from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from . import SCHEMA_CONFIG


class PerformanceReviewBase(BaseModel):
    model_config = SCHEMA_CONFIG

    employee_id: str = Field(..., alias="employeeId")
    reviewer_id: str = Field(..., alias="reviewerId")
    status: str = Field("draft")
    overall_rating: float = Field(0, ge=0, le=5, alias="overallRating")


class PerformanceReviewCreate(PerformanceReviewBase):
    pass


class PerformanceReviewUpdate(BaseModel):
    model_config = SCHEMA_CONFIG

    status: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=5, alias="overallRating")


class PerformanceReview(PerformanceReviewBase):
    model_config = SCHEMA_CONFIG

    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




