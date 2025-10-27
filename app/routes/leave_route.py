from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.dependencies import get_current_user, get_company_id
from app.schemas.user_schema import User
from app.schemas.leave_schema import LeaveRequest, LeaveRequestCreate, LeaveRequestUpdate
from app.services.leave_service import LeaveService


router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])
svc = LeaveService()


@router.get("/", response_model=List[LeaveRequest])
async def get_leaves(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    return await svc.get_all(company_id)


@router.get("/{leave_id}", response_model=LeaveRequest)
async def get_leave(leave_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    row = await svc.get_by_id(leave_id, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return row


@router.post("/", response_model=dict)
async def create_leave(payload: LeaveRequestCreate, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    leave_id = await svc.create(company_id, payload)
    return {"message": "Leave request created", "leave_id": leave_id}


@router.put("/{leave_id}", response_model=dict)
async def update_leave(leave_id: int, payload: LeaveRequestUpdate, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.update(leave_id, company_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request updated"}


@router.delete("/{leave_id}", response_model=dict)
async def delete_leave(leave_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.delete(leave_id, company_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request deleted"}

@router.get("/stats", response_model=dict)
async def get_leave_stats(current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    return await svc.get_stats(company_id)


@router.post("/{leave_id}/approve", response_model=dict)
async def approve_leave(leave_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.approve(leave_id, company_id, approved_by=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request approved"}


@router.post("/{leave_id}/reject", response_model=dict)
async def reject_leave(leave_id: int, current_user: User = Depends(get_current_user), company_id: str = Depends(get_company_id)):
    ok = await svc.reject(leave_id, company_id, approved_by=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return {"message": "Leave request rejected"}