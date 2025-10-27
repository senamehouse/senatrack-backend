from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_sessionmaker
from app.models.employee_model import Employee as EmployeeModel
from app.schemas.employee_schema import Employee as EmployeeSchema, EmployeeCreate, EmployeeUpdate


class EmployeeService:
    async def get_all(self, company_id: str) -> List[EmployeeSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(EmployeeModel).where(
                        EmployeeModel.company_id == company_id,
                        EmployeeModel.is_active == True,
                    )
                )
                rows = result.scalars().all()
                return [EmployeeSchema(**r.to_dict()) for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving employees: {str(e)}")

    async def get_by_id(self, employee_id: int, company_id: str) -> Optional[EmployeeSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(EmployeeModel).where(
                        EmployeeModel.id == employee_id,
                        EmployeeModel.company_id == company_id,
                    )
                )
                row = result.scalar_one_or_none()
                return EmployeeSchema(**row.to_dict()) if row else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving employee: {str(e)}")

    async def create(self, company_id: str, payload: EmployeeCreate) -> int:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def update(self, employee_id: int, company_id: str, payload: EmployeeUpdate) -> bool:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def delete(self, employee_id: int, company_id: str) -> bool:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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
            Session = get_sessionmaker()
            async with Session() as session:
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
            Session = get_sessionmaker()
            async with Session() as session:
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