from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from . import SCHEMA_CONFIG

# Platform Permission Constants
class PlatformPermissions:
    """Platform-level permissions"""
    ADMIN_ACCESS = "admin.access"
    ADMIN_USERS_VIEW = "admin.users.view"
    ADMIN_USERS_MANAGE = "admin.users.manage"
    ADMIN_COMPANIES_VIEW = "admin.companies.view"
    ADMIN_COMPANIES_MANAGE = "admin.companies.manage"
    ADMIN_ROLES_VIEW = "admin.roles.view"
    ADMIN_ROLES_MANAGE = "admin.roles.manage"
    ADMIN_ACTIVATION_KEYS_VIEW = "admin.activation_keys.view"
    ADMIN_ACTIVATION_KEYS_MANAGE = "admin.activation_keys.manage"
    ADMIN_STATS_VIEW = "admin.stats.view"
    ADMIN_SYSTEM_SETTINGS = "admin.system_settings"

# UserRole Schemas
class UserRoleBase(BaseModel):
    """Base user role schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    is_preset: bool = Field(default=False)
    is_system: bool = Field(default=False)

class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role"""
    pass

class UserRoleUpdate(BaseModel):
    """Schema for updating a user role"""
    model_config = SCHEMA_CONFIG
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None

class UserRole(UserRoleBase):
    """Complete user role schema"""
    model_config = SCHEMA_CONFIG
    
    id: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# UserRoleAssignment Schemas
class UserRoleAssignmentBase(BaseModel):
    """Base user role assignment schema"""
    model_config = SCHEMA_CONFIG
    
    user_id: str = Field(..., alias="userId")
    role_id: str = Field(..., alias="roleId")
    assigned_by: Optional[str] = Field(None, alias="assignedBy")

class UserRoleAssignmentCreate(UserRoleAssignmentBase):
    """Schema for creating a user role assignment"""
    pass

class UserRoleAssignment(UserRoleAssignmentBase):
    """Complete user role assignment schema"""
    model_config = SCHEMA_CONFIG
    
    id: str
    assigned_at: datetime = Field(..., alias="assignedAt")

# Permission Check Schema
class PermissionCheck(BaseModel):
    """Schema for checking permissions"""
    model_config = SCHEMA_CONFIG
    
    permission: str = Field(..., description="Permission to check")
    user_id: Optional[str] = Field(None, alias="userId", description="User ID to check (defaults to current user)")

class PermissionCheckResponse(BaseModel):
    """Response for permission check"""
    model_config = SCHEMA_CONFIG
    
    has_permission: bool = Field(..., alias="hasPermission")
    user_id: str = Field(..., alias="userId")
    permission: str
    roles: List[str] = Field(default_factory=list)

# Default Platform Role Presets
DEFAULT_PLATFORM_ROLES = {
    "platform_admin": {
        "name": "Platform Administrator",
        "description": "Full administrative access to the platform",
        "permissions": [
            PlatformPermissions.ADMIN_ACCESS,
            PlatformPermissions.ADMIN_USERS_VIEW,
            PlatformPermissions.ADMIN_USERS_MANAGE,
            PlatformPermissions.ADMIN_COMPANIES_VIEW,
            PlatformPermissions.ADMIN_COMPANIES_MANAGE,
            PlatformPermissions.ADMIN_ROLES_VIEW,
            PlatformPermissions.ADMIN_ROLES_MANAGE,
            PlatformPermissions.ADMIN_ACTIVATION_KEYS_VIEW,
            PlatformPermissions.ADMIN_ACTIVATION_KEYS_MANAGE,
            PlatformPermissions.ADMIN_STATS_VIEW,
            PlatformPermissions.ADMIN_SYSTEM_SETTINGS,
        ],
        "is_preset": True,
        "is_system": True
    },
    "regular_user": {
        "name": "Regular User",
        "description": "Standard platform user with basic access",
        "permissions": [],
        "is_preset": True,
        "is_system": True
    }
}
