import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text, select, update, delete
from sqlalchemy.sql import func
from app.schemas.user import User as UserSchema
from app.core.settings import settings

# Async SQLAlchemy Base
class Base(DeclarativeBase):
    pass

# Async Models
class User(Base):
    """Async SQLAlchemy model for User table"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class RefreshToken(Base):
    """Async SQLAlchemy model for refresh tokens"""
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SyncLog(Base):
    """Async SQLAlchemy model for sync operations tracking"""
    __tablename__ = "sync_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON data
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "operation": self.operation,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "data": self.data,
            "synced": self.synced,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None
        }

# Async Database Setup
DATABASE_URL = f"sqlite+aiosqlite:///{settings.LOCAL_DB_PATH}"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_database():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_db() -> AsyncSession:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class AsyncDatabase:
    """Fully async SQLite database operations"""
    
    def __init__(self):
        self.db_path = settings.LOCAL_DB_PATH
        self.engine = async_engine
        self.SessionLocal = AsyncSessionLocal
    
    async def get_all_users(self) -> List[UserSchema]:
        """Get all active users from the database"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()
            return [UserSchema(**user.to_dict()) for user in users]
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserSchema]:
        """Get a user by ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            return UserSchema(**user.to_dict()) if user else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create a new user and return the ID"""
        async with AsyncSessionLocal() as session:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                phone_number=user_data.get('phone_number'),
                hashed_password=user_data['hashed_password']
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Log sync operation
            sync_log = SyncLog(
                operation='CREATE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return user.id
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update a user by ID"""
        async with AsyncSessionLocal() as session:
            # Get existing user
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Update fields
            if 'name' in user_data:
                user.name = user_data['name']
            if 'email' in user_data:
                user.email = user_data['email']
            if 'phone_number' in user_data:
                user.phone_number = user_data['phone_number']
            
            user.updated_at = datetime.now()
            await session.commit()
            
            # Log sync operation
            sync_log = SyncLog(
                operation='UPDATE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return True
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID (soft delete)"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Soft delete
            user.is_active = False
            user.updated_at = datetime.now()
            await session.commit()
            
            # Log sync operation
            sync_log = SyncLog(
                operation='DELETE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return True
    
    async def get_users_count(self) -> int:
        """Get the count of active users"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            return result.scalar()
    
    async def get_unsynced_changes(self) -> List[Dict[str, Any]]:
        """Get all unsynced changes"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SyncLog).where(SyncLog.synced == False)
            )
            sync_logs = result.scalars().all()
            
            changes = []
            for log in sync_logs:
                change = {
                    'id': log.id,
                    'operation': log.operation,
                    'record_id': log.record_id,
                    'table_name': log.table_name,
                    'data': json.loads(log.data) if log.data else {}
                }
                # Add user fields for easier processing
                if log.data:
                    user_data = json.loads(log.data)
                    change.update({
                        'name': user_data.get('name'),
                        'email': user_data.get('email'),
                        'phone_number': user_data.get('phone_number')
                    })
                changes.append(change)
            return changes
    
    async def mark_sync_log_as_synced(self, log_id: int):
        """Mark a sync log entry as synced"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SyncLog).where(SyncLog.id == log_id)
            )
            sync_log = result.scalar_one_or_none()
            
            if sync_log:
                sync_log.synced = True
                sync_log.synced_at = datetime.now()
                await session.commit()
    
    async def sync_data(self, data: List[Dict[str, Any]]) -> bool:
        """Sync data from external source"""
        async with AsyncSessionLocal() as session:
            try:
                for item in data:
                    # Check if user exists
                    result = await session.execute(
                        select(User).where(User.email == item['email'])
                    )
                    existing_user = result.scalar_one_or_none()
                    
                    if existing_user:
                        # Update existing user
                        existing_user.name = item['name']
                        existing_user.phone_number = item.get('phone_number')
                        existing_user.updated_at = datetime.now()
                    else:
                        # Create new user
                        new_user = User(
                            name=item['name'],
                            email=item['email'],
                            phone_number=item.get('phone_number')
                        )
                        session.add(new_user)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"Sync error: {e}")
                return False
    
    async def export_data(self) -> List[Dict[str, Any]]:
        """Export all data for synchronization"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()
            return [user.to_dict() for user in users]
    
    async def clear_all_data(self):
        """Clear all data from database"""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(User))
            await session.execute(delete(RefreshToken))
            await session.execute(delete(SyncLog))
            await session.commit()
    
    # Authentication-specific methods
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
    
    async def update_user_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.last_login = datetime.now()
                await session.commit()
    
    async def create_refresh_token(self, user_id: int, token: str, expires_at: datetime) -> int:
        """Create a refresh token"""
        async with AsyncSessionLocal() as session:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
            session.add(refresh_token)
            await session.commit()
            await session.refresh(refresh_token)
            return refresh_token.id
    
    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get a refresh token by token string"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RefreshToken).where(
                    RefreshToken.token == token,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.now()
                )
            )
            return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token: str):
        """Revoke a refresh token"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RefreshToken).where(RefreshToken.token == token)
            )
            refresh_token = result.scalar_one_or_none()
            if refresh_token:
                refresh_token.is_revoked = True
                await session.commit()
    
    async def revoke_all_user_tokens(self, user_id: int):
        """Revoke all refresh tokens for a user"""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .values(is_revoked=True)
            )
            await session.commit()

# Global async database instance
db_instance = None

async def get_database() -> AsyncDatabase:
    """Get the current async database instance"""
    global db_instance
    if db_instance is None:
        db_instance = AsyncDatabase()
        # Initialize database tables
        await init_database()
    return db_instance