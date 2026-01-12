# RISKCORE Trade Models

from pydantic import BaseModel, Field, field_validator
from datetime import date, time, datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional

from .common import TradeSide, PositionSource


class TradeBase(BaseModel):
    """Base trade model with shared fields."""

    book_id: UUID = Field(..., description="Book/portfolio this trade belongs to")
    security_id: Optional[UUID] = Field(
        None, description="Security ID (resolved from identifier)"
    )
    side: TradeSide = Field(..., description="Trade side: buy, sell, short, cover")
    quantity: Decimal = Field(..., gt=0, description="Trade quantity (always positive)")
    price: Decimal = Field(..., ge=0, description="Execution price per unit")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="Trade currency"
    )
    trade_date: date = Field(..., description="Trade date")
    trade_time: Optional[time] = Field(None, description="Trade execution time")
    settlement_date: Optional[date] = Field(None, description="Settlement date")
    source: PositionSource = Field(..., description="Data source (API, file, FIX)")
    source_reference: Optional[str] = Field(
        None, max_length=255, description="Source reference ID"
    )

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper()


class TradeCreate(TradeBase):
    """Model for creating a new trade."""

    tenant_id: UUID = Field(..., description="Tenant ID for RLS")

    # Optional identifiers for security resolution
    ticker: Optional[str] = Field(None, description="Ticker symbol for security lookup")
    cusip: Optional[str] = Field(None, description="CUSIP for security lookup")
    isin: Optional[str] = Field(None, description="ISIN for security lookup")
    sedol: Optional[str] = Field(None, description="SEDOL for security lookup")

    # External IDs
    trade_id_external: Optional[str] = Field(
        None, max_length=100, description="External trade ID from source system"
    )
    order_id_external: Optional[str] = Field(
        None, max_length=100, description="External order ID"
    )

    # Counterparty info
    broker: Optional[str] = Field(None, max_length=255, description="Executing broker")
    counterparty: Optional[str] = Field(
        None, max_length=255, description="Trade counterparty"
    )

    # Costs
    commission: Optional[Decimal] = Field(None, ge=0, description="Commission amount")
    fees: Optional[Decimal] = Field(None, ge=0, description="Other fees")


class TradeResponse(TradeBase):
    """Trade response model with all fields."""

    id: UUID
    tenant_id: UUID
    trade_id_external: Optional[str] = None
    order_id_external: Optional[str] = None
    notional: Optional[Decimal] = None
    broker: Optional[str] = None
    counterparty: Optional[str] = None
    commission: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    is_cancelled: bool = False
    cancelled_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeList(BaseModel):
    """Paginated list of trades."""

    items: list[TradeResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class TradePnL(BaseModel):
    """Trade P&L calculation result."""

    trade_id: UUID
    realized_pnl: Decimal
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    net_pnl: Decimal
