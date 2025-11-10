from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.core.database import get_db_session
from app.models.company_model import Company as CompanyModel, CompanyMember as CompanyMemberModel
from app.models.user_model import User as UserModel
from app.models.company_role_model import UserCompanyRole
from app.services.company_role_service import CompanyRoleService
from app.schemas.company_schema import (
    CompanyCreate, CompanyUpdate, CompanyMemberCreate,
    CompanyStats, CompanySettings, CompanySubscription, CompanyMember, Company, CompanyMemberResponse
)
from app.schemas.user_schema import User
from app.services.user_service import UserService
import secrets
from datetime import datetime, timedelta

class CompanyService:
    """Service for company-related operations"""

    def __init__(self):
        self.user_service = UserService()
        self.company_role_service = CompanyRoleService()

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

            # Create default company role presets and assign the Owner preset
            try:
                await self.company_role_service.create_default_presets(company.id)
                result_role = await session.execute(
                    select(UserCompanyRole).where(
                        and_(
                            UserCompanyRole.company_id == company.id,
                            UserCompanyRole.name == "Propriétaire"
                        )
                    )
                )
                owner_role = result_role.scalar_one_or_none()
                if owner_role:
                    await self.company_role_service.assign_role_to_user(
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

    async def update_company(self, company_id: str, company_data: CompanyUpdate) -> Company:
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

    async def delete_company(self, company_id: str) -> bool:
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
                from app.services.user_role_service import UserRoleService
                user_role_service = UserRoleService()
                platform_roles = await user_role_service.get_user_roles(user_model.id)
                user_dict['platformRoles'] = [role.name for role in platform_roles]
                user_list.append(User(**user_dict))

            return user_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company users: {str(e)}")
