# RISKCORE Trade Service
# Business logic for trade management
# Uses psycopg2 for direct PostgreSQL access (on-premises)

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date, time, datetime
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class TradeService:
    """
    Service for managing trades.

    Handles:
    - CRUD operations
    - Security resolution
    - Trade cancellation
    - Validation

    Uses psycopg2 for direct PostgreSQL access.
    All data stays on-premises - no cloud storage.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    def create_trade(
        self,
        tenant_id: UUID,
        book_id: UUID,
        security_id: UUID,
        side: str,
        quantity: Decimal,
        price: Decimal,
        currency: str,
        trade_date: date,
        source: str,
        trade_time: Optional[time] = None,
        settlement_date: Optional[date] = None,
        trade_id_external: Optional[str] = None,
        order_id_external: Optional[str] = None,
        broker: Optional[str] = None,
        counterparty: Optional[str] = None,
        commission: Optional[Decimal] = None,
        fees: Optional[Decimal] = None,
        source_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new trade.

        Returns the created trade record.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Calculate notional
        notional = float(quantity) * float(price)

        logger.info(f"Creating trade for book {book_id}, security {security_id}, side {side}")

        cur.execute("""
            INSERT INTO trades (
                tenant_id, book_id, security_id, side, quantity, price, notional,
                currency, trade_date, trade_time, settlement_date,
                trade_id_external, order_id_external, broker, counterparty,
                commission, fees, source, source_reference
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING *
        """, (
            str(tenant_id), str(book_id), str(security_id), side,
            float(quantity), float(price), notional,
            currency, trade_date, trade_time, settlement_date,
            trade_id_external, order_id_external, broker, counterparty,
            float(commission) if commission else None,
            float(fees) if fees else None,
            source, source_reference,
        ))

        result = cur.fetchone()
        self.conn.commit()

        if not result:
            raise ValueError("Failed to create trade")

        return dict(result)

    def get_trade(
        self,
        trade_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a single trade by ID."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if tenant_id:
            cur.execute("""
                SELECT * FROM trades
                WHERE id = %s AND tenant_id = %s
            """, (str(trade_id), str(tenant_id)))
        else:
            cur.execute("""
                SELECT * FROM trades WHERE id = %s
            """, (str(trade_id),))

        result = cur.fetchone()
        return dict(result) if result else None

    def list_trades(
        self,
        tenant_id: Optional[UUID] = None,
        book_id: Optional[UUID] = None,
        security_id: Optional[UUID] = None,
        side: Optional[str] = None,
        trade_date_from: Optional[date] = None,
        trade_date_to: Optional[date] = None,
        include_cancelled: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        List trades with filters and pagination.

        Returns dict with items, total, page, page_size, total_pages.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build WHERE clause
        conditions = []
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(str(tenant_id))
        if book_id:
            conditions.append("book_id = %s")
            params.append(str(book_id))
        if security_id:
            conditions.append("security_id = %s")
            params.append(str(security_id))
        if side:
            conditions.append("side = %s")
            params.append(side)
        if trade_date_from:
            conditions.append("trade_date >= %s")
            params.append(trade_date_from)
        if trade_date_to:
            conditions.append("trade_date <= %s")
            params.append(trade_date_to)
        if not include_cancelled:
            conditions.append("is_cancelled = false")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM trades {where_clause}"
        cur.execute(count_query, params)
        total = cur.fetchone()["count"]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Calculate offset
        offset = (page - 1) * page_size

        # If page is beyond available data, return empty
        if offset >= total and total > 0:
            return {
                "items": [],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        # Get data with pagination
        data_query = f"""
            SELECT * FROM trades
            {where_clause}
            ORDER BY trade_date DESC, trade_time DESC NULLS LAST, created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(data_query, params + [page_size, offset])
        items = [dict(row) for row in cur.fetchall()]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def cancel_trade(
        self,
        trade_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a trade (soft delete).

        Sets is_cancelled = true and cancelled_at = now().
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if tenant_id:
            cur.execute("""
                UPDATE trades
                SET is_cancelled = true, cancelled_at = NOW()
                WHERE id = %s AND tenant_id = %s AND is_cancelled = false
                RETURNING *
            """, (str(trade_id), str(tenant_id)))
        else:
            cur.execute("""
                UPDATE trades
                SET is_cancelled = true, cancelled_at = NOW()
                WHERE id = %s AND is_cancelled = false
                RETURNING *
            """, (str(trade_id),))

        result = cur.fetchone()
        self.conn.commit()

        return dict(result) if result else None

    def delete_trade(
        self,
        trade_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete a trade (hard delete).

        Returns True if deleted, False if not found.
        """
        cur = self.conn.cursor()

        if tenant_id:
            cur.execute("""
                DELETE FROM trades
                WHERE id = %s AND tenant_id = %s
                RETURNING id
            """, (str(trade_id), str(tenant_id)))
        else:
            cur.execute("""
                DELETE FROM trades WHERE id = %s RETURNING id
            """, (str(trade_id),))

        result = cur.fetchone()
        self.conn.commit()

        return result is not None

    def get_trades_for_book(
        self,
        book_id: UUID,
        trade_date: Optional[date] = None,
        include_cancelled: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all trades for a book, optionally filtered by date.

        Useful for position calculation and reconciliation.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        conditions = ["book_id = %s"]
        params = [str(book_id)]

        if trade_date:
            conditions.append("trade_date = %s")
            params.append(trade_date)

        if not include_cancelled:
            conditions.append("is_cancelled = false")

        where_clause = "WHERE " + " AND ".join(conditions)

        cur.execute(f"""
            SELECT * FROM trades
            {where_clause}
            ORDER BY trade_date, trade_time
        """, params)

        return [dict(row) for row in cur.fetchall()]

    def resolve_security_id(
        self,
        ticker: Optional[str] = None,
        cusip: Optional[str] = None,
        isin: Optional[str] = None,
        sedol: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Resolve a security identifier to a security_id.

        Looks up in security_identifiers table.
        """
        if not any([ticker, cusip, isin, sedol]):
            return None

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build query conditions
        identifiers = []
        if ticker:
            identifiers.append(("ticker", ticker))
        if cusip:
            identifiers.append(("cusip", cusip))
        if isin:
            identifiers.append(("isin", isin))
        if sedol:
            identifiers.append(("sedol", sedol))

        # Try each identifier
        for id_type, id_value in identifiers:
            cur.execute("""
                SELECT security_id FROM security_identifiers
                WHERE identifier_type = %s AND identifier_value = %s
                LIMIT 1
            """, (id_type, id_value))

            result = cur.fetchone()
            if result:
                return UUID(result["security_id"])

        return None

    def validate_book_exists(self, book_id: UUID, tenant_id: UUID) -> bool:
        """Check if a book exists and belongs to the tenant."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 1 FROM books
            WHERE id = %s AND tenant_id = %s
            LIMIT 1
        """, (str(book_id), str(tenant_id)))
        return cur.fetchone() is not None

    def validate_security_exists(self, security_id: UUID) -> bool:
        """Check if a security exists."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 1 FROM securities WHERE id = %s LIMIT 1
        """, (str(security_id),))
        return cur.fetchone() is not None
