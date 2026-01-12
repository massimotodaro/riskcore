# RISKCORE Netting Service
# Cross-PM netting calculations for position aggregation
# THE CORE - Week 4 Aggregation Engine

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class NetPosition:
    """
    Represents a netted position across multiple PMs/books.

    This is the core data model for RISKCORE's aggregation engine.
    """
    security_id: UUID
    security_name: str

    # Gross positions
    gross_long_quantity: Decimal = Decimal("0")
    gross_short_quantity: Decimal = Decimal("0")
    gross_long_value: Decimal = Decimal("0")
    gross_short_value: Decimal = Decimal("0")

    # Net position
    net_quantity: Decimal = Decimal("0")
    net_value: Decimal = Decimal("0")
    net_direction: str = "flat"

    # Source breakdown
    long_book_ids: List[UUID] = field(default_factory=list)
    short_book_ids: List[UUID] = field(default_factory=list)
    contributing_pm_count: int = 0

    # Metadata
    base_currency: str = "USD"
    as_of_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "security_id": str(self.security_id),
            "security_name": self.security_name,
            "gross_long_quantity": float(self.gross_long_quantity),
            "gross_short_quantity": float(self.gross_short_quantity),
            "gross_long_value": float(self.gross_long_value),
            "gross_short_value": float(self.gross_short_value),
            "net_quantity": float(self.net_quantity),
            "net_value": float(self.net_value),
            "net_direction": self.net_direction,
            "long_book_count": len(self.long_book_ids),
            "short_book_count": len(self.short_book_ids),
            "contributing_pm_count": self.contributing_pm_count,
            "base_currency": self.base_currency,
            "as_of_timestamp": self.as_of_timestamp.isoformat() if self.as_of_timestamp else None,
        }


class NettingService:
    """
    Service for cross-PM position netting.

    The netting engine is RISKCORE's core differentiator:
    - Aggregates positions across all PMs for each security
    - Calculates gross long, gross short, and net positions
    - Identifies contributing books and PMs
    - Handles currency conversion to base currency

    Example:
        PM1 long 1000 AAPL + PM2 short 300 AAPL = firm net 700 AAPL

    All data stays on-premises - no cloud storage.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    def calculate_net_position(
        self,
        tenant_id: UUID,
        security_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Optional[NetPosition]:
        """
        Calculate net position for a single security across all PMs.

        Args:
            tenant_id: Tenant ID (firm-level)
            security_id: Security to calculate net position for
            fund_id: Optional fund filter

        Returns:
            NetPosition object or None if no positions found
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build query with optional fund filter
        fund_filter = ""
        params = [str(tenant_id), str(security_id)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT
                p.book_id,
                p.quantity,
                p.direction,
                p.market_value,
                p.market_value_base,
                p.base_currency,
                p.as_of_timestamp,
                b.pm_id,
                b.name as book_name,
                s.name as security_name
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s
              AND p.security_id = %s
              {fund_filter}
        """, params)

        positions = cur.fetchall()

        if not positions:
            return None

        # Get security name from first position
        security_name = positions[0]["security_name"]

        # Initialize net position
        net_pos = NetPosition(
            security_id=security_id,
            security_name=security_name,
        )

        # Track unique PMs
        pm_ids = set()
        latest_timestamp = None

        for p in positions:
            quantity = Decimal(str(p["quantity"]))
            # Use base currency value if available, otherwise market value
            value = Decimal(str(p["market_value_base"] or p["market_value"] or 0))
            direction = p["direction"]
            book_id = UUID(p["book_id"])
            pm_id = p["pm_id"]

            if pm_id:
                pm_ids.add(pm_id)

            # Track latest timestamp
            if p["as_of_timestamp"]:
                if latest_timestamp is None or p["as_of_timestamp"] > latest_timestamp:
                    latest_timestamp = p["as_of_timestamp"]

            if direction == "long":
                net_pos.gross_long_quantity += abs(quantity)
                net_pos.gross_long_value += abs(value)
                net_pos.long_book_ids.append(book_id)
            elif direction == "short":
                net_pos.gross_short_quantity += abs(quantity)
                net_pos.gross_short_value += abs(value)
                net_pos.short_book_ids.append(book_id)

        # Calculate net position
        net_pos.net_quantity = net_pos.gross_long_quantity - net_pos.gross_short_quantity
        net_pos.net_value = net_pos.gross_long_value - net_pos.gross_short_value

        # Determine net direction
        if net_pos.net_quantity > 0:
            net_pos.net_direction = "long"
        elif net_pos.net_quantity < 0:
            net_pos.net_direction = "short"
        else:
            net_pos.net_direction = "flat"

        net_pos.contributing_pm_count = len(pm_ids)
        net_pos.as_of_timestamp = latest_timestamp
        net_pos.base_currency = positions[0]["base_currency"] or "USD"

        return net_pos

    def calculate_all_net_positions(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
        min_gross_value: Optional[Decimal] = None,
    ) -> List[NetPosition]:
        """
        Calculate net positions for ALL securities across all PMs.

        Args:
            tenant_id: Tenant ID (firm-level)
            fund_id: Optional fund filter
            min_gross_value: Filter out positions below this gross value

        Returns:
            List of NetPosition objects sorted by gross value descending
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # First, get all distinct securities with positions
        fund_filter = ""
        params = [str(tenant_id)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT DISTINCT p.security_id
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s
              {fund_filter}
        """, params)

        security_ids = [row["security_id"] for row in cur.fetchall()]

        # Calculate net position for each security
        net_positions = []
        for sec_id in security_ids:
            net_pos = self.calculate_net_position(
                tenant_id=tenant_id,
                security_id=UUID(sec_id),
                fund_id=fund_id,
            )
            if net_pos:
                # Apply minimum gross value filter
                gross_value = net_pos.gross_long_value + net_pos.gross_short_value
                if min_gross_value is None or gross_value >= min_gross_value:
                    net_positions.append(net_pos)

        # Sort by gross value (long + short) descending
        net_positions.sort(
            key=lambda x: x.gross_long_value + x.gross_short_value,
            reverse=True
        )

        return net_positions

    def get_firm_netting_summary(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get a summary of firm-level netting.

        Shows:
        - Total gross long/short exposure
        - Total net exposure
        - Netting efficiency (reduction from gross to net)
        - Number of securities with offsetting positions

        Args:
            tenant_id: Tenant ID (firm-level)
            fund_id: Optional fund filter

        Returns:
            Summary dict with netting statistics
        """
        net_positions = self.calculate_all_net_positions(tenant_id, fund_id)

        if not net_positions:
            return {
                "tenant_id": str(tenant_id),
                "fund_id": str(fund_id) if fund_id else None,
                "total_gross_long": 0.0,
                "total_gross_short": 0.0,
                "total_gross": 0.0,
                "total_net": 0.0,
                "netting_benefit": 0.0,
                "netting_efficiency_pct": 0.0,
                "securities_with_offsetting": 0,
                "total_securities": 0,
                "net_long_securities": 0,
                "net_short_securities": 0,
                "flat_securities": 0,
            }

        # Calculate totals
        total_gross_long = sum(float(p.gross_long_value) for p in net_positions)
        total_gross_short = sum(float(p.gross_short_value) for p in net_positions)
        total_gross = total_gross_long + total_gross_short
        total_net = sum(abs(float(p.net_value)) for p in net_positions)

        # Netting benefit = gross exposure - net exposure
        netting_benefit = total_gross - total_net

        # Netting efficiency = % reduction from gross to net
        netting_efficiency = (netting_benefit / total_gross * 100) if total_gross > 0 else 0

        # Count securities with offsetting positions (both long and short)
        offsetting = sum(
            1 for p in net_positions
            if len(p.long_book_ids) > 0 and len(p.short_book_ids) > 0
        )

        # Count by net direction
        net_long = sum(1 for p in net_positions if p.net_direction == "long")
        net_short = sum(1 for p in net_positions if p.net_direction == "short")
        flat = sum(1 for p in net_positions if p.net_direction == "flat")

        return {
            "tenant_id": str(tenant_id),
            "fund_id": str(fund_id) if fund_id else None,
            "total_gross_long": round(total_gross_long, 2),
            "total_gross_short": round(total_gross_short, 2),
            "total_gross": round(total_gross, 2),
            "total_net": round(total_net, 2),
            "netting_benefit": round(netting_benefit, 2),
            "netting_efficiency_pct": round(netting_efficiency, 2),
            "securities_with_offsetting": offsetting,
            "total_securities": len(net_positions),
            "net_long_securities": net_long,
            "net_short_securities": net_short,
            "flat_securities": flat,
        }

    def get_security_netting_detail(
        self,
        tenant_id: UUID,
        security_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get detailed netting breakdown for a specific security.

        Shows each book's contribution to the net position.

        Args:
            tenant_id: Tenant ID
            security_id: Security ID

        Returns:
            Detailed breakdown with per-book positions
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                p.book_id,
                p.quantity,
                p.direction,
                p.market_value,
                p.market_value_base,
                p.price,
                p.as_of_timestamp,
                b.name as book_name,
                b.pm_id,
                b.strategy,
                f.name as fund_name,
                u.name as pm_name,
                s.name as security_name
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            LEFT JOIN funds f ON b.fund_id = f.id
            LEFT JOIN users u ON b.pm_id = u.id
            WHERE p.tenant_id = %s
              AND p.security_id = %s
            ORDER BY ABS(p.market_value) DESC
        """, (str(tenant_id), str(security_id)))

        positions = cur.fetchall()

        if not positions:
            return {
                "security_id": str(security_id),
                "security_name": None,
                "positions": [],
                "net_position": None,
            }

        security_name = positions[0]["security_name"]

        # Build position breakdown
        position_breakdown = []
        for p in positions:
            position_breakdown.append({
                "book_id": str(p["book_id"]),
                "book_name": p["book_name"],
                "pm_name": p["pm_name"],
                "fund_name": p["fund_name"],
                "strategy": p["strategy"],
                "quantity": float(p["quantity"]),
                "direction": p["direction"],
                "market_value": float(p["market_value"]) if p["market_value"] else None,
                "price": float(p["price"]) if p["price"] else None,
                "as_of": p["as_of_timestamp"].isoformat() if p["as_of_timestamp"] else None,
            })

        # Get net position
        net_pos = self.calculate_net_position(tenant_id, security_id)

        return {
            "security_id": str(security_id),
            "security_name": security_name,
            "positions": position_breakdown,
            "position_count": len(positions),
            "net_position": net_pos.to_dict() if net_pos else None,
        }

    def get_pm_contribution_to_netting(
        self,
        tenant_id: UUID,
        pm_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get a PM's contribution to firm-level netting.

        Shows how much of a PM's positions offset other PMs.

        Args:
            tenant_id: Tenant ID
            pm_id: PM user ID

        Returns:
            PM's netting contribution statistics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get PM's positions
        cur.execute("""
            SELECT
                p.security_id,
                p.quantity,
                p.direction,
                p.market_value,
                s.name as security_name
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
        """, (str(tenant_id), str(pm_id)))

        pm_positions = cur.fetchall()

        if not pm_positions:
            return {
                "pm_id": str(pm_id),
                "total_positions": 0,
                "offsetting_positions": 0,
                "gross_exposure": 0.0,
                "offsetting_value": 0.0,
            }

        # For each position, check if it offsets other PMs
        offsetting_count = 0
        offsetting_value = Decimal("0")
        total_gross = Decimal("0")

        for p in pm_positions:
            mv = Decimal(str(p["market_value"] or 0))
            total_gross += abs(mv)

            # Get net position for this security
            net_pos = self.calculate_net_position(
                tenant_id=tenant_id,
                security_id=UUID(p["security_id"]),
            )

            if net_pos:
                # PM contributes to netting if there are positions on both sides
                has_long = len(net_pos.long_book_ids) > 0
                has_short = len(net_pos.short_book_ids) > 0

                if has_long and has_short:
                    offsetting_count += 1
                    # This PM's contribution to the offset
                    if p["direction"] == "long":
                        # Offset is limited by the smaller side
                        offset_amount = min(abs(mv), float(net_pos.gross_short_value))
                    else:
                        offset_amount = min(abs(mv), float(net_pos.gross_long_value))
                    offsetting_value += Decimal(str(offset_amount))

        return {
            "pm_id": str(pm_id),
            "total_positions": len(pm_positions),
            "offsetting_positions": offsetting_count,
            "gross_exposure": float(total_gross),
            "offsetting_value": float(offsetting_value),
            "offsetting_pct": float(offsetting_value / total_gross * 100) if total_gross > 0 else 0,
        }
