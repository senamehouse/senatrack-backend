from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.client_model import Client as ClientModel
from app.schemas.client_schema import Client as ClientSchema, ClientCreate, ClientUpdate


class ClientService:
    async def get_all_clients(self, company_id: str) -> List[ClientSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ClientModel).where(
                    ClientModel.company_id == company_id,
                    ClientModel.is_active == True,
                )
            )
            clients = result.scalars().all()
            return [ClientSchema(**c.to_dict()) for c in clients]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving clients: {str(e)}")

    async def get_client_by_id(self, client_id: int, company_id: str) -> Optional[ClientSchema]:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ClientModel).where(
                    ClientModel.id == client_id,
                    ClientModel.company_id == company_id,
                    ClientModel.is_active == True,
                )
            )
            client = result.scalar_one_or_none()
            return ClientSchema(**client.to_dict()) if client else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving client: {str(e)}")

    async def create_client(self, company_id: str, client_data: ClientCreate) -> int:
        try:
            session = get_db_session()
            client = ClientModel(
                company_id=company_id,
                name=client_data.name,
                email=client_data.email,
                phone=client_data.phone,
                address=client_data.address,
                invoices=client_data.invoices or 0,
            )
            session.add(client)
            await session.commit()
            await session.refresh(client)
            return client.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating client: {str(e)}")

    async def update_client(self, client_id: int, company_id: str, client_data: ClientUpdate) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ClientModel).where(
                    ClientModel.id == client_id,
                    ClientModel.company_id == company_id,
                )
            )
            client = result.scalar_one_or_none()
            if not client:
                return False
            if client_data.name is not None:
                client.name = client_data.name
            if client_data.email is not None:
                client.email = client_data.email
            if client_data.phone is not None:
                client.phone = client_data.phone
            if client_data.address is not None:
                client.address = client_data.address
            if client_data.invoices is not None:
                client.invoices = client_data.invoices
            if client_data.is_active is not None:
                client.is_active = client_data.is_active
            client.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating client: {str(e)}")

    async def delete_client(self, client_id: int, company_id: str) -> bool:
        try:
            session = get_db_session()
            result = await session.execute(
                select(ClientModel).where(
                    ClientModel.id == client_id,
                    ClientModel.company_id == company_id,
                )
            )
            client = result.scalar_one_or_none()
            if not client:
                return False
            client.is_active = False
            client.updated_at = datetime.now()
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting client: {str(e)}")




