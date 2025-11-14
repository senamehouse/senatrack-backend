from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import select, and_
from app.core.database import get_db_session
from app.models.tva_rate_model import TvaRateModel
from app.schemas.tva_rate_schema import (
    TvaRateCreate,
    TvaRateUpdate,
    TvaRate,
)
from app.utils.activity_logger import audit, ActivityActor


class TvaRateService:
    """Service for TVA rate-related database operations"""
    
    async def get_all(self, company_id: str) -> List[TvaRate]:
        """Get all active TVA rates for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.company_id == company_id,
                        TvaRateModel.is_active == True
                    )
                ).order_by(TvaRateModel.is_default.desc(), TvaRateModel.created_at)
            )
            rates = result.scalars().all()
            return [TvaRate.model_validate(rate.to_dict()) for rate in rates]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving TVA rates: {str(e)}")
    
    async def get_by_id(self, rate_id: str, company_id: str) -> Optional[TvaRate]:
        """Get a TVA rate by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.id == rate_id,
                        TvaRateModel.company_id == company_id,
                        TvaRateModel.is_active == True
                    )
                )
            )
            rate = result.scalar_one_or_none()
            return TvaRate.model_validate(rate.to_dict()) if rate else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving TVA rate: {str(e)}")
    
    async def get_default(self, company_id: str) -> Optional[TvaRate]:
        """Get the default TVA rate for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.company_id == company_id,
                        TvaRateModel.is_default == True,
                        TvaRateModel.is_active == True
                    )
                )
            )
            rate = result.scalar_one_or_none()
            return TvaRate.model_validate(rate.to_dict()) if rate else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving default TVA rate: {str(e)}")
    
    @audit(
        action="CREATE",
        entity_type="tva_rate",
        details=lambda result, _a, kw: f"Taux de TVA {kw['rate_data'].name} créé",
        entity_id=lambda result, _a, _kw: result.id if isinstance(result, TvaRate) else result,
        extra=lambda _r, _a, kw: {"payload": kw["rate_data"].model_dump(exclude_none=True)},
    )
    async def create(self, rate_data: TvaRateCreate, actor: ActivityActor | None = None) -> TvaRate:
        """Create a new TVA rate"""
        try:
            session = get_db_session()
            
            # If setting as default, unset other defaults for this company
            if rate_data.is_default:
                await self._unset_defaults(rate_data.company_id, session)
            
            rate = TvaRateModel(
                company_id=rate_data.company_id,
                name=rate_data.name,
                rate=rate_data.rate,
                is_default=rate_data.is_default,
                is_active=rate_data.is_active,
            )
            session.add(rate)
            await session.commit()
            await session.refresh(rate)
            
            return TvaRate.model_validate(rate.to_dict())
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating TVA rate: {str(e)}")
    
    @audit(
        action="UPDATE",
        entity_type="tva_rate",
        details=lambda _r, _a, kw: f"Taux de TVA {kw['rate_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["rate_id"],
        extra=lambda _r, _a, kw: kw["rate_data"].model_dump(exclude_unset=True),
    )
    async def update(self, rate_id: str, rate_data: TvaRateUpdate, company_id: str, actor: ActivityActor | None = None) -> TvaRate:
        """Update a TVA rate by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.id == rate_id,
                        TvaRateModel.company_id == company_id
                    )
                )
            )
            rate = result.scalar_one_or_none()
            
            if not rate:
                raise HTTPException(status_code=404, detail="TVA rate not found")
            
            # If setting as default, unset other defaults for this company
            if rate_data.is_default is not None and rate_data.is_default:
                await self._unset_defaults(company_id, session, exclude_id=rate_id)
            
            # Update fields
            update_data = rate_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                # Convert camelCase to snake_case for model attributes
                snake_key = key
                if key == "isDefault":
                    snake_key = "is_default"
                elif key == "isActive":
                    snake_key = "is_active"
                setattr(rate, snake_key, value)
            
            await session.commit()
            await session.refresh(rate)
            
            return TvaRate.model_validate(rate.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating TVA rate: {str(e)}")
    
    @audit(
        action="DELETE",
        entity_type="tva_rate",
        details=lambda _r, _a, kw: f"Taux de TVA {kw['rate_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["rate_id"],
    )
    async def delete(self, rate_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        """Soft delete a TVA rate by setting is_active to False"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.id == rate_id,
                        TvaRateModel.company_id == company_id
                    )
                )
            )
            rate = result.scalar_one_or_none()
            
            if not rate:
                raise HTTPException(status_code=404, detail="TVA rate not found")
            
            # Check if it's the only active rate
            all_rates_result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.company_id == company_id,
                        TvaRateModel.is_active == True
                    )
                )
            )
            all_rates = all_rates_result.scalars().all()
            
            if len(all_rates) == 1 and all_rates[0].id == rate_id:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the only active TVA rate. Please create another rate first."
                )
            
            # Soft delete
            rate.is_active = False
            await session.commit()
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting TVA rate: {str(e)}")
    
    @audit(
        action="UPDATE",
        entity_type="tva_rate",
        details=lambda _r, _a, kw: f"Taux de TVA {kw['rate_id']} défini comme défaut",
        entity_id=lambda _r, _a, kw: kw["rate_id"],
    )
    async def set_default(self, rate_id: str, company_id: str, actor: ActivityActor | None = None) -> TvaRate:
        """Set a TVA rate as the default for a company"""
        try:
            session = get_db_session()
            
            # Unset other defaults
            await self._unset_defaults(company_id, session, exclude_id=rate_id)
            
            # Set this rate as default
            result = await session.execute(
                select(TvaRateModel).where(
                    and_(
                        TvaRateModel.id == rate_id,
                        TvaRateModel.company_id == company_id
                    )
                )
            )
            rate = result.scalar_one_or_none()
            
            if not rate:
                raise HTTPException(status_code=404, detail="TVA rate not found")
            
            rate.is_default = True
            await session.commit()
            await session.refresh(rate)
            
            return TvaRate.model_validate(rate.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error setting default TVA rate: {str(e)}")
    
    async def _unset_defaults(self, company_id: str, session, exclude_id: Optional[str] = None):
        """Helper method to unset all default flags for a company"""
        query = select(TvaRateModel).where(
            and_(
                TvaRateModel.company_id == company_id,
                TvaRateModel.is_default == True
            )
        )
        if exclude_id:
            query = query.where(TvaRateModel.id != exclude_id)
        
        result = await session.execute(query)
        default_rates = result.scalars().all()
        
        for rate in default_rates:
            rate.is_default = False

