from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.invitation import (
    CompanyInvitation, CompanyInvitationCreate, CompanyInvitationUpdate,
    InvitationStats, InvitationResponse
)
from app.services.invitation import InvitationService

router = APIRouter(prefix="/invitations", tags=["Invitations"])
invitation_service = InvitationService()

@router.post("/", response_model=CompanyInvitation, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: CompanyInvitationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new company invitation"""
    return await invitation_service.create_invitation(invitation_data)

@router.get("/", response_model=List[CompanyInvitation])
async def get_company_invitations(
    company_id: int = Query(..., description="Company ID"),
    current_user: User = Depends(get_current_user)
):
    """Get all invitations for a company"""
    return await invitation_service.get_company_invitations(company_id)

@router.get("/pending", response_model=List[CompanyInvitation])
async def get_pending_invitations(
    email: str = Query(..., description="Email address"),
    current_user: User = Depends(get_current_user)
):
    """Get pending invitations for an email"""
    return await invitation_service.get_pending_invitations(email)

@router.get("/{invitation_id}", response_model=CompanyInvitation)
async def get_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get an invitation by ID"""
    invitation = await invitation_service.get_invitation_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation

@router.get("/token/{token}", response_model=CompanyInvitation)
async def get_invitation_by_token(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Get an invitation by token"""
    invitation = await invitation_service.get_invitation_by_token(token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation

@router.put("/{invitation_id}", response_model=CompanyInvitation)
async def update_invitation(
    invitation_id: int,
    invitation_data: CompanyInvitationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an invitation"""
    return await invitation_service.update_invitation(invitation_id, invitation_data)

@router.post("/accept/{token}", response_model=InvitationResponse)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Accept an invitation"""
    success = await invitation_service.accept_invitation(token, current_user.id)
    if success:
        invitation = await invitation_service.get_invitation_by_token(token)
        return InvitationResponse(
            success=True,
            message="Invitation accepted successfully",
            invitation=invitation
        )
    else:
        return InvitationResponse(
            success=False,
            message="Failed to accept invitation"
        )

@router.post("/decline/{token}", response_model=InvitationResponse)
async def decline_invitation(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Decline an invitation"""
    success = await invitation_service.decline_invitation(token)
    if success:
        return InvitationResponse(
            success=True,
            message="Invitation declined successfully"
        )
    else:
        return InvitationResponse(
            success=False,
            message="Failed to decline invitation"
        )

@router.delete("/{invitation_id}")
async def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Cancel an invitation"""
    success = await invitation_service.cancel_invitation(invitation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel invitation")
    return {"message": "Invitation cancelled successfully"}

@router.get("/stats/overview", response_model=InvitationStats)
async def get_invitation_stats(
    current_user: User = Depends(get_current_user)
):
    """Get invitation statistics (admin only)"""
    # TODO: Add admin check
    return await invitation_service.get_invitation_stats()
