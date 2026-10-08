from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.core.database import get_db_session
from app.models.proforma_model import Proforma
from app.schemas.proforma_schema import (
    ProformaCreate, ProformaUpdate, ProformaStats, ProformaFilter
)
from datetime import datetime, timedelta
import re

class ProformaService:
    """Service for proforma-related operations"""

    async def create_proforma(self, proforma_data: ProformaCreate, company_id: str, created_by: str) -> Proforma:
        """Create a new proforma"""
        session = get_db_session()
        auto_number = not proforma_data.number or not proforma_data.number.strip()
        try:
            for attempt in range(3):
                number = await self.generate_proforma_number(company_id) if auto_number else proforma_data.number
                proforma_dict = proforma_data.model_dump(exclude={"objet"})
                proforma_dict["number"] = number
                proforma_dict["client"] = proforma_data.client.model_dump(by_alias=True)
                proforma_dict["items"] = [item.model_dump(by_alias=True) for item in proforma_data.items]
                proforma_dict.update({"company_id": company_id, "created_by": created_by,
                                      "notes": proforma_data.objet, "created_at": datetime.utcnow(),
                                      "updated_at": datetime.utcnow()})

                proforma = Proforma(**proforma_dict)
                session.add(proforma)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    existing_number = await session.scalar(
                        select(Proforma.id).where(Proforma.number == number)
                    )
                    if existing_number:
                        if auto_number and attempt < 2:
                            continue
                        raise HTTPException(status_code=409, detail="Ce numéro de devis existe déjà.")
                    raise

                return proforma.to_dict()
            raise HTTPException(status_code=409, detail="Impossible d'attribuer un numéro de devis unique. Réessayez.")
        except HTTPException:
            raise
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Impossible d'enregistrer le devis. Réessayez.")

    async def get_proforma_by_id(self, proforma_id: str, company_id: str) -> Optional[Proforma]:
        """Get a proforma by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id, Proforma.company_id == company_id, Proforma.is_active == True)
            )
            proforma = result.scalar_one_or_none()
            return proforma.to_dict() if proforma else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving proforma: {str(e)}")

    async def get_company_proformas(self, company_id: str, filters: Optional[ProformaFilter] = None) -> List[Proforma]:
        """Get all proformas for a company"""
        try:
            session = get_db_session()
            query = select(Proforma).where(
                and_(
                    Proforma.company_id == company_id,
                    Proforma.is_active == True
                )
            ).order_by(desc(Proforma.date))

            # Apply filters
            if filters:
                if filters.client_name:
                    # Note: This is a simplified filter. In a real app, you'd want to store client data separately
                    query = query.where(Proforma.client.contains({"name": filters.client_name}))

                if filters.status:
                    query = query.where(Proforma.status == filters.status)

                if filters.date_from:
                    query = query.where(Proforma.date >= filters.date_from)

                if filters.date_to:
                    query = query.where(Proforma.date <= filters.date_to)

                if filters.limit:
                    query = query.limit(filters.limit)

            result = await session.execute(query)
            return [proforma.to_dict() for proforma in result.scalars().all()]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving proformas: {str(e)}")

    async def update_proforma(self, proforma_id: str, company_id: str, proforma_data: ProformaUpdate) -> Proforma:
        """Update a proforma"""
        try:
            session = get_db_session()
            # Get existing proforma
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id, Proforma.company_id == company_id, Proforma.is_active == True)
            )
            proforma = result.scalar_one_or_none()

            if not proforma:
                raise HTTPException(status_code=404, detail="Proforma not found")

            # Update fields
            update_data = proforma_data.model_dump(exclude_unset=True)
            if "objet" in update_data:
                update_data["notes"] = update_data.pop("objet")
            if "client" in update_data and proforma_data.client:
                update_data["client"] = proforma_data.client.model_dump(by_alias=True)
            if "items" in update_data and proforma_data.items is not None:
                update_data["items"] = [item.model_dump(by_alias=True) for item in proforma_data.items]
            update_data["updated_at"] = datetime.utcnow()

            await session.execute(
                update(Proforma).where(Proforma.id == proforma_id).values(**update_data)
            )
            await session.commit()

            # Return updated proforma
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id)
            )
            return result.scalar_one().to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating proforma: {str(e)}")

    async def delete_proforma(self, proforma_id: str, company_id: str) -> bool:
        """Delete a proforma (soft delete)"""
        try:
            session = get_db_session()
            result = await session.execute(
                update(Proforma).where(Proforma.id == proforma_id, Proforma.company_id == company_id).values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting proforma: {str(e)}")

    async def get_proforma_stats(self, company_id: str) -> ProformaStats:
        """Get proforma statistics for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(Proforma).where(
                    and_(
                        Proforma.company_id == company_id,
                        Proforma.is_active == True
                    )
                )
            )
            proformas = result.scalars().all()

            total = len(proformas)
            total_value = sum(p.total for p in proformas)
            average_amount = total_value / total if total > 0 else 0

            # Recent count (24h)
            day_ago = datetime.utcnow() - timedelta(days=1)
            recent_count = sum(1 for p in proformas if p.created_at >= day_ago)

            # By status
            by_status = {}
            for proforma in proformas:
                status = proforma.status
                by_status[status] = by_status.get(status, 0) + 1

            return ProformaStats(
                total=total,
                total_value=total_value,
                average_amount=average_amount,
                recent_count=recent_count,
                by_status=by_status
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting proforma stats: {str(e)}")

    async def generate_proforma_number(self, company_id: str) -> str:
        """Generate a unique proforma number"""
        try:
            session = get_db_session()
            # The database enforces globally unique numbers, including across companies.
            result = await session.execute(select(Proforma.number))
            existing_numbers = {row[0] for row in result.fetchall()}

            # Generate new number
            year = datetime.utcnow().year
            counter = 1
            proforma_number = f"PRO-{year}-{counter:04d}"

            while proforma_number in existing_numbers:
                counter += 1
                proforma_number = f"PRO-{year}-{counter:04d}"

            return proforma_number
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating proforma number: {str(e)}")

    async def get_proformas_by_client(self, company_id: str, client_name: str) -> List[Proforma]:
        """Get proformas by client name"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(Proforma).where(
                    and_(
                        Proforma.company_id == company_id,
                        Proforma.is_active == True,
                        Proforma.client.contains({"name": client_name})
                    )
                ).order_by(desc(Proforma.date))
            )
            return [proforma.to_dict() for proforma in result.scalars().all()]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving proformas by client: {str(e)}")

    async def get_recent_proformas(self, company_id: str, limit: int = 10) -> List[Proforma]:
        """Get recent proformas for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(Proforma).where(
                    and_(
                        Proforma.company_id == company_id,
                        Proforma.is_active == True
                    )
                ).order_by(desc(Proforma.date)).limit(limit)
            )
            return [proforma.to_dict() for proforma in result.scalars().all()]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving recent proformas: {str(e)}")
