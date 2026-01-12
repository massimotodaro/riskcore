# RISKCORE Correlation API Endpoints
# PM-to-PM and Pod-to-Pod correlation analysis
# Week 4 Enhancement: Foundation for AI-native queries

from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.services.returns import ReturnsService, ReturnWindow
from backend.services.realized_correlation import (
    RealizedCorrelationService,
    CorrelationEntityType,
    CorrelationType,
)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class CorrelationResponse(BaseModel):
    """Single correlation result."""
    entity1_id: str
    entity1_name: str
    entity2_id: str
    entity2_name: str
    entity_type: str
    correlation_type: str
    window: str
    correlation: float
    strength: str
    is_concerning: bool
    data_points: int
    as_of_date: Optional[str] = None


class PMCorrelationMatrixResponse(BaseModel):
    """Full PM correlation matrix."""
    tenant_id: str
    window: str
    correlation_type: str
    pm_count: int
    pm_names: List[str]
    pm_ids: List[str]
    matrix: List[List[float]]
    as_of_date: str
    high_correlation_count: int
    high_correlation_pairs: List[dict]


class ReturnSummaryResponse(BaseModel):
    """Return summary for an entity."""
    entity_id: str
    entity_name: str
    windows: dict


# =============================================================================
# PM CORRELATION ENDPOINTS
# =============================================================================

@router.get("/pm/{pm1_id}/correlation/{pm2_id}")
def get_pm_correlation(
    pm1_id: UUID,
    pm2_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    window: str = Query(default="21d", description="Window: 1d, 5d, 21d, 63d"),
):
    """
    Get realized correlation between two PMs.

    Returns correlation coefficient based on historical returns.
    Window options: 1d (yesterday), 5d (week), 21d (month), 63d (quarter)
    """
    try:
        return_window = ReturnWindow(window)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid window: {window}. Must be: 1d, 5d, 21d, 63d, 252d"
        )

    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        result = service.calculate_pm_correlation(
            tenant_id, pm1_id, pm2_id, return_window
        )
        return result.to_dict()


@router.get("/pm/{pm1_id}/correlation/{pm2_id}/all-windows")
def get_pm_correlation_all_windows(
    pm1_id: UUID,
    pm2_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get PM correlation for all standard time windows.

    Returns correlations for 1d, 5d, 21d, and 63d windows.
    Useful for seeing how correlation changes over time.
    """
    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        results = service.calculate_pm_correlation_all_windows(tenant_id, pm1_id, pm2_id)
        return {window: result.to_dict() for window, result in results.items()}


@router.get("/pm/{pm1_id}/correlation/{pm2_id}/analysis")
def get_pm_correlation_analysis(
    pm1_id: UUID,
    pm2_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get comprehensive correlation analysis between two PMs.

    **This is the main endpoint for AI queries like:**
    "Show me the correlation between PM Smith and PM Jones"

    Returns:
    - Realized correlations for all windows (1d, 5d, 21d, 63d)
    - Implied correlation from portfolio structure
    - Pod exposure breakdown for both PMs
    - Risk analysis and recommendations
    """
    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        return service.get_pm_correlation_analysis(tenant_id, pm1_id, pm2_id)


@router.get("/pm/{pm1_id}/correlation/{pm2_id}/implied")
def get_pm_implied_correlation(
    pm1_id: UUID,
    pm2_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get implied correlation between two PMs based on portfolio structure.

    Implied correlation is forward-looking, estimated from:
    - Security overlap (common holdings)
    - RiskPod exposure similarity

    Higher implied correlation suggests future returns will be correlated.
    """
    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        result = service.calculate_implied_pm_correlation(tenant_id, pm1_id, pm2_id)
        return result.to_dict()


# =============================================================================
# CORRELATION MATRIX ENDPOINTS
# =============================================================================

@router.get("/pm/matrix", response_model=PMCorrelationMatrixResponse)
def get_pm_correlation_matrix(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    window: str = Query(default="21d", description="Window: 1d, 5d, 21d, 63d"),
):
    """
    Get full PM-to-PM correlation matrix.

    Returns a symmetric matrix with correlation coefficients between all PMs.
    Also identifies high correlation pairs (|corr| >= 0.7) that may indicate
    concentration risk.
    """
    try:
        return_window = ReturnWindow(window)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid window: {window}. Must be: 1d, 5d, 21d, 63d, 252d"
        )

    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        matrix = service.build_pm_correlation_matrix(tenant_id, return_window)
        return PMCorrelationMatrixResponse(**matrix.to_dict())


@router.get("/pm/high-correlations")
def get_high_pm_correlations(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    threshold: float = Query(default=0.7, ge=0, le=1, description="Correlation threshold"),
    window: str = Query(default="21d", description="Window: 1d, 5d, 21d, 63d"),
):
    """
    Get PM pairs with high correlations.

    Identifies PM pairs where |correlation| >= threshold.
    These pairs may represent concentration risk.
    """
    try:
        return_window = ReturnWindow(window)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid window: {window}"
        )

    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        matrix = service.build_pm_correlation_matrix(tenant_id, return_window)

        # Filter by threshold
        high_pairs = [
            p.to_dict() for p in matrix.high_correlation_pairs
            if abs(p.correlation) >= threshold
        ]

        return {
            "tenant_id": str(tenant_id),
            "window": window,
            "threshold": threshold,
            "high_correlation_count": len(high_pairs),
            "pairs": high_pairs,
        }


# =============================================================================
# RETURN ENDPOINTS
# =============================================================================

@router.get("/pm/{pm_id}/returns")
def get_pm_returns(
    pm_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    window: str = Query(default="21d", description="Window: 1d, 5d, 21d, 63d"),
):
    """
    Get return time series for a PM.

    Returns daily P&L and returns for the specified window.
    """
    try:
        return_window = ReturnWindow(window)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid window: {window}"
        )

    with get_db_connection() as conn:
        service = ReturnsService(conn)
        series = service.get_pm_returns(tenant_id, pm_id, return_window)
        return series.to_dict()


@router.get("/pm/{pm_id}/returns/summary")
def get_pm_return_summary(
    pm_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get return summary for a PM across all windows.

    Returns total P&L and average returns for 1d, 5d, 21d, 63d.
    """
    with get_db_connection() as conn:
        service = ReturnsService(conn)
        return service.get_pm_return_summary(tenant_id, pm_id)


@router.get("/firm/returns/summary")
def get_firm_return_summary(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    return_date: Optional[str] = Query(default=None, description="Date (YYYY-MM-DD)"),
):
    """
    Get firm-wide return summary for a date.

    Returns:
    - Total firm P&L
    - P&L breakdown by RiskPod
    - Top and bottom performing PMs
    """
    date_obj = None
    if return_date:
        try:
            date_obj = date.fromisoformat(return_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    with get_db_connection() as conn:
        service = ReturnsService(conn)
        return service.get_firm_return_summary(tenant_id, date_obj)


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("/pm/refresh-cache")
def refresh_pm_correlation_cache(
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Refresh PM correlation cache.

    Recalculates all PM correlations for all windows and caches the results.
    Call this after daily return capture to update correlations.
    """
    with get_db_connection() as conn:
        service = RealizedCorrelationService(conn)
        service.refresh_all_pm_correlations(tenant_id)
        return {"status": "success", "message": "PM correlation cache refreshed"}


@router.post("/book/{book_id}/capture-return")
def capture_book_return(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    return_date: str = Query(..., description="Date (YYYY-MM-DD)"),
    daily_pnl: float = Query(..., description="Daily P&L"),
    start_nav: Optional[float] = Query(default=None, description="Start of day NAV"),
    end_nav: Optional[float] = Query(default=None, description="End of day NAV"),
):
    """
    Capture daily return for a book.

    This endpoint would be called by an EOD process to record daily returns.
    """
    try:
        date_obj = date.fromisoformat(return_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    from decimal import Decimal

    with get_db_connection() as conn:
        service = ReturnsService(conn)
        result = service.capture_book_daily_return(
            tenant_id=tenant_id,
            book_id=book_id,
            return_date=date_obj,
            daily_pnl=Decimal(str(daily_pnl)),
            start_nav=Decimal(str(start_nav)) if start_nav else None,
            end_nav=Decimal(str(end_nav)) if end_nav else None,
        )
        return result


@router.post("/pm/aggregate-returns")
def aggregate_pm_returns(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    return_date: str = Query(..., description="Date (YYYY-MM-DD)"),
):
    """
    Aggregate book returns to PM level for a date.

    Call this after capturing all book returns for a day.
    """
    try:
        date_obj = date.fromisoformat(return_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    with get_db_connection() as conn:
        service = ReturnsService(conn)
        results = service.aggregate_pm_daily_returns(tenant_id, date_obj)
        return {
            "status": "success",
            "pm_count": len(results),
            "date": return_date,
        }
