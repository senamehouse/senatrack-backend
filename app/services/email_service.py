"""
Email service for sending emails via Resend API.
Handles both online and offline modes.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.core.settings import settings
import resend
import os


class EmailService:
    """Service for sending emails via Resend"""
    
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.email_from = settings.EMAIL_FROM
        self.email_from_name = settings.EMAIL_FROM_NAME
    
    def _get_from_address(self) -> str:
        """Get the 'from' address in the format 'Name <email>'"""
        if self.email_from_name and self.email_from:
            return f"{self.email_from_name} <{self.email_from}>"
        elif self.email_from:
            return self.email_from
        else:
            # Fallback to default format if not configured
            website = os.getenv("WEBSITE", "senatrack.app")
            app_name = os.getenv("APPLICATION_NAME", "SenaTrack")
            return f"{app_name} <noreply@{website}>"
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        html_content: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Resend API.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            html_content: HTML content of the email
            from_address: Optional custom 'from' address (defaults to settings)
        
        Returns:
            Dict with email send result
            
        Raises:
            HTTPException: If email service is not configured or sending fails
        """
        # Check if in online mode
        if settings.DATABASE_MODE != "online":
            raise HTTPException(
                status_code=400,
                detail="Email sending is only available in online mode"
            )
        
        # Check if Resend API key is configured
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="Email service not configured (RESEND_API_KEY missing)"
            )
        
        # Set Resend API key
        resend.api_key = self.api_key
        
        # Use provided from_address or default from settings
        from_addr = from_address or self._get_from_address()
        
        try:
            # Send email
            result = resend.Emails.send({
                "from": from_addr,
                "to": to,
                "subject": subject,
                "html": html_content,
            })
            
            # Check for errors in response
            if result.get("error"):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to send email: {result['error']}"
                )
            
            return {"success": True, "data": result}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error sending email: {str(e)}"
            )
    
    def send_password_reset_email(
        self,
        to: str,
        code: str,
        app_url: str,
        app_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send password reset email with verification code.
        
        Args:
            to: Recipient email address
            code: Six-digit verification code
            app_url: Base application URL for reset instructions
            app_name: Optional app name (defaults to env variable)
        
        Returns:
            Dict with email send result
        """
        from app.utils.email_templates import get_password_reset_template, get_app_config
        
        config = get_app_config()
        app_name = app_name or config["app_name"]
        
        html_content = get_password_reset_template(code, app_name, app_url)
        subject = f"Réinitialisation de mot de passe - {app_name}"
        
        return self.send_email(
            to=[to],
            subject=subject,
            html_content=html_content
        )
    
    def send_invitation_email(
        self,
        to: str,
        invitation_url: str,
        company_name: str,
        invited_by_name: str,
        role_label: str,
        expires_at: Optional[Any] = None,
        message: Optional[str] = None,
        app_name: Optional[str] = None,
        app_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send company invitation email.
        
        Args:
            to: Recipient email address
            invitation_url: Invitation acceptance URL
            company_name: Name of the company
            invited_by_name: Name of the person sending the invitation
            role_label: Label for the role being offered
            expires_at: Optional expiration datetime
            message: Optional personal message
            app_name: Optional app name (defaults to env variable)
            app_description: Optional app description (defaults to env variable)
        
        Returns:
            Dict with email send result
        """
        from app.utils.email_templates import get_invitation_template, get_app_config
        
        config = get_app_config()
        app_name = app_name or config["app_name"]
        app_description = app_description or config["app_description"]
        
        html_content = get_invitation_template(
            invitation_url=invitation_url,
            company_name=company_name,
            invited_by_name=invited_by_name,
            role_label=role_label,
            expires_at=expires_at,
            message=message,
            app_name=app_name,
            app_description=app_description
        )
        subject = f"Invitation à rejoindre {company_name} sur {app_name}"
        
        return self.send_email(
            to=[to],
            subject=subject,
            html_content=html_content
        )


# Singleton instance
email_service = EmailService()

