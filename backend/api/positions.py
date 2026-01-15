# RISKCORE Position API Endpoints
# On-premises PostgreSQL - NO CLOUD STORAGE

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional
from datetime import datetime
from decimal import Decimal
import logging

import psycopg2

from ..database import get_db_connection
from ..models.position import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionList,
)
from ..services.position_service import PositionService
from ..services.composition_service import CompositionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PositionList)
def list_positions(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    book_id: Optional[UUID] = Query(None, description="Filter by book"),
    security_id: Optional[UUID] = Query(None, description="Filter by security"),
    direction: Optional[str] = Query(None, description="Filter by direction (long/short/flat)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    List positions with optional filtering.

    - **tenant_id**: Filter positions by tenant
    - **book_id**: Filter positions by book/portfolio
    - **security_id**: Filter positions by security
    - **direction**: Filter by position direction (long, short, flat)
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)
            result = service.list_positions(
                tenant_id=tenant_id,
                book_id=book_id,
                security_id=security_id,
                direction=direction,
                page=page,
                page_size=page_size,
            )

            # Convert to response model
            return PositionList(
                items=[PositionResponse(**item) for item in result["items"]],
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
                total_pages=result["total_pages"],
            )
    except Exception as e:
        logger.error(f"Error listing positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list positions: {str(e)}",
        )


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Get a specific position by ID.

    - **position_id**: UUID of the position to retrieve
    - **tenant_id**: Optional tenant ID for row-level security
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)
            position = service.get_position(position_id, tenant_id)

            if not position:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found",
                )

            return PositionResponse(**position)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get position: {str(e)}",
        )


@router.post("/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(position: PositionCreate):
    """
    Create a new position.

    **Security resolution:**
    - If `security_id` provided, uses it directly
    - If `ticker`, `cusip`, `isin`, or `sedol` provided, resolves via security_identifiers table

    **Validation:**
    - Book must exist and belong to tenant
    - Security must exist (or be resolvable)
    - Quantity must be positive
    - Required fields: tenant_id, book_id, security_id (or identifier), quantity, direction, source, as_of_timestamp

    **P&L Calculation:**
    - If price provided, calculates market_value = quantity * price
    - If cost_basis provided, calculates unrealized_pnl = market_value - cost_basis
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)

            # Resolve security_id if not provided
            security_id = position.security_id

            if not security_id:
                # Try to resolve from identifiers
                security_id = service.resolve_security_id(
                    ticker=position.ticker,
                    cusip=position.cusip,
                    isin=position.isin,
                    sedol=position.sedol,
                )

                if not security_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Could not resolve security. Provide security_id or a valid identifier (ticker, cusip, isin, sedol).",
                    )

            # Validate book exists
            if not service.validate_book_exists(position.book_id, position.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Book {position.book_id} not found or does not belong to tenant {position.tenant_id}",
                )

            # Validate security exists
            if not service.validate_security_exists(security_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security {security_id} not found. Create the security first or use an identifier for auto-resolution.",
                )

            # Create position
            result = service.create_position(
                tenant_id=position.tenant_id,
                book_id=position.book_id,
                security_id=security_id,
                quantity=position.quantity,
                direction=position.direction.value,
                source=position.source.value,
                as_of_timestamp=position.as_of_timestamp,
                price=position.price,
                price_source=position.price_source.value if position.price_source else "market",
                price_as_of=position.price_as_of,
                local_currency=position.local_currency,
                base_currency=position.base_currency,
                fx_rate=position.fx_rate,
                cost_basis=position.cost_basis,
                source_reference=position.source_reference,
            )

            return PositionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create position: {str(e)}",
        )


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: UUID,
    position: PositionUpdate,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Update an existing position.

    Only provided fields are updated. Omitted fields remain unchanged.

    **Updatable fields:**
    - quantity, direction, price, price_source, price_as_of
    - fx_rate, cost_basis, market_value, as_of_timestamp
    - Greeks: delta, gamma, vega, theta, rho
    - Fixed income: dv01, cs01
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)

            # Check position exists
            existing = service.get_position(position_id, tenant_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found",
                )

            # Build update dict from non-None fields
            updates = {}
            update_fields = position.model_dump(exclude_unset=True)

            for field, value in update_fields.items():
                if value is not None:
                    # Handle enums
                    if hasattr(value, "value"):
                        updates[field] = value.value
                    else:
                        updates[field] = value

            # Perform update
            result = service.update_position(
                position_id=position_id,
                tenant_id=tenant_id,
                **updates,
            )

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found after update",
                )

            return PositionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update position: {str(e)}",
        )


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Delete a position.

    This is a hard delete. The position record will be permanently removed.
    For audit purposes, consider archiving to position_history table first.
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)

            # Check position exists first
            existing = service.get_position(position_id, tenant_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found",
                )

            # Delete
            deleted = service.delete_position(position_id, tenant_id)

            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete position {position_id}",
                )

            # 204 No Content - no response body
            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete position: {str(e)}",
        )


@router.get("/{position_id}/pnl")
def get_position_pnl(
    position_id: UUID,
    current_price: Optional[float] = Query(None, description="Override current price for P&L calculation"),
):
    """
    Calculate P&L for a position.

    **Returns:**
    - quantity: Position quantity
    - price: Current price (provided or from position)
    - market_value: quantity * price
    - cost_basis: Original cost basis
    - unrealized_pnl: market_value - cost_basis
    - pnl_percentage: (unrealized_pnl / cost_basis) * 100
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)
            price = Decimal(str(current_price)) if current_price else None
            result = service.calculate_pnl(position_id, price)
            return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error calculating P&L for position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate P&L: {str(e)}",
        )


@router.get("/book/{book_id}/pnl")
def get_book_pnl(
    book_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Calculate aggregated P&L for all positions in a book.

    **Returns:**
    - book_id: Book UUID
    - total_market_value: Sum of all position market values
    - total_cost_basis: Sum of all position cost bases
    - total_unrealized_pnl: Sum of all unrealized P&L
    - pnl_percentage: Overall P&L percentage
    - position_count: Number of positions
    - positions_with_pnl: Count of positions with P&L data
    - long_value: Total value of long positions
    - short_value: Total value of short positions
    - net_exposure: long_value - short_value
    """
    try:
        with get_db_connection() as conn:
            service = PositionService(conn)
            result = service.calculate_book_pnl(book_id, tenant_id)
            return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error calculating book P&L for {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate book P&L: {str(e)}",
        )


@router.post("/bulk", response_model=dict)
def create_positions_bulk(positions: list[PositionCreate]):
    """
    Create multiple positions in bulk.

    **Returns:**
    - created: Number of positions created successfully
    - failed: Number of positions that failed
    - errors: List of error details for failed positions
    """
    created = 0
    failed = 0
    errors = []

    with get_db_connection() as conn:
        service = PositionService(conn)

        for i, position in enumerate(positions):
            try:
                # Resolve security_id if not provided
                security_id = position.security_id
                if not security_id:
                    security_id = service.resolve_security_id(
                        ticker=position.ticker,
                        cusip=position.cusip,
                        isin=position.isin,
                        sedol=position.sedol,
                    )
                    if not security_id:
                        raise ValueError("Could not resolve security")

                service.create_position(
                    tenant_id=position.tenant_id,
                    book_id=position.book_id,
                    security_id=security_id,
                    quantity=position.quantity,
                    direction=position.direction.value,
                    source=position.source.value,
                    as_of_timestamp=position.as_of_timestamp,
                    price=position.price,
                    price_source=position.price_source.value if position.price_source else "market",
                    price_as_of=position.price_as_of,
                    local_currency=position.local_currency,
                    base_currency=position.base_currency,
                    fx_rate=position.fx_rate,
                    cost_basis=position.cost_basis,
                    source_reference=position.source_reference,
                )
                created += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "index": i,
                    "error": str(e),
                    "position": {
                        "book_id": str(position.book_id),
                        "security_id": str(position.security_id) if position.security_id else None,
                        "ticker": position.ticker,
                    }
                })

    return {
        "created": created,
        "failed": failed,
        "total": len(positions),
        "errors": errors if errors else None,
    }


# =============================================================================
# Composition & Risk Attribution Endpoints
# =============================================================================

@router.get("/{position_id}/composition")
def get_position_composition(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID"),
):
    """
    Get the composition applied to a position.

    Returns the structured note breakdown if a composition template
    has been applied to this position. Returns null if no composition.
    """
    try:
        with get_db_connection() as conn:
            service = CompositionService(conn, str(tenant_id) if tenant_id else None)
            composition = service.get_position_composition(str(position_id))

            if not composition:
                return None

            return composition.to_dict()
    except Exception as e:
        logger.error(f"Error getting composition for position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get composition: {str(e)}",
        )


@router.post("/{position_id}/composition")
def apply_composition_to_position(
    position_id: UUID,
    composition_id: UUID = Query(..., description="Composition UUID to apply"),
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None, description="User applying composition"),
):
    """
    Apply a composition template to this position.

    Links the position to a composition for risk attribution.
    The position's value will be broken down across RiskPods
    based on the composition's component allocations.
    """
    try:
        with get_db_connection() as conn:
            # Verify position exists
            pos_service = PositionService(conn)
            position = pos_service.get_position(position_id, tenant_id)

            if not position:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found",
                )

            # Apply composition
            comp_service = CompositionService(conn, str(tenant_id) if tenant_id else None)
            success = comp_service.apply_to_position(
                position_id=str(position_id),
                composition_id=str(composition_id),
                applied_by=str(user_id) if user_id else None,
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to apply composition",
                )

            return {
                "status": "applied",
                "position_id": str(position_id),
                "composition_id": str(composition_id),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying composition to position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply composition: {str(e)}",
        )


@router.delete("/{position_id}/composition")
def remove_position_composition(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Remove composition from this position.

    The position will no longer have risk attribution across RiskPods.
    """
    try:
        with get_db_connection() as conn:
            service = CompositionService(conn, str(tenant_id) if tenant_id else None)
            success = service.remove_from_position(str(position_id))

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No composition found for this position",
                )

            return {"status": "removed", "position_id": str(position_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing composition from position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove composition: {str(e)}",
        )


@router.get("/{position_id}/risk-attribution")
def get_position_risk_attribution(
    position_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
):
    """
    Get risk attribution for this position.

    Returns the position's value broken down by RiskPod based on
    its composition. If no composition is applied, the entire
    value is attributed to "other" RiskPod.

    **Response:**
    ```json
    {
        "position_id": "uuid",
        "total_value": 30000000,
        "attribution": {
            "equity": 20000000,
            "credit": 10000000,
            "rates": 0,
            "fx": 0,
            "other": 0
        },
        "components": [
            {"name": "S&P Future", "value": 10000000, "riskpod": "equity"},
            {"name": "NVIDIA Put", "value": 10000000, "riskpod": "equity"},
            {"name": "NVIDIA Bond", "value": 10000000, "riskpod": "credit"}
        ]
    }
    ```
    """
    try:
        with get_db_connection() as conn:
            service = CompositionService(conn, str(tenant_id) if tenant_id else None)
            attribution = service.get_risk_attribution(str(position_id))

            if not attribution:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Position {position_id} not found",
                )

            return attribution.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk attribution for position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk attribution: {str(e)}",
        )
