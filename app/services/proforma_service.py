from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
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

    async def create_proforma(self, proforma_data: ProformaCreate) -> Proforma:
        """Create a new proforma"""
        try:
            session = get_db_session()
            # Generate proforma number if not provided
            if not proforma_data.number:
                proforma_data.number = await self.generate_proforma_number(proforma_data.company_id)

            proforma_dict = proforma_data.model_dump()
            proforma_dict.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

            proforma = Proforma(**proforma_dict)
            session.add(proforma)
            await session.commit()
            await session.refresh(proforma)

            return proforma
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating proforma: {str(e)}")

    async def get_proforma_by_id(self, proforma_id: str) -> Optional[Proforma]:
        """Get a proforma by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id, Proforma.is_active == True)
            )
            return result.scalar_one_or_none()
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
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving proformas: {str(e)}")

    async def update_proforma(self, proforma_id: str, proforma_data: ProformaUpdate) -> Proforma:
        """Update a proforma"""
        try:
            session = get_db_session()
            # Get existing proforma
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id, Proforma.is_active == True)
            )
            proforma = result.scalar_one_or_none()

            if not proforma:
                raise HTTPException(status_code=404, detail="Proforma not found")

            # Update fields
            update_data = proforma_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            await session.execute(
                update(Proforma).where(Proforma.id == proforma_id).values(**update_data)
            )
            await session.commit()

            # Return updated proforma
            result = await session.execute(
                select(Proforma).where(Proforma.id == proforma_id)
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating proforma: {str(e)}")

    async def delete_proforma(self, proforma_id: str) -> bool:
        """Delete a proforma (soft delete)"""
        try:
            session = get_db_session()
            await session.execute(
                update(Proforma).where(Proforma.id == proforma_id).values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            return True
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
            # Get existing proforma numbers for this company
            result = await session.execute(
                select(Proforma.number).where(
                    and_(
                        Proforma.company_id == company_id,
                        Proforma.is_active == True
                    )
                )
            )
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
            return result.scalars().all()
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
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving recent proformas: {str(e)}")
