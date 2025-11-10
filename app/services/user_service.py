import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.models.user_model import User as UserModel
from app.models.sync_model import SyncLog
from app.schemas.user_schema import User, UserInternal, UserUpdate

class UserService:
    """Service for user-related database operations"""
    
    async def get_all_users(self) -> List[User]:
        """Get all active users from the database"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.is_active == True)
            )
            users = result.scalars().all()
            return [User(**user.to_dict()) for user in users]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id, UserModel.is_active == True)
            )
            user = result.scalar_one_or_none()
            return User(**user.to_dict()) if user else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[UserInternal]:
        """Get a user by email (with hashed password for authentication)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.email == email, UserModel.is_active == True)
            )
            user = result.scalar_one_or_none()
            return UserInternal(**user.to_dict(include_password=True)) if user else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user by email: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user and return the ID"""
        try:
            session = get_db_session()
            user = UserModel(
                name=user_data['name'],
                email=user_data['email'],
                phone_number=user_data.get('phone_number'),
                hashed_password=user_data['hashed_password']
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Log sync operation
            sync_log = SyncLog(
                operation='CREATE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return user.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update a user by ID and return the updated user"""
        try:
            session = get_db_session()
            # Get existing user
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Convert schema to dict, excluding unset fields
            update_dict = user_data.model_dump(exclude_unset=True)
            
            # Update fields
            if 'name' in update_dict:
                user.name = update_dict['name']
            if 'email' in update_dict:
                user.email = update_dict['email']
            if 'phone_number' in update_dict:
                user.phone_number = update_dict['phone_number']
            if 'hashed_password' in update_dict:
                user.hashed_password = update_dict['hashed_password']
            if 'current_company_id' in update_dict:
                user.current_company_id = update_dict['current_company_id']
            
            user.updated_at = datetime.now()
            await session.commit()
            await session.refresh(user)
            
            # Log sync operation
            sync_log = SyncLog(
                operation='UPDATE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return User(**user.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID (soft delete)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Soft delete
            user.is_active = False
            user.updated_at = datetime.now()
            await session.commit()
            
            # Log sync operation
            sync_log = SyncLog(
                operation='DELETE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    async def get_users_count(self) -> int:
        """Get the count of active users"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(func.count(UserModel.id)).where(UserModel.is_active == True)
            )
            return result.scalar()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")
    
    async def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.last_login = datetime.now()
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating last login: {str(e)}")
    
    async def export_data(self) -> List[Dict[str, Any]]:
        """Export all data for synchronization"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.is_active == True)
            )
            users = result.scalars().all()
            return [user.to_dict() for user in users]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")
    
    async def sync_data(self, data: List[Dict[str, Any]]) -> bool:
        """Sync data from external source"""
        try:
            session = get_db_session()
            for item in data:
                # Check if user exists
                result = await session.execute(
                    select(UserModel).where(UserModel.email == item['email'])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    existing_user.name = item['name']
                    existing_user.phone_number = item.get('phone_number')
                    existing_user.updated_at = datetime.now()
                else:
                    # Create new user
                    new_user = UserModel(
                        name=item['name'],
                        email=item['email'],
                        phone_number=item.get('phone_number')
                    )
                    session.add(new_user)
            
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error syncing data: {str(e)}")
