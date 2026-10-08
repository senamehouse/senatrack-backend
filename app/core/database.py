from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator, Optional
from contextvars import ContextVar
from app.core.settings import settings


# Async SQLAlchemy Base
class Base(DeclarativeBase):
    pass

# Context variable to store the current database session per request
_db_session: ContextVar[Optional[AsyncSession]] = ContextVar('db_session', default=None)

def get_db_session() -> AsyncSession:
    """Get the current database session from context variable"""
    session = _db_session.get()
    if session is None:
        raise RuntimeError("Database session not set in context. Ensure get_async_db dependency is used in route handler.")
    return session

def set_db_session(session: AsyncSession) -> None:
    """Set the database session in context variable"""
    _db_session.set(session)

# Engines per mode
def _resolve_local_url() -> str:
    return f"sqlite+aiosqlite:///{settings.LOCAL_DB_PATH}"

def _resolve_remote_url() -> Optional[str]:
    return settings.REMOTE_DB_URL

local_async_engine = create_async_engine(
    _resolve_local_url(),
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)

remote_async_engine = None
remote_url = _resolve_remote_url()
if remote_url:
    remote_async_engine = create_async_engine(
        remote_url,
        echo=False,
        future=True,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=1800,  # Reduced recycle time (30 minutes)
        pool_timeout=30,  # Add timeout
        connect_args={
            "server_settings": {
                "application_name": "senatrack_backend",
            },
            "command_timeout": 60,
        },
    )

LocalAsyncSession = async_sessionmaker(
    local_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

RemoteAsyncSession = None
if remote_async_engine is not None:
    RemoteAsyncSession = async_sessionmaker(
        remote_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

def get_sessionmaker():
    """Return the sessionmaker based on current DATABASE_MODE.
    - online -> RemoteAsyncSession
    - offline -> LocalAsyncSession
    """
    mode = (settings.DATABASE_MODE or "offline").lower()
    if mode == "online":
        if RemoteAsyncSession is None:
            raise RuntimeError("REMOTE_DB_URL not configured for online mode")
        return RemoteAsyncSession
    return LocalAsyncSession

async def init_database():
    """Initialize database tables based on mode and run non-destructive schema updates."""
    mode = (settings.DATABASE_MODE or "offline").lower()
    
    print(f"Initializing database in '{mode}' mode...")

    if mode == "online":
        # Online mode: Initialize remote PostgreSQL only
        if remote_async_engine is None:
            raise RuntimeError("REMOTE_DB_URL not configured for online mode")
        async with remote_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _apply_non_destructive_alters(conn, dialect="postgresql")
        print("✅ Online mode: Remote PostgreSQL database initialized")
        
    elif mode == "offline":
        # Offline mode: Initialize local SQLite only
        async with local_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _apply_non_destructive_alters(conn, dialect="sqlite")
        print("✅ Offline mode: Local SQLite database initialized")
        
    elif mode == "offline":
        # Already handled above; keep explicit else guard below
        pass
    else:
        raise ValueError(f"Invalid DATABASE_MODE: {mode}. Must be 'online', 'offline', or 'both'")

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a session according to DATABASE_MODE and set it in context"""
    mode = (settings.DATABASE_MODE or "offline").lower()
    
    if mode == "online":
        # Online mode: Use remote PostgreSQL
        if RemoteAsyncSession is None:
            raise RuntimeError("REMOTE_DB_URL not configured for online mode")
        async with RemoteAsyncSession() as session:
            set_db_session(session)  # Set in context
            try:
                yield session
            finally:
                _db_session.set(None)  # Clear after request
    elif mode == "offline":
        # Offline mode: Use local SQLite
        async with LocalAsyncSession() as session:
            set_db_session(session)  # Set in context
            try:
                yield session
            finally:
                _db_session.set(None)  # Clear after request
    else:
        # Default to offline mode
        async with LocalAsyncSession() as session:
            set_db_session(session)  # Set in context
            try:
                yield session
            finally:
                _db_session.set(None)  # Clear after request


async def get_local_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with LocalAsyncSession() as session:
        yield session


async def get_remote_async_db() -> AsyncGenerator[AsyncSession, None]:
    if RemoteAsyncSession is None:
        raise RuntimeError("REMOTE_DB_URL not configured")
    async with RemoteAsyncSession() as session:
        yield session


def get_database_info() -> dict:
    """Get information about current database configuration"""
    mode = (settings.DATABASE_MODE or "offline").lower()
    
    info = {
        "mode": mode,
        "local_db_path": settings.LOCAL_DB_PATH,
        "remote_db_configured": remote_async_engine is not None,
        "auto_migrate_remote": settings.AUTO_MIGRATE_REMOTE,
    }
    
    if mode == "online":
        info["active_database"] = "Remote PostgreSQL"
        info["local_available"] = True
    elif mode == "offline":
        info["active_database"] = "Local SQLite"
        info["remote_available"] = remote_async_engine is not None
    elif mode == "both":
        info["active_database"] = "Local SQLite"
    
    return info


async def _apply_non_destructive_alters(conn, dialect: str):
    """Best-effort schema evolutions: add company_id columns and indexes if missing.
    Keep columns nullable to avoid destructive changes. Backfill local with COMPANY_ID.
    """
    company_id = settings.COMPANY_ID
    # Quote/form totals were added after the first deployments.
    for column in ("discount", "tva"):
        if dialect == "postgresql":
            await conn.execute(text(f"ALTER TABLE proformas ADD COLUMN IF NOT EXISTS {column} DOUBLE PRECISION DEFAULT 0"))
        else:
            columns = await conn.execute(text("PRAGMA table_info(proformas)"))
            if column not in {row[1] for row in columns}:
                await conn.execute(text(f"ALTER TABLE proformas ADD COLUMN {column} FLOAT DEFAULT 0"))
    # Tables to alter (must match models): simple list approach
    tables = [
        "users","product_categories","units","products","suppliers","clients","services",
        "tva","abic","stock_movements","stock_movement_items","sales","sale_items",
        "activity_logs","proformas","company_members","companies","sync_log","activation_keys",
        "company_invitations","user_roles","user_role_assignments","user_company_roles","user_company_role_assignments"
    ]

    if dialect == "sqlite":
        for t in tables:
            try:
                # Add column if not exists (SQLite supports ADD COLUMN without IF NOT EXISTS prior to 3.35; tolerant try)
                await conn.execute(text(f"ALTER TABLE {t} ADD COLUMN company_id VARCHAR(64)"))
            except Exception:
                pass
            # best-effort backfill for local
            if company_id:
                try:
                    await conn.execute(text(f"UPDATE {t} SET company_id = :cid WHERE company_id IS NULL"), {"cid": company_id})
                except Exception:
                    pass
    elif dialect == "postgresql":
        for t in tables:
            try:
                await conn.execute(text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = :t AND column_name = 'company_id'
                        ) THEN
                            EXECUTE format('ALTER TABLE %I ADD COLUMN company_id TEXT', :t);
                        END IF;
                    END$$;
                    """
                ), {"t": t})
            except Exception:
                pass

# Database configuration and setup only
# All database operations are handled by services
