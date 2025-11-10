from app.utils.casing import BaseCamelModel
from pydantic import Field
from datetime import datetime
from typing import Optional


class PerformanceReviewBase(BaseCamelModel):

    employee_id: str = Field(..., alias="employeeId")
    reviewer_id: str = Field(..., alias="reviewerId")
    status: str = Field("draft")
    overall_rating: float = Field(0, ge=0, le=5, alias="overallRating")


class PerformanceReviewCreate(PerformanceReviewBase):
    pass


class PerformanceReviewUpdate(BaseCamelModel):

    status: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=5, alias="overallRating")


class PerformanceReview(PerformanceReviewBase):
    id: str
    company_id: Optional[str] = Field(None, alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")




