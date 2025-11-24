from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.core.database import get_db_session
from app.models.company_model import Company as CompanyModel, CompanyMember as CompanyMemberModel, UserCompanyRoleModel, UserCompanyRoleAssignmentModel
from app.models.user_model import User as UserModel
from app.schemas.company_schema import (
    CompanyCreate, CompanyUpdate, CompanyMemberCreate,
    CompanyStats, CompanySettings, CompanySubscription, CompanyMember, Company, CompanyMemberResponse
)
from app.schemas.user_schema import User
from app.services.user_service import UserService
from app.schemas.company_role_schema import (
    UserCompanyRoleCreate, UserCompanyRoleUpdate, UserCompanyRoleAssignmentCreate,
    DEFAULT_COMPANY_ROLES, CompanyPermissions, CompanyPermissionCheckResponse,
    CompanyRoleDeleteResponse, CompanyRoleAssignResponse, CompanyRoleRemoveResponse
)
from app.utils.activity_logger import audit, ActivityActor
import secrets
from datetime import datetime, timedelta

class CompanyService:
    """Service for company-related operations"""

    def __init__(self):
        self.user_service = UserService()

    def _model_to_schema(self, company_model: CompanyModel) -> Company:
        """Convert CompanyModel to Company schema"""
        # Get base company dict
        company_dict = company_model.to_dict()

        # Convert members to schemas
        members = []
        if hasattr(company_model, 'members') and company_model.members:
            for member_model in company_model.members:
                member_dict = member_model.to_dict()
                # Add company_roles and company_permissions (default to empty lists)
                member_dict['company_roles'] = []
                member_dict['company_permissions'] = []
                members.append(CompanyMember(**member_dict))

        # Handle subscription conversion
        subscription = company_dict.get('subscription')

        # Build company schema dict
        company_schema_dict = {
            **company_dict,
            'members': members,
            'subscription': subscription
        }

        return Company(**company_schema_dict)

    async def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company"""
        try:
            session = get_db_session()
            # Create company
            company_dict = company_data.model_dump(by_alias=False)

            # Set default settings
            default_settings = {
                "modules": {
                    "clients": True,
                    "products": True,
                    "invoices": True,
                    "inventory": True,
                    "accounting": False,
                    "hr": False,
                }
            }

            # Set default subscription (14-day free trial)
            now = datetime.utcnow()
            access_end_date = now + timedelta(days=14)
            default_subscription = CompanySubscription(
                plan="free_trial",
                access_end_date=access_end_date.isoformat(),
            )

            company_dict.update({
                "settings": default_settings,
                "subscription": default_subscription.model_dump(by_alias=True),
                "created_at": now,
                "updated_at": now
            })

            company = CompanyModel(**company_dict)
            session.add(company)
            await session.commit()
            await session.refresh(company)

            # Ensure company member record exists for owner
            owner_member = CompanyMemberModel(
                company_id=company.id,
                user_id=company.owner_id,
                invited_by=company.owner_id,
                invited_at=now,
                joined_at=now,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            session.add(owner_member)
            await session.commit()

            # Ensure the creator is scoped to this new company
            await self.user_service.update_user(
                company.owner_id,
                {
                    "current_company_id": company.id,
                },
            )

            # Create default company role presets and assign the Owner preset
            try:
                await self.create_company_default_presets(company.id)
                result_role = await session.execute(
                    select(UserCompanyRoleModel).where(
                        and_(
                            UserCompanyRoleModel.company_id == company.id,
                            UserCompanyRoleModel.name == "Propriétaire"
                        )
                    )
                )
                owner_role = result_role.scalar_one_or_none()
                if owner_role:
                    await self.assign_company_role_to_user(
                        user_id=company.owner_id,
                        company_id=company.id,
                        role_id=owner_role.id,
                        assigned_by=company.owner_id,
                    )
            except Exception:
                pass

            # Get the company with members relationship loaded
            result = await session.execute(
                select(CompanyModel)
                .options(selectinload(CompanyModel.members))
                .where(CompanyModel.id == company.id)
            )
            company_with_members = result.scalar_one()

            # Convert to schema
            return self._model_to_schema(company_with_members)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")

    async def get_company_by_id(self, company_id: str) -> Optional[Company]:
        """Get a company by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyModel)
                .options(selectinload(CompanyModel.members))
                .where(CompanyModel.id == company_id, CompanyModel.is_active == True)
            )
            company = result.scalar_one_or_none()
            if not company:
                return None
            return self._model_to_schema(company)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company: {str(e)}")

    async def get_user_companies(self, user_id: str) -> List[Company]:
        """Get all companies for a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyModel)
                .options(selectinload(CompanyModel.members))
                .join(CompanyMemberModel)
                .where(
                    and_(
                        CompanyMemberModel.user_id == user_id,
                        CompanyMemberModel.is_active == True,
                        CompanyModel.is_active == True
                    )
                )
                .order_by(CompanyModel.created_at.desc())
            )
            companies = result.scalars().all()
            return [self._model_to_schema(company) for company in companies]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user companies: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="company",
        details=lambda _r, _a, kw: f"Paramètres de l’entreprise {kw['company_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["company_id"],
        extra=lambda _r, _a, kw: kw["company_data"].model_dump(exclude_unset=True),
    )
    async def update_company(self, company_id: str, company_data: CompanyUpdate, actor: ActivityActor | None = None) -> Company:
        """Update a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(CompanyModel).where(CompanyModel.id == company_id, CompanyModel.is_active == True)
            )
            company = result.scalar_one_or_none()

            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            update_data = company_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            await session.execute(
                update(CompanyModel).where(CompanyModel.id == company_id).values(**update_data)
            )
            await session.commit()

            result = await session.execute(
                select(CompanyModel)
                .options(selectinload(CompanyModel.members))
                .where(CompanyModel.id == company_id)
            )
            updated_company = result.scalar_one()
            return self._model_to_schema(updated_company)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="company",
        details=lambda _r, _a, kw: f"Entreprise {kw['company_id']} supprimée",
        entity_id=lambda _r, _a, kw: kw["company_id"],
    )
    async def delete_company(self, company_id: str, actor: ActivityActor | None = None) -> bool:
        """Delete a company (soft delete)"""
        try:
            session = get_db_session()
            await session.execute(
                update(CompanyModel).where(CompanyModel.id == company_id).values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")

    async def add_company_member(self, company_id: str, member_data: CompanyMemberCreate) -> CompanyMemberResponse:
        """Add a member to a company and return response"""
        try:
            session = get_db_session()
            company = await self.get_company_by_id(company_id)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            result = await session.execute(
                select(CompanyMemberModel).where(
                    and_(
                        CompanyMemberModel.company_id == company_id,
                        CompanyMemberModel.user_id == member_data.user_id,
                        CompanyMemberModel.is_active == True
                    )
                )
            )
            existing_member = result.scalar_one_or_none()
            if existing_member:
                raise HTTPException(status_code=400, detail="User is already a member of this company")

            payload = member_data.model_dump()
            base_fields = {
                "user_id": payload.get("user_id"),
                "invited_by": payload.get("invited_by"),
                "invited_at": payload.get("invited_at"),
                "joined_at": payload.get("joined_at"),
                "is_active": payload.get("is_active", True),
                "company_id": company_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            member = CompanyMemberModel(**base_fields)
            session.add(member)
            await session.commit()
            await session.refresh(member)

            member_dict = member.to_dict()
            member_schema = CompanyMember.model_validate(member_dict)

            return CompanyMemberResponse(
                message="Member added successfully",
                member=member_schema
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error adding company member: {str(e)}")

    async def remove_company_member(self, company_id: str, user_id: str) -> bool:
        """Remove a member from a company"""
        try:
            session = get_db_session()
            await session.execute(
                update(CompanyMemberModel).where(
                    and_(
                        CompanyMemberModel.company_id == company_id,
                        CompanyMemberModel.user_id == user_id
                    )
                ).values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error removing company member: {str(e)}")

    async def get_company_stats(self) -> CompanyStats:
        """Get company statistics"""
        try:
            session = get_db_session()
            result = await session.execute(select(CompanyModel).where(CompanyModel.is_active == True))
            total_companies = len(result.scalars().all())

            day_ago = datetime.utcnow() - timedelta(days=1)
            result = await session.execute(
                select(CompanyModel).where(
                    and_(
                        CompanyModel.is_active == True,
                        CompanyModel.created_at >= day_ago
                    )
                )
            )
            recent_companies = len(result.scalars().all())

            result = await session.execute(select(CompanyModel).where(CompanyModel.is_active == True))
            companies = result.scalars().all()
            active_subscriptions = 0
            expired_subscriptions = 0

            now = datetime.utcnow()
            for company in companies:
                if company.subscription and company.subscription.get("access_end_date"):
                    access_end = datetime.fromisoformat(company.subscription["access_end_date"])
                    if now <= access_end:
                        active_subscriptions += 1
                    else:
                        expired_subscriptions += 1

            return CompanyStats(
                total=total_companies,
                recent_24h=recent_companies,
                active_subscriptions=active_subscriptions,
                expired_subscriptions=expired_subscriptions
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting company stats: {str(e)}")

    async def extend_company_access(self, company_id: str, days: int) -> bool:
        """Extend company access by specified days"""
        try:
            session = get_db_session()
            company = await self.get_company_by_id(company_id)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            now = datetime.utcnow()
            current_end_date = now

            if company.subscription and company.subscription.get("access_end_date"):
                current_end_date = datetime.fromisoformat(company.subscription["access_end_date"])

            new_end_date = max(now, current_end_date) + timedelta(days=days)

            updated_subscription = company.subscription or {}
            updated_subscription["access_end_date"] = new_end_date.isoformat()

            await session.execute(
                update(CompanyModel).where(CompanyModel.id == company_id).values(
                    subscription=updated_subscription,
                    updated_at=now
                )
            )
            await session.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extending company access: {str(e)}")

    async def get_company_users(self, company_id: str) -> List[User]:
        """Get all users who are members of a company"""
        try:
            session = get_db_session()
            company = await self.get_company_by_id(company_id)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            result = await session.execute(
                select(UserModel)
                .join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id)
                .where(
                    and_(
                        CompanyMemberModel.company_id == company_id,
                        CompanyMemberModel.is_active == True,
                        UserModel.is_active == True
                    )
                )
                .order_by(UserModel.name)
            )
            users = result.scalars().all()

            user_list = []
            for user_model in users:
                user_dict = user_model.to_dict()
                platform_roles = await self.user_service.get_user_roles(user_model.id)
                user_dict['platformRoles'] = [role.name for role in platform_roles]
                user_list.append(User(**user_dict))

            return user_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company users: {str(e)}")

    # ========== Company Role Methods ==========
    
    async def create_company_default_presets(self, company_id: str) -> List[UserCompanyRoleModel]:
        """Create default company role presets"""
        try:
            session = get_db_session()
            created_roles = []

            for preset_key, preset_data in DEFAULT_COMPANY_ROLES.items():
                # Check if preset already exists for this company
                result = await session.execute(
                    select(UserCompanyRoleModel).where(
                        and_(
                            UserCompanyRoleModel.company_id == company_id,
                            UserCompanyRoleModel.name == preset_data["name"]
                        )
                    )
                )
                existing_role = result.scalar_one_or_none()

                if not existing_role:
                    role = UserCompanyRoleModel(
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

    @audit(
        action="CREATE",
        entity_type="company_role",
        details=lambda result, _a, kw: f"Rôle d'entreprise {kw['role_data'].name} créé",
        entity_id=lambda result, _a, _kw: result.id if result else None,
        extra=lambda _r, _a, kw: {"payload": kw["role_data"].model_dump(exclude_none=True)},
    )
    async def create_company_role(self, company_id: str, role_data: UserCompanyRoleCreate, actor: ActivityActor | None = None) -> UserCompanyRoleModel:
        """Create a new company role"""
        try:
            session = get_db_session()
            # Check if role name already exists for this company
            result = await session.execute(
                select(UserCompanyRoleModel).where(
                    and_(
                        UserCompanyRoleModel.company_id == company_id,
                        UserCompanyRoleModel.name == role_data.name
                    )
                )
            )
            existing_role = result.scalar_one_or_none()

            if existing_role:
                raise HTTPException(status_code=400, detail="Role name already exists for this company")

            role = UserCompanyRoleModel(
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

    async def get_company_preset_roles(self, company_id: str) -> List[UserCompanyRoleModel]:
        """Get preset roles for a company"""
        roles = await self.get_company_roles(company_id)
        return [role for role in roles if role.is_preset]

    async def get_company_roles(self, company_id: str) -> List[UserCompanyRoleModel]:
        """Get all roles for a company"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRoleModel).where(UserCompanyRoleModel.company_id == company_id)
            )
            return result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company roles: {str(e)}")

    async def get_company_role_by_id(self, company_id: str, role_id: str) -> Optional[UserCompanyRoleModel]:
        """Get a company role by ID"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRoleModel).where(
                    and_(
                        UserCompanyRoleModel.id == role_id,
                        UserCompanyRoleModel.company_id == company_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving role: {str(e)}")

    @audit(
        action="UPDATE",
        entity_type="company_role",
        details=lambda _r, _a, kw: f"Rôle d'entreprise {kw['role_id']} mis à jour",
        entity_id=lambda _r, _a, kw: kw["role_id"],
        extra=lambda _r, _a, kw: kw["role_data"].model_dump(exclude_unset=True),
    )
    async def update_company_role(self, company_id: str, role_id: str, role_data: UserCompanyRoleUpdate, actor: ActivityActor | None = None) -> UserCompanyRoleModel:
        """Update a company role"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserCompanyRoleModel).where(
                    and_(
                        UserCompanyRoleModel.id == role_id,
                        UserCompanyRoleModel.company_id == company_id
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
                update(UserCompanyRoleModel)
                .where(
                    and_(
                        UserCompanyRoleModel.id == role_id,
                        UserCompanyRoleModel.company_id == company_id
                    )
                )
                .values(**update_data)
            )
            await session.commit()

            # Return updated role
            result = await session.execute(
                select(UserCompanyRoleModel).where(UserCompanyRoleModel.id == role_id)
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")

    @audit(
        action="DELETE",
        entity_type="company_role",
        details=lambda _r, _a, kw: f"Rôle d'entreprise {kw['role_id']} supprimé",
        entity_id=lambda _r, _a, kw: kw["role_id"],
    )
    async def delete_company_role(self, company_id: str, role_id: str, actor: ActivityActor | None = None) -> CompanyRoleDeleteResponse:
        """Delete a company role and return response"""
        try:
            session = get_db_session()
            # Get existing role
            result = await session.execute(
                select(UserCompanyRoleModel).where(
                    and_(
                        UserCompanyRoleModel.id == role_id,
                        UserCompanyRoleModel.company_id == company_id
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
                select(UserCompanyRoleAssignmentModel).where(
                    and_(
                        UserCompanyRoleAssignmentModel.role_id == role_id,
                        UserCompanyRoleAssignmentModel.company_id == company_id
                    )
                )
            )
            assignments = result.scalars().all()

            if assignments:
                raise HTTPException(status_code=400, detail="Cannot delete role with active assignments")

            await session.execute(
                delete(UserCompanyRoleModel).where(
                    and_(
                        UserCompanyRoleModel.id == role_id,
                        UserCompanyRoleModel.company_id == company_id
                    )
                )
            )
            await session.commit()

            return CompanyRoleDeleteResponse(message="Role deleted successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting role: {str(e)}")

    @audit(
        action="ASSIGN",
        entity_type="company_role_assignment",
        details=lambda result, _a, kw: f"Rôle {kw['role_id']} attribué à l'utilisateur {kw['user_id']} dans l'entreprise {kw['company_id']}",
        entity_id=lambda result, _a, _kw: result.assignment_id if result else None,
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"], "companyId": kw["company_id"]},
    )
    async def assign_company_role_to_user(self, user_id: str, company_id: str, role_id: str, assigned_by: str, actor: ActivityActor | None = None) -> CompanyRoleAssignResponse:
        """Assign a company role to a user and return response"""
        try:
            session = get_db_session()
            # Check if assignment already exists
            result = await session.execute(
                select(UserCompanyRoleAssignmentModel).where(
                    and_(
                        UserCompanyRoleAssignmentModel.user_id == user_id,
                        UserCompanyRoleAssignmentModel.company_id == company_id,
                        UserCompanyRoleAssignmentModel.role_id == role_id
                    )
                )
            )
            existing_assignment = result.scalar_one_or_none()

            if existing_assignment:
                raise HTTPException(status_code=400, detail="User already has this role in this company")

            # Create assignment
            assignment = UserCompanyRoleAssignmentModel(
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

    @audit(
        action="REVOKE",
        entity_type="company_role_assignment",
        details=lambda _r, _a, kw: f"Rôle {kw['role_id']} retiré de l'utilisateur {kw['user_id']} dans l'entreprise {kw['company_id']}",
        entity_id=lambda _r, _a, kw: f"{kw['user_id']}:{kw['company_id']}:{kw['role_id']}",
        extra=lambda _r, _a, kw: {"userId": kw["user_id"], "roleId": kw["role_id"], "companyId": kw["company_id"]},
    )
    async def remove_company_role_from_user(self, user_id: str, company_id: str, role_id: str, actor: ActivityActor | None = None) -> CompanyRoleRemoveResponse:
        """Remove a company role from a user and return response"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRoleAssignmentModel).where(
                    and_(
                        UserCompanyRoleAssignmentModel.user_id == user_id,
                        UserCompanyRoleAssignmentModel.company_id == company_id,
                        UserCompanyRoleAssignmentModel.role_id == role_id
                    )
                )
            )
            assignment = result.scalar_one_or_none()

            if not assignment:
                raise HTTPException(status_code=404, detail="Role assignment not found")

            await session.execute(
                delete(UserCompanyRoleAssignmentModel).where(UserCompanyRoleAssignmentModel.id == assignment.id)
            )
            await session.commit()

            return CompanyRoleRemoveResponse(message="Role removed successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error removing role: {str(e)}")

    async def get_user_company_roles(self, user_id: str, company_id: str) -> List[UserCompanyRoleModel]:
        """Get all company roles assigned to a user"""
        try:
            session = get_db_session()
            result = await session.execute(
                select(UserCompanyRoleModel)
                .join(UserCompanyRoleAssignmentModel)
                .where(
                    and_(
                        UserCompanyRoleAssignmentModel.user_id == user_id,
                        UserCompanyRoleAssignmentModel.company_id == company_id
                    )
                )
                .order_by(UserCompanyRoleModel.name)
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

    async def check_company_permission(self, user_id: str, company_id: str, permission: str) -> bool:
        """Check if a user has a specific company permission"""
        try:
            permissions = await self.get_user_company_permissions(user_id, company_id)
            return permission in permissions
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error checking permission: {str(e)}")

    async def check_company_permission_with_response(self, user_id: str, company_id: str, permission: str) -> CompanyPermissionCheckResponse:
        """Check if a user has a specific company permission and return response"""
        try:
            has_permission = await self.check_company_permission(user_id, company_id, permission)
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
