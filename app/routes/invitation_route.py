from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.invitation_schema import (
    CompanyInvitation, CompanyInvitationCreate, CompanyInvitationUpdate,
    InvitationStats, InvitationResponse, InvitationCancelResponse
)
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/invitations", tags=["Invitations"])
invitation_service = InvitationService()

@router.post("/", response_model=CompanyInvitation, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: CompanyInvitationCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new company invitation"""
    return await invitation_service.create_invitation(invitation_data)

@router.get("/", response_model=List[CompanyInvitation])
async def get_company_invitations(
    company_id: str = Query(..., description="Company ID"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invitations for a company"""
    return await invitation_service.get_company_invitations(company_id)

@router.get("/pending", response_model=List[CompanyInvitation])
async def get_pending_invitations(
    email: str = Query(..., description="Email address"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending invitations for an email"""
    return await invitation_service.get_pending_invitations(email)

@router.get("/{invitation_id}", response_model=CompanyInvitation)
async def get_invitation(
    invitation_id: str,
    session: AsyncSession = Depends(get_async_db),
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
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get an invitation by token"""
    invitation = await invitation_service.get_invitation_by_token(token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation

@router.put("/{invitation_id}", response_model=CompanyInvitation)
async def update_invitation(
    invitation_id: str,
    invitation_data: CompanyInvitationUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update an invitation"""
    return await invitation_service.update_invitation(invitation_id, invitation_data)

@router.post("/accept/{token}", response_model=InvitationResponse)
async def accept_invitation(
    token: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Accept an invitation"""
    return await invitation_service.accept_invitation(token, current_user.id)

@router.post("/decline/{token}", response_model=InvitationResponse)
async def decline_invitation(
    token: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Decline an invitation"""
    return await invitation_service.decline_invitation(token)

@router.delete("/{invitation_id}", response_model=InvitationCancelResponse)
async def cancel_invitation(
    invitation_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an invitation"""
    return await invitation_service.cancel_invitation(invitation_id)

@router.get("/stats/overview", response_model=InvitationStats)
async def get_invitation_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get invitation statistics (admin only)"""
    # TODO: Add admin check
    return await invitation_service.get_invitation_stats()

class SendInvitationEmailRequest(BaseModel):
    invitation_id: str
    company_name: str
    invited_by_name: str
    app_url: Optional[str] = None

@router.post("/send-email", status_code=status.HTTP_200_OK)
async def send_invitation_email(
    request: SendInvitationEmailRequest,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Send invitation email"""
    # Get invitation by ID
    invitation = await invitation_service.get_invitation_by_id(request.invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Send email
    result = await invitation_service.send_invitation_email(
        invitation=invitation,
        company_name=request.company_name,
        invited_by_name=request.invited_by_name,
        app_url=request.app_url
    )
    
    return result
