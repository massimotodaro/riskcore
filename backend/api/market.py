# RISKCORE Market Data API Endpoints
# Market indices for dashboard snapshot

from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.services.market_data_service import MarketDataService

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class MarketIndex(BaseModel):
    """Market index data."""
    symbol: str
    name: str
    value: float
    formatted_value: str
    change_pct: float
    change_direction: str  # 'up', 'down', 'flat'
    sparkline: List[float]
    category: str
    as_of: str


class MarketSnapshotResponse(BaseModel):
    """Market snapshot response."""
    indices: List[MarketIndex]
    as_of: str


class AvailableSymbolsResponse(BaseModel):
    """Available market symbols."""
    symbols: List[str]
    categories: dict


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/snapshot", response_model=MarketSnapshotResponse)
def get_market_snapshot(
    symbols: Optional[str] = Query(
        default=None,
        description="Comma-separated symbols (default: SPX,VIX,US10Y,EURUSD)"
    ),
):
    """
    Get market snapshot for dashboard.

    Returns current values, change percentages, and sparklines for
    major market indices.

    Used by: MarketSnapshot component in Riskboard TopBar

    Default symbols:
    - SPX: S&P 500
    - VIX: Volatility Index
    - US10Y: 10-Year Treasury Yield
    - EURUSD: EUR/USD Exchange Rate
    """
    service = MarketDataService(use_live=False)  # Demo mode

    # Parse symbols
    symbol_list = None
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

    data = service.get_market_snapshot(symbol_list)

    from datetime import datetime, timezone
    return MarketSnapshotResponse(
        indices=[MarketIndex(**d) for d in data],
        as_of=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/quote/{symbol}", response_model=MarketIndex)
def get_single_quote(symbol: str):
    """
    Get quote for a single market symbol.

    Returns current value, change, and sparkline for the symbol.
    """
    service = MarketDataService(use_live=False)
    result = service.get_single_quote(symbol.upper())

    if not result:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} not found"
        )

    return MarketIndex(**result)


@router.get("/symbols", response_model=AvailableSymbolsResponse)
def get_available_symbols():
    """
    Get list of available market symbols.

    Returns symbols grouped by category (equity, rates, fx, etc.)
    """
    service = MarketDataService(use_live=False)

    return AvailableSymbolsResponse(
        symbols=service.get_available_symbols(),
        categories=service.get_symbol_categories(),
    )
