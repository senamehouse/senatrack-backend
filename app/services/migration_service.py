from typing import List, Dict, Any
from sqlalchemy import select, update, insert
from fastapi import HTTPException
from app.core.database import get_db_session
from app.models.user_model import User
from app.models.company_model import CompanyMember
from app.models.user_model import UserRoleModel, UserRoleAssignmentModel
from app.models.company_model import UserCompanyRoleModel, UserCompanyRoleAssignmentModel
from app.schemas.user_role_schema import DEFAULT_PLATFORM_ROLES
from app.schemas.company_role_schema import DEFAULT_COMPANY_ROLES
from datetime import datetime

class MigrationService:
    """Service for migrating existing roles to the new role system"""

    async def migrate_user_roles(self) -> Dict[str, Any]:
        """Migrate old user.role field to UserRole system"""
        try:
            session = get_db_session()
            # Get all users with old role field
            result = await session.execute(
                select(User).where(User.role.isnot(None))
            )
            users = result.scalars().all()

            # Get platform_admin role (should exist after creating presets)
            admin_role_result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.name == "Platform Administrator")
            )
            admin_role = admin_role_result.scalar_one_or_none()

            # Get regular_user role
            user_role_result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.name == "Regular User")
            )
            user_role = user_role_result.scalar_one_or_none()

            if not admin_role or not user_role:
                raise HTTPException(status_code=500, detail="Platform role presets not found. Run create_default_presets first.")

            migrated_count = 0
            skipped_count = 0

            for user in users:
                # Check if user already has role assignments
                existing_assignments = await session.execute(
                    select(UserRoleAssignmentModel).where(UserRoleAssignmentModel.user_id == user.id)
                )
                if existing_assignments.scalar_one_or_none():
                    skipped_count += 1
                    continue

                # Determine which role to assign based on old role
                role_to_assign = user_role  # Default to regular user
                if user.role in ["admin", "administrator"]:
                    role_to_assign = admin_role

                # Create role assignment
                assignment = UserRoleAssignmentModel(
                    user_id=user.id,
                    role_id=role_to_assign.id,
                    assigned_by=None,  # System migration
                    assigned_at=datetime.utcnow()
                )
                session.add(assignment)
                migrated_count += 1

            await session.commit()

            return {
                "migrated_users": migrated_count,
                "skipped_users": skipped_count,
                "message": f"Successfully migrated {migrated_count} users to new role system"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error migrating user roles: {str(e)}")

    async def migrate_company_member_roles(self) -> Dict[str, Any]:
        """Migrate old CompanyMember.role field to UserCompanyRole system"""
        try:
            session = get_db_session()
            # Get all company members with old role field
            result = await session.execute(
                select(CompanyMember).where(CompanyMember.role.isnot(None))
            )
            members = result.scalars().all()

            migrated_count = 0
            skipped_count = 0
            companies_processed = set()

            for member in members:
                company_id = member.company_id

                # Create default presets for this company if not already done
                if company_id not in companies_processed:
                    from app.services.company_service import CompanyService
                    company_service = CompanyService()
                    await company_service.create_company_default_presets(company_id)
                    companies_processed.add(company_id)

                # Check if user already has role assignments for this company
                existing_assignments = await session.execute(
                    select(UserCompanyRoleAssignmentModel).where(
                        UserCompanyRoleAssignmentModel.user_id == member.user_id,
                        UserCompanyRoleAssignmentModel.company_id == company_id
                    )
                )
                if existing_assignments.scalar_one_or_none():
                    skipped_count += 1
                    continue

                # Map old role to new role name
                role_mapping = {
                    "owner": "Propriétaire",
                    "admin": "Administrateur",
                    "manager": "Gestionnaire",
                    "operator": "Opérateur",
                    "comptable": "Comptable",
                    "viewer": "Observateur"
                }

                new_role_name = role_mapping.get(member.role, "Opérateur")

                # Find the corresponding role in the company
                role_result = await session.execute(
                    select(UserCompanyRoleModel).where(
                        UserCompanyRoleModel.company_id == company_id,
                        UserCompanyRoleModel.name == new_role_name
                    )
                )
                company_role = role_result.scalar_one_or_none()

                if not company_role:
                    # Fallback to operator role
                    role_result = await session.execute(
                        select(UserCompanyRoleModel).where(
                            UserCompanyRoleModel.company_id == company_id,
                            UserCompanyRoleModel.name == "Opérateur"
                        )
                    )
                    company_role = role_result.scalar_one_or_none()

                if company_role:
                    # Create role assignment
                    assignment = UserCompanyRoleAssignmentModel(
                        user_id=member.user_id,
                        company_id=company_id,
                        role_id=company_role.id,
                        assigned_by=None,  # System migration
                        assigned_at=datetime.utcnow()
                    )
                    session.add(assignment)
                    migrated_count += 1
                else:
                    skipped_count += 1

            await session.commit()

            return {
                "migrated_members": migrated_count,
                "skipped_members": skipped_count,
                "companies_processed": len(companies_processed),
                "message": f"Successfully migrated {migrated_count} company members to new role system"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error migrating company member roles: {str(e)}")

    async def run_full_migration(self) -> Dict[str, Any]:
        """Run complete migration from old role system to new role system"""
        try:
            # Step 1: Create platform role presets
            from app.services.user_service import UserService
            user_service = UserService()
            platform_roles = await user_service.create_default_role_presets()

            # Step 2: Migrate user roles
            user_migration_result = await self.migrate_user_roles()

            # Step 3: Migrate company member roles
            company_migration_result = await self.migrate_company_member_roles()

            return {
                "platform_roles_created": len(platform_roles),
                "user_migration": user_migration_result,
                "company_migration": company_migration_result,
                "message": "Full migration completed successfully"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error running full migration: {str(e)}")

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get the current migration status"""
        try:
            session = get_db_session()
            # Count users with old role field
            old_users_result = await session.execute(
                select(User).where(User.role.isnot(None))
            )
            old_users_count = len(old_users_result.scalars().all())

            # Count users with new role assignments
            new_users_result = await session.execute(
                select(UserRoleAssignmentModel)
            )
            new_users_count = len(new_users_result.scalars().all())

            # Count company members with old role field
            old_members_result = await session.execute(
                select(CompanyMember).where(CompanyMember.role.isnot(None))
            )
            old_members_count = len(old_members_result.scalars().all())

            # Count company members with new role assignments
            new_members_result = await session.execute(
                select(UserCompanyRoleAssignmentModel)
            )
            new_members_count = len(new_members_result.scalars().all())

            # Count platform roles
            platform_roles_result = await session.execute(
                select(UserRoleModel)
            )
            platform_roles_count = len(platform_roles_result.scalars().all())

            # Count company roles
            company_roles_result = await session.execute(
                select(UserCompanyRoleModel)
            )
            company_roles_count = len(company_roles_result.scalars().all())

            return {
                "old_system": {
                    "users_with_old_roles": old_users_count,
                    "company_members_with_old_roles": old_members_count
                },
                "new_system": {
                    "platform_roles": platform_roles_count,
                    "company_roles": company_roles_count,
                    "user_role_assignments": new_users_count,
                    "company_role_assignments": new_members_count
                },
                "migration_needed": old_users_count > 0 or old_members_count > 0
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting migration status: {str(e)}")
