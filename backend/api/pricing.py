# RISKCORE Pricing API Endpoints
# Pricing runs and valuation services

from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.services.pricing_service import PricingService, ValuationService

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class PricingRunInfo(BaseModel):
    """Information about a pricing run."""
    id: Optional[str] = None
    trigger_type: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    securities_priced: int = 0
    securities_failed: int = 0
    status: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class PricingStatusResponse(BaseModel):
    """Pricing status for a tenant."""
    latest_run: Optional[PricingRunInfo] = None
    price_sources: Dict[str, int]
    stale_price_count: int


class RepriceResponse(BaseModel):
    """Response from reprice operation."""
    run_id: str
    status: str
    securities_priced: int
    securities_failed: int
    message: str


class SecurityPriceResponse(BaseModel):
    """Security price details."""
    security_id: str
    security_name: str
    asset_class: str
    price: float
    price_date: str
    price_source: str
    model_id: Optional[str] = None
    is_stale: bool


class PriceOverrideRequest(BaseModel):
    """Request to override a security price."""
    price: float = Field(..., gt=0, description="New price value")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for override")


class PriceOverrideResponse(BaseModel):
    """Response from price override."""
    security_id: str
    price: float
    price_date: str
    price_source: str
    updated_by: str
    reason: Optional[str] = None


class ModelInputs(BaseModel):
    """Model valuation inputs."""
    model_name: str
    model_version: Optional[str] = None
    inputs: Dict[str, Any]
    model_price: Optional[float] = None
    has_override: bool = False
    override_inputs: Optional[Dict[str, Any]] = None
    override_by: Optional[str] = None
    override_at: Optional[str] = None
    override_reason: Optional[str] = None
    calculated_at: Optional[str] = None


class ValuationResponse(BaseModel):
    """Position valuation details."""
    position_id: str
    security_id: str
    ticker: Optional[str] = None
    security_name: str
    asset_class: str
    security_type: Optional[str] = None
    book_id: str
    quantity: float
    direction: str
    current_price: float
    market_value: float
    price_source: str
    price_as_of: Optional[str] = None
    has_model_details: bool
    model_inputs: Optional[ModelInputs] = None
    can_override: bool


class ModelOverrideRequest(BaseModel):
    """Request to override model inputs."""
    override_inputs: Dict[str, Any] = Field(..., description="New model input values")
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for override")


class ModelOverrideResponse(BaseModel):
    """Response from model override."""
    model_id: str
    has_override: bool
    override_inputs: Dict[str, Any]
    override_by: str
    override_reason: str
    message: str


# =============================================================================
# PRICING STATUS ENDPOINTS
# =============================================================================

@router.get("/status", response_model=PricingStatusResponse)
def get_pricing_status(
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get pricing status for a tenant.

    Returns:
    - Latest pricing run information
    - Distribution of price sources (market, model, manual, stale)
    - Count of securities with stale prices

    Used by: TopBar component (last priced timestamp)
    """
    with get_db_connection() as conn:
        service = PricingService(conn)
        result = service.get_pricing_status(tenant_id)

        return PricingStatusResponse(
            latest_run=PricingRunInfo(**result['latest_run']) if result['latest_run'] else None,
            price_sources=result['price_sources'],
            stale_price_count=result['stale_price_count'],
        )


@router.post("/reprice-all", response_model=RepriceResponse)
def trigger_reprice_all(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(default=None, description="User triggering the reprice"),
):
    """
    Trigger a full reprice of all securities.

    This will:
    1. Fetch latest prices from market data (OpenBB)
    2. Run FinancePy models for derivatives
    3. Update all security prices
    4. Update position market values

    Note: This is a placeholder - actual pricing integration with OpenBB
    and FinancePy would be implemented in production.

    Used by: "Reprice All" button in Riskboard
    """
    with get_db_connection() as conn:
        service = PricingService(conn)
        result = service.trigger_reprice_all(tenant_id, user_id)

        return RepriceResponse(**result)


# =============================================================================
# SECURITY PRICE ENDPOINTS
# =============================================================================

@router.get("/security/{security_id}", response_model=SecurityPriceResponse)
def get_security_price(
    security_id: UUID,
):
    """
    Get the latest price for a security.

    Returns price with source information and stale indicator.
    """
    with get_db_connection() as conn:
        service = PricingService(conn)
        result = service.get_security_price(security_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price not found for security {security_id}"
            )

        return SecurityPriceResponse(**result)


@router.put("/security/{security_id}/override", response_model=PriceOverrideResponse)
def override_security_price(
    security_id: UUID,
    request: PriceOverrideRequest,
    user_id: UUID = Query(..., description="User making the override"),
):
    """
    Manually override a security's price.

    This creates a new price entry with source='manual'.

    Used by: Valuation popup "Save Override" button
    """
    with get_db_connection() as conn:
        service = PricingService(conn)
        result = service.update_price_manual(
            security_id=security_id,
            price=Decimal(str(request.price)),
            user_id=user_id,
            reason=request.reason,
        )

        return PriceOverrideResponse(**result)


# =============================================================================
# VALUATION ENDPOINTS
# =============================================================================

@router.get("/valuation/{position_id}", response_model=ValuationResponse)
def get_position_valuation(
    position_id: UUID,
):
    """
    Get valuation details for a position.

    Returns:
    - Current price and source
    - Model inputs (if model-derived)
    - Override information (if any)

    Used by: Valuation popup in Riskboard
    """
    with get_db_connection() as conn:
        service = ValuationService(conn)
        result = service.get_position_valuation(position_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {position_id} not found"
            )

        return ValuationResponse(**result)


@router.put("/valuation/{position_id}/override", response_model=ModelOverrideResponse)
def override_model_inputs(
    position_id: UUID,
    request: ModelOverrideRequest,
    user_id: UUID = Query(..., description="User making the override"),
):
    """
    Override model inputs for a position's valuation.

    This allows authorized users to adjust model parameters
    (e.g., spread, volatility, recovery rate) for model-derived prices.

    Used by: Valuation popup "Save Override" button (for model-priced positions)
    """
    with get_db_connection() as conn:
        service = ValuationService(conn)
        try:
            result = service.override_model_inputs(
                position_id=position_id,
                override_inputs=request.override_inputs,
                user_id=user_id,
                reason=request.reason,
            )

            return ModelOverrideResponse(**result)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/valuation/{position_id}/recalculate")
def recalculate_position(
    position_id: UUID,
):
    """
    Recalculate a position's valuation.

    Reruns the pricing model with current inputs (including overrides).

    Note: This is a placeholder - actual FinancePy integration
    would be implemented in production.

    Used by: Valuation popup "Recalculate" button
    """
    with get_db_connection() as conn:
        service = ValuationService(conn)
        result = service.recalculate_position(position_id)

        return result
