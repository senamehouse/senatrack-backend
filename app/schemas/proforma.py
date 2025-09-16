from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from . import SCHEMA_CONFIG

# Proforma Item Schema
class ProformaItem(BaseModel):
    """Proforma item schema"""
    model_config = SCHEMA_CONFIG
    
    item_id: int = Field(..., alias="itemId")
    item_name: str = Field(..., min_length=1, max_length=255, alias="itemName")
    item_reference: Optional[str] = Field(None, max_length=100, alias="itemReference")
    item_type: str = Field(..., pattern="^(product|service)$", alias="itemType")
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0, alias="unitPrice")
    total: float = Field(..., ge=0)
    unit: Optional[str] = Field(None, max_length=50)

# Proforma Client Schema
class ProformaClient(BaseModel):
    """Proforma client schema"""
    model_config = SCHEMA_CONFIG
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, alias="taxId")

# Proforma Schemas
class ProformaBase(BaseModel):
    """Base proforma schema"""
    model_config = SCHEMA_CONFIG
    
    number: str = Field(..., min_length=1, max_length=100)
    date: datetime
    client: ProformaClient
    items: List[ProformaItem]
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0, alias="taxAmount")
    total: float = Field(..., ge=0)
    notes: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|sent|accepted|rejected)$")

class ProformaCreate(ProformaBase):
    """Schema for creating a proforma"""
    model_config = SCHEMA_CONFIG
    
    company_id: int = Field(..., alias="companyId")
    created_by: int = Field(..., alias="createdBy")

class ProformaUpdate(BaseModel):
    """Schema for updating a proforma"""
    model_config = SCHEMA_CONFIG
    
    number: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[datetime] = None
    client: Optional[ProformaClient] = None
    items: Optional[List[ProformaItem]] = None
    subtotal: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0, alias="taxAmount")
    total: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|sent|accepted|rejected)$")

class Proforma(ProformaBase):
    """Complete proforma schema"""
    model_config = SCHEMA_CONFIG
    
    id: int
    company_id: int = Field(..., alias="companyId")
    created_by: int = Field(..., alias="createdBy")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Proforma Stats Schema
class ProformaStats(BaseModel):
    """Proforma statistics schema"""
    model_config = SCHEMA_CONFIG
    
    total: int
    total_value: float = Field(..., alias="totalValue")
    average_amount: float = Field(..., alias="averageAmount")
    recent_count: int = Field(..., alias="recentCount")
    by_status: Dict[str, int] = Field(..., alias="byStatus")

# Proforma Filter Schema
class ProformaFilter(BaseModel):
    """Proforma filter schema"""
    model_config = SCHEMA_CONFIG
    
    client_name: Optional[str] = Field(None, alias="clientName")
    status: Optional[str] = None
    date_from: Optional[datetime] = Field(None, alias="dateFrom")
    date_to: Optional[datetime] = Field(None, alias="dateTo")
    limit: Optional[int] = Field(None, ge=1, le=100)
