import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from app.core.database import get_sessionmaker
from app.models.auth_model import RefreshToken
from app.core.settings import settings
from app.schemas.user_schema import UserRegister, UserLogin, PasswordChange
from app.schemas.auth_schema import Token, TokenData
from app.schemas.user_schema import User as UserSchema, UserInternal
from app.services.user_service import UserService

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None
            
            user_id: str = payload.get("user_id")
            email: str = payload.get("email")
            
            if user_id is None or email is None:
                return None
            
            return TokenData(user_id=user_id, email=email)
        except JWTError:
            return None
    
    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user
        user_dict = {
            "name": user_data.name,
            "email": user_data.email,
            "phone_number": user_data.phone_number,
            "hashed_password": hashed_password
        }
        
        user_id = await self.user_service.create_user(user_dict)

        # Build tokens like login
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"user_id": user_id, "email": user_data.email},
            expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(data={"user_id": user_id, "email": user_data.email})

        # Store refresh token
        refresh_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.create_refresh_token_db(user_id, refresh_token, refresh_expires)

        # Load full user to return
        user = await self.user_service.get_user_by_id(user_id)
        if isinstance(user, UserInternal):
            user_dict_ret = user.model_dump()
            user_dict_ret.pop('hashed_password', None)
            user_ret = UserSchema(**user_dict_ret)
        else:
            user_ret = user  # already schema

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ).model_dump(by_alias=True) | {"user": user_ret.model_dump(by_alias=True)}
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserSchema]:
        """Authenticate a user with email and password"""
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Convert UserInternal to UserSchema (without hashed_password)
        user_dict = user.model_dump()
        user_dict.pop('hashed_password', None)  # Remove password field
        return UserSchema(**user_dict)
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """Login a user and return tokens"""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        await self.user_service.update_user_last_login(user.id)
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"user_id": user.id, "email": user.email}
        )
        
        # Store refresh token in database
        refresh_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.create_refresh_token_db(user.id, refresh_token, refresh_expires)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def create_refresh_token_db(self, user_id: str, token: str, expires_at: datetime) -> int:
        """Create a refresh token in database"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                refresh_token = RefreshToken(
                    user_id=user_id,
                    token=token,
                    expires_at=expires_at
                )
                session.add(refresh_token)
                await session.commit()
                await session.refresh(refresh_token)
                return refresh_token.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating refresh token: {str(e)}")
    
    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get a refresh token by token string"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(RefreshToken).where(
                        RefreshToken.token == token,
                        RefreshToken.is_revoked == False,
                        RefreshToken.expires_at > datetime.now()
                    )
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving refresh token: {str(e)}")
    
    async def revoke_refresh_token(self, token: str):
        """Revoke a refresh token"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                result = await session.execute(
                    select(RefreshToken).where(RefreshToken.token == token)
                )
                refresh_token = result.scalar_one_or_none()
                if refresh_token:
                    refresh_token.is_revoked = True
                    await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error revoking refresh token: {str(e)}")
    
    async def revoke_all_user_tokens(self, user_id: str):
        """Revoke all refresh tokens for a user"""
        try:
            Session = get_sessionmaker()
            async with Session() as session:
                await session.execute(
                    update(RefreshToken)
                    .where(RefreshToken.user_id == user_id)
                    .values(is_revoked=True)
                )
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error revoking user tokens: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh an access token using a refresh token"""
        # Verify refresh token
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if refresh token exists in database
        db_refresh_token = await self.get_refresh_token(refresh_token)
        if not db_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = await self.user_service.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def logout_user(self, refresh_token: str) -> Dict[str, str]:
        """Logout a user by revoking their refresh token"""
        await self.revoke_refresh_token(refresh_token)
        return {"message": "Successfully logged out"}
    
    async def logout_all_sessions(self, user_id: int) -> Dict[str, str]:
        """Logout user from all sessions"""
        await self.revoke_all_user_tokens(user_id)
        return {"message": "Successfully logged out from all sessions"}
    
    async def change_password(self, user_id: str, password_data: PasswordChange) -> Dict[str, str]:
        """Change user password"""
        # Get user
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = self.get_password_hash(password_data.new_password)
        
        # Update password
        user_data = {"hashed_password": new_hashed_password}
        success = await self.user_service.update_user(user_id, user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Revoke all refresh tokens for security
        await self.revoke_all_user_tokens(user_id)
        
        return {"message": "Password changed successfully"}
    
    async def get_current_user(self, token: str) -> UserSchema:
        """Get current user from access token"""
        token_data = self.verify_token(token, "access")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await self.user_service.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user companies
        from app.services.company_service import CompanyService
        company_service = CompanyService()
        companies = await company_service.get_user_companies(user.id)
        
        # Get user platform roles and permissions
        from app.services.user_role_service import UserRoleService
        user_role_service = UserRoleService()
        platform_roles = await user_role_service.get_user_roles(user.id)
        platform_permissions = await user_role_service.get_user_permissions(user.id)
        
        # Convert user to dict and add companies, roles, and permissions
        user_dict = user.model_dump()
        user_dict['companies'] = [str(company.id) for company in companies]
        user_dict['currentCompany'] = str(user.current_company_id) if user.current_company_id else None
        user_dict['platformRoles'] = [role.name for role in platform_roles]
        user_dict['platformPermissions'] = platform_permissions
        
        return UserSchema(**user_dict)
