from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.employee_model import Employee as EmployeeModel
from app.models.department_model import Department as DepartmentModel
from app.schemas.employee_schema import (
    Employee as EmployeeSchema, 
    EmployeeCreate, 
    EmployeeUpdate,
    Department as DepartmentSchema,
    DepartmentCreate,
    DepartmentUpdate
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
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create(self, company_id: str, payload: EmployeeCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            emp = EmployeeModel(
                company_id=company_id,
                employee_number=payload.employee_number,
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                phone=payload.phone,
                department=payload.department,
                position=payload.position,
                employment_status=payload.employment_status,
                salary_amount=payload.salary_amount,
                salary_currency=payload.salary_currency,
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

            # By department (active only)
            dept_rows = await session.execute(
                select(EmployeeModel.department, func.count())
                .where(
                    EmployeeModel.company_id == company_id,
                    EmployeeModel.is_active == True,
                )
                .group_by(EmployeeModel.department)
            )
            by_department: Dict[str, int] = {}
            for name, count in dept_rows.all():
                key = name or "Unknown"
                by_department[key] = count

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

    # Department methods
    async def get_all_departments(self, company_id: str) -> List[DepartmentSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(DepartmentModel).where(
                    DepartmentModel.company_id == company_id,
                    DepartmentModel.is_active == True,
                )
            )
            departments = result.scalars().all()
            return [DepartmentSchema.model_validate(d.to_dict()) for d in departments]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving departments: {str(e)}")

    async def get_department_by_id(self, department_id: str, company_id: str) -> Optional[DepartmentSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(DepartmentModel).where(
                    DepartmentModel.id == department_id,
                    DepartmentModel.company_id == company_id,
                    DepartmentModel.is_active == True,
                )
            )
            department = result.scalar_one_or_none()
            return DepartmentSchema.model_validate(department.to_dict()) if department else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving department: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="department",
        details=lambda result, _a, kw: f"Département {kw['payload'].name} créé",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["payload"].model_dump(exclude_none=True)},
    )
    async def create_department(self, company_id: str, payload: DepartmentCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            department = DepartmentModel(
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
        entity_type="department",
        details=lambda _r, _a, kw: f"Département {kw['department_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["department_id"],
        extra=lambda _r, _a, kw: kw["payload"].model_dump(exclude_unset=True),
    )
    async def update_department(self, department_id: str, company_id: str, payload: DepartmentUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(DepartmentModel).where(
                    DepartmentModel.id == department_id,
                    DepartmentModel.company_id == company_id,
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
        entity_type="department",
        details=lambda _r, _a, kw: f"Département {kw['department_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["department_id"],
    )
    async def delete_department(self, department_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(DepartmentModel).where(
                    DepartmentModel.id == department_id,
                    DepartmentModel.company_id == company_id,
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