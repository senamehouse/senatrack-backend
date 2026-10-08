from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_current_user, ensure_company_access, require_admin_access
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.schemas.invitation_schema import (
    CompanyInvitation, CompanyInvitationCreate, CompanyInvitationUpdate,
    InvitationStats, InvitationResponse, InvitationCancelResponse
)
from app.services.invitation_service import InvitationService
from app.services.company_service import CompanyService
from app.models.company_model import Company as CompanyModel
from app.utils.activity_logger import ActivityActor

router = APIRouter(prefix="/invitations", tags=["Invitations"])
invitation_service = InvitationService()
company_service = CompanyService()


async def require_invitation_manager(company_id: str, current_user: User, session: AsyncSession) -> CompanyModel:
    await ensure_company_access(company_id, current_user, session)
    company = await session.get(CompanyModel, company_id)
    if company.owner_id == current_user.id or "admin.access" in current_user.platform_permissions:
        return company
    if await company_service.check_company_permission(current_user.id, company_id, "company.users.manage"):
        return company
    raise HTTPException(status_code=403, detail="Company user management required")


async def require_invitation_reader(invitation: CompanyInvitation, current_user: User, session: AsyncSession) -> None:
    if invitation.email.casefold() == current_user.email.casefold():
        return
    await require_invitation_manager(invitation.company_id, current_user, session)

@router.post("/", response_model=CompanyInvitation, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: CompanyInvitationCreate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new company invitation"""
    await require_invitation_manager(invitation_data.company_id, current_user, session)
    return await invitation_service.create_invitation(
        invitation_data=invitation_data.model_copy(update={"invited_by": current_user.id, "email": invitation_data.email.lower()}),
        actor=ActivityActor.from_user(current_user),
    )

@router.get("/", response_model=List[CompanyInvitation])
async def get_company_invitations(
    company_id: str = Query(..., description="Company ID"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invitations for a company"""
    await require_invitation_manager(company_id, current_user, session)
    return await invitation_service.get_company_invitations(company_id)

@router.get("/pending", response_model=List[CompanyInvitation])
async def get_pending_invitations(
    email: str = Query(..., description="Email address"),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending invitations for an email"""
    if email.casefold() != current_user.email.casefold():
        raise HTTPException(status_code=403, detail="Email access denied")
    return await invitation_service.get_pending_invitations(current_user.email)

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
    await require_invitation_reader(invitation, current_user, session)
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
    await require_invitation_reader(invitation, current_user, session)
    return invitation

@router.put("/{invitation_id}", response_model=CompanyInvitation)
async def update_invitation(
    invitation_id: str,
    invitation_data: CompanyInvitationUpdate,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update an invitation"""
    invitation = await invitation_service.get_invitation_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    await require_invitation_manager(invitation.company_id, current_user, session)
    if invitation_data.status not in (None, "pending"):
        raise HTTPException(status_code=400, detail="Use the acceptance flow to change invitation status")
    return await invitation_service.update_invitation(invitation_id=invitation_id, invitation_data=invitation_data, actor=ActivityActor.from_user(current_user))

@router.post("/accept/{token}", response_model=InvitationResponse)
async def accept_invitation(
    token: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Accept an invitation"""
    return await invitation_service.accept_invitation(token=token, user_id=current_user.id, user_email=current_user.email, actor=ActivityActor.from_user(current_user))

@router.post("/decline/{token}", response_model=InvitationResponse)
async def decline_invitation(
    token: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Decline an invitation"""
    return await invitation_service.decline_invitation(token=token, user_email=current_user.email, actor=ActivityActor.from_user(current_user))

@router.delete("/{invitation_id}", response_model=InvitationCancelResponse)
async def cancel_invitation(
    invitation_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an invitation"""
    invitation = await invitation_service.get_invitation_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    await require_invitation_manager(invitation.company_id, current_user, session)
    return await invitation_service.cancel_invitation(invitation_id=invitation_id, actor=ActivityActor.from_user(current_user))

@router.get("/stats/overview", response_model=InvitationStats)
async def get_invitation_stats(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access)
):
    """Get invitation statistics (admin only)"""
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
    company = await require_invitation_manager(invitation.company_id, current_user, session)
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending invitations can be emailed")
    
    # Send email
    result = await invitation_service.send_invitation_email(
        invitation=invitation,
        company_name=company.name,
        invited_by_name=current_user.name,
        app_url=None,
    )
    
    return result
