from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import require_admin_access
from app.core.database import get_async_db
from app.schemas.user_schema import User
from app.services.migration_service import MigrationService

router = APIRouter(prefix="/migration", tags=["Migration"], dependencies=[Depends(require_admin_access)])
migration_service = MigrationService()

@router.post("/run-full-migration")
async def run_full_migration(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access)
):
    """Run complete migration from old role system to new role system (admin only)"""
    return await migration_service.run_full_migration()

@router.post("/migrate-user-roles")
async def migrate_user_roles(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access)
):
    """Migrate old user.role field to UserRole system (admin only)"""
    return await migration_service.migrate_user_roles()

@router.post("/migrate-company-member-roles")
async def migrate_company_member_roles(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access)
):
    """Migrate old CompanyMember.role field to UserCompanyRole system (admin only)"""
    return await migration_service.migrate_company_member_roles()

@router.get("/status")
async def get_migration_status(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_access)
):
    """Get the current migration status"""
    return await migration_service.get_migration_status()

