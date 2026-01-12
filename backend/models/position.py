# RISKCORE Position Models

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional

from .common import PositionDirection, PositionSource, PriceSource


class PositionBase(BaseModel):
    """Base position model with shared fields."""

    book_id: UUID = Field(..., description="Book/portfolio this position belongs to")
    security_id: Optional[UUID] = Field(
        None, description="Security ID (resolved from identifier)"
    )
    quantity: Decimal = Field(..., ge=0, description="Position quantity (always positive)")
    direction: PositionDirection = Field(..., description="Long, short, or flat")
    price: Optional[Decimal] = Field(None, ge=0, description="Current price per unit")
    price_source: PriceSource = Field(
        default=PriceSource.MARKET, description="Source of price data"
    )
    price_as_of: Optional[datetime] = Field(None, description="Price timestamp")
    local_currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Position currency"
    )
    base_currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Reporting currency"
    )
    fx_rate: Optional[Decimal] = Field(None, gt=0, description="FX rate to base currency")
    source: PositionSource = Field(..., description="Data source (API, file, FIX)")
    source_reference: Optional[str] = Field(
        None, max_length=255, description="Source reference ID"
    )
    as_of_timestamp: datetime = Field(..., description="Position validity timestamp")

    @field_validator("local_currency", "base_currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        """Ensure currency codes are uppercase."""
        return v.upper()


class PositionCreate(PositionBase):
    """Model for creating a new position."""

    tenant_id: UUID = Field(..., description="Tenant ID for RLS")

    # Optional identifiers for security resolution
    ticker: Optional[str] = Field(None, description="Ticker symbol for security lookup")
    cusip: Optional[str] = Field(None, description="CUSIP for security lookup")
    isin: Optional[str] = Field(None, description="ISIN for security lookup")
    sedol: Optional[str] = Field(None, description="SEDOL for security lookup")

    # Optional financial metrics
    cost_basis: Optional[Decimal] = Field(None, description="Total cost basis")
    market_value: Optional[Decimal] = Field(None, description="Current market value")


class PositionUpdate(BaseModel):
    """Model for updating an existing position."""

    quantity: Optional[Decimal] = Field(None, ge=0)
    direction: Optional[PositionDirection] = None
    price: Optional[Decimal] = Field(None, ge=0)
    price_source: Optional[PriceSource] = None
    price_as_of: Optional[datetime] = None
    fx_rate: Optional[Decimal] = Field(None, gt=0)
    cost_basis: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    as_of_timestamp: Optional[datetime] = None

    # Greeks (for derivatives)
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    rho: Optional[Decimal] = None

    # Fixed income
    dv01: Optional[Decimal] = None
    cs01: Optional[Decimal] = None


class PositionResponse(PositionBase):
    """Position response model with all fields."""

    id: UUID
    tenant_id: UUID
    # Override quantity to allow negative values from database (short positions)
    quantity: Decimal = Field(..., description="Position quantity (negative for shorts in legacy data)")
    market_value: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    market_value_base: Optional[Decimal] = None

    # Greeks
    beta: Optional[Decimal] = None
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    rho: Optional[Decimal] = None

    # Fixed income
    dv01: Optional[Decimal] = None
    cs01: Optional[Decimal] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PositionList(BaseModel):
    """Paginated list of positions."""

    items: list[PositionResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
