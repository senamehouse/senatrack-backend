from typing import List, Optional
from fastapi import HTTPException
from app.core.database import get_database
from app.schemas.user import User

class UserService:
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """Get async database instance"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def get_all_users(self) -> List[User]:
        try:
            db = await self._get_db()
            return await db.get_all_users()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            db = await self._get_db()
            return await db.get_user_by_id(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")
    
    async def create_user(self, user_data: dict) -> int:
        try:
            db = await self._get_db()
            return await db.create_user(user_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    
    async def update_user(self, user_id: int, user_data: dict) -> bool:
        try:
            db = await self._get_db()
            return await db.update_user(user_id, user_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")
    
    async def delete_user(self, user_id: int) -> bool:
        try:
            db = await self._get_db()
            return await db.delete_user(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    async def get_users_count(self) -> int:
        try:
            db = await self._get_db()
            return await db.get_users_count()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")
