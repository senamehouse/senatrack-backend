from fastapi import APIRouter, HTTPException
from typing import List
from schemas.user import User
from services.user import UserService

router = APIRouter()
user_service = UserService()

@router.get("/users", response_model=List[User])
async def get_all_users():
    return await user_service.get_all_users()

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/count")
async def get_users_count():
    count = await user_service.get_users_count()
    return {"count": count}
