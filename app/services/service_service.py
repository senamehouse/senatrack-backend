from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.service_model import Service as ServiceModel
from app.schemas.service_schema import Service as ServiceSchema, ServiceCreate, ServiceUpdate
from app.utils.activity_logger import audit, ActivityActor


class ServiceService:
    async def get_all_services(self, company_id: str) -> List[ServiceSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ServiceModel).where(
                    ServiceModel.company_id == company_id,
                    ServiceModel.is_active == True,
                )
            )
            services = result.scalars().all()
            return [ServiceSchema(**s.to_dict()) for s in services]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving services: {str(e)}")

    async def get_service_by_id(self, service_id: str, company_id: str) -> Optional[ServiceSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ServiceModel).where(
                    ServiceModel.id == service_id,
                    ServiceModel.company_id == company_id,
                    ServiceModel.is_active == True,
                )
            )
            service = result.scalar_one_or_none()
            return ServiceSchema(**service.to_dict()) if service else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving service: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="service",
        details=lambda result, _a, kw: f"Prestation {kw['service_data'].name} créée",
        entity_id=lambda result, _a, _kw: result,
        extra=lambda _r, _a, kw: {"payload": kw["service_data"].model_dump(exclude_none=True)},
    )
    async def create_service(self, company_id: str, service_data: ServiceCreate, actor: ActivityActor | None = None) -> str:
        try:
            session = get_db_session()
            service = ServiceModel(
                company_id=company_id,
                name=service_data.name,
                unit=service_data.unit,
                price=service_data.price,
                description=service_data.description,
            )
            session.add(service)
            await session.commit()
            await session.refresh(service)
            return service.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating service: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="service",
        details=lambda _r, _a, kw: f"Prestation {kw['service_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["service_id"],
        extra=lambda _r, _a, kw: kw["service_data"].model_dump(exclude_unset=True),
    )
    async def update_service(self, service_id: str, company_id: str, service_data: ServiceUpdate, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ServiceModel).where(
                    ServiceModel.id == service_id,
                    ServiceModel.company_id == company_id,
                )
            )
            service = result.scalar_one_or_none()
            if not service:
                return False
            if service_data.name is not None:
                service.name = service_data.name
            if service_data.unit is not None:
                service.unit = service_data.unit
            if service_data.price is not None:
                service.price = service_data.price
            if service_data.description is not None:
                service.description = service_data.description
            if service_data.is_active is not None:
                service.is_active = service_data.is_active
            service.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating service: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="service",
        details=lambda _r, _a, kw: f"Prestation {kw['service_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["service_id"],
    )
    async def delete_service(self, service_id: str, company_id: str, actor: ActivityActor | None = None) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ServiceModel).where(
                    ServiceModel.id == service_id,
                    ServiceModel.company_id == company_id,
                )
            )
            service = result.scalar_one_or_none()
            if not service:
                return False
            service.is_active = False
            service.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting service: {str(e)}")




