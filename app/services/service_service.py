from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_sessionmaker
from app.models.service_model import Service as ServiceModel
from app.schemas.service_schema import Service as ServiceSchema, ServiceCreate, ServiceUpdate


class ServiceService:
    async def get_all_services(self, company_id: str) -> List[ServiceSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def get_service_by_id(self, service_id: int, company_id: str) -> Optional[ServiceSchema]:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def create_service(self, company_id: str, service_data: ServiceCreate) -> int:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def update_service(self, service_id: int, company_id: str, service_data: ServiceUpdate) -> bool:
        try:
            Session = get_sessionmaker()
            async with Session() as session:
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

    async def delete_service(self, service_id: int, company_id: str) -> bool:
        try:
            async with LocalAsyncSession() as session:
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




