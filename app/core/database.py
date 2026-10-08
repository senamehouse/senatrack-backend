from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, inspect
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
        print("Online mode: Remote PostgreSQL database initialized")
        
    elif mode == "offline":
        # Offline mode: Initialize local SQLite only
        async with local_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _apply_non_destructive_alters(conn, dialect="sqlite")
        print("Offline mode: Local SQLite database initialized")
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
    """Add missing nullable tenant columns and recover ownership where it is known."""
    company_id = settings.COMPANY_ID
    # Pending company logos use `temp-company-<user id>`, which is longer than
    # the original file_records.entity_id VARCHAR(20) on PostgreSQL.
    if dialect == "postgresql":
        file_columns = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_columns("file_records"))
        entity_column = next(column for column in file_columns if column["name"] == "entity_id")
        entity_length = getattr(entity_column["type"], "length", None)
        if entity_length is not None and entity_length < 64:
            await conn.execute(text("ALTER TABLE file_records ALTER COLUMN entity_id TYPE VARCHAR(64)"))
    # Quote/form totals were added after the first deployments.
    for column in ("discount", "tva"):
        if dialect == "postgresql":
            await conn.execute(text(f"ALTER TABLE proformas ADD COLUMN IF NOT EXISTS {column} DOUBLE PRECISION DEFAULT 0"))
        else:
            columns = await conn.execute(text("PRAGMA table_info(proformas)"))
            if column not in {row[1] for row in columns}:
                await conn.execute(text(f"ALTER TABLE proformas ADD COLUMN {column} FLOAT DEFAULT 0"))
    if dialect == "postgresql":
        await conn.execute(text("ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS details JSONB"))
        await conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS details JSONB"))
    else:
        columns = await conn.execute(text("PRAGMA table_info(purchase_orders)"))
        if "details" not in {row[1] for row in columns}:
            await conn.execute(text("ALTER TABLE purchase_orders ADD COLUMN details JSON"))
        columns = await conn.execute(text("PRAGMA table_info(suppliers)"))
        if "details" not in {row[1] for row in columns}:
            await conn.execute(text("ALTER TABLE suppliers ADD COLUMN details JSON"))
    # Preserve legacy sync tables and include every current model that owns a
    # company_id. create_all() does not add columns to existing tables.
    legacy_tables = [
        "users","product_categories","units","products","suppliers","clients","services",
        "tva","abic","stock_movements","stock_movement_items","sales","sale_items",
        "activity_logs","proformas","company_members","companies","sync_log","activation_keys",
        "company_invitations","user_roles","user_role_assignments","user_company_roles","user_company_role_assignments"
    ]
    model_tables = [table.name for table in Base.metadata.tables.values() if "company_id" in table.c]
    tables = list(dict.fromkeys([*legacy_tables, *model_tables]))
    child_sources = {
        "employee_leave_requests": ("employees", "employee_id"),
        "employee_payrolls": ("employees", "employee_id"),
        "purchase_orders": ("suppliers", "supplier_id"),
    }

    existing_tables = set(await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names()))
    for table_name in tables:
        if table_name not in existing_tables:
            continue
        # Names come from the fixed list above; quote identifiers for both dialects.
        quoted_table = conn.dialect.identifier_preparer.quote(table_name)
        if dialect == "postgresql":
            await conn.execute(text(f"ALTER TABLE {quoted_table} ADD COLUMN IF NOT EXISTS company_id VARCHAR(64)"))
        elif dialect == "sqlite":
            columns = await conn.execute(text(f"PRAGMA table_info({quoted_table})"))
            if "company_id" not in {column[1] for column in columns}:
                await conn.execute(text(f"ALTER TABLE {quoted_table} ADD COLUMN company_id VARCHAR(64)"))
            if company_id and table_name not in child_sources and table_name != "file_records":
                await conn.execute(text(f"UPDATE {quoted_table} SET company_id = :cid WHERE company_id IS NULL"), {"cid": company_id})

    # Recover tenant ownership from parent records, never the local fallback.
    # Do not assign an unrelated tenant to orphaned historical records.
    for child, (parent, foreign_key) in child_sources.items():
        if child not in existing_tables or parent not in existing_tables:
            continue
        quoted_child = conn.dialect.identifier_preparer.quote(child)
        quoted_parent = conn.dialect.identifier_preparer.quote(parent)
        await conn.execute(text(f"""
            UPDATE {quoted_child} SET company_id = (
                SELECT owner.company_id FROM {quoted_parent} AS owner
                WHERE owner.id = {quoted_child}.{foreign_key}
            )
            WHERE company_id IS NULL AND EXISTS (
                SELECT 1 FROM {quoted_parent} AS owner
                WHERE owner.id = {quoted_child}.{foreign_key} AND owner.company_id IS NOT NULL
            )
        """))

# Database configuration and setup only
# All database operations are handled by services
