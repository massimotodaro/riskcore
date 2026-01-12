# RISKCORE Position Service
# Business logic for position management
# Uses psycopg2 for direct PostgreSQL access (on-premises)

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class PositionService:
    """
    Service for managing positions.

    Handles:
    - CRUD operations
    - P&L calculations
    - Security resolution
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

    def create_position(
        self,
        tenant_id: UUID,
        book_id: UUID,
        security_id: UUID,
        quantity: Decimal,
        direction: str,
        source: str,
        as_of_timestamp: datetime,
        price: Optional[Decimal] = None,
        price_source: str = "market",
        price_as_of: Optional[datetime] = None,
        local_currency: str = "USD",
        base_currency: str = "USD",
        fx_rate: Optional[Decimal] = None,
        cost_basis: Optional[Decimal] = None,
        source_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new position.

        Returns the created position record.
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Calculate market value if price provided
        market_value = None
        if price is not None:
            market_value = float(quantity) * float(price)

        # Calculate unrealized P&L if we have both market value and cost basis
        unrealized_pnl = None
        if market_value is not None and cost_basis is not None:
            unrealized_pnl = market_value - float(cost_basis)

        # Calculate base currency market value
        market_value_base = market_value
        if fx_rate is not None and market_value is not None:
            market_value_base = market_value * float(fx_rate)

        logger.info(f"Creating position for book {book_id}, security {security_id}")

        cur.execute("""
            INSERT INTO positions (
                tenant_id, book_id, security_id, quantity, direction,
                market_value, cost_basis, unrealized_pnl, price, price_source,
                price_as_of, local_currency, base_currency, fx_rate,
                market_value_base, source, source_reference, as_of_timestamp
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING *
        """, (
            str(tenant_id), str(book_id), str(security_id), float(quantity), direction,
            market_value, float(cost_basis) if cost_basis else None, unrealized_pnl,
            float(price) if price else None, price_source,
            price_as_of, local_currency, base_currency,
            float(fx_rate) if fx_rate else None,
            market_value_base, source, source_reference, as_of_timestamp,
        ))

        result = cur.fetchone()
        self.conn.commit()

        if not result:
            raise ValueError("Failed to create position")

        return dict(result)

    def get_position(
        self,
        position_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a single position by ID."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if tenant_id:
            cur.execute("""
                SELECT * FROM positions
                WHERE id = %s AND tenant_id = %s
            """, (str(position_id), str(tenant_id)))
        else:
            cur.execute("""
                SELECT * FROM positions WHERE id = %s
            """, (str(position_id),))

        result = cur.fetchone()
        return dict(result) if result else None

    def list_positions(
        self,
        tenant_id: Optional[UUID] = None,
        book_id: Optional[UUID] = None,
        security_id: Optional[UUID] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        List positions with filters and pagination.

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
        if direction:
            conditions.append("direction = %s")
            params.append(direction)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM positions {where_clause}"
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
            SELECT * FROM positions
            {where_clause}
            ORDER BY as_of_timestamp DESC
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

    def update_position(
        self,
        position_id: UUID,
        tenant_id: Optional[UUID] = None,
        **updates,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a position.

        Only updates provided fields.
        """
        if not updates:
            return self.get_position(position_id, tenant_id)

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build SET clause
        set_parts = []
        params = []

        for key, value in updates.items():
            if value is not None:
                set_parts.append(f"{key} = %s")
                if isinstance(value, Decimal):
                    params.append(float(value))
                elif isinstance(value, UUID):
                    params.append(str(value))
                else:
                    params.append(value)

        # Add updated_at
        set_parts.append("updated_at = NOW()")

        set_clause = ", ".join(set_parts)

        # Build WHERE clause
        params.append(str(position_id))
        if tenant_id:
            where_clause = "WHERE id = %s AND tenant_id = %s"
            params.append(str(tenant_id))
        else:
            where_clause = "WHERE id = %s"

        query = f"""
            UPDATE positions
            SET {set_clause}
            {where_clause}
            RETURNING *
        """

        cur.execute(query, params)
        result = cur.fetchone()
        self.conn.commit()

        return dict(result) if result else None

    def delete_position(
        self,
        position_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete a position.

        Returns True if deleted, False if not found.
        """
        cur = self.conn.cursor()

        if tenant_id:
            cur.execute("""
                DELETE FROM positions
                WHERE id = %s AND tenant_id = %s
                RETURNING id
            """, (str(position_id), str(tenant_id)))
        else:
            cur.execute("""
                DELETE FROM positions WHERE id = %s RETURNING id
            """, (str(position_id),))

        result = cur.fetchone()
        self.conn.commit()

        return result is not None

    def calculate_pnl(
        self,
        position_id: UUID,
        current_price: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """
        Calculate P&L for a position.

        If current_price not provided, uses the position's stored price.
        """
        position = self.get_position(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        quantity = Decimal(str(position["quantity"]))
        price = Decimal(str(current_price)) if current_price else Decimal(str(position.get("price") or 0))
        cost_basis = Decimal(str(position.get("cost_basis") or 0)) if position.get("cost_basis") else None

        # Market value
        market_value = quantity * price

        # Unrealized P&L
        unrealized_pnl = None
        if cost_basis is not None:
            unrealized_pnl = market_value - cost_basis

        # P&L percentage
        pnl_percentage = None
        if cost_basis and cost_basis != 0:
            pnl_percentage = ((market_value - cost_basis) / cost_basis) * 100

        return {
            "position_id": str(position_id),
            "quantity": float(quantity),
            "price": float(price),
            "market_value": float(market_value),
            "cost_basis": float(cost_basis) if cost_basis else None,
            "unrealized_pnl": float(unrealized_pnl) if unrealized_pnl else None,
            "pnl_percentage": float(pnl_percentage) if pnl_percentage else None,
        }

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
