from app.utils.casing import BaseCamelModel
from pydantic import Field
from typing import List, Optional
from datetime import datetime

# Company Permission Constants
class CompanyPermissions:
    """Company-level permissions"""
    # Sales module
    SALES_VIEW = "sales.view"
    SALES_CREATE = "sales.create"
    SALES_UPDATE = "sales.update"
    SALES_DELETE = "sales.delete"
    SALES_EXPORT = "sales.export"
    
    # Clients module
    CLIENTS_VIEW = "clients.view"
    CLIENTS_CREATE = "clients.create"
    CLIENTS_UPDATE = "clients.update"
    CLIENTS_DELETE = "clients.delete"
    CLIENTS_EXPORT = "clients.export"
    
    # Products module
    PRODUCTS_VIEW = "products.view"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_UPDATE = "products.update"
    PRODUCTS_DELETE = "products.delete"
    PRODUCTS_EXPORT = "products.export"
    
    # Inventory module
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"
    INVENTORY_EXPORT = "inventory.export"
    
    # Suppliers module
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_CREATE = "suppliers.create"
    SUPPLIERS_UPDATE = "suppliers.update"
    SUPPLIERS_DELETE = "suppliers.delete"
    
    # Reports module
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"
    
    # Company management
    COMPANY_VIEW = "company.view"
    COMPANY_UPDATE = "company.update"
    COMPANY_USERS_VIEW = "company.users.view"
    COMPANY_USERS_MANAGE = "company.users.manage"
    COMPANY_ROLES_VIEW = "company.roles.view"
    COMPANY_ROLES_MANAGE = "company.roles.manage"
    
    # Financial operations
    ACCOUNTING_VIEW = "accounting.view"
    ACCOUNTING_MANAGE = "accounting.manage"
    INVOICES_VIEW = "invoices.view"
    INVOICES_CREATE = "invoices.create"
    INVOICES_UPDATE = "invoices.update"
    INVOICES_DELETE = "invoices.delete"

# UserCompanyRole Schemas
class UserCompanyRoleBase(BaseCamelModel):
    """Base user company role schema"""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    is_preset: bool = Field(default=False)
    is_system: bool = Field(default=False)

class UserCompanyRoleCreate(UserCompanyRoleBase):
    """Schema for creating a user company role"""
    pass

class UserCompanyRoleUpdate(BaseCamelModel):
    """Schema for updating a user company role"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None

class UserCompanyRole(UserCompanyRoleBase):
    """Complete user company role schema"""
    
    id: str
    company_id: str = Field(..., alias="companyId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# UserCompanyRoleAssignment Schemas
class UserCompanyRoleAssignmentBase(BaseCamelModel):
    """Base user company role assignment schema"""
    
    user_id: str = Field(..., alias="userId")
    company_id: str = Field(..., alias="companyId")
    role_id: str = Field(..., alias="roleId")
    assigned_by: Optional[str] = Field(None, alias="assignedBy")

class UserCompanyRoleAssignmentCreate(UserCompanyRoleAssignmentBase):
    """Schema for creating a user company role assignment"""
    pass

class UserCompanyRoleAssignment(UserCompanyRoleAssignmentBase):
    """Complete user company role assignment schema"""
    
    id: str
    assigned_at: datetime = Field(..., alias="assignedAt")

# Company Permission Check Schema
class CompanyPermissionCheck(BaseCamelModel):
    """Schema for checking company permissions"""
    
    permission: str = Field(..., description="Permission to check")
    company_id: str = Field(..., alias="companyId", description="Company ID")
    user_id: Optional[str] = Field(None, alias="userId", description="User ID to check (defaults to current user)")

class CompanyPermissionCheckResponse(BaseCamelModel):
    """Response for company permission check"""
    
    has_permission: bool = Field(..., alias="hasPermission")
    user_id: str = Field(..., alias="userId")
    company_id: str = Field(..., alias="companyId")
    permission: str
    roles: List[str] = Field(default_factory=list)

# Response Schemas
class CompanyRoleDeleteResponse(BaseCamelModel):
    """Response schema for deleting company role"""
    message: str

class CompanyRoleAssignResponse(BaseCamelModel):
    """Response schema for assigning company role"""
    message: str
    assignment_id: str = Field(..., alias="assignmentId")

class CompanyRoleRemoveResponse(BaseCamelModel):
    """Response schema for removing company role"""
    message: str

# Default Company Role Presets
DEFAULT_COMPANY_ROLES = {
    "owner": {
        "name": "Propriétaire",
        "description": "Propriétaire de l'entreprise avec tous les droits",
        "permissions": [
            # All permissions
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.SALES_CREATE,
            CompanyPermissions.SALES_UPDATE,
            CompanyPermissions.SALES_DELETE,
            CompanyPermissions.SALES_EXPORT,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.CLIENTS_CREATE,
            CompanyPermissions.CLIENTS_UPDATE,
            CompanyPermissions.CLIENTS_DELETE,
            CompanyPermissions.CLIENTS_EXPORT,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.PRODUCTS_CREATE,
            CompanyPermissions.PRODUCTS_UPDATE,
            CompanyPermissions.PRODUCTS_DELETE,
            CompanyPermissions.PRODUCTS_EXPORT,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.INVENTORY_MANAGE,
            CompanyPermissions.INVENTORY_EXPORT,
            CompanyPermissions.SUPPLIERS_VIEW,
            CompanyPermissions.SUPPLIERS_CREATE,
            CompanyPermissions.SUPPLIERS_UPDATE,
            CompanyPermissions.SUPPLIERS_DELETE,
            CompanyPermissions.REPORTS_VIEW,
            CompanyPermissions.REPORTS_EXPORT,
            CompanyPermissions.COMPANY_VIEW,
            CompanyPermissions.COMPANY_UPDATE,
            CompanyPermissions.COMPANY_USERS_VIEW,
            CompanyPermissions.COMPANY_USERS_MANAGE,
            CompanyPermissions.COMPANY_ROLES_VIEW,
            CompanyPermissions.COMPANY_ROLES_MANAGE,
            CompanyPermissions.ACCOUNTING_VIEW,
            CompanyPermissions.ACCOUNTING_MANAGE,
            CompanyPermissions.INVOICES_VIEW,
            CompanyPermissions.INVOICES_CREATE,
            CompanyPermissions.INVOICES_UPDATE,
            CompanyPermissions.INVOICES_DELETE,
        ],
        "is_preset": True,
        "is_system": True
    },
    "admin": {
        "name": "Administrateur",
        "description": "Administrateur avec la plupart des droits sauf le transfert de propriété",
        "permissions": [
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.SALES_CREATE,
            CompanyPermissions.SALES_UPDATE,
            CompanyPermissions.SALES_DELETE,
            CompanyPermissions.SALES_EXPORT,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.CLIENTS_CREATE,
            CompanyPermissions.CLIENTS_UPDATE,
            CompanyPermissions.CLIENTS_DELETE,
            CompanyPermissions.CLIENTS_EXPORT,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.PRODUCTS_CREATE,
            CompanyPermissions.PRODUCTS_UPDATE,
            CompanyPermissions.PRODUCTS_DELETE,
            CompanyPermissions.PRODUCTS_EXPORT,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.INVENTORY_MANAGE,
            CompanyPermissions.INVENTORY_EXPORT,
            CompanyPermissions.SUPPLIERS_VIEW,
            CompanyPermissions.SUPPLIERS_CREATE,
            CompanyPermissions.SUPPLIERS_UPDATE,
            CompanyPermissions.SUPPLIERS_DELETE,
            CompanyPermissions.REPORTS_VIEW,
            CompanyPermissions.REPORTS_EXPORT,
            CompanyPermissions.COMPANY_VIEW,
            CompanyPermissions.COMPANY_UPDATE,
            CompanyPermissions.COMPANY_USERS_VIEW,
            CompanyPermissions.COMPANY_USERS_MANAGE,
            CompanyPermissions.COMPANY_ROLES_VIEW,
            CompanyPermissions.COMPANY_ROLES_MANAGE,
            CompanyPermissions.ACCOUNTING_VIEW,
            CompanyPermissions.ACCOUNTING_MANAGE,
            CompanyPermissions.INVOICES_VIEW,
            CompanyPermissions.INVOICES_CREATE,
            CompanyPermissions.INVOICES_UPDATE,
            CompanyPermissions.INVOICES_DELETE,
        ],
        "is_preset": True,
        "is_system": True
    },
    "manager": {
        "name": "Gestionnaire",
        "description": "Gestionnaire avec droits de supervision et gestion d'équipe",
        "permissions": [
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.SALES_CREATE,
            CompanyPermissions.SALES_UPDATE,
            CompanyPermissions.SALES_EXPORT,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.CLIENTS_CREATE,
            CompanyPermissions.CLIENTS_UPDATE,
            CompanyPermissions.CLIENTS_EXPORT,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.PRODUCTS_CREATE,
            CompanyPermissions.PRODUCTS_UPDATE,
            CompanyPermissions.PRODUCTS_EXPORT,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.INVENTORY_MANAGE,
            CompanyPermissions.INVENTORY_EXPORT,
            CompanyPermissions.SUPPLIERS_VIEW,
            CompanyPermissions.SUPPLIERS_CREATE,
            CompanyPermissions.SUPPLIERS_UPDATE,
            CompanyPermissions.REPORTS_VIEW,
            CompanyPermissions.REPORTS_EXPORT,
            CompanyPermissions.COMPANY_USERS_VIEW,
            CompanyPermissions.ACCOUNTING_VIEW,
            CompanyPermissions.INVOICES_VIEW,
            CompanyPermissions.INVOICES_CREATE,
            CompanyPermissions.INVOICES_UPDATE,
        ],
        "is_preset": True,
        "is_system": True
    },
    "operator": {
        "name": "Opérateur",
        "description": "Opérateur avec droits pour les opérations quotidiennes",
        "permissions": [
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.SALES_CREATE,
            CompanyPermissions.SALES_UPDATE,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.CLIENTS_CREATE,
            CompanyPermissions.CLIENTS_UPDATE,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.PRODUCTS_CREATE,
            CompanyPermissions.PRODUCTS_UPDATE,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.INVENTORY_MANAGE,
            CompanyPermissions.SUPPLIERS_VIEW,
            CompanyPermissions.REPORTS_VIEW,
        ],
        "is_preset": True,
        "is_system": True
    },
    "comptable": {
        "name": "Comptable",
        "description": "Comptable avec droits pour les opérations financières",
        "permissions": [
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.SALES_EXPORT,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.CLIENTS_EXPORT,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.REPORTS_VIEW,
            CompanyPermissions.REPORTS_EXPORT,
            CompanyPermissions.ACCOUNTING_VIEW,
            CompanyPermissions.ACCOUNTING_MANAGE,
            CompanyPermissions.INVOICES_VIEW,
            CompanyPermissions.INVOICES_CREATE,
            CompanyPermissions.INVOICES_UPDATE,
            CompanyPermissions.INVOICES_DELETE,
        ],
        "is_preset": True,
        "is_system": True
    },
    "viewer": {
        "name": "Observateur",
        "description": "Accès en lecture seule",
        "permissions": [
            CompanyPermissions.SALES_VIEW,
            CompanyPermissions.CLIENTS_VIEW,
            CompanyPermissions.PRODUCTS_VIEW,
            CompanyPermissions.INVENTORY_VIEW,
            CompanyPermissions.SUPPLIERS_VIEW,
            CompanyPermissions.REPORTS_VIEW,
            CompanyPermissions.COMPANY_VIEW,
        ],
        "is_preset": True,
        "is_system": True
    }
}

