from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.employee_model import (
    EmployeeModel,
    EmployeeDepartmentModel,
    EmployeeLeaveModel,
    EmployeePayrollModel,
    EmployeePerformanceReviewModel
)
from app.schemas.employee_schema import (
    Employee as EmployeeSchema, 
    EmployeeCreate, 
    EmployeeUpdate,
    EmployeeDepartment as EmployeeDepartmentSchema,
    EmployeeDepartmentCreate,
    EmployeeDepartmentUpdate,
    EmployeeLeaveRequest as EmployeeLeaveRequestSchema,
    EmployeeLeaveRequestCreate,
    EmployeeLeaveRequestUpdate,
    EmployeePayroll as EmployeePayrollSchema,
    EmployeePayrollCreate,
    EmployeePayrollUpdate,
    EmployeePerformanceReview as EmployeePerformanceReviewSchema,
    EmployeePerformanceReviewCreate,
    EmployeePerformanceReviewUpdate
)
from app.utils.activity_logger import audit, ActivityActor


class EmployeeService:
    async def get_all(self, company_id: str) -> List[EmployeeSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeModel).where(
                    EmployeeModel.company_id == company_id,
                    EmployeeModel.is_active == True,
                )
            )
            rows = result.scalars().all()
            return [EmployeeSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving employees: {str(e)}")

    async def get_by_id(self, employee_id: str, company_id: str) -> Optional[EmployeeSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeModel).where(
                    EmployeeModel.id == employee_id,
                    EmployeeModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return EmployeeSchema.model_validate(row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving employee: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="employee",
        details=lambda result, _a, kw: f"Employé {kw['payload'].first_name} {kw['payload'].last_name} créé",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(mode='json', exclude_none=True)},
    )
    async def create(self, company_id: str, payload: EmployeeCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            # Always generate employee_number if not provided or empty
            employee_number = payload.employee_number
            if not employee_number or not employee_number.strip():
                employee_number = await self.generate_employee_number(company_id)
            
            salary_data = payload.salary if hasattr(payload, 'salary') else {}
            emp = EmployeeModel(
                company_id=company_id,
                employee_number=employee_number,
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                phone=payload.phone,
                address=getattr(payload, 'address', None),
                department_id=getattr(payload, 'department_id', None),
                position=payload.position,
                employment_type=getattr(payload, 'employment_type', 'full_time'),
                is_active=getattr(payload, 'is_active', True),
                hire_date=getattr(payload, 'hire_date', None),
                salary_type=salary_data.get('type') if salary_data else None,
                salary_amount=salary_data.get('amount') if salary_data else payload.salary_amount,
                salary_currency=salary_data.get('currency') if salary_data else payload.salary_currency,
                salary_payment_frequency=salary_data.get('payment_frequency') if salary_data else None,
            )
            session.add(emp)
            await session.commit()
            await session.refresh(emp)
            return emp.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="employee",
        details=lambda _r, _a, kw: f"Employé {kw['employee_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["employee_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update(self, employee_id: str, company_id: str, payload: EmployeeUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeModel).where(
                    EmployeeModel.id == employee_id,
                    EmployeeModel.company_id == company_id,
                )
            )
            emp = result.scalar_one_or_none()
            if not emp:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(emp, field, value)
            emp.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="employee",
        details=lambda _r, _a, kw: f"Employé {kw['employee_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["employee_id"],
    )
    async def delete(self, employee_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeModel).where(
                    EmployeeModel.id == employee_id,
                    EmployeeModel.company_id == company_id,
                )
            )
            emp = result.scalar_one_or_none()
            if not emp:
                return False
            emp.is_active = False
            emp.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

    async def get_stats(self, company_id: str) -> Dict:
        """Return counts and department breakdown for active/inactive employees."""
        try:
            session = get_db_session()
            # Total
            total_q = await session.execute(
                select(func.count()).select_from(EmployeeModel).where(
                    EmployeeModel.company_id == company_id
                )
            )
            total = total_q.scalar() or 0

            # Active
            active_q = await session.execute(
                select(func.count()).select_from(EmployeeModel).where(
                    EmployeeModel.company_id == company_id,
                    EmployeeModel.is_active == True,
                )
            )
            active = active_q.scalar() or 0

            inactive = max(total - active, 0)

            # By department (active only) - using relationship
            from sqlalchemy.orm import joinedload
            result = await session.execute(
                select(EmployeeModel)
                .options(joinedload(EmployeeModel.department_relation))
                .where(
                    EmployeeModel.company_id == company_id,
                    EmployeeModel.is_active == True,
                )
            )
            employees = result.unique().scalars().all()
            by_department: Dict[str, int] = {}
            for emp in employees:
                dept_name = emp.department_relation.name if emp.department_relation else "Unknown"
                by_department[dept_name] = by_department.get(dept_name, 0) + 1

            return {
                "total": total,
                "active": active,
                "inactive": inactive,
                "byDepartment": by_department,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing employee stats: {str(e)}")

    async def generate_employee_number(self, company_id: str) -> str:
        """Generate employee number like EMP-YYYY-0001 per company."""
        try:
            session = get_db_session()
            year = datetime.utcnow().year
            prefix = f"EMP-{year}-"
            rows = await session.execute(
                select(EmployeeModel.employee_number)
                .where(
                    EmployeeModel.company_id == company_id,
                    EmployeeModel.employee_number.like(f"{prefix}%"),
                )
            )
            existing = {r[0] for r in rows.fetchall() if r[0]}
            counter = 1
            next_ref = f"{prefix}{counter:04d}"
            while next_ref in existing:
                counter += 1
                next_ref = f"{prefix}{counter:04d}"
            return next_ref
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating employee number: {str(e)}")

    # Employee Department methods
    async def get_all_departments(self, company_id: str) -> List[EmployeeDepartmentSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeDepartmentModel).where(
                    EmployeeDepartmentModel.company_id == company_id,
                    EmployeeDepartmentModel.is_active == True,
                )
            )
            departments = result.scalars().all()
            return [EmployeeDepartmentSchema.model_validate(d.to_dict()) for d in departments]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving departments: {str(e)}")

    async def get_department_by_id(self, department_id: str, company_id: str) -> Optional[EmployeeDepartmentSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeDepartmentModel).where(
                    EmployeeDepartmentModel.id == department_id,
                    EmployeeDepartmentModel.company_id == company_id,
                    EmployeeDepartmentModel.is_active == True,
                )
            )
            department = result.scalar_one_or_none()
            return EmployeeDepartmentSchema.model_validate(department.to_dict()) if department else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving department: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="employee_department",
        details=lambda result, _a, kw: f"Département {kw['payload'].name} créé",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create_department(self, company_id: str, payload: EmployeeDepartmentCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            department = EmployeeDepartmentModel(
                company_id=company_id,
                name=payload.name,
                description=payload.description,
                manager_id=payload.manager_id,
                budget=payload.budget,
                location=payload.location,
            )
            session.add(department)
            await session.commit()
            await session.refresh(department)
            return department.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating department: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="employee_department",
        details=lambda _r, _a, kw: f"Département {kw['department_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["department_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update_department(self, department_id: str, company_id: str, payload: EmployeeDepartmentUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeDepartmentModel).where(
                    EmployeeDepartmentModel.id == department_id,
                    EmployeeDepartmentModel.company_id == company_id,
                )
            )
            department = result.scalar_one_or_none()
            if not department:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(department, field, value)
            department.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating department: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="employee_department",
        details=lambda _r, _a, kw: f"Département {kw['department_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["department_id"],
    )
    async def delete_department(self, department_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeDepartmentModel).where(
                    EmployeeDepartmentModel.id == department_id,
                    EmployeeDepartmentModel.company_id == company_id,
                )
            )
            department = result.scalar_one_or_none()
            if not department:
                return False
            department.is_active = False
            department.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting department: {str(e)}")

    # Leave Request methods
    async def get_all_leave_requests(self, company_id: str) -> List[EmployeeLeaveRequestSchema]:
        """Get all leave requests for a company (across all employees)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeeLeaveRequestSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving leave requests: {str(e)}")

    async def get_leave_requests(self, employee_id: str, company_id: str) -> List[EmployeeLeaveRequestSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeeLeaveRequestSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving leave requests: {str(e)}")

    async def get_leave_request_by_id(self, leave_id: str, employee_id: str, company_id: str) -> Optional[EmployeeLeaveRequestSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.id == leave_id,
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return EmployeeLeaveRequestSchema.model_validate(row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving leave request: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="employee_leave",
        details=lambda result, _a, kw: f"Demande de congé créée pour employé {kw['employee_id']}",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create_leave_request(self, employee_id: str, company_id: str, payload: EmployeeLeaveRequestCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            lv = EmployeeLeaveModel(
                company_id=company_id,
                employee_id=employee_id,
                leave_type=payload.leave_type,
                status=payload.status,
                start_date=payload.start_date,
                end_date=payload.end_date,
                days_requested=payload.days_requested,
                reason=payload.reason,
                requested_date=datetime.utcnow().isoformat(),
            )
            session.add(lv)
            await session.commit()
            await session.refresh(lv)
            return lv.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating leave request: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="employee_leave",
        details=lambda _r, _a, kw: f"Demande de congé {kw['leave_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["leave_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update_leave_request(self, leave_id: str, employee_id: str, company_id: str, payload: EmployeeLeaveRequestUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.id == leave_id,
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(lv, field, value)
            lv.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating leave request: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="employee_leave",
        details=lambda _r, _a, kw: f"Demande de congé {kw['leave_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["leave_id"],
    )
    async def delete_leave_request(self, leave_id: str, employee_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.id == leave_id,
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            await session.delete(lv)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting leave request: {str(e)}")

    async def approve_leave_request(self, leave_id: str, employee_id: str, company_id: str, approved_by: Optional[str] = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.id == leave_id,
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            lv.status = "approved"
            lv.approved_by = approved_by
            lv.approved_date = datetime.utcnow().isoformat()
            lv.updated_at = datetime.utcnow()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error approving leave request: {str(e)}")

    async def reject_leave_request(self, leave_id: str, employee_id: str, company_id: str, approved_by: Optional[str] = None, rejection_reason: Optional[str] = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeeLeaveModel).where(
                    EmployeeLeaveModel.id == leave_id,
                    EmployeeLeaveModel.employee_id == employee_id,
                    EmployeeLeaveModel.company_id == company_id,
                )
            )
            lv = result.scalar_one_or_none()
            if not lv:
                return False
            lv.status = "rejected"
            lv.approved_by = approved_by
            lv.approved_date = datetime.utcnow().isoformat()
            lv.rejection_reason = rejection_reason
            lv.updated_at = datetime.utcnow()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error rejecting leave request: {str(e)}")

    # Payroll methods
    async def get_all_payrolls(self, company_id: str) -> List[EmployeePayrollSchema]:
        """Get all payrolls for a company (across all employees)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePayrollModel).where(
                    EmployeePayrollModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeePayrollSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving payrolls: {str(e)}")

    async def get_payrolls(self, employee_id: str, company_id: str) -> List[EmployeePayrollSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePayrollModel).where(
                    EmployeePayrollModel.employee_id == employee_id,
                    EmployeePayrollModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeePayrollSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving payrolls: {str(e)}")

    async def get_payroll_by_id(self, payroll_id: str, employee_id: str, company_id: str) -> Optional[EmployeePayrollSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePayrollModel).where(
                    EmployeePayrollModel.id == payroll_id,
                    EmployeePayrollModel.employee_id == employee_id,
                    EmployeePayrollModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return EmployeePayrollSchema.model_validate(row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving payroll: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="employee_payroll",
        details=lambda result, _a, kw: f"Paie créée pour employé {kw['employee_id']}",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create_payroll(self, employee_id: str, company_id: str, payload: EmployeePayrollCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            pr = EmployeePayrollModel(
                company_id=company_id,
                employee_id=employee_id,
                period_year=payload.period_year,
                period_month=payload.period_month,
                period_start_date=f"{payload.period_year}-{payload.period_month:02d}-01",
                period_end_date=f"{payload.period_year}-{payload.period_month:02d}-28",
                net_salary=payload.net_salary,
                status=payload.status,
                payment_method=payload.payment_method,
                paid_date=payload.paid_date,
            )
            session.add(pr)
            await session.commit()
            await session.refresh(pr)
            return pr.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating payroll: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="employee_payroll",
        details=lambda _r, _a, kw: f"Paie {kw['payroll_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["payroll_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update_payroll(self, payroll_id: str, employee_id: str, company_id: str, payload: EmployeePayrollUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePayrollModel).where(
                    EmployeePayrollModel.id == payroll_id,
                    EmployeePayrollModel.employee_id == employee_id,
                    EmployeePayrollModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(pr, field, value)
            pr.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating payroll: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="employee_payroll",
        details=lambda _r, _a, kw: f"Paie {kw['payroll_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["payroll_id"],
    )
    async def delete_payroll(self, payroll_id: str, employee_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePayrollModel).where(
                    EmployeePayrollModel.id == payroll_id,
                    EmployeePayrollModel.employee_id == employee_id,
                    EmployeePayrollModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            await session.delete(pr)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting payroll: {str(e)}")

    # Performance Review methods
    async def get_all_performance_reviews(self, company_id: str) -> List[EmployeePerformanceReviewSchema]:
        """Get all performance reviews for a company (across all employees)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePerformanceReviewModel).where(
                    EmployeePerformanceReviewModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeePerformanceReviewSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving performance reviews: {str(e)}")

    async def get_performance_reviews(self, employee_id: str, company_id: str) -> List[EmployeePerformanceReviewSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePerformanceReviewModel).where(
                    EmployeePerformanceReviewModel.employee_id == employee_id,
                    EmployeePerformanceReviewModel.company_id == company_id,
                )
            )
            rows = result.scalars().all()
            return [EmployeePerformanceReviewSchema.model_validate(r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving performance reviews: {str(e)}")

    async def get_performance_review_by_id(self, review_id: str, employee_id: str, company_id: str) -> Optional[EmployeePerformanceReviewSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePerformanceReviewModel).where(
                    EmployeePerformanceReviewModel.id == review_id,
                    EmployeePerformanceReviewModel.employee_id == employee_id,
                    EmployeePerformanceReviewModel.company_id == company_id,
                )
            )
            row = result.scalar_one_or_none()
            return EmployeePerformanceReviewSchema.model_validate(row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving performance review: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="employee_performance_review",
        details=lambda result, _a, kw: f"Évaluation créée pour employé {kw['employee_id']}",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create_performance_review(self, employee_id: str, company_id: str, payload: EmployeePerformanceReviewCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            pr = EmployeePerformanceReviewModel(
                company_id=company_id,
                employee_id=employee_id,
                reviewer_id=payload.reviewer_id,
                status=payload.status,
                overall_rating=payload.overall_rating,
                review_period_start_date="",
                review_period_end_date="",
            )
            session.add(pr)
            await session.commit()
            await session.refresh(pr)
            return pr.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating performance review: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="employee_performance_review",
        details=lambda _r, _a, kw: f"Évaluation {kw['review_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["review_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update_performance_review(self, review_id: str, employee_id: str, company_id: str, payload: EmployeePerformanceReviewUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePerformanceReviewModel).where(
                    EmployeePerformanceReviewModel.id == review_id,
                    EmployeePerformanceReviewModel.employee_id == employee_id,
                    EmployeePerformanceReviewModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(pr, field, value)
            pr.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating performance review: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="employee_performance_review",
        details=lambda _r, _a, kw: f"Évaluation {kw['review_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["review_id"],
    )
    async def delete_performance_review(self, review_id: str, employee_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(EmployeePerformanceReviewModel).where(
                    EmployeePerformanceReviewModel.id == review_id,
                    EmployeePerformanceReviewModel.employee_id == employee_id,
                    EmployeePerformanceReviewModel.company_id == company_id,
                )
            )
            pr = result.scalar_one_or_none()
            if not pr:
                return False
            await session.delete(pr)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting performance review: {str(e)}")