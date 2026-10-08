"""Idempotent migration from optional legacy role columns to role assignments."""

from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import inspect, select, text

from app.core.database import get_db_session
from app.models.company_model import (
    Company, CompanyMember, UserCompanyRoleAssignmentModel, UserCompanyRoleModel,
)
from app.models.user_model import User, UserRoleAssignmentModel, UserRoleModel
from app.services.company_service import CompanyService
from app.services.user_service import UserService


class MigrationService:
    """Assign missing roles without changing any existing assignments."""

    @staticmethod
    async def _legacy_roles(session, table_name: str, key_columns: tuple[str, ...]) -> dict:
        # Old `role` columns may still exist in deployed databases, but are
        # deliberately absent from the current ORM models.
        columns = await session.run_sync(
            lambda sync_session: {
                column["name"] for column in inspect(sync_session.connection()).get_columns(table_name)
            }
        )
        if "role" not in columns:
            return {}
        selected = ", ".join((*key_columns, "role"))
        rows = await session.execute(text(f"SELECT {selected} FROM {table_name}"))
        return {
            tuple(row[index] for index in range(len(key_columns))): row[-1]
            for row in rows if row[-1]
        }

    async def migrate_user_roles(self) -> Dict[str, Any]:
        session = get_db_session()
        await UserService().create_default_role_presets()
        legacy = await self._legacy_roles(session, "users", ("id",))
        role_rows = await session.execute(select(UserRoleModel))
        roles = {role.name: role for role in role_rows.scalars()}
        existing_rows = await session.execute(select(UserRoleAssignmentModel.user_id))
        assigned_ids = set(existing_rows.scalars())
        user_rows = await session.execute(select(User.id))
        user_ids = list(user_rows.scalars())

        migrated = 0
        for user_id in user_ids:
            if user_id in assigned_ids:
                continue
            old_role = str(legacy.get((user_id,), "")).lower()
            role_name = "Platform Administrator" if old_role in {"admin", "administrator"} else "Regular User"
            session.add(UserRoleAssignmentModel(user_id=user_id, role_id=roles[role_name].id))
            migrated += 1
        await session.commit()
        return {
            "migrated_users": migrated,
            "skipped_users": len(user_ids) - migrated,
            "message": f"Successfully migrated {migrated} users to new role system",
        }

    async def migrate_company_member_roles(self) -> Dict[str, Any]:
        session = get_db_session()
        legacy = await self._legacy_roles(session, "company_members", ("user_id", "company_id"))
        company_rows = await session.execute(select(Company.id, Company.owner_id))
        owners = dict(company_rows.all())
        member_rows = await session.execute(select(CompanyMember.user_id, CompanyMember.company_id))
        members = set(member_rows)
        # Some older company records did not create an owner membership row.
        members.update((owner_id, company_id) for company_id, owner_id in owners.items())
        assignment_rows = await session.execute(
            select(UserCompanyRoleAssignmentModel.user_id, UserCompanyRoleAssignmentModel.company_id)
            .join(UserCompanyRoleModel, UserCompanyRoleModel.id == UserCompanyRoleAssignmentModel.role_id)
            .where(UserCompanyRoleModel.company_id == UserCompanyRoleAssignmentModel.company_id)
        )
        assigned = set(assignment_rows)
        owner_assignment_rows = await session.execute(
            select(UserCompanyRoleAssignmentModel.user_id, UserCompanyRoleAssignmentModel.company_id)
            .join(UserCompanyRoleModel, UserCompanyRoleModel.id == UserCompanyRoleAssignmentModel.role_id)
            .where(
                UserCompanyRoleModel.name == "Propriétaire",
                UserCompanyRoleModel.company_id == UserCompanyRoleAssignmentModel.company_id,
            )
        )
        owners_with_owner_role = set(owner_assignment_rows)
        role_mapping = {
            "owner": "Propriétaire", "admin": "Administrateur",
            "manager": "Gestionnaire", "operator": "Opérateur",
            "comptable": "Comptable", "viewer": "Observateur",
        }

        migrated = 0
        processed_companies = set()
        for user_id, company_id in sorted(members):
            is_owner = owners.get(company_id) == user_id
            if (user_id, company_id) in assigned and (not is_owner or (user_id, company_id) in owners_with_owner_role):
                continue
            if company_id not in processed_companies:
                await CompanyService().create_company_default_presets(company_id)
                processed_companies.add(company_id)
            if is_owner:
                role_name = "Propriétaire"
            else:
                role_name = role_mapping.get(str(legacy.get((user_id, company_id), "")).lower(), "Opérateur")
                if role_name == "Propriétaire":
                    role_name = "Opérateur"
            role = await session.scalar(select(UserCompanyRoleModel).where(
                UserCompanyRoleModel.company_id == company_id,
                UserCompanyRoleModel.name == role_name,
            ))
            if role is None:
                raise HTTPException(status_code=500, detail=f"Missing company role preset: {role_name}")
            session.add(UserCompanyRoleAssignmentModel(
                user_id=user_id, company_id=company_id, role_id=role.id,
            ))
            migrated += 1
        await session.commit()
        return {
            "migrated_members": migrated,
            "skipped_members": len(members) - migrated,
            "companies_processed": len(processed_companies),
            "message": f"Successfully migrated {migrated} company members to new role system",
        }

    async def run_full_migration(self) -> Dict[str, Any]:
        platform_roles = await UserService().create_default_role_presets()
        user_result = await self.migrate_user_roles()
        company_result = await self.migrate_company_member_roles()
        return {
            "platform_roles_created": len(platform_roles),
            "user_migration": user_result,
            "company_migration": company_result,
            "message": "Full migration completed successfully",
        }

    async def get_migration_status(self) -> Dict[str, Any]:
        session = get_db_session()
        old_users = await self._legacy_roles(session, "users", ("id",))
        old_members = await self._legacy_roles(session, "company_members", ("user_id", "company_id"))
        user_rows = await session.execute(select(User.id))
        user_ids = set(user_rows.scalars())
        member_rows = await session.execute(select(CompanyMember.user_id, CompanyMember.company_id))
        member_keys = set(member_rows)
        owner_rows = await session.execute(select(Company.owner_id, Company.id))
        owner_keys = set(owner_rows)
        assigned_user_rows = await session.execute(select(UserRoleAssignmentModel.user_id))
        assigned_user_list = list(assigned_user_rows.scalars())
        assigned_user_ids = set(assigned_user_list)
        assigned_member_rows = await session.execute(
            select(UserCompanyRoleAssignmentModel.user_id, UserCompanyRoleAssignmentModel.company_id)
            .join(UserCompanyRoleModel, UserCompanyRoleModel.id == UserCompanyRoleAssignmentModel.role_id)
            .where(UserCompanyRoleModel.company_id == UserCompanyRoleAssignmentModel.company_id)
        )
        assigned_member_list = list(assigned_member_rows)
        assigned_member_keys = set(assigned_member_list)
        owner_role_rows = await session.execute(
            select(UserCompanyRoleAssignmentModel.user_id, UserCompanyRoleAssignmentModel.company_id)
            .join(UserCompanyRoleModel, UserCompanyRoleModel.id == UserCompanyRoleAssignmentModel.role_id)
            .where(
                UserCompanyRoleModel.name == "Propriétaire",
                UserCompanyRoleModel.company_id == UserCompanyRoleAssignmentModel.company_id,
            )
        )
        owners_with_owner_role = set(owner_role_rows)
        platform_role_rows = await session.execute(select(UserRoleModel.id))
        company_role_rows = await session.execute(select(UserCompanyRoleModel.id))
        return {
            "old_system": {
                "users_with_old_roles": len(old_users),
                "company_members_with_old_roles": len(old_members),
            },
            "new_system": {
                "platform_roles": len(platform_role_rows.all()),
                "company_roles": len(company_role_rows.all()),
                "user_role_assignments": len(assigned_user_list),
                "company_role_assignments": len(assigned_member_list),
            },
            "users_without_new_roles": len(user_ids - assigned_user_ids),
            "company_members_without_new_roles": len(member_keys - assigned_member_keys),
            "owners_without_new_roles": len(owner_keys - owners_with_owner_role),
            "migration_needed": bool(
                user_ids - assigned_user_ids
                or member_keys - assigned_member_keys
                or owner_keys - owners_with_owner_role
            ),
        }
