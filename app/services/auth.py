import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.database import get_database
from app.core.settings import settings
from app.schemas.user import UserRegister, UserLogin, PasswordChange
from app.schemas.auth import Token, TokenData
from app.schemas.user import User as UserSchema

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """Get async database instance"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
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
            
            user_id: int = payload.get("user_id")
            email: str = payload.get("email")
            
            if user_id is None or email is None:
                return None
            
            return TokenData(user_id=user_id, email=email)
        except JWTError:
            return None
    
    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """Register a new user"""
        db = await self._get_db()
        
        # Check if user already exists
        existing_user = await db.get_user_by_email(user_data.email)
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
        
        user_id = await db.create_user(user_dict)
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "email": user_data.email
        }
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserSchema]:
        """Authenticate a user with email and password"""
        db = await self._get_db()
        
        user = await db.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return UserSchema(**user.to_dict())
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """Login a user and return tokens"""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        db = await self._get_db()
        
        # Update last login
        await db.update_user_last_login(user.id)
        
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
        await db.create_refresh_token(user.id, refresh_token, refresh_expires)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh an access token using a refresh token"""
        db = await self._get_db()
        
        # Verify refresh token
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if refresh token exists in database
        db_refresh_token = await db.get_refresh_token(refresh_token)
        if not db_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = await db.get_user_by_id(token_data.user_id)
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
        db = await self._get_db()
        await db.revoke_refresh_token(refresh_token)
        return {"message": "Successfully logged out"}
    
    async def logout_all_sessions(self, user_id: int) -> Dict[str, str]:
        """Logout user from all sessions"""
        db = await self._get_db()
        await db.revoke_all_user_tokens(user_id)
        return {"message": "Successfully logged out from all sessions"}
    
    async def change_password(self, user_id: int, password_data: PasswordChange) -> Dict[str, str]:
        """Change user password"""
        db = await self._get_db()
        
        # Get user
        user = await db.get_user_by_id(user_id)
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
        success = await db.update_user(user_id, user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Revoke all refresh tokens for security
        await db.revoke_all_user_tokens(user_id)
        
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
        
        db = await self._get_db()
        user = await db.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
