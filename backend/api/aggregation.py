# RISKCORE Aggregation API Endpoints
# Cross-PM netting, overlap detection, and firm-level aggregation
# THE CORE - Week 4 Aggregation Engine

from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.services.aggregation import AggregationService
from backend.services.netting import NettingService
from backend.services.overlap import OverlapDetectionService, OverlapSeverity

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class NetPositionResponse(BaseModel):
    """Net position for a security across all PMs."""
    security_id: str
    security_name: str
    gross_long_quantity: float
    gross_short_quantity: float
    gross_long_value: float
    gross_short_value: float
    net_quantity: float
    net_value: float
    net_direction: str
    long_book_count: int
    short_book_count: int
    contributing_pm_count: int
    base_currency: str
    as_of_timestamp: Optional[str] = None


class NettingSummaryResponse(BaseModel):
    """Summary of firm-level netting."""
    tenant_id: str
    fund_id: Optional[str] = None
    total_gross_long: float
    total_gross_short: float
    total_gross: float
    total_net: float
    netting_benefit: float
    netting_efficiency_pct: float
    securities_with_offsetting: int
    total_securities: int
    net_long_securities: int
    net_short_securities: int
    flat_securities: int


class PMPositionDetail(BaseModel):
    """PM's position details in an overlap."""
    pm_id: str
    pm_name: str
    direction: Optional[str]
    total_quantity: float
    total_value: float
    book_count: int


class OverlapResponse(BaseModel):
    """Position overlap across PMs."""
    security_id: str
    security_name: str
    overlap_type: str  # same_direction, opposing, mixed
    severity: str  # high, medium, low
    pm_count: int
    pm_positions: List[dict]
    total_long_quantity: float
    total_short_quantity: float
    total_long_value: float
    total_short_value: float
    net_quantity: float
    net_value: float
    concentration_pct: float
    correlation_concern: bool


class OverlapSummaryResponse(BaseModel):
    """Summary of all overlaps."""
    tenant_id: str
    fund_id: Optional[str] = None
    total_overlaps: int
    high_severity: int
    medium_severity: int
    low_severity: int
    same_direction_count: int
    opposing_count: int
    correlation_concerns: int
    top_overlaps: List[dict]


class HierarchyNodeResponse(BaseModel):
    """Node in the firm hierarchy."""
    level: str
    id: Optional[str]
    name: str
    position_count: int
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    children: Optional[List["HierarchyNodeResponse"]] = None


# Allow self-referential model
HierarchyNodeResponse.model_rebuild()


class FirmSummaryResponse(BaseModel):
    """Comprehensive firm summary."""
    tenant_id: str
    as_of: str
    total_positions: int
    unique_securities: int
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    leverage_ratio: float
    long_short_ratio: Optional[float] = None
    fund_count: int
    pm_count: int
    book_count: int
    netting: dict
    overlaps: dict


class PMSummaryResponse(BaseModel):
    """PM-level summary."""
    pm_id: str
    pm_name: str
    tenant_id: str
    total_positions: int
    unique_securities: int
    book_count: int
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    firm_exposure_pct: float
    netting_contribution: dict
    overlap_exposure: dict


class FundSummaryResponse(BaseModel):
    """Fund-level summary."""
    fund_id: str
    fund_name: str
    tenant_id: str
    total_positions: int
    unique_securities: int
    book_count: int
    pm_count: int
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    netting: dict
    overlaps: dict


# =============================================================================
# FIRM-LEVEL ENDPOINTS
# =============================================================================

@router.get("/firm/summary", response_model=FirmSummaryResponse)
def get_firm_summary(
    tenant_id: UUID = Query(..., description="Tenant ID (firm)"),
):
    """
    Get comprehensive firm-level summary.

    Includes:
    - Exposure metrics (gross, net, long, short)
    - Netting summary
    - Overlap summary
    - Hierarchy counts
    """
    with get_db_connection() as conn:
        service = AggregationService(conn)
        try:
            summary = service.get_firm_summary(tenant_id)
            return FirmSummaryResponse(**summary)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


@router.get("/firm/hierarchy")
def get_firm_hierarchy(
    tenant_id: UUID = Query(..., description="Tenant ID (firm)"),
    include_metrics: bool = Query(default=True, description="Include exposure metrics"),
):
    """
    Get firm hierarchy with optional metrics.

    Hierarchy: Firm → Fund → PM → Book

    Returns tree structure with aggregated metrics at each level.
    """
    with get_db_connection() as conn:
        service = AggregationService(conn)
        try:
            hierarchy = service.get_firm_hierarchy(tenant_id, include_metrics)
            return hierarchy.to_dict()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


@router.get("/firm/positions")
def get_firm_positions(
    tenant_id: UUID = Query(..., description="Tenant ID (firm)"),
    netted: bool = Query(default=True, description="Return net positions"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """
    Get firm-level positions.

    Args:
        netted: If True, return net positions across PMs.
                If False, return all raw positions.
    """
    with get_db_connection() as conn:
        service = AggregationService(conn)
        return service.get_firm_positions(tenant_id, netted, page, page_size)


# =============================================================================
# NETTING ENDPOINTS
# =============================================================================

@router.get("/netting/summary", response_model=NettingSummaryResponse)
def get_netting_summary(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
):
    """
    Get firm-level netting summary.

    Shows:
    - Total gross long/short exposure
    - Total net exposure
    - Netting efficiency (reduction from gross to net)
    - Number of securities with offsetting positions
    """
    with get_db_connection() as conn:
        service = NettingService(conn)
        summary = service.get_firm_netting_summary(tenant_id, fund_id)
        return NettingSummaryResponse(**summary)


@router.get("/netting/positions", response_model=List[NetPositionResponse])
def get_net_positions(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
    min_gross_value: Optional[float] = Query(default=None, description="Minimum gross value filter"),
):
    """
    Get all net positions across PMs.

    Returns list of net positions sorted by gross value descending.

    Example:
        PM1 long 1000 AAPL + PM2 short 300 AAPL = net 700 AAPL
    """
    with get_db_connection() as conn:
        service = NettingService(conn)
        min_val = Decimal(str(min_gross_value)) if min_gross_value else None
        net_positions = service.calculate_all_net_positions(tenant_id, fund_id, min_val)
        return [NetPositionResponse(**p.to_dict()) for p in net_positions]


@router.get("/netting/security/{security_id}")
def get_security_netting_detail(
    security_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get detailed netting breakdown for a specific security.

    Shows each book's contribution to the net position.
    """
    with get_db_connection() as conn:
        service = NettingService(conn)
        return service.get_security_netting_detail(tenant_id, security_id)


@router.get("/netting/pm/{pm_id}")
def get_pm_netting_contribution(
    pm_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get a PM's contribution to firm-level netting.

    Shows how much of a PM's positions offset other PMs.
    """
    with get_db_connection() as conn:
        service = NettingService(conn)
        return service.get_pm_contribution_to_netting(tenant_id, pm_id)


# =============================================================================
# OVERLAP DETECTION ENDPOINTS
# =============================================================================

@router.get("/overlaps/summary", response_model=OverlapSummaryResponse)
def get_overlap_summary(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
):
    """
    Get summary of all position overlaps.

    Shows:
    - Total overlaps by severity
    - Same-direction vs opposing counts
    - Correlation concerns
    - Top 5 overlaps
    """
    with get_db_connection() as conn:
        service = OverlapDetectionService(conn)
        summary = service.get_overlap_summary(tenant_id, fund_id)
        return OverlapSummaryResponse(**summary)


@router.get("/overlaps", response_model=List[OverlapResponse])
def get_overlaps(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
    min_pm_count: int = Query(default=2, ge=2, description="Minimum PMs for overlap"),
    min_severity: Optional[str] = Query(default=None, description="Filter by severity: low, medium, high"),
):
    """
    Get all position overlaps across PMs.

    Overlaps occur when 2+ PMs hold the same security.

    Types:
    - same_direction: All PMs in same direction (concentration risk)
    - opposing: Some long, some short (netting opportunity)
    - mixed: Complex case with multiple directions
    """
    with get_db_connection() as conn:
        service = OverlapDetectionService(conn)
        severity = None
        if min_severity:
            try:
                severity = OverlapSeverity(min_severity)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity: {min_severity}. Must be: low, medium, high"
                )

        overlaps = service.detect_overlaps(tenant_id, fund_id, min_pm_count, severity)
        return [OverlapResponse(**o.to_dict()) for o in overlaps]


@router.get("/overlaps/concentration-risks")
def get_concentration_risks(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    threshold_pct: float = Query(default=5.0, ge=0, description="Minimum concentration % to flag"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
):
    """
    Get concentration risks.

    These are same-direction overlaps where multiple PMs hold the same
    security in the same direction, creating correlated risk.
    """
    with get_db_connection() as conn:
        service = OverlapDetectionService(conn)
        return service.detect_concentration_risks(tenant_id, threshold_pct, fund_id)


@router.get("/overlaps/netting-opportunities")
def get_netting_opportunities(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    fund_id: Optional[UUID] = Query(default=None, description="Optional fund filter"),
):
    """
    Get netting opportunities.

    These are opposing overlaps where PMs have opposite positions in the
    same security, which could be netted for capital efficiency.
    """
    with get_db_connection() as conn:
        service = OverlapDetectionService(conn)
        return service.detect_netting_opportunities(tenant_id, fund_id)


@router.get("/overlaps/pm/{pm_id}")
def get_pm_overlap_exposure(
    pm_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get overlap exposure for a specific PM.

    Shows which of a PM's positions overlap with other PMs.
    """
    with get_db_connection() as conn:
        service = OverlapDetectionService(conn)
        return service.get_pm_overlap_exposure(tenant_id, pm_id)


# =============================================================================
# PM-LEVEL ENDPOINTS
# =============================================================================

@router.get("/pm/{pm_id}/summary", response_model=PMSummaryResponse)
def get_pm_summary(
    pm_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get PM-level aggregated summary.

    Includes exposure metrics and contribution to firm netting.
    """
    with get_db_connection() as conn:
        service = AggregationService(conn)
        try:
            summary = service.get_pm_summary(tenant_id, pm_id)
            return PMSummaryResponse(**summary)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


# =============================================================================
# FUND-LEVEL ENDPOINTS
# =============================================================================

@router.get("/fund/{fund_id}/summary", response_model=FundSummaryResponse)
def get_fund_summary(
    fund_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get fund-level aggregated summary.

    Includes exposure metrics and netting/overlap summaries.
    """
    with get_db_connection() as conn:
        service = AggregationService(conn)
        try:
            summary = service.get_fund_summary(tenant_id, fund_id)
            return FundSummaryResponse(**summary)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
