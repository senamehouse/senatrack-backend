from typing import Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.id_generator import generate_id


class EmployeeDepartmentModel(Base):
    """SQLAlchemy model for Employee Department table"""
    __tablename__ = "employee_departments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employees: Mapped[list["EmployeeModel"]] = relationship("EmployeeModel", back_populates="department_relation")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "manager_id": self.manager_id,
            "budget": self.budget,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmployeeModel(Base):
    """SQLAlchemy model for Employee table"""
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    employee_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("employee_departments.id"), nullable=True, index=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="full_time")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hire_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    salary_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    salary_payment_frequency: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    department_relation: Mapped[Optional["EmployeeDepartmentModel"]] = relationship("EmployeeDepartmentModel", back_populates="employees")
    leave_requests: Mapped[list["EmployeeLeaveModel"]] = relationship("EmployeeLeaveModel", back_populates="employee", cascade="all, delete-orphan")
    payrolls: Mapped[list["EmployeePayrollModel"]] = relationship("EmployeePayrollModel", back_populates="employee", cascade="all, delete-orphan")
    performance_reviews: Mapped[list["EmployeePerformanceReviewModel"]] = relationship("EmployeePerformanceReviewModel", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companyId": self.company_id,
            "employeeNumber": self.employee_number,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "department": self.department_relation.name if self.department_relation else None,
            "departmentId": self.department_id,
            "departmentInfo": self.department_relation.to_dict() if self.department_relation else None,
            "position": self.position,
            "employmentType": self.employment_type,
            "isActive": self.is_active,
            "hireDate": self.hire_date,
            "salary": {
                "type": self.salary_type or "monthly",
                "amount": self.salary_amount or 0.0,
                "currency": self.salary_currency or "XOF",
                "paymentFrequency": self.salary_payment_frequency or "monthly",
            },
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmployeeLeaveModel(Base):
    """SQLAlchemy model for Employee Leave Request table"""
    __tablename__ = "employee_leave_requests"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    employee_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    days_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", back_populates="leave_requests")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companyId": self.company_id,
            "employeeId": self.employee_id,
            "employeeName": f"{self.employee.first_name} {self.employee.last_name}" if self.employee else "",
            "leaveType": self.leave_type,
            "status": self.status,
            "startDate": self.start_date,
            "endDate": self.end_date,
            "daysRequested": self.days_requested,
            "reason": self.reason,
            "approvedBy": self.approved_by,
            "approvedDate": self.approved_date,
            "rejectionReason": self.rejection_reason,
            "requestedDate": self.requested_date or (self.created_at.isoformat() if self.created_at else None),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmployeePayrollModel(Base):
    """SQLAlchemy model for Employee Payroll table"""
    __tablename__ = "employee_payrolls"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    employee_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False, index=True)
    period_start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    period_end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    basic_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transport_allowance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meal_allowance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    housing_allowance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_allowance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    social_security_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    health_insurance_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overtime_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overtime_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overtime_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    performance_bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attendance_bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gross_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    paid_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", back_populates="payrolls")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companyId": self.company_id,
            "employeeId": self.employee_id,
            "employeeName": f"{self.employee.first_name} {self.employee.last_name}" if self.employee else "",
            "period": {
                "startDate": self.period_start_date,
                "endDate": self.period_end_date,
                "month": self.period_month,
                "year": self.period_year,
            },
            "basicSalary": self.basic_salary,
            "allowances": {
                "transport": self.transport_allowance,
                "meal": self.meal_allowance,
                "housing": self.housing_allowance,
                "other": self.other_allowance,
            },
            "deductions": {
                "tax": self.tax_deduction,
                "socialSecurity": self.social_security_deduction,
                "healthInsurance": self.health_insurance_deduction,
                "other": self.other_deduction,
            },
            "overtime": {
                "hours": self.overtime_hours,
                "rate": self.overtime_rate,
                "amount": self.overtime_amount,
            },
            "bonuses": {
                "performance": self.performance_bonus,
                "attendance": self.attendance_bonus,
                "other": self.other_bonus,
            },
            "grossSalary": self.gross_salary,
            "totalDeductions": self.total_deductions,
            "netSalary": self.net_salary,
            "status": self.status,
            "paidDate": self.paid_date,
            "paymentMethod": self.payment_method,
            "notes": self.notes,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmployeePerformanceReviewModel(Base):
    """SQLAlchemy model for Employee Performance Review table"""
    __tablename__ = "employee_performance_reviews"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, default=generate_id)
    company_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    employee_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    review_period_start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    review_period_end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    areas_for_improvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    development_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    competencies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", back_populates="performance_reviews")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        goals = []
        competencies = []
        strengths = []
        areas_for_improvement = []
        
        try:
            if self.goals:
                goals = json.loads(self.goals)
            if self.competencies:
                competencies = json.loads(self.competencies)
            if self.strengths:
                strengths = json.loads(self.strengths)
            if self.areas_for_improvement:
                areas_for_improvement = json.loads(self.areas_for_improvement)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return {
            "id": self.id,
            "companyId": self.company_id,
            "employeeId": self.employee_id,
            "employeeName": f"{self.employee.first_name} {self.employee.last_name}" if self.employee else "",
            "reviewPeriod": {
                "startDate": self.review_period_start_date,
                "endDate": self.review_period_end_date,
            },
            "reviewerId": self.reviewer_id,
            "reviewerName": "",  # Will be populated by service if needed
            "goals": goals,
            "competencies": competencies,
            "overallRating": self.overall_rating,
            "strengths": strengths,
            "areasForImprovement": areas_for_improvement,
            "developmentPlan": self.development_plan,
            "nextReviewDate": self.next_review_date,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
