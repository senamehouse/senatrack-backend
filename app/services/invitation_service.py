from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, desc, func
from fastapi import HTTPException
from app.core.database import get_db_session
from app.core.settings import settings
from app.models.invitation_model import CompanyInvitation
from app.models.company_model import Company, CompanyMember, UserCompanyRoleModel, UserCompanyRoleAssignmentModel
from app.models.user_model import User
from app.schemas.invitation_schema import (
    CompanyInvitationCreate, CompanyInvitationUpdate, CompanyInvitation as CompanyInvitationSchema,
    InvitationStats, InvitationResponse, InvitationCancelResponse
)
from datetime import datetime, timedelta
import secrets
import string
import os
from app.services.email_service import email_service
from app.utils.email_templates import get_app_config
from app.utils.activity_logger import audit, ActivityActor
from app.schemas.company_role_schema import DEFAULT_COMPANY_ROLES

class InvitationService:
    """Service for company invitation-related operations"""
    
    def generate_invitation_token(self) -> str:
        """Generate a unique invitation token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    @audit(
        action="CREATE",
        entity_type="invitation",
        details=lambda result, _a, kw: f"Invitation envoyée à {kw['invitation_data'].email} pour l’entreprise {kw['invitation_data'].company_id}",
        entity_id=lambda result, _a, _kw: result.id if result else None,
        extra=lambda _r, _a, kw: {"payload": kw["invitation_data"].model_dump(exclude_none=True)},
    )
    async def create_invitation(self, invitation_data: CompanyInvitationCreate, actor: ActivityActor | None = None) -> CompanyInvitation:
        """Create a new company invitation"""
        try:
            session = get_db_session()
            # Check if company exists
            result = await session.execute(
                select(Company).where(Company.id == invitation_data.company_id, Company.is_active == True)
            )
            company = result.scalar_one_or_none()
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Check if invitation already exists for this email and company
            result = await session.execute(
                select(CompanyInvitation).where(
                    and_(
                        CompanyInvitation.company_id == invitation_data.company_id,
                        CompanyInvitation.email == invitation_data.email,
                        CompanyInvitation.status == "pending"
                    )
                )
            )
            existing_invitation = result.scalar_one_or_none()
            if existing_invitation:
                raise HTTPException(status_code=400, detail="Invitation already exists for this email")
            
            # Create invitation
            invitation_dict = invitation_data.model_dump()
            invitation_dict.update({
                "token": self.generate_invitation_token(),
                "invited_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            invitation = CompanyInvitation(**invitation_dict)
            session.add(invitation)
            await session.commit()
            await session.refresh(invitation)
            
            return invitation
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating invitation: {str(e)}")
    
    async def get_invitation_by_id(self, invitation_id: str) -> Optional[CompanyInvitation]:
        """Get an invitation by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving invitation: {str(e)}")
    
    async def get_invitation_by_token(self, token: str) -> Optional[CompanyInvitation]:
        """Get an invitation by token"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.token == token)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving invitation: {str(e)}")
    
    async def get_company_invitations(self, company_id: str) -> List[CompanyInvitation]:
        """Get all invitations for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyInvitation).where(
                    CompanyInvitation.company_id == company_id
                ).order_by(desc(CompanyInvitation.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company invitations: {str(e)}")
    
    async def get_pending_invitations(self, email: str) -> List[CompanyInvitation]:
        """Get pending invitations for an email"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyInvitation).where(
                    and_(
                        func.lower(CompanyInvitation.email) == email.lower(),
                        CompanyInvitation.status == "pending",
                        CompanyInvitation.expires_at > datetime.utcnow()
                    )
                ).order_by(desc(CompanyInvitation.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving pending invitations: {str(e)}")
    
    @audit(
        action="UPDATE",
        entity_type="invitation",
        details=lambda _r, _a, kw: f"Invitation {kw['invitation_id']} mise à jour",
        entity_id=lambda _r, _a, kw: kw["invitation_id"],
        extra=lambda _r, _a, kw: kw["invitation_data"].model_dump(exclude_unset=True),
    )
    async def update_invitation(self, invitation_id: str, invitation_data: CompanyInvitationUpdate, actor: ActivityActor | None = None) -> CompanyInvitation:
        """Update an invitation"""
        try:
            session = get_db_session()
            # Get existing invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                raise HTTPException(status_code=404, detail="Invitation not found")
            
            # Update fields
            update_data = invitation_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Set timestamps based on status
            if update_data.get("status") == "accepted":
                update_data["accepted_at"] = datetime.utcnow()
            elif update_data.get("status") == "declined":
                update_data["declined_at"] = datetime.utcnow()
            
            await session.execute(
                update(CompanyInvitation).where(CompanyInvitation.id == invitation_id).values(**update_data)
            )
            await session.commit()
            
            # Return updated invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating invitation: {str(e)}")
    
    @audit(
        action="ACCEPT",
        entity_type="invitation",
        details=lambda result, _a, kw: f"Invitation acceptée par l’utilisateur {kw['user_id']}",
        entity_id=lambda result, _a, _kw: result.invitation.id if (hasattr(result, 'invitation') and result.invitation) else None,
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "token": kw["token"]},
    )
    async def accept_invitation(self, token: str, user_id: str, user_email: str, actor: ActivityActor | None = None) -> InvitationResponse:
        """Accept an invitation and return response"""
        try:
            session = get_db_session()
            # Get invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.token == token)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                raise HTTPException(status_code=404, detail="Invitation not found")
            if invitation.email.casefold() != user_email.casefold():
                raise HTTPException(status_code=403, detail="Invitation belongs to another email")
            
            if invitation.status != "pending":
                raise HTTPException(status_code=400, detail="Invitation is not pending")
            
            if invitation.expires_at < datetime.utcnow():
                # Mark as expired
                await session.execute(
                    update(CompanyInvitation).where(CompanyInvitation.id == invitation.id).values(
                        status="expired",
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                raise HTTPException(status_code=400, detail="Invitation has expired")
            
            now = datetime.utcnow()
            member = await session.scalar(select(CompanyMember).where(
                CompanyMember.company_id == invitation.company_id,
                CompanyMember.user_id == user_id,
            ))
            if member is None:
                member = CompanyMember(
                    company_id=invitation.company_id, user_id=user_id,
                    invited_by=invitation.invited_by, invited_at=invitation.invited_at,
                    joined_at=now, is_active=True,
                )
                session.add(member)
            else:
                member.is_active = True
                member.joined_at = now

            preset = DEFAULT_COMPANY_ROLES.get(invitation.role)
            if preset is None:
                raise HTTPException(status_code=400, detail="Invalid invitation role")
            role = await session.scalar(select(UserCompanyRoleModel).where(
                UserCompanyRoleModel.company_id == invitation.company_id,
                UserCompanyRoleModel.name == preset["name"],
            ))
            if role is None:
                role = UserCompanyRoleModel(
                    company_id=invitation.company_id,
                    name=preset["name"], description=preset["description"],
                    permissions=preset["permissions"], is_preset=True, is_system=True,
                )
                session.add(role)
                await session.flush()
            existing_assignment = await session.scalar(select(UserCompanyRoleAssignmentModel).where(
                UserCompanyRoleAssignmentModel.company_id == invitation.company_id,
                UserCompanyRoleAssignmentModel.user_id == user_id,
                UserCompanyRoleAssignmentModel.role_id == role.id,
            ))
            if existing_assignment is None:
                session.add(UserCompanyRoleAssignmentModel(
                    company_id=invitation.company_id, user_id=user_id,
                    role_id=role.id, assigned_by=invitation.invited_by,
                ))
            user = await session.get(User, user_id)
            if user is not None:
                user.current_company_id = invitation.company_id
            invitation.status = "accepted"
            invitation.accepted_at = now
            invitation.accepted_by = user_id
            invitation.updated_at = now
            await session.commit()
            
            # Get updated invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.token == token)
            )
            updated_invitation = result.scalar_one_or_none()
            
            return InvitationResponse(
                success=True,
                message="Invitation accepted successfully",
                invitation=CompanyInvitationSchema.model_validate(updated_invitation.to_dict())
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error accepting invitation: {str(e)}")
    
    @audit(
        action="DECLINE",
        entity_type="invitation",
        details=lambda _r, _a, kw: f"Invitation refusée (token {kw['token']})",
        entity_id=lambda _r, _a, kw: kw["token"],
    )
    async def decline_invitation(self, token: str, user_email: str, actor: ActivityActor | None = None) -> InvitationResponse:
        """Decline an invitation and return response"""
        try:
            session = get_db_session()
            # Get invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.token == token)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                raise HTTPException(status_code=404, detail="Invitation not found")
            if invitation.email.casefold() != user_email.casefold():
                raise HTTPException(status_code=403, detail="Invitation belongs to another email")
            
            if invitation.status != "pending":
                raise HTTPException(status_code=400, detail="Invitation is not pending")
            
            # Update invitation status
            await session.execute(
                update(CompanyInvitation).where(CompanyInvitation.id == invitation.id).values(
                    status="declined",
                    declined_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            
            return InvitationResponse(
                success=True,
                message="Invitation declined successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error declining invitation: {str(e)}")
    
    @audit(
        action="DELETE",
        entity_type="invitation",
        details=lambda _r, _a, kw: f"Invitation {kw['invitation_id']} annulée",
        entity_id=lambda _r, _a, kw: kw["invitation_id"],
    )
    async def cancel_invitation(self, invitation_id: str, actor: ActivityActor | None = None) -> InvitationCancelResponse:
        """Cancel an invitation and return response"""
        try:
            session = get_db_session()
            # Check if invitation exists
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                raise HTTPException(status_code=404, detail="Invitation not found")
            
            await session.execute(
                delete(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
            )
            await session.commit()
            
            return InvitationCancelResponse(message="Invitation cancelled successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cancelling invitation: {str(e)}")
    
    async def get_invitation_stats(self) -> InvitationStats:
        """Get invitation statistics"""
        try:
            session = get_db_session()
            result = await session.execute(select(CompanyInvitation))
            invitations = result.scalars().all()
            
            total = len(invitations)
            pending = sum(1 for i in invitations if i.status == "pending")
            accepted = sum(1 for i in invitations if i.status == "accepted")
            declined = sum(1 for i in invitations if i.status == "declined")
            expired = sum(1 for i in invitations if i.status == "expired")
            
            return InvitationStats(
                total=total,
                pending=pending,
                accepted=accepted,
                declined=declined,
                expired=expired
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting invitation stats: {str(e)}")
    
    async def send_invitation_email(
        self, 
        invitation: CompanyInvitation, 
        company_name: str, 
        invited_by_name: str,
        app_url: str = None
    ) -> Dict[str, Any]:
        """Send invitation email via email service"""
        try:
            # Get app config
            config = get_app_config()
            
            # Get app URL from parameter or config
            if not app_url:
                app_url = config["app_url"]
            
            invitation_url = f"{app_url.rstrip('/')}/mon-espace/rejoindre?token={invitation.token}"
            
            # Role labels mapping
            role_labels = {
                "admin": "Administrateur",
                "manager": "Gestionnaire",
                "operator": "Opérateur",
                "viewer": "Observateur",
                "comptable": "Comptable"
            }
            role_label = role_labels.get(invitation.role, invitation.role)
            
            # Send email via email service
            result = email_service.send_invitation_email(
                to=invitation.email,
                invitation_url=invitation_url,
                company_name=company_name,
                invited_by_name=invited_by_name,
                role_label=role_label,
                expires_at=invitation.expires_at,
                message=invitation.message,
                app_name=config["app_name"],
                app_description=config["app_description"]
            )
            
            return {"success": True, "data": result.get("data", {})}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending invitation email: {str(e)}")
