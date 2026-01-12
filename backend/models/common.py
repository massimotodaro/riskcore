# RISKCORE Common Models - Enums and Mixins

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class PositionDirection(str, Enum):
    """Position direction enum - matches database."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class PositionSource(str, Enum):
    """Position data source enum - matches database."""

    FILE_UPLOAD = "file_upload"
    API = "api"
    FIX = "fix"
    CALCULATED = "calculated"


class PriceSource(str, Enum):
    """Price source enum - matches database."""

    MARKET = "market"
    MODEL = "model"
    CLIENT_OVERRIDE = "client_override"
    STALE = "stale"


class TradeSide(str, Enum):
    """Trade side enum - matches database."""

    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"


class TenantMixin(BaseModel):
    """Mixin for tenant-scoped models."""

    tenant_id: UUID = Field(..., description="Tenant identifier for RLS")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
