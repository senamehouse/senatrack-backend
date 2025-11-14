from app.utils.casing import BaseCamelModel
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Proforma Item Schema
class ProformaItem(BaseCamelModel):
    """Proforma item schema"""
    
    item_id: str = Field(..., alias="itemId")
    item_name: str = Field(..., min_length=1, max_length=255, alias="itemName")
    item_reference: Optional[str] = Field(None, max_length=100, alias="itemReference")
    item_type: str = Field(..., pattern="^(product|service)$", alias="itemType")
    quantity: int = Field(..., gt=0)
    sell_price: float = Field(..., ge=0, alias="sellPrice")
    total: float = Field(..., ge=0)
    unit: Optional[str] = Field(None, max_length=50)

# Proforma Client Schema
class ProformaClient(BaseCamelModel):
    """Proforma client schema"""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, alias="taxId")

# Proforma Schemas
class ProformaBase(BaseCamelModel):
    """Base proforma schema"""
    
    number: str = Field(..., min_length=1, max_length=100)
    date: datetime
    client: ProformaClient
    items: List[ProformaItem]
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0, alias="taxAmount")
    total: float = Field(..., ge=0)
    notes: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|sent|accepted|rejected)$")

class ProformaCreate(BaseCamelModel):
    """Schema for creating a proforma"""
    
    number: Optional[str] = Field(None, min_length=1, max_length=100)
    date: datetime
    client: ProformaClient
    items: List[ProformaItem]
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0, alias="taxAmount")
    total: float = Field(..., ge=0)
    notes: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|sent|accepted|rejected)$")
    company_id: str = Field(..., alias="companyId")
    created_by: int = Field(..., alias="createdBy")

class ProformaUpdate(BaseCamelModel):
    """Schema for updating a proforma"""
    
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
    
    id: str
    company_id: str = Field(..., alias="companyId")
    created_by: int = Field(..., alias="createdBy")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

# Proforma Stats Schema
class ProformaStats(BaseCamelModel):
    """Proforma statistics schema"""
    
    total: int
    total_value: float = Field(..., alias="totalValue")
    average_amount: float = Field(..., alias="averageAmount")
    recent_count: int = Field(..., alias="recentCount")
    by_status: Dict[str, int] = Field(..., alias="byStatus")

# Proforma Filter Schema
class ProformaFilter(BaseCamelModel):
    """Proforma filter schema"""
    
    client_name: Optional[str] = Field(None, alias="clientName")
    status: Optional[str] = None
    date_from: Optional[datetime] = Field(None, alias="dateFrom")
    date_to: Optional[datetime] = Field(None, alias="dateTo")
    limit: Optional[int] = Field(None, ge=1, le=100)
