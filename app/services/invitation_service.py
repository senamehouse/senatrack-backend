from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, desc
from fastapi import HTTPException
from app.core.database import get_db_session
from app.core.settings import settings
from app.models.invitation_model import CompanyInvitation
from app.models.company_model import Company
from app.models.user_model import User
from app.schemas.invitation_schema import (
    CompanyInvitationCreate, CompanyInvitationUpdate, InvitationStats, InvitationResponse, InvitationCancelResponse
)
from datetime import datetime, timedelta
import secrets
import string
import os
import resend

class InvitationService:
    """Service for company invitation-related operations"""
    
    def generate_invitation_token(self) -> str:
        """Generate a unique invitation token"""
        return ''.join(secrets.choices(string.ascii_letters + string.digits, k=32))
    
    async def create_invitation(self, invitation_data: CompanyInvitationCreate) -> CompanyInvitation:
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
                        CompanyInvitation.email == email,
                        CompanyInvitation.status == "pending",
                        CompanyInvitation.expires_at > datetime.utcnow()
                    )
                ).order_by(desc(CompanyInvitation.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving pending invitations: {str(e)}")
    
    async def update_invitation(self, invitation_id: str, invitation_data: CompanyInvitationUpdate) -> CompanyInvitation:
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
    
    async def accept_invitation(self, token: str, user_id: str) -> InvitationResponse:
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
            
            # Update invitation status
            await session.execute(
                update(CompanyInvitation).where(CompanyInvitation.id == invitation.id).values(
                    status="accepted",
                    accepted_at=datetime.utcnow(),
                    accepted_by=user_id,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            
            # Get updated invitation
            result = await session.execute(
                select(CompanyInvitation).where(CompanyInvitation.token == token)
            )
            updated_invitation = result.scalar_one_or_none()
            
            return InvitationResponse(
                success=True,
                message="Invitation accepted successfully",
                invitation=updated_invitation
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error accepting invitation: {str(e)}")
    
    async def decline_invitation(self, token: str) -> InvitationResponse:
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
    
    async def cancel_invitation(self, invitation_id: str) -> InvitationCancelResponse:
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
        """Send invitation email via Resend"""
        try:
            if not settings.RESEND_API_KEY:
                raise HTTPException(status_code=500, detail="Resend API key not configured")
            
            resend.api_key = settings.RESEND_API_KEY
            
            # Get app URL from environment or use default
            if not app_url:
                app_url = os.getenv("NEXT_PUBLIC_APP_URL", "https://gestion.senatrack.app")
            
            invitation_url = f"{app_url}/invitations?id={invitation.id}"
            
            # Role labels mapping
            role_labels = {
                "admin": "Administrateur",
                "manager": "Gestionnaire",
                "operator": "Opérateur",
                "viewer": "Observateur",
                "comptable": "Comptable"
            }
            role_label = role_labels.get(invitation.role, invitation.role)
            
            # Application name
            app_name = os.getenv("APPLICATION_NAME", "SenaTrack")
            website = os.getenv("WEBSITE", "senatrack.app")
            app_description = os.getenv("APP_DESCRIPTION", "SenaTrack est une solution complète pour la gestion de vos factures, stocks, et clients.")
            
            # Build HTML email
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
              <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #1f2937; margin-bottom: 10px;">{app_name}</h1>
                <p style="color: #6b7280; font-size: 16px;">{app_description}</p>
              </div>
              
              <div style="background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 30px;">
                <h2 style="color: #1f2937; margin-bottom: 20px;">Invitation à rejoindre une entreprise</h2>
                
                <p style="color: #374151; margin-bottom: 15px;">
                  Bonjour,
                </p>
                
                <p style="color: #374151; margin-bottom: 20px;">
                  <strong>{invited_by_name}</strong> vous invite à rejoindre l'entreprise <strong>{company_name}</strong> sur {app_name}.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 6px; margin: 20px 0;">
                  <h3 style="color: #1f2937; margin-bottom: 10px;">Détails de l'invitation :</h3>
                  <ul style="color: #374151; margin: 0; padding-left: 20px;">
                    <li><strong>Entreprise :</strong> {company_name}</li>
                    <li><strong>Rôle proposé :</strong> {role_label}</li>
                    <li><strong>Expire le :</strong> {invitation.expires_at.strftime('%d/%m/%Y') if invitation.expires_at else 'N/A'}</li>
                  </ul>
                </div>
                
                {f'''
                <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin: 20px 0;">
                  <h4 style="color: #92400e; margin-bottom: 10px;">Message de {invited_by_name} :</h4>
                  <p style="color: #92400e; margin: 0;">{invitation.message}</p>
                </div>
                ''' if invitation.message else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                  <a href="{invitation_url}" 
                     style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                    Accepter l'invitation
                  </a>
                </div>
                
                <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 30px;">
                  Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
                  <a href="{invitation_url}" style="color: #3b82f6;">{invitation_url}</a>
                </p>
              </div>
              
              <div style="text-align: center; color: #6b7280; font-size: 12px;">
                <p>Cet email a été envoyé par {app_name}. Si vous n'avez pas demandé cette invitation, vous pouvez ignorer cet email.</p>
              </div>
            </div>
            """
            
            # Send email
            result = resend.emails.send({
                "from": f"{app_name} <noreply@{website}>",
                "to": [invitation.email],
                "subject": f"Invitation à rejoindre {company_name} sur {app_name}",
                "html": html_content,
            })
            
            if result.get("error"):
                raise HTTPException(status_code=500, detail=f"Failed to send email: {result['error']}")
            
            return {"success": True, "data": result}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending invitation email: {str(e)}")
