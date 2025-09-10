from typing import List, Optional
from fastapi import HTTPException
from core.firebase import db
from schemas.user import User
from utils.datetime_utils import convert_timestamps

class UserService:
    def __init__(self):
        self.db = db
        self.collection_name = 'users'
    
    async def get_all_users(self) -> List[User]:
        try:
            docs = self.db.collection(self.collection_name).stream()
            users = []
            
            for doc in docs:
                user_data = doc.to_dict()
                created_at, updated_at = convert_timestamps(user_data)
                
                user = User(
                    id=doc.id,
                    name=user_data.get('name', ''),
                    email=user_data.get('email', ''),
                    phone_number=user_data.get('phone_number', ''),
                    created_at=created_at,
                    updated_at=updated_at
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            doc = self.db.collection(self.collection_name).document(user_id).get()
            
            if not doc.exists:
                return None
            
            user_data = doc.to_dict()
            created_at, updated_at = convert_timestamps(user_data)
            
            return User(
                id=doc.id,
                name=user_data.get('name', ''),
                email=user_data.get('email', ''),
                phone_number=user_data.get('phone_number', ''),
                created_at=created_at,
                updated_at=updated_at
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")
    
    async def get_users_count(self) -> int:
        try:
            docs = self.db.collection(self.collection_name).stream()
            return sum(1 for _ in docs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")
