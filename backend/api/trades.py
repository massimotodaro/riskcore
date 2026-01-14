# RISKCORE Trade API Endpoints
# On-premises PostgreSQL - NO CLOUD STORAGE

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional
from datetime import date
from decimal import Decimal
import logging

import psycopg2

from ..database import get_db_connection
from ..models.trade import (
    TradeCreate,
    TradeResponse,
    TradeList,
)
from ..services.trade_service import TradeService
from ..services.historical_service import HistoricalService

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Response Models for Position Trades
# =============================================================================

from pydantic import BaseModel
from typing import List


class UnderlyingTrade(BaseModel):
    """Trade that makes up a position."""
    trade_id: str
    trade_id_external: Optional[str] = None
    side: str
    quantity: float
    price: float
    notional: float
    currency: str
    trade_date: Optional[str] = None
    trade_time: Optional[str] = None
    settlement_date: Optional[str] = None
    counterparty: Optional[str] = None  # CRITICAL for OTC
    broker: Optional[str] = None
    commission: float
    fees: float
    source: Optional[str] = None
    is_cancelled: bool
    cancelled_at: Optional[str] = None
    created_at: Optional[str] = None


@router.get("/", response_model=TradeList)
def list_trades(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    book_id: Optional[UUID] = Query(None, description="Filter by book"),
    security_id: Optional[UUID] = Query(None, description="Filter by security"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell/short/cover)"),
    trade_date_from: Optional[date] = Query(None, description="Filter trades from this date"),
    trade_date_to: Optional[date] = Query(None, description="Filter trades to this date"),
    include_cancelled: bool = Query(False, description="Include cancelled trades"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    List trades with optional filtering.

    - **tenant_id**: Filter trades by tenant
    - **book_id**: Filter trades by book/portfolio
    - **security_id**: Filter trades by security
    - **side**: Filter by trade side (buy, sell, short, cover)
    - **trade_date_from**: Filter trades from this date (inclusive)
    - **trade_date_to**: Filter trades to this date (inclusive)
    - **include_cancelled**: Include cancelled trades (default: false)
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)
            result = service.list_trades(
                tenant_id=tenant_id,
                book_id=book_id,
                security_id=security_id,
                side=side,
                trade_date_from=trade_date_from,
                trade_date_to=trade_date_to,
                include_cancelled=include_cancelled,
                page=page,
                page_size=page_size,
            )

            return TradeList(
                items=[TradeResponse(**item) for item in result["items"]],
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
                total_pages=result["total_pages"],
            )
    except Exception as e:
        logger.error(f"Error listing trades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list trades: {str(e)}",
        )


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Get a specific trade by ID.

    - **trade_id**: UUID of the trade to retrieve
    - **tenant_id**: Optional tenant ID for row-level security
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)
            trade = service.get_trade(trade_id, tenant_id)

            if not trade:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trade {trade_id} not found",
                )

            return TradeResponse(**trade)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade {trade_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trade: {str(e)}",
        )


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade(trade: TradeCreate):
    """
    Create a new trade.

    **Security resolution:**
    - If `security_id` provided, uses it directly
    - If `ticker`, `cusip`, `isin`, or `sedol` provided, resolves via security_identifiers table

    **Validation:**
    - Book must exist and belong to tenant
    - Security must exist (or be resolvable)
    - Quantity must be positive
    - Price must be non-negative
    - Required fields: tenant_id, book_id, security_id (or identifier), side, quantity, price, currency, trade_date, source

    **Notional Calculation:**
    - notional = quantity * price
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)

            # Resolve security_id if not provided
            security_id = trade.security_id

            if not security_id:
                # Try to resolve from identifiers
                security_id = service.resolve_security_id(
                    ticker=trade.ticker,
                    cusip=trade.cusip,
                    isin=trade.isin,
                    sedol=trade.sedol,
                )

                if not security_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Could not resolve security. Provide security_id or a valid identifier (ticker, cusip, isin, sedol).",
                    )

            # Validate book exists
            if not service.validate_book_exists(trade.book_id, trade.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Book {trade.book_id} not found or does not belong to tenant {trade.tenant_id}",
                )

            # Validate security exists
            if not service.validate_security_exists(security_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security {security_id} not found. Create the security first or use an identifier for auto-resolution.",
                )

            # Create trade
            result = service.create_trade(
                tenant_id=trade.tenant_id,
                book_id=trade.book_id,
                security_id=security_id,
                side=trade.side.value,
                quantity=trade.quantity,
                price=trade.price,
                currency=trade.currency,
                trade_date=trade.trade_date,
                source=trade.source.value,
                trade_time=trade.trade_time,
                settlement_date=trade.settlement_date,
                trade_id_external=trade.trade_id_external,
                order_id_external=trade.order_id_external,
                broker=trade.broker,
                counterparty=trade.counterparty,
                commission=trade.commission,
                fees=trade.fees,
                source_reference=trade.source_reference,
            )

            return TradeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trade: {str(e)}",
        )


@router.post("/{trade_id}/cancel", response_model=TradeResponse)
def cancel_trade(
    trade_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Cancel a trade (soft delete).

    Sets is_cancelled = true and records the cancellation timestamp.
    The trade record is preserved for audit purposes.

    For hard delete, use DELETE endpoint instead.
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)
            result = service.cancel_trade(trade_id, tenant_id)

            if not result:
                # Check if trade exists
                existing = service.get_trade(trade_id, tenant_id)
                if not existing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Trade {trade_id} not found",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Trade {trade_id} is already cancelled",
                    )

            return TradeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling trade {trade_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel trade: {str(e)}",
        )


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    trade_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID for RLS"),
):
    """
    Delete a trade (hard delete).

    This permanently removes the trade record.
    For audit purposes, consider using cancel endpoint instead.
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)

            # Check trade exists first
            existing = service.get_trade(trade_id, tenant_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trade {trade_id} not found",
                )

            # Delete
            deleted = service.delete_trade(trade_id, tenant_id)

            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete trade {trade_id}",
                )

            # 204 No Content - no response body
            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trade {trade_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trade: {str(e)}",
        )


@router.get("/book/{book_id}", response_model=list[TradeResponse])
def get_trades_for_book(
    book_id: UUID,
    trade_date: Optional[date] = Query(None, description="Filter by specific trade date"),
    include_cancelled: bool = Query(False, description="Include cancelled trades"),
):
    """
    Get all trades for a specific book.

    Useful for position calculation and reconciliation.

    - **book_id**: UUID of the book
    - **trade_date**: Optional filter for specific trade date
    - **include_cancelled**: Include cancelled trades (default: false)
    """
    try:
        with get_db_connection() as conn:
            service = TradeService(conn)
            trades = service.get_trades_for_book(
                book_id=book_id,
                trade_date=trade_date,
                include_cancelled=include_cancelled,
            )

            return [TradeResponse(**trade) for trade in trades]

    except Exception as e:
        logger.error(f"Error getting trades for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trades: {str(e)}",
        )


@router.post("/bulk", response_model=dict)
def create_trades_bulk(trades: list[TradeCreate]):
    """
    Create multiple trades in bulk.

    **Returns:**
    - created: Number of trades created successfully
    - failed: Number of trades that failed
    - errors: List of error details for failed trades
    """
    created = 0
    failed = 0
    errors = []

    with get_db_connection() as conn:
        service = TradeService(conn)

        for i, trade in enumerate(trades):
            try:
                # Resolve security_id if not provided
                security_id = trade.security_id
                if not security_id:
                    security_id = service.resolve_security_id(
                        ticker=trade.ticker,
                        cusip=trade.cusip,
                        isin=trade.isin,
                        sedol=trade.sedol,
                    )
                    if not security_id:
                        raise ValueError("Could not resolve security")

                service.create_trade(
                    tenant_id=trade.tenant_id,
                    book_id=trade.book_id,
                    security_id=security_id,
                    side=trade.side.value,
                    quantity=trade.quantity,
                    price=trade.price,
                    currency=trade.currency,
                    trade_date=trade.trade_date,
                    source=trade.source.value,
                    trade_time=trade.trade_time,
                    settlement_date=trade.settlement_date,
                    trade_id_external=trade.trade_id_external,
                    order_id_external=trade.order_id_external,
                    broker=trade.broker,
                    counterparty=trade.counterparty,
                    commission=trade.commission,
                    fees=trade.fees,
                    source_reference=trade.source_reference,
                )
                created += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "index": i,
                    "error": str(e),
                    "trade": {
                        "book_id": str(trade.book_id),
                        "security_id": str(trade.security_id) if trade.security_id else None,
                        "ticker": trade.ticker,
                        "trade_date": str(trade.trade_date),
                    }
                })

    return {
        "created": created,
        "failed": failed,
        "total": len(trades),
        "errors": errors if errors else None,
    }


# =============================================================================
# POSITION TRADES ENDPOINT (for Trades page drill-down)
# =============================================================================

@router.get("/position/{book_id}/{security_id}", response_model=List[UnderlyingTrade])
def get_trades_for_position(
    book_id: UUID,
    security_id: UUID,
    include_cancelled: bool = Query(False, description="Include cancelled trades"),
):
    """
    Get all trades that make up a position.

    Returns the underlying trades for a given book + security combination.
    This is used when expanding a position row on the Trades page to see
    individual trade details including counterparty.

    **For equities:** Shows all buys/sells that sum to net position
    **For OTC (CDS, swaps):** Shows each open contract with different counterparties

    Parameters:
    - book_id: The book UUID
    - security_id: The security UUID
    - include_cancelled: Whether to include cancelled trades (default: false)

    Returns:
    - List of trades with counterparty, broker, and execution details
    """
    try:
        with get_db_connection() as conn:
            service = HistoricalService(conn)
            trades = service.get_trades_for_position(
                book_id=book_id,
                security_id=security_id,
                include_cancelled=include_cancelled,
            )

            return [UnderlyingTrade(**t) for t in trades]

    except Exception as e:
        logger.error(f"Error getting trades for position book={book_id}, security={security_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trades for position: {str(e)}",
        )
