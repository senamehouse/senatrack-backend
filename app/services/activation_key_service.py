from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, desc
from fastapi import HTTPException
from app.core.database import get_sessionmaker
from app.models.activation_key_model import ActivationKey
from app.schemas.activation_key_schema import (
    ActivationKeyCreate, ActivationKeyUpdate, ActivationKeyStats
)
from datetime import datetime, timedelta
import secrets
import string

class ActivationKeyService:
    """Service for activation key-related operations"""
    
    def generate_activation_key(self) -> str:
        """Generate a unique activation key"""
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        result = ''
        for i in range(16):
            result += chars[secrets.randbelow(len(chars))]
            if i == 3 or i == 7 or i == 11:
                result += '-'
        return result
    
    async def create_activation_key(self, key_data: ActivationKeyCreate) -> ActivationKey:
        """Create a new activation key"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                # Generate unique key
                key = self.generate_activation_key()
                
                # Ensure key is unique
                while True:
                    result = await session.execute(
                        select(ActivationKey).where(ActivationKey.key == key)
                    )
                    if not result.scalar_one_or_none():
                        break
                    key = self.generate_activation_key()
                
                key_dict = key_data.model_dump()
                key_dict.update({
                    "key": key,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                activation_key = ActivationKey(**key_dict)
                session.add(activation_key)
                await session.commit()
                await session.refresh(activation_key)
                
                return activation_key
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating activation key: {str(e)}")
    
    async def get_activation_key_by_id(self, key_id: int) -> Optional[ActivationKey]:
        """Get an activation key by ID"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ActivationKey).where(ActivationKey.id == key_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving activation key: {str(e)}")
    
    async def get_activation_key_by_key(self, key: str) -> Optional[ActivationKey]:
        """Get an activation key by key string"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ActivationKey).where(ActivationKey.key == key)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving activation key: {str(e)}")
    
    async def get_all_activation_keys(self) -> List[ActivationKey]:
        """Get all activation keys"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(ActivationKey).order_by(desc(ActivationKey.created_at))
                )
                return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving activation keys: {str(e)}")
    
    async def update_activation_key(self, key_id: int, key_data: ActivationKeyUpdate) -> ActivationKey:
        """Update an activation key"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                # Get existing key
                result = await session.execute(
                    select(ActivationKey).where(ActivationKey.id == key_id)
                )
                activation_key = result.scalar_one_or_none()
                
                if not activation_key:
                    raise HTTPException(status_code=404, detail="Activation key not found")
                
                # Update fields
                update_data = key_data.model_dump(exclude_unset=True)
                update_data["updated_at"] = datetime.utcnow()
                
                await session.execute(
                    update(ActivationKey).where(ActivationKey.id == key_id).values(**update_data)
                )
                await session.commit()
                
                # Return updated key
                result = await session.execute(
                    select(ActivationKey).where(ActivationKey.id == key_id)
                )
                return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating activation key: {str(e)}")
    
    async def delete_activation_key(self, key_id: int) -> bool:
        """Delete an activation key"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                await session.execute(
                    delete(ActivationKey).where(ActivationKey.id == key_id)
                )
                await session.commit()
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting activation key: {str(e)}")
    
    async def use_activation_key(self, key: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """Use an activation key"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                # Get activation key
                result = await session.execute(
                    select(ActivationKey).where(ActivationKey.key == key)
                )
                activation_key = result.scalar_one_or_none()
                
                if not activation_key:
                    return {
                        "success": False,
                        "message": "Clé d'activation introuvable"
                    }
                
                # Check if key is active
                if activation_key.status != "active":
                    return {
                        "success": False,
                        "message": "Cette clé d'activation n'est plus valide"
                    }
                
                # Check if key has expired
                if activation_key.expires_at and activation_key.expires_at < datetime.utcnow():
                    # Mark as expired
                    await session.execute(
                        update(ActivationKey).where(ActivationKey.id == activation_key.id).values(
                            status="expired",
                            updated_at=datetime.utcnow()
                        )
                    )
                    await session.commit()
                    return {
                        "success": False,
                        "message": "Cette clé d'activation a expiré"
                    }
                
                # Check if key is already used
                if activation_key.used_by:
                    return {
                        "success": False,
                        "message": "Cette clé d'activation a déjà été utilisée"
                    }
                
                # Use the activation key
                now = datetime.utcnow()
                await session.execute(
                    update(ActivationKey).where(ActivationKey.id == activation_key.id).values(
                        status="used",
                        used_by=company_id,
                        used_at=now,
                        updated_at=now
                    )
                )
                await session.commit()
                
                return {
                    "success": True,
                    "message": f"Accès étendu de {activation_key.duration} jours avec le plan {activation_key.plan}",
                    "activation_key": {
                        "id": activation_key.id,
                        "key": activation_key.key,
                        "plan": activation_key.plan,
                        "duration": activation_key.duration,
                        "status": "used",
                        "used_by": company_id,
                        "used_at": now.isoformat()
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Une erreur est survenue lors de l'activation"
            }
    
    async def get_activation_key_stats(self) -> ActivationKeyStats:
        """Get activation key statistics"""
        try:
            async with LocalAsyncSession() as session:
                result = await session.execute(select(ActivationKey))
                keys = result.scalars().all()
                
                total = len(keys)
                active = sum(1 for k in keys if k.status == "active")
                used = sum(1 for k in keys if k.status == "used")
                expired = sum(1 for k in keys if k.status == "expired")
                cancelled = sum(1 for k in keys if k.status == "cancelled")
                
                return ActivationKeyStats(
                    total=total,
                    active=active,
                    used=used,
                    expired=expired,
                    cancelled=cancelled
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting activation key stats: {str(e)}")
