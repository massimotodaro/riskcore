# RISKCORE Riskboard API Endpoints
# Dashboard API for CIO/PM unified risk view
# NO P&L - Risk metrics and correlation analysis only

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.services.riskpod import RiskPodService

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class AssetClassRisk(BaseModel):
    """Risk metrics for a single asset class."""
    asset_class: str
    asset_class_display: str
    position_count: int
    book_count: int
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    dv01: float
    cs01: float
    convexity: float
    primary_risk_metric: str
    primary_risk_value: float


class RiskSummary(BaseModel):
    """Risk summary for top bar."""
    nav: float
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    position_count: int
    security_count: int
    book_count: int
    total_delta: float
    total_dv01: float
    total_cs01: float
    last_priced: Optional[str] = None


class BookInfo(BaseModel):
    """Book information for portfolio selector."""
    book_id: str
    name: str
    book_type: str
    strategy: Optional[str] = None
    pm_id: Optional[str] = None
    pm_name: Optional[str] = None
    fund_name: Optional[str] = None


class PositionOverlapItem(BaseModel):
    """Position held by multiple books."""
    security_id: str
    ticker: Optional[str] = None
    security_name: str
    asset_class: str
    book_count: int
    books: List[str]
    book_ids: List[str]
    net_quantity: float
    gross_exposure: float
    net_exposure: float
    netting_opportunity: float
    net_delta: float
    net_dv01: float
    net_cs01: float


class ConcentrationItem(BaseModel):
    """Concentration risk item."""
    sector: Optional[str] = None
    security_id: Optional[str] = None
    ticker: Optional[str] = None
    security_name: Optional[str] = None
    asset_class: Optional[str] = None
    security_count: Optional[int] = None
    book_count: int
    gross_exposure: float
    net_exposure: float
    percentage: float
    is_warning: bool


class PositionDetail(BaseModel):
    """Position detail for trades drill-down."""
    position_id: str
    book_id: str
    book_name: str
    security_id: str
    ticker: Optional[str] = None
    security_name: str
    asset_class: str
    direction: str
    quantity: float
    cost_basis: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    delta: float
    gamma: float
    vega: float
    theta: float
    dv01: float
    cs01: float
    price_source: str
    price_date: Optional[str] = None
    has_model_details: bool


class PositionsResponse(BaseModel):
    """Paginated positions response."""
    positions: List[PositionDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# RISK SUMMARY ENDPOINTS
# =============================================================================

@router.get("/summary", response_model=RiskSummary)
def get_risk_summary(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    book_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated book IDs (optional - all books if not provided)"
    ),
):
    """
    Get risk summary for the Riskboard top bar.

    Returns NAV, gross/net exposures, position counts, and last pricing timestamp.

    Used by: TopBar component
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids if provided
        book_id_list = None
        if book_ids:
            try:
                book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid book_ids format. Use comma-separated UUIDs."
                )

        result = service.get_risk_summary(tenant_id, book_id_list)
        return RiskSummary(**result)


# =============================================================================
# RISK BY ASSET CLASS ENDPOINTS (RiskPod Cards)
# =============================================================================

@router.get("/risk-by-asset-class", response_model=List[AssetClassRisk])
def get_risk_by_asset_class(
    book_ids: str = Query(..., description="Comma-separated book IDs"),
):
    """
    Get risk aggregated by asset class for selected books.

    This is the core endpoint for RiskPod cards. Returns 5 asset class
    categories: equity, rates (fixed_income), credit (cds), fx, other.

    Used by: RiskCard components
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids
        try:
            book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid book_ids format. Use comma-separated UUIDs."
            )

        if not book_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one book_id is required."
            )

        results = service.get_risk_by_asset_class_multi_book(book_id_list)
        return [AssetClassRisk(**r) for r in results]


# =============================================================================
# BOOKS ENDPOINT (Portfolio Selector)
# =============================================================================

@router.get("/books", response_model=List[BookInfo])
def get_books(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    book_type: Optional[str] = Query(
        default=None,
        description="Filter by type: 'trading' or 'overlay'"
    ),
):
    """
    Get all books for portfolio selector.

    Returns book list filtered by user permissions (handled at auth layer).
    Supports filtering by book_type for separating trading vs overlay books.

    Used by: PortfolioSelector component
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)
        results = service.get_all_books(tenant_id, book_type)
        return [BookInfo(**r) for r in results]


# =============================================================================
# CORRELATION PANEL ENDPOINTS
# =============================================================================

@router.get("/position-overlap", response_model=List[PositionOverlapItem])
def get_position_overlap(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    book_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated book IDs to filter overlaps"
    ),
):
    """
    Get position overlaps for correlation analysis.

    Shows securities held by multiple books with netting opportunities.
    Sorted by netting opportunity (highest first).

    Used by: CorrelationPanel component - Position Overlap section
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids if provided
        book_id_list = None
        if book_ids:
            try:
                book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid book_ids format. Use comma-separated UUIDs."
                )

        results = service.get_position_overlap(tenant_id, book_id_list)
        return [PositionOverlapItem(**r) for r in results]


@router.get("/concentration/sector", response_model=List[ConcentrationItem])
def get_concentration_by_sector(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    book_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated book IDs (optional)"
    ),
):
    """
    Get sector concentration for correlation panel.

    Shows exposure by sector with warning flags for >40% concentration.

    Used by: CorrelationPanel component - Concentration Risk section
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids if provided
        book_id_list = None
        if book_ids:
            try:
                book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid book_ids format. Use comma-separated UUIDs."
                )

        results = service.get_concentration_by_sector(tenant_id, book_id_list)
        return [ConcentrationItem(**r) for r in results]


@router.get("/concentration/security", response_model=List[ConcentrationItem])
def get_concentration_by_security(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    book_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated book IDs (optional)"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
):
    """
    Get single-name concentration for correlation panel.

    Shows top securities by exposure with warning flags for >10% concentration.

    Used by: CorrelationPanel component - Concentration Risk section
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids if provided
        book_id_list = None
        if book_ids:
            try:
                book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid book_ids format. Use comma-separated UUIDs."
                )

        results = service.get_concentration_by_security(tenant_id, book_id_list, limit)
        return [ConcentrationItem(**r) for r in results]


# =============================================================================
# TRADES DRILL-DOWN ENDPOINTS
# =============================================================================

@router.get("/positions", response_model=PositionsResponse)
def get_positions_by_asset_class(
    book_ids: str = Query(..., description="Comma-separated book IDs"),
    asset_class: str = Query(..., description="Asset class filter"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
):
    """
    Get positions filtered by books and asset class.

    Returns paginated list of positions with valuation info for the trades
    drill-down page. Includes price source and model details flag.

    Used by: PositionsDrilldown page
    """
    with get_db_connection() as conn:
        service = RiskPodService(conn)

        # Parse book_ids
        try:
            book_id_list = [UUID(bid.strip()) for bid in book_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid book_ids format. Use comma-separated UUIDs."
            )

        if not book_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one book_id is required."
            )

        result = service.get_positions_by_asset_class(
            book_id_list, asset_class, page, page_size
        )

        return PositionsResponse(
            positions=[PositionDetail(**p) for p in result['positions']],
            total=result['total'],
            page=result['page'],
            page_size=result['page_size'],
            total_pages=result['total_pages'],
        )
