# RISKCORE Risk API Endpoints
# VaR, exposures, and Greeks endpoints

from typing import Optional, List
from uuid import UUID
from datetime import date
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.services.risk_engine import RiskEngine, VaRMethod, RiskMetricType, MetricLevel
from backend.services.exposures import ExposureService, ExposureDimension
from backend.services.greeks import GreeksService, OptionType

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class VaRRequest(BaseModel):
    """Request for VaR calculation."""
    book_id: UUID
    tenant_id: UUID
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.999)
    horizon_days: int = Field(default=1, ge=1, le=30)
    method: str = Field(default="historical")


class VaRResponse(BaseModel):
    """VaR calculation response."""
    book_id: str
    var: float
    var_pct: Optional[float] = None
    cvar: float
    cvar_pct: Optional[float] = None
    confidence_level: float
    horizon_days: int
    method: str
    position_count: int
    total_market_value: float
    lookback_days: Optional[int] = None
    note: Optional[str] = None
    error: Optional[str] = None


class ExposureBreakdownItem(BaseModel):
    """Single item in exposure breakdown."""
    dimension_value: str
    long_value: float
    short_value: float
    net_value: float
    gross_value: float
    gross_pct: float
    net_pct: float
    position_count: int


class ExposureResponse(BaseModel):
    """Exposure breakdown response."""
    book_id: str
    dimension: str
    breakdown: List[ExposureBreakdownItem]
    total_exposure: float
    position_count: int
    error: Optional[str] = None


class ConcentrationResponse(BaseModel):
    """Concentration metrics response."""
    book_id: str
    top_10_concentration: float
    single_name_max: float
    single_name_max_security: Optional[str] = None
    sector_hhi: float
    position_count: int
    total_gross_exposure: float


class ExposureSummaryResponse(BaseModel):
    """Exposure summary response."""
    book_id: str
    long_exposure: float
    short_exposure: float
    net_exposure: float
    gross_exposure: float
    long_short_ratio: Optional[float] = None
    leverage_ratio: float
    position_count: int


class GreeksRequest(BaseModel):
    """Request for Greeks calculation."""
    spot_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    time_to_expiry: float = Field(ge=0, description="Years to expiry")
    volatility: float = Field(default=0.20, gt=0, le=2.0)
    risk_free_rate: float = Field(default=0.05, ge=0, le=0.5)
    option_type: str = Field(default="call")


class GreeksResponse(BaseModel):
    """Greeks calculation response."""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    spot_price: float
    strike_price: float
    time_to_expiry: float
    volatility: float
    option_type: str


class BookGreeksResponse(BaseModel):
    """Book-level Greeks response."""
    book_id: str
    option_count: int
    net_delta: float
    net_gamma: float
    net_vega: float
    net_theta: float
    net_rho: float
    note: Optional[str] = None


class RiskMetricResponse(BaseModel):
    """Risk metric response."""
    id: str
    tenant_id: str
    level: str
    book_id: Optional[str] = None
    metric_type: str
    value: float
    unit: Optional[str] = None
    as_of_timestamp: str


# =============================================================================
# VaR Endpoints
# =============================================================================

@router.get("/var/{book_id}", response_model=VaRResponse)
def calculate_book_var(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    confidence_level: float = Query(default=0.95, ge=0.90, le=0.999),
    horizon_days: int = Query(default=1, ge=1, le=30),
    method: str = Query(default="historical", pattern="^(historical|parametric|monte_carlo)$"),
):
    """
    Calculate VaR (Value at Risk) for a book.

    VaR represents the maximum expected loss at a given confidence level
    over a specified time horizon.

    - **confidence_level**: 0.95 (95%) or 0.99 (99%) typical
    - **horizon_days**: 1 (daily) or 10 (10-day) typical
    - **method**: historical, parametric, or monte_carlo
    """
    with get_db_connection() as conn:
        risk_engine = RiskEngine(conn)

        var_method = VaRMethod(method)
        result = risk_engine.calculate_book_var(
            book_id=book_id,
            tenant_id=tenant_id,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            method=var_method,
        )

        return VaRResponse(**result)


@router.post("/var/calculate-all/{book_id}")
def calculate_and_save_all_var(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    method: str = Query(default="historical"),
):
    """
    Calculate all VaR/CVaR metrics for a book and save to database.

    Calculates and persists:
    - VaR 95% (1-day, 10-day)
    - VaR 99% (1-day, 10-day)
    - CVaR 95%, CVaR 99%
    """
    with get_db_connection() as conn:
        risk_engine = RiskEngine(conn)

        var_method = VaRMethod(method)
        result = risk_engine.calculate_and_save_all_var_metrics(
            book_id=book_id,
            tenant_id=tenant_id,
            method=var_method,
        )

        return {
            "book_id": str(book_id),
            "metrics_saved": 6,
            "var_95_1d": result["var_95_1d"]["var"],
            "var_99_1d": result["var_99_1d"]["var"],
            "var_95_10d": result["var_95_10d"]["var"],
            "var_99_10d": result["var_99_10d"]["var"],
            "cvar_95": result["cvar_95"],
            "cvar_99": result["cvar_99"],
        }


# =============================================================================
# Exposure Endpoints
# =============================================================================

@router.get("/exposures/{book_id}", response_model=ExposureResponse)
def get_exposure_breakdown(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    dimension: str = Query(default="sector", pattern="^(sector|geography|asset_class|currency)$"),
):
    """
    Get exposure breakdown by dimension.

    - **sector**: Industry sector breakdown
    - **geography**: Country/region breakdown
    - **asset_class**: Asset class breakdown (equity, fixed_income, etc.)
    - **currency**: Currency exposure breakdown
    """
    with get_db_connection() as conn:
        exposure_service = ExposureService(conn)

        dim = ExposureDimension(dimension)
        result = exposure_service.calculate_exposure_breakdown(
            book_id=book_id,
            tenant_id=tenant_id,
            dimension=dim,
        )

        return ExposureResponse(**result)


@router.get("/exposures/{book_id}/all")
def get_all_exposures(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """Get all exposure breakdowns for a book."""
    with get_db_connection() as conn:
        exposure_service = ExposureService(conn)

        return exposure_service.calculate_all_exposures(
            book_id=book_id,
            tenant_id=tenant_id,
        )


@router.get("/exposures/{book_id}/summary", response_model=ExposureSummaryResponse)
def get_exposure_summary(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get exposure summary for a book.

    Returns long, short, net, and gross exposures with leverage ratio.
    """
    with get_db_connection() as conn:
        exposure_service = ExposureService(conn)

        return exposure_service.calculate_exposure_summary(
            book_id=book_id,
            tenant_id=tenant_id,
        )


@router.get("/exposures/{book_id}/concentration", response_model=ConcentrationResponse)
def get_concentration_metrics(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get concentration metrics for a book.

    Returns:
    - Top 10 concentration (% of portfolio in top 10 positions)
    - Single name max (largest single position %)
    - Sector HHI (Herfindahl-Hirschman Index for sector concentration)
    """
    with get_db_connection() as conn:
        exposure_service = ExposureService(conn)

        return exposure_service.calculate_concentration_metrics(
            book_id=book_id,
            tenant_id=tenant_id,
        )


# =============================================================================
# Greeks Endpoints
# =============================================================================

@router.post("/greeks/calculate", response_model=GreeksResponse)
def calculate_greeks(request: GreeksRequest):
    """
    Calculate option Greeks for given parameters.

    Returns delta, gamma, vega, theta, and rho for a vanilla option.
    """
    with get_db_connection() as conn:
        greeks_service = GreeksService(conn)

        opt_type = OptionType.CALL if request.option_type.lower() == "call" else OptionType.PUT

        result = greeks_service.calculate_all_greeks(
            spot_price=request.spot_price,
            strike_price=request.strike_price,
            time_to_expiry=request.time_to_expiry,
            risk_free_rate=request.risk_free_rate,
            volatility=request.volatility,
            option_type=opt_type,
        )

        return GreeksResponse(**result)


@router.get("/greeks/position/{position_id}")
def get_position_greeks(
    position_id: UUID,
    volatility: float = Query(default=0.20, gt=0, le=2.0),
    risk_free_rate: float = Query(default=0.05, ge=0, le=0.5),
):
    """
    Calculate Greeks for an options position.

    Uses position's security details to determine option parameters.
    """
    with get_db_connection() as conn:
        greeks_service = GreeksService(conn)

        result = greeks_service.calculate_position_greeks(
            position_id=position_id,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result


@router.get("/greeks/book/{book_id}", response_model=BookGreeksResponse)
def get_book_greeks(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    volatility: float = Query(default=0.20, gt=0, le=2.0),
    risk_free_rate: float = Query(default=0.05, ge=0, le=0.5),
):
    """
    Calculate aggregate Greeks for all options in a book.

    Returns net delta, gamma, vega, theta, and rho for the book.
    """
    with get_db_connection() as conn:
        greeks_service = GreeksService(conn)

        result = greeks_service.calculate_book_greeks(
            book_id=book_id,
            tenant_id=tenant_id,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        )

        return BookGreeksResponse(**result)


# =============================================================================
# Risk Metrics Storage Endpoints
# =============================================================================

@router.get("/metrics/{book_id}")
def get_book_risk_metrics(
    book_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_types: Optional[str] = Query(None, description="Comma-separated metric types"),
):
    """
    Get latest risk metrics for a book.

    Optionally filter by metric types (e.g., "var_95_1d,cvar_95").
    """
    with get_db_connection() as conn:
        risk_engine = RiskEngine(conn)

        types = None
        if metric_types:
            types = [RiskMetricType(t.strip()) for t in metric_types.split(",")]

        metrics = risk_engine.get_latest_risk_metrics(
            tenant_id=tenant_id,
            book_id=book_id,
            metric_types=types,
        )

        return {
            "book_id": str(book_id),
            "metrics": metrics,
        }
