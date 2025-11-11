"""
Email templates for different use cases.
All templates return HTML content with consistent styling.
"""
import os
from typing import Optional
from datetime import datetime


def get_app_config() -> dict:
    """Get application configuration from environment variables"""
    return {
        "app_name": os.getenv("APPLICATION_NAME", "SenaTrack"),
        "app_description": os.getenv("APP_DESCRIPTION", "SenaTrack est une solution complète pour la gestion de vos factures, stocks, et clients."),
        "app_url": os.getenv("NEXT_PUBLIC_APP_URL", "https://gestion.senatrack.app"),
        "website": os.getenv("WEBSITE", "senatrack.app"),
    }


def get_base_template(content: str, app_name: str, app_description: Optional[str] = None) -> str:
    """Base email template with consistent styling"""
    description_html = f'<p style="color: #6b7280; font-size: 16px;">{app_description}</p>' if app_description else ''
    
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #1f2937; margin-bottom: 10px;">{app_name}</h1>
        {description_html}
      </div>
      
      {content}
      
      <div style="text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px;">
        <p>Cet email a été envoyé par {app_name}.</p>
      </div>
    </div>
    """


def get_password_reset_template(reset_url: str, app_name: str) -> str:
    """Template for password reset emails"""
    content = f"""
      <div style="background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 30px;">
        <h2 style="color: #1f2937; margin-bottom: 20px;">Réinitialisation de mot de passe</h2>
        
        <p style="color: #374151; margin-bottom: 15px;">
          Bonjour,
        </p>
        
        <p style="color: #374151; margin-bottom: 20px;">
          Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe.
        </p>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="{reset_url}" 
             style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
            Réinitialiser mon mot de passe
          </a>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 30px;">
          Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
          <a href="{reset_url}" style="color: #3b82f6; word-break: break-all;">{reset_url}</a>
        </p>
        
        <p style="color: #9ca3af; font-size: 12px; margin-top: 30px;">
          ⚠️ Ce lien expire dans 1 heure. Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
        </p>
      </div>
    """
    return get_base_template(content, app_name)


def get_invitation_template(
    invitation_url: str,
    company_name: str,
    invited_by_name: str,
    role_label: str,
    expires_at: Optional[datetime],
    message: Optional[str],
    app_name: str,
    app_description: Optional[str] = None
) -> str:
    """Template for company invitation emails"""
    expires_text = expires_at.strftime('%d/%m/%Y') if expires_at else 'N/A'
    message_html = f'''
      <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <h4 style="color: #92400e; margin-bottom: 10px;">Message de {invited_by_name} :</h4>
        <p style="color: #92400e; margin: 0;">{message}</p>
      </div>
    ''' if message else ''
    
    content = f"""
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
            <li><strong>Expire le :</strong> {expires_text}</li>
          </ul>
        </div>
        
        {message_html}
        
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
    """
    return get_base_template(content, app_name, app_description)

