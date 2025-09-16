from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.core.database import AsyncSessionLocal
from app.models.company import Company, CompanyMember
from app.schemas.company import (
    CompanyCreate, CompanyUpdate, CompanyMemberCreate,
    CompanyStats, CompanySettings, CompanySubscription
)
from app.services.user import UserService
import secrets
from datetime import datetime, timedelta

class CompanyService:
    """Service for company-related operations"""
    
    def __init__(self):
        self.user_service = UserService()
    
    async def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company"""
        try:
            async with AsyncSessionLocal() as session:
                # Create company
                company_dict = company_data.model_dump()
                
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
                
                company = Company(**company_dict)
                session.add(company)
                await session.commit()
                await session.refresh(company)
                
                # Create owner member
                owner_member = CompanyMember(
                    company_id=company.id,
                    user_id=company.owner_id,
                    role="owner",
                    permissions=["*"],
                    invited_by=company.owner_id,
                    invited_at=now,
                    joined_at=now,
                    is_active=True,
                    created_at=now,
                    updated_at=now
                )
                session.add(owner_member)
                await session.commit()
                
                # Get the company with members relationship loaded
                result = await session.execute(
                    select(Company)
                    .options(selectinload(Company.members))
                    .where(Company.id == company.id)
                )
                company_with_members = result.scalar_one()
                
                # Convert subscription to CompanySubscription schema
                if company_with_members.subscription:
                    company_with_members.subscription = CompanySubscription(**company_with_members.subscription).model_dump(by_alias=True)
                
                return company_with_members
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")
    
    async def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """Get a company by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Company)
                    .options(selectinload(Company.members))
                    .where(Company.id == company_id, Company.is_active == True)
                )
                company = result.scalar_one_or_none()
                if company and company.subscription:
                    # Convert subscription to CompanySubscription schema
                    company.subscription = CompanySubscription(**company.subscription).model_dump(by_alias=True)
                return company
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving company: {str(e)}")
    
    async def get_user_companies(self, user_id: int) -> List[Company]:
        """Get all companies for a user"""
        try:
            async with AsyncSessionLocal() as session:
                # Get companies where user is a member with eager loading
                result = await session.execute(
                    select(Company)
                    .options(selectinload(Company.members))
                    .join(CompanyMember)
                    .where(
                        and_(
                            CompanyMember.user_id == user_id,
                            CompanyMember.is_active == True,
                            Company.is_active == True
                        )
                    )
                    .order_by(Company.created_at.desc())
                )
                companies = result.scalars().all()
                # Convert subscription to CompanySubscription schema for each company
                for company in companies:
                    if company.subscription:
                        company.subscription = CompanySubscription(**company.subscription).model_dump(by_alias=True)
                return companies
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user companies: {str(e)}")
    
    async def update_company(self, company_id: int, company_data: CompanyUpdate) -> Company:
        """Update a company"""
        try:
            async with AsyncSessionLocal() as session:
                # Get existing company
                result = await session.execute(
                    select(Company).where(Company.id == company_id, Company.is_active == True)
                )
                company = result.scalar_one_or_none()
                
                if not company:
                    raise HTTPException(status_code=404, detail="Company not found")
                
                # Update fields
                update_data = company_data.model_dump(exclude_unset=True)
                update_data["updated_at"] = datetime.utcnow()
                
                await session.execute(
                    update(Company).where(Company.id == company_id).values(**update_data)
                )
                await session.commit()
                
                # Return updated company
                result = await session.execute(
                    select(Company).where(Company.id == company_id)
                )
                return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")
    
    async def delete_company(self, company_id: int) -> bool:
        """Delete a company (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Company).where(Company.id == company_id).values(
                        is_active=False,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
    
    async def add_company_member(self, company_id: int, member_data: CompanyMemberCreate) -> CompanyMember:
        """Add a member to a company"""
        try:
            async with AsyncSessionLocal() as session:
                # Check if company exists
                company = await self.get_company_by_id(company_id)
                if not company:
                    raise HTTPException(status_code=404, detail="Company not found")
                
                # Check if user is already a member
                result = await session.execute(
                    select(CompanyMember).where(
                        and_(
                            CompanyMember.company_id == company_id,
                            CompanyMember.user_id == member_data.user_id,
                            CompanyMember.is_active == True
                        )
                    )
                )
                existing_member = result.scalar_one_or_none()
                if existing_member:
                    raise HTTPException(status_code=400, detail="User is already a member of this company")
                
                # Create member
                member_dict = member_data.model_dump()
                member_dict.update({
                    "company_id": company_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                member = CompanyMember(**member_dict)
                session.add(member)
                await session.commit()
                await session.refresh(member)
                
                return member
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error adding company member: {str(e)}")
    
    async def remove_company_member(self, company_id: int, user_id: int) -> bool:
        """Remove a member from a company"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(CompanyMember).where(
                        and_(
                            CompanyMember.company_id == company_id,
                            CompanyMember.user_id == user_id
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
            async with AsyncSessionLocal() as session:
                # Total companies
                result = await session.execute(select(Company).where(Company.is_active == True))
                total_companies = len(result.scalars().all())
                
                # Recent companies (24h)
                day_ago = datetime.utcnow() - timedelta(days=1)
                result = await session.execute(
                    select(Company).where(
                        and_(
                            Company.is_active == True,
                            Company.created_at >= day_ago
                        )
                    )
                )
                recent_companies = len(result.scalars().all())
                
                # Active subscriptions
                result = await session.execute(select(Company).where(Company.is_active == True))
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
    
    async def extend_company_access(self, company_id: int, days: int) -> bool:
        """Extend company access by specified days"""
        try:
            async with AsyncSessionLocal() as session:
                company = await self.get_company_by_id(company_id)
                if not company:
                    raise HTTPException(status_code=404, detail="Company not found")
                
                # Calculate new access end date
                now = datetime.utcnow()
                current_end_date = now
                
                if company.subscription and company.subscription.get("access_end_date"):
                    current_end_date = datetime.fromisoformat(company.subscription["access_end_date"])
                
                # Extend from whichever is later
                new_end_date = max(now, current_end_date) + timedelta(days=days)
                
                # Update subscription
                updated_subscription = company.subscription or {}
                updated_subscription["access_end_date"] = new_end_date.isoformat()
                
                await session.execute(
                    update(Company).where(Company.id == company_id).values(
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
