from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.core.database import get_db_session
from app.models.user_role_model import UserRole, UserRoleAssignment
from app.schemas.user_role_schema import (
    UserRoleCreate, UserRoleUpdate, UserRoleAssignmentCreate,
    DEFAULT_PLATFORM_ROLES, PlatformPermissions
)
from datetime import datetime
from app.utils.activity_logger import audit, ActivityActor

class UserRoleService:
    """Service for platform-level role management"""

    async def create_default_presets(self) -> List[UserRole]:
        """Create default platform role presets"""
        try:
            session = get_db_session()
            created_roles = []

            for preset_key, preset_data in DEFAULT_PLATFORM_ROLES.items():
                # Check if preset already exists
                result = await session.execute(
                    select(UserRole).where(UserRole.name == preset_data["name"])
                )
                existing_role = result.scalar_one_or_none()

                if not existing_role:
                    role = UserRole(
                        name=preset_data["name"],
                        description=preset_data["description"],
                        permissions=preset_data["permissions"],
                        is_preset=preset_data["is_preset"],
                        is_system=preset_data["is_system"]
                    )
                    session.add(role)
                    created_roles.append(role)

            await session.commit()

            # Refresh all created roles
            for role in created_roles:
                await session.refresh(role)

            return created_roles
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating default presets: {str(e)}")

    @audit(
        action="CREATE",
        entity_type="platform_role",
        details=lambda result, _a, kw: f"Rôle plateforme {kw['role_data'].name} créé",
        entity_id=lambda result, _a, _kw: result.id if result else None,
        extra=lambda _r, _a, kw: {"payload": kw["role_data"].model_dump(exclude_none=True)},
    )
    async def create_role(self, role_data: UserRoleCreate, actor: ActivityActor | None = None) -> UserRole:
        """Create a new platform role"""
        try:
            session = get_db_session()
            # Check if role name already exists
            result = await session.execute(
                select(UserRole).where(UserRole.name == role_data.name)
            )
            existing_role = result.scalar_one_or_none()

            if existing_role:
                raise HTTPException(status_code=400, detail="Role name already exists")

            role = UserRole(
                name=role_data.name,
                description=role_data.description,
                permissions=role_data.permissions,
                is_preset=role_data.is_preset,
                is_system=role_data.is_system
            )

            session.add(role)
            await session.commit()
            await session.refresh(role)

            return role
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating role: {str(e)}")

    async def get_all_roles(self) -> List[UserRole]:
        """Get all platform roles"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRole).order_by(UserRole.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving roles: {str(e)}")

    async def get_role_by_id(self, role_id: str) -> Optional[UserRole]:
        """Get a platform role by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRole).where(UserRole.id == role_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving role: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="platform_role",
        details=lambda _r, _a, kw: f"Rôle plateforme {kw['role_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["role_id"],
        extra=lambda _r, _a, kw: kw["role_data"].model_dump(exclude_unset=True),
    )
    async def update_role(self, role_id: str, role_data: UserRoleUpdate, actor: ActivityActor | None = None) -> UserRole:
        """Update a platform role"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserRole).where(UserRole.id == role_id)
            )
            role = result.scalar_one_or_none()

            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot modify system roles")

            # Update fields
            update_data = role_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            await session.execute(
                update(UserRole).where(UserRole.id == role_id).values(**update_data)
            )
            await session.commit()

            # Return updated role
            result = await session.execute(
                select(UserRole).where(UserRole.id == role_id)
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="platform_role",
        details=lambda _r, _a, kw: f"Rôle plateforme {kw['role_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["role_id"],
    )
    async def delete_role(self, role_id: str, actor: ActivityActor | None = None) -> bool:
        """Delete a platform role"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserRole).where(UserRole.id == role_id)
            )
            role = result.scalar_one_or_none()

            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot delete system roles")

            # Check if role has assignments
            result = await session.execute(
                select(UserRoleAssignment).where(UserRoleAssignment.role_id == role_id)
            )
            assignments = result.scalars().all()

            if assignments:
                raise HTTPException(status_code=400, detail="Cannot delete role with active assignments")

            await session.execute(
                delete(UserRole).where(UserRole.id == role_id)
            )
            await session.commit()

            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting role: {str(e)}")

    @audit(
        action="ASSIGN",
        entity_type="platform_role_assignment",
        details=lambda result, _a, kw: f"Rôle {kw['role_id']} attribué à l’utilisateur {kw['user_id']}",
        entity_id=lambda result, _a, _kw: result.id if result else None,
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"]},
    )
    async def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str, actor: ActivityActor | None = None) -> UserRoleAssignment:
        """Assign a platform role to a user"""
        try:
            session = get_db_session()
            # Check if assignment already exists
            result = await session.execute(
                select(UserRoleAssignment).where(
                    and_(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.role_id == role_id
                    )
                )
            )
            existing_assignment = result.scalar_one_or_none()

            if existing_assignment:
                raise HTTPException(status_code=400, detail="User already has this role")

            # Create assignment
            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by
            )

            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            return assignment
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error assigning role: {str(e)}")

    @audit(
        action="REVOKE",
        entity_type="platform_role_assignment",
        details=lambda _r, _a, kw: f"Rôle {kw['role_id']} retiré de l’utilisateur {kw['user_id']}",
        entity_id=lambda _r, _a, kw: f"{kw['user_id']}:{kw['role_id']}",
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"]},
    )
    async def remove_role_from_user(self, user_id: str, role_id: str, actor: ActivityActor | None = None) -> bool:
        """Remove a platform role from a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRoleAssignment).where(
                    and_(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.role_id == role_id
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                raise HTTPException(status_code=404, detail="Role assignment not found")

            await session.execute(
                delete(UserRoleAssignment).where(UserRoleAssignment.id == assignment.id)
            )
            await session.commit()

            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error removing role: {str(e)}")

    async def get_user_roles(self, user_id: str) -> List[UserRole]:
        """Get all roles assigned to a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRole)
                .join(UserRoleAssignment)
                .where(UserRoleAssignment.user_id == user_id)
                .order_by(UserRole.name)
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user roles: {str(e)}")

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        try:
            roles = await self.get_user_roles(user_id)
            permissions = set()

            for role in roles:
                permissions.update(role.permissions)

            return list(permissions)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user permissions: {str(e)}")

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission"""
        try:
            permissions = await self.get_user_permissions(user_id)
            return permission in permissions
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error checking permission: {str(e)}")
