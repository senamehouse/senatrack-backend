from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.core.database import get_db_session
from app.models.company_role_model import UserCompanyRole, UserCompanyRoleAssignment
from app.schemas.company_role_schema import (
    UserCompanyRoleCreate, UserCompanyRoleUpdate, UserCompanyRoleAssignmentCreate,
    DEFAULT_COMPANY_ROLES, CompanyPermissions, CompanyPermissionCheckResponse,
    CompanyRoleDeleteResponse, CompanyRoleAssignResponse, CompanyRoleRemoveResponse
)
from datetime import datetime

class CompanyRoleService:
    """Service for company-specific role management"""

    async def create_default_presets(self, company_id: str) -> List[UserCompanyRole]:
        """Create default company role presets"""
        try:
            session = get_db_session()
            created_roles = []

            for preset_key, preset_data in DEFAULT_COMPANY_ROLES.items():
                # Check if preset already exists for this company
                result = await session.execute(
                    select(UserCompanyRole).where(
                        and_(
                            UserCompanyRole.company_id == company_id,
                            UserCompanyRole.name == preset_data["name"]
                        )
                    )
                )
                existing_role = result.scalar_one_or_none()

                if not existing_role:
                    role = UserCompanyRole(
                        company_id=company_id,
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

    async def create_role(self, company_id: str, role_data: UserCompanyRoleCreate) -> UserCompanyRole:
        """Create a new company role"""
        try:
            session = get_db_session()
            # Check if role name already exists for this company
            result = await session.execute(
                select(UserCompanyRole).where(
                    and_(
                        UserCompanyRole.company_id == company_id,
                        UserCompanyRole.name == role_data.name
                    )
                )
            )
            existing_role = result.scalar_one_or_none()

            if existing_role:
                raise HTTPException(status_code=400, detail="Role name already exists for this company")

            role = UserCompanyRole(
                company_id=company_id,
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

    async def get_company_preset_roles(self, company_id: str) -> List[UserCompanyRole]:
        """Get preset roles for a company"""
        roles = await self.get_company_roles(company_id)
        return [role for role in roles if role.is_preset]

    async def get_company_roles(self, company_id: str) -> List[UserCompanyRole]:
        """Get all roles for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRole).where(UserCompanyRole.company_id == company_id)
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company roles: {str(e)}")

    async def get_role_by_id(self, company_id: str, role_id: str) -> Optional[UserCompanyRole]:
        """Get a company role by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRole).where(
                    and_(
                        UserCompanyRole.id == role_id,
                        UserCompanyRole.company_id == company_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving role: {str(e)}")

    async def update_role(self, company_id: str, role_id: str, role_data: UserCompanyRoleUpdate) -> UserCompanyRole:
        """Update a company role"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserCompanyRole).where(
                    and_(
                        UserCompanyRole.id == role_id,
                        UserCompanyRole.company_id == company_id
                    )
                )
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
                update(UserCompanyRole)
                .where(
                    and_(
                        UserCompanyRole.id == role_id,
                        UserCompanyRole.company_id == company_id
                    )
                )
                .values(**update_data)
            )
            await session.commit()

            # Return updated role
            result = await session.execute(
                select(UserCompanyRole).where(UserCompanyRole.id == role_id)
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")

    async def delete_role(self, company_id: str, role_id: str) -> CompanyRoleDeleteResponse:
        """Delete a company role and return response"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserCompanyRole).where(
                    and_(
                        UserCompanyRole.id == role_id,
                        UserCompanyRole.company_id == company_id
                    )
                )
            )
            role = result.scalar_one_or_none()

            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot delete system roles")

            # Check if role has assignments
            result = await session.execute(
                select(UserCompanyRoleAssignment).where(
                    and_(
                        UserCompanyRoleAssignment.role_id == role_id,
                        UserCompanyRoleAssignment.company_id == company_id
                    )
                )
            )
            assignments = result.scalars().all()

            if assignments:
                raise HTTPException(status_code=400, detail="Cannot delete role with active assignments")

            await session.execute(
                delete(UserCompanyRole).where(
                    and_(
                        UserCompanyRole.id == role_id,
                        UserCompanyRole.company_id == company_id
                    )
                )
            )
            await session.commit()

            return CompanyRoleDeleteResponse(message="Role deleted successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting role: {str(e)}")

    async def assign_role_to_user(self, user_id: str, company_id: str, role_id: str, assigned_by: str) -> CompanyRoleAssignResponse:
        """Assign a company role to a user and return response"""
        try:
            session = get_db_session()
            # Check if assignment already exists
            result = await session.execute(
                select(UserCompanyRoleAssignment).where(
                    and_(
                        UserCompanyRoleAssignment.user_id == user_id,
                        UserCompanyRoleAssignment.company_id == company_id,
                        UserCompanyRoleAssignment.role_id == role_id
                    )
                )
            )
            existing_assignment = result.scalar_one_or_none()

            if existing_assignment:
                raise HTTPException(status_code=400, detail="User already has this role in this company")

            # Create assignment
            assignment = UserCompanyRoleAssignment(
                user_id=user_id,
                company_id=company_id,
                role_id=role_id,
                assigned_by=assigned_by
            )

            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)

            return CompanyRoleAssignResponse(
                message="Role assigned successfully",
                assignment_id=assignment.id
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error assigning role: {str(e)}")

    async def remove_role_from_user(self, user_id: str, company_id: str, role_id: str) -> CompanyRoleRemoveResponse:
        """Remove a company role from a user and return response"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRoleAssignment).where(
                    and_(
                        UserCompanyRoleAssignment.user_id == user_id,
                        UserCompanyRoleAssignment.company_id == company_id,
                        UserCompanyRoleAssignment.role_id == role_id
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                raise HTTPException(status_code=404, detail="Role assignment not found")

            await session.execute(
                delete(UserCompanyRoleAssignment).where(UserCompanyRoleAssignment.id == assignment.id)
            )
            await session.commit()

            return CompanyRoleRemoveResponse(message="Role removed successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error removing role: {str(e)}")

    async def get_user_company_roles(self, user_id: str, company_id: str) -> List[UserCompanyRole]:
        """Get all company roles assigned to a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRole)
                .join(UserCompanyRoleAssignment)
                .where(
                    and_(
                        UserCompanyRoleAssignment.user_id == user_id,
                        UserCompanyRoleAssignment.company_id == company_id
                    )
                )
                .order_by(UserCompanyRole.name)
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user company roles: {str(e)}")

    async def get_user_company_permissions(self, user_id: str, company_id: str) -> List[str]:
        """Get all company permissions for a user"""
        try:
            roles = await self.get_user_company_roles(user_id, company_id)
            permissions = set()

            for role in roles:
                permissions.update(role.permissions)

            return list(permissions)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user company permissions: {str(e)}")

    async def check_permission(self, user_id: str, company_id: str, permission: str) -> bool:
        """Check if a user has a specific company permission"""
        try:
            permissions = await self.get_user_company_permissions(user_id, company_id)
            return permission in permissions
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error checking permission: {str(e)}")

    async def check_permission_with_response(self, user_id: str, company_id: str, permission: str) -> CompanyPermissionCheckResponse:
        """Check if a user has a specific company permission and return response"""
        try:
            has_permission = await self.check_permission(user_id, company_id, permission)
            user_roles = await self.get_user_company_roles(user_id, company_id)
            role_names = [role.name for role in user_roles]

            return CompanyPermissionCheckResponse(
                has_permission=has_permission,
                user_id=user_id,
                company_id=company_id,
                permission=permission,
                roles=role_names
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error checking permission: {str(e)}")
