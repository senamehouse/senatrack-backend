from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.schemas.user_schema import User
from app.services.migration_service import MigrationService

router = APIRouter(prefix="/migration", tags=["Migration"])
migration_service = MigrationService()

@router.post("/run-full-migration")
async def run_full_migration(
    current_user: User = Depends(get_current_user)
):
    """Run complete migration from old role system to new role system (admin only)"""
    # TODO: Add admin permission check
    return await migration_service.run_full_migration()

@router.post("/migrate-user-roles")
async def migrate_user_roles(
    current_user: User = Depends(get_current_user)
):
    """Migrate old user.role field to UserRole system (admin only)"""
    # TODO: Add admin permission check
    return await migration_service.migrate_user_roles()

@router.post("/migrate-company-member-roles")
async def migrate_company_member_roles(
    current_user: User = Depends(get_current_user)
):
    """Migrate old CompanyMember.role field to UserCompanyRole system (admin only)"""
    # TODO: Add admin permission check
    return await migration_service.migrate_company_member_roles()

@router.get("/status")
async def get_migration_status(
    current_user: User = Depends(get_current_user)
):
    """Get the current migration status"""
    return await migration_service.get_migration_status()
