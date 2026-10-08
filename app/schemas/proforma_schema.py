from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from app.utils.casing import BaseCamelModel


class ProformaItem(BaseCamelModel):
    description: str = Field(..., min_length=1, max_length=255)
    item_id: Optional[str] = Field(None, alias="itemId")
    item_type: Optional[str] = Field(None, alias="itemType")
    quantity: int = Field(..., gt=0)
    sell_price: float = Field(..., ge=0, alias="sellPrice")
    total: float = Field(..., ge=0)


class ProformaClient(BaseCamelModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ProformaBase(BaseCamelModel):
    number: str
    date: datetime
    client: ProformaClient
    items: List[ProformaItem] = Field(..., min_length=1)
    subtotal: float = Field(..., ge=0)
    discount: float = Field(0, ge=0, le=99)
    tva: float = Field(0, ge=0, le=100)
    tax_amount: float = Field(0, ge=0, alias="taxAmount")
    total: float = Field(..., ge=0)
    objet: Optional[str] = None
    status: str = Field("draft", pattern="^(draft|sent|accepted|rejected)$")


class ProformaCreate(ProformaBase):
    number: Optional[str] = None


class ProformaUpdate(BaseCamelModel):
    number: Optional[str] = None
    date: Optional[datetime] = None
    client: Optional[ProformaClient] = None
    items: Optional[List[ProformaItem]] = None
    subtotal: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0, le=99)
    tva: Optional[float] = Field(None, ge=0, le=100)
    tax_amount: Optional[float] = Field(None, ge=0, alias="taxAmount")
    total: Optional[float] = Field(None, ge=0)
    objet: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|sent|accepted|rejected)$")


class Proforma(ProformaBase):
    id: str
    company_id: str = Field(..., alias="companyId")
    created_by: str = Field(..., alias="createdBy")
    is_active: bool = Field(True, alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


class ProformaStats(BaseCamelModel):
    total: int
    total_value: float = Field(..., alias="totalValue")
    average_amount: float = Field(..., alias="averageAmount")
    recent_count: int = Field(..., alias="recentCount")
    by_status: Dict[str, int] = Field(..., alias="byStatus")


class ProformaFilter(BaseCamelModel):
    client_name: Optional[str] = Field(None, alias="clientName")
    status: Optional[str] = None
    date_from: Optional[datetime] = Field(None, alias="dateFrom")
    date_to: Optional[datetime] = Field(None, alias="dateTo")
    limit: Optional[int] = Field(None, ge=1, le=100)
