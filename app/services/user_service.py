import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func, update, delete, and_
from app.core.database import get_db_session
from app.models.user_model import User as UserModel, UserRoleModel, UserRoleAssignmentModel
from app.models.company_model import Company as CompanyModel, CompanyMember as CompanyMemberModel
from app.models.sync_model import SyncLog
from app.schemas.user_schema import User, UserInternal, UserUpdate
from app.schemas.user_role_schema import (
    UserRoleCreate, UserRoleUpdate, UserRoleAssignmentCreate,
    DEFAULT_PLATFORM_ROLES, PlatformPermissions
)
from app.utils.activity_logger import audit, ActivityActor

class UserService:
    """Service for user-related database operations"""

    async def _with_platform_roles(self, users: List[UserModel]) -> List[User]:
        if not users:
            return []
        session = get_db_session()
        user_ids = [user.id for user in users]
        role_rows = await session.execute(
            select(UserRoleAssignmentModel.user_id, UserRoleModel.name, UserRoleModel.permissions)
            .join(UserRoleModel, UserRoleAssignmentModel.role_id == UserRoleModel.id)
            .where(UserRoleAssignmentModel.user_id.in_(user_ids))
        )
        roles: Dict[str, List[str]] = {user_id: [] for user_id in user_ids}
        permissions: Dict[str, set[str]] = {user_id: set() for user_id in user_ids}
        for user_id, role_name, role_permissions in role_rows:
            roles[user_id].append(role_name)
            permissions[user_id].update(role_permissions or [])
        member_rows = await session.execute(select(CompanyMemberModel.user_id, CompanyMemberModel.company_id).where(
            CompanyMemberModel.user_id.in_(user_ids), CompanyMemberModel.is_active == True,
        ))
        companies: Dict[str, set[str]] = {user_id: set() for user_id in user_ids}
        for user_id, company_id in member_rows:
            companies[user_id].add(company_id)
        owner_rows = await session.execute(select(CompanyModel.owner_id, CompanyModel.id).where(
            CompanyModel.owner_id.in_(user_ids), CompanyModel.is_active == True,
        ))
        for user_id, company_id in owner_rows:
            companies[user_id].add(company_id)
        return [User.model_validate({
            **user.to_dict(),
            "platform_roles": roles[user.id],
            "platform_permissions": sorted(permissions[user.id]),
            "companies": sorted(companies[user.id]),
        }) for user in users]
    
    async def get_all_users(self, limit: int = 100) -> List[User]:
        """Get users, including deactivated accounts, for the admin list."""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).order_by(UserModel.created_at.desc()).limit(limit)
            )
            users = result.scalars().all()
            return await self._with_platform_roles(users)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")
    
    async def get_user_by_id(self, user_id: str, include_inactive: bool = False) -> Optional[User]:
        """Get a user by ID"""
        try:
            session = get_db_session()
            query = select(UserModel).where(UserModel.id == user_id)
            if not include_inactive:
                query = query.where(UserModel.is_active == True)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return (await self._with_platform_roles([user]))[0] if user else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[UserInternal]:
        """Get a user by email (with hashed password for authentication)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.email == email, UserModel.is_active == True)
            )
            user = result.scalar_one_or_none()
            return UserInternal(**user.to_dict(include_password=True)) if user else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user by email: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user and return the ID"""
        session = get_db_session()
        try:
            user = UserModel(
                name=user_data['name'],
                email=user_data['email'],
                phone_number=user_data.get('phone_number'),
                hashed_password=user_data['hashed_password']
            )
            session.add(user)
            await session.flush()

            preset = DEFAULT_PLATFORM_ROLES["regular_user"]
            role = await session.scalar(select(UserRoleModel).where(UserRoleModel.name == preset["name"]))
            if role is None:
                role = UserRoleModel(**preset)
                session.add(role)
                await session.flush()
            session.add(UserRoleAssignmentModel(user_id=user.id, role_id=role.id))
            
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
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    
    async def update_user(self, user_id: str, user_data: UserUpdate | Dict[str, Any]) -> User:
        """Update a user by ID and return the updated user"""
        try:
            session = get_db_session()
            # Get existing user
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Convert schema to dict, excluding unset fields
            if isinstance(user_data, dict):
                update_dict = user_data
            else:
                update_dict = user_data.model_dump(exclude_unset=True)
            
            # Update fields
            if 'name' in update_dict:
                user.name = update_dict['name']
            if 'email' in update_dict:
                user.email = update_dict['email']
            if 'phone_number' in update_dict:
                user.phone_number = update_dict['phone_number']
            if 'hashed_password' in update_dict:
                user.hashed_password = update_dict['hashed_password']
            if 'current_company_id' in update_dict:
                user.current_company_id = update_dict['current_company_id']
            
            user.updated_at = datetime.now()
            await session.commit()
            await session.refresh(user)
            
            # Log sync operation
            sync_log = SyncLog(
                operation='UPDATE',
                table_name='users',
                record_id=user.id,
                data=json.dumps(user.to_dict())
            )
            session.add(sync_log)
            await session.commit()
            
            return User(**user.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID (soft delete)"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    async def get_users_count(self) -> int:
        """Get the count of active users"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(func.count(UserModel.id)).where(UserModel.is_active == True)
            )
            return result.scalar()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")

    async def get_user_stats(self) -> Dict[str, int]:
        session = get_db_session()
        total = await session.scalar(select(func.count(UserModel.id)))
        recent = await session.scalar(select(func.count(UserModel.id)).where(
            UserModel.created_at >= datetime.utcnow() - timedelta(days=1)
        ))
        return {"total": total or 0, "recent24h": recent or 0}

    async def set_user_active(self, user_id: str, is_active: bool) -> User:
        session = get_db_session()
        user = await session.get(UserModel, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        await session.commit()
        return await self.get_user_by_id(user_id, include_inactive=True)

    async def set_platform_role(self, user_id: str, role_name: str, assigned_by: str) -> User:
        session = get_db_session()
        user = await session.get(UserModel, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        preset = next((item for item in DEFAULT_PLATFORM_ROLES.values() if item["name"] == role_name), None)
        if preset is None:
            raise HTTPException(status_code=400, detail="Unsupported platform role")
        role = await session.scalar(select(UserRoleModel).where(UserRoleModel.name == role_name))
        if role is None:
            role = UserRoleModel(
                name=preset["name"], description=preset["description"],
                permissions=preset["permissions"], is_preset=True, is_system=True,
            )
            session.add(role)
            await session.flush()
        await session.execute(delete(UserRoleAssignmentModel).where(UserRoleAssignmentModel.user_id == user_id))
        session.add(UserRoleAssignmentModel(user_id=user_id, role_id=role.id, assigned_by=assigned_by))
        await session.commit()
        return await self.get_user_by_id(user_id, include_inactive=True)
    
    async def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.last_login = datetime.now()
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating last login: {str(e)}")
    
    async def export_data(self) -> List[Dict[str, Any]]:
        """Export all data for synchronization"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserModel).where(UserModel.is_active == True)
            )
            users = result.scalars().all()
            return [user.to_dict() for user in users]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")
    
    async def sync_data(self, data: List[Dict[str, Any]]) -> bool:
        """Sync data from external source"""
        try:
            session = get_db_session()
            for item in data:
                # Check if user exists
                result = await session.execute(
                    select(UserModel).where(UserModel.email == item['email'])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    existing_user.name = item['name']
                    existing_user.phone_number = item.get('phone_number')
                    existing_user.updated_at = datetime.now()
                else:
                    # Create new user
                    new_user = UserModel(
                        name=item['name'],
                        email=item['email'],
                        phone_number=item.get('phone_number')
                    )
                    session.add(new_user)
            
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error syncing data: {str(e)}")

    # ========== Platform Role Methods ==========
    
    async def create_default_role_presets(self) -> List[UserRoleModel]:
        """Create default platform role presets"""
        try:
            session = get_db_session()
            created_roles = []

            for preset_key, preset_data in DEFAULT_PLATFORM_ROLES.items():
                # Check if preset already exists
                result = await session.execute(
                    select(UserRoleModel).where(UserRoleModel.name == preset_data["name"])
                )
                existing_role = result.scalar_one_or_none()

                if not existing_role:
                    role = UserRoleModel(
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
    async def create_role(self, role_data: UserRoleCreate, actor: ActivityActor | None = None) -> UserRoleModel:
        """Create a new platform role"""
        try:
            session = get_db_session()
            # Check if role name already exists
            result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.name == role_data.name)
            )
            existing_role = result.scalar_one_or_none()

            if existing_role:
                raise HTTPException(status_code=400, detail="Role name already exists")

            role = UserRoleModel(
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

    async def get_all_roles(self) -> List[UserRoleModel]:
        """Get all platform roles"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRoleModel).order_by(UserRoleModel.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving roles: {str(e)}")

    async def get_role_by_id(self, role_id: str) -> Optional[UserRoleModel]:
        """Get a platform role by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.id == role_id)
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
    async def update_role(self, role_id: str, role_data: UserRoleUpdate, actor: ActivityActor | None = None) -> UserRoleModel:
        """Update a platform role"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.id == role_id)
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
                update(UserRoleModel).where(UserRoleModel.id == role_id).values(**update_data)
            )
            await session.commit()

            # Return updated role
            result = await session.execute(
                select(UserRoleModel).where(UserRoleModel.id == role_id)
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
                select(UserRoleModel).where(UserRoleModel.id == role_id)
            )
            role = result.scalar_one_or_none()

            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot delete system roles")

            # Check if role has assignments
            result = await session.execute(
                select(UserRoleAssignmentModel).where(UserRoleAssignmentModel.role_id == role_id)
            )
            assignments = result.scalars().all()

            if assignments:
                raise HTTPException(status_code=400, detail="Cannot delete role with active assignments")

            await session.execute(
                delete(UserRoleModel).where(UserRoleModel.id == role_id)
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
        details=lambda result, _a, kw: f"Rôle {kw['role_id']} attribué à l'utilisateur {kw['user_id']}",
        entity_id=lambda result, _a, _kw: result.id if result else None,
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"]},
    )
    async def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str, actor: ActivityActor | None = None) -> UserRoleAssignmentModel:
        """Assign a platform role to a user"""
        try:
            session = get_db_session()
            # Check if assignment already exists
            result = await session.execute(
                select(UserRoleAssignmentModel).where(
                    and_(
                        UserRoleAssignmentModel.user_id == user_id,
                        UserRoleAssignmentModel.role_id == role_id
                    )
                )
            )
            existing_assignment = result.scalar_one_or_none()

            if existing_assignment:
                raise HTTPException(status_code=400, detail="User already has this role")

            # Create assignment
            assignment = UserRoleAssignmentModel(
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
        details=lambda _r, _a, kw: f"Rôle {kw['role_id']} retiré de l'utilisateur {kw['user_id']}",
        entity_id=lambda _r, _a, kw: f"{kw['user_id']}:{kw['role_id']}",
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"]},
    )
    async def remove_role_from_user(self, user_id: str, role_id: str, actor: ActivityActor | None = None) -> bool:
        """Remove a platform role from a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRoleAssignmentModel).where(
                    and_(
                        UserRoleAssignmentModel.user_id == user_id,
                        UserRoleAssignmentModel.role_id == role_id
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                raise HTTPException(status_code=404, detail="Role assignment not found")

            await session.execute(
                delete(UserRoleAssignmentModel).where(UserRoleAssignmentModel.id == assignment.id)
            )
            await session.commit()

            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error removing role: {str(e)}")

    async def get_user_roles(self, user_id: str) -> List[UserRoleModel]:
        """Get all roles assigned to a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserRoleModel)
                .join(UserRoleAssignmentModel)
                .where(UserRoleAssignmentModel.user_id == user_id)
                .order_by(UserRoleModel.name)
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
