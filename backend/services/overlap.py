# RISKCORE Overlap Detection Service
# Identifies cross-PM position overlaps and concentration risks
# THE CORE - Week 4 Aggregation Engine

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class OverlapType(str, Enum):
    """Classification of position overlap."""
    SAME_DIRECTION = "same_direction"      # All PMs in same direction - concentration risk
    OPPOSING = "opposing"                   # Some long, some short - netting opportunity
    MIXED = "mixed"                        # Complex case with multiple directions


class OverlapSeverity(str, Enum):
    """Severity classification for overlaps."""
    HIGH = "high"       # >3 PMs or >10% of firm gross exposure
    MEDIUM = "medium"   # 2-3 PMs or 5-10% of firm gross exposure
    LOW = "low"        # 2 PMs with small exposure


@dataclass
class PositionOverlap:
    """
    Represents an overlap where multiple PMs hold the same security.

    Overlaps are critical for:
    - Concentration risk (all long same stock)
    - Netting opportunities (long vs short)
    - Correlation analysis
    """
    security_id: UUID
    security_name: str
    overlap_type: OverlapType
    severity: OverlapSeverity

    # PM breakdown
    pm_positions: List[Dict[str, Any]] = field(default_factory=list)
    pm_count: int = 0

    # Aggregated metrics
    total_long_quantity: Decimal = Decimal("0")
    total_short_quantity: Decimal = Decimal("0")
    total_long_value: Decimal = Decimal("0")
    total_short_value: Decimal = Decimal("0")
    net_quantity: Decimal = Decimal("0")
    net_value: Decimal = Decimal("0")

    # Risk metrics
    concentration_pct: float = 0.0  # % of firm gross exposure
    correlation_concern: bool = False  # True if all same direction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "security_id": str(self.security_id),
            "security_name": self.security_name,
            "overlap_type": self.overlap_type.value,
            "severity": self.severity.value,
            "pm_count": self.pm_count,
            "pm_positions": self.pm_positions,
            "total_long_quantity": float(self.total_long_quantity),
            "total_short_quantity": float(self.total_short_quantity),
            "total_long_value": float(self.total_long_value),
            "total_short_value": float(self.total_short_value),
            "net_quantity": float(self.net_quantity),
            "net_value": float(self.net_value),
            "concentration_pct": round(self.concentration_pct, 2),
            "correlation_concern": self.correlation_concern,
        }


class OverlapDetectionService:
    """
    Service for detecting cross-PM position overlaps.

    Overlaps occur when 2+ PMs hold the same security:
    - Same direction: Concentration risk (correlated losses)
    - Opposing directions: Netting opportunity (inefficient capital)

    Key metrics:
    - Concentration %: How much of firm exposure is in this security
    - PM count: Number of PMs holding this security
    - Severity: High/Medium/Low based on exposure and PM count

    All data stays on-premises.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    def detect_overlaps(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
        min_pm_count: int = 2,
        min_severity: Optional[OverlapSeverity] = None,
    ) -> List[PositionOverlap]:
        """
        Detect all position overlaps across PMs.

        Args:
            tenant_id: Tenant ID (firm-level)
            fund_id: Optional fund filter
            min_pm_count: Minimum PMs to consider an overlap (default: 2)
            min_severity: Filter by minimum severity

        Returns:
            List of PositionOverlap objects sorted by severity/concentration
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get firm's total gross exposure for concentration calculation
        fund_filter = ""
        params = [str(tenant_id)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT COALESCE(SUM(ABS(p.market_value)), 0) as total_gross
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s {fund_filter}
        """, params)

        firm_gross = Decimal(str(cur.fetchone()["total_gross"]))

        # Find securities held by multiple PMs
        params = [str(tenant_id)]
        if fund_id:
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT
                p.security_id,
                s.name as security_name,
                COUNT(DISTINCT b.pm_id) as pm_count,
                array_agg(DISTINCT b.pm_id) as pm_ids
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s
              AND b.pm_id IS NOT NULL
              {fund_filter}
            GROUP BY p.security_id, s.name
            HAVING COUNT(DISTINCT b.pm_id) >= %s
            ORDER BY COUNT(DISTINCT b.pm_id) DESC
        """, params + [min_pm_count])

        overlapping_securities = cur.fetchall()

        overlaps = []
        for row in overlapping_securities:
            overlap = self._build_overlap(
                tenant_id=tenant_id,
                security_id=UUID(row["security_id"]),
                security_name=row["security_name"],
                pm_ids=row["pm_ids"],
                firm_gross=firm_gross,
                fund_id=fund_id,
            )

            # Apply severity filter
            if min_severity:
                severity_order = {
                    OverlapSeverity.LOW: 0,
                    OverlapSeverity.MEDIUM: 1,
                    OverlapSeverity.HIGH: 2,
                }
                if severity_order[overlap.severity] >= severity_order[min_severity]:
                    overlaps.append(overlap)
            else:
                overlaps.append(overlap)

        # Sort by severity (HIGH first) then concentration %
        severity_order = {
            OverlapSeverity.HIGH: 0,
            OverlapSeverity.MEDIUM: 1,
            OverlapSeverity.LOW: 2,
        }
        overlaps.sort(
            key=lambda x: (severity_order[x.severity], -x.concentration_pct)
        )

        return overlaps

    def _build_overlap(
        self,
        tenant_id: UUID,
        security_id: UUID,
        security_name: str,
        pm_ids: List[str],
        firm_gross: Decimal,
        fund_id: Optional[UUID] = None,
    ) -> PositionOverlap:
        """Build a PositionOverlap object with full details."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        fund_filter = ""
        params = [str(tenant_id), str(security_id)]
        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        # Get per-PM position details
        cur.execute(f"""
            SELECT
                b.pm_id,
                u.name as pm_name,
                b.id as book_id,
                b.name as book_name,
                p.quantity,
                p.direction,
                p.market_value,
                p.as_of_timestamp
            FROM positions p
            JOIN books b ON p.book_id = b.id
            LEFT JOIN users u ON b.pm_id = u.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s
              AND p.security_id = %s
              {fund_filter}
            ORDER BY ABS(p.market_value) DESC
        """, params)

        positions = cur.fetchall()

        # Build PM position breakdown
        pm_breakdown = {}
        total_long_qty = Decimal("0")
        total_short_qty = Decimal("0")
        total_long_val = Decimal("0")
        total_short_val = Decimal("0")

        for p in positions:
            pm_id = str(p["pm_id"]) if p["pm_id"] else "unknown"
            qty = Decimal(str(p["quantity"]))
            val = Decimal(str(p["market_value"] or 0))
            direction = p["direction"]

            if pm_id not in pm_breakdown:
                pm_breakdown[pm_id] = {
                    "pm_id": pm_id,
                    "pm_name": p["pm_name"] or "Unknown",
                    "books": [],
                    "total_quantity": Decimal("0"),
                    "total_value": Decimal("0"),
                    "direction": None,
                }

            pm_breakdown[pm_id]["books"].append({
                "book_id": str(p["book_id"]),
                "book_name": p["book_name"],
                "quantity": float(qty),
                "direction": direction,
                "market_value": float(val),
            })

            pm_breakdown[pm_id]["total_quantity"] += qty
            pm_breakdown[pm_id]["total_value"] += abs(val)

            if direction == "long":
                total_long_qty += abs(qty)
                total_long_val += abs(val)
                if pm_breakdown[pm_id]["direction"] is None:
                    pm_breakdown[pm_id]["direction"] = "long"
                elif pm_breakdown[pm_id]["direction"] == "short":
                    pm_breakdown[pm_id]["direction"] = "mixed"
            else:
                total_short_qty += abs(qty)
                total_short_val += abs(val)
                if pm_breakdown[pm_id]["direction"] is None:
                    pm_breakdown[pm_id]["direction"] = "short"
                elif pm_breakdown[pm_id]["direction"] == "long":
                    pm_breakdown[pm_id]["direction"] = "mixed"

        # Finalize PM breakdown for API
        pm_positions = []
        for pm_id, data in pm_breakdown.items():
            pm_positions.append({
                "pm_id": data["pm_id"],
                "pm_name": data["pm_name"],
                "direction": data["direction"],
                "total_quantity": float(data["total_quantity"]),
                "total_value": float(data["total_value"]),
                "book_count": len(data["books"]),
                "books": data["books"],
            })

        # Determine overlap type
        directions = set(p["direction"] for p in pm_positions if p["direction"])
        if len(directions) == 1:
            if "long" in directions:
                overlap_type = OverlapType.SAME_DIRECTION
            elif "short" in directions:
                overlap_type = OverlapType.SAME_DIRECTION
            else:
                overlap_type = OverlapType.MIXED
        elif "mixed" in directions:
            overlap_type = OverlapType.MIXED
        else:
            overlap_type = OverlapType.OPPOSING

        # Calculate concentration
        gross_value = total_long_val + total_short_val
        concentration_pct = float(gross_value / firm_gross * 100) if firm_gross > 0 else 0

        # Determine severity
        pm_count = len(pm_positions)
        if pm_count > 3 or concentration_pct > 10:
            severity = OverlapSeverity.HIGH
        elif pm_count >= 2 and concentration_pct > 5:
            severity = OverlapSeverity.MEDIUM
        else:
            severity = OverlapSeverity.LOW

        # Correlation concern = all same direction (concentration risk)
        correlation_concern = overlap_type == OverlapType.SAME_DIRECTION

        return PositionOverlap(
            security_id=security_id,
            security_name=security_name,
            overlap_type=overlap_type,
            severity=severity,
            pm_positions=pm_positions,
            pm_count=pm_count,
            total_long_quantity=total_long_qty,
            total_short_quantity=total_short_qty,
            total_long_value=total_long_val,
            total_short_value=total_short_val,
            net_quantity=total_long_qty - total_short_qty,
            net_value=total_long_val - total_short_val,
            concentration_pct=concentration_pct,
            correlation_concern=correlation_concern,
        )

    def get_overlap_summary(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for all overlaps.

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            Summary with counts, severity breakdown, and top overlaps
        """
        overlaps = self.detect_overlaps(tenant_id, fund_id)

        if not overlaps:
            return {
                "tenant_id": str(tenant_id),
                "fund_id": str(fund_id) if fund_id else None,
                "total_overlaps": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
                "same_direction_count": 0,
                "opposing_count": 0,
                "correlation_concerns": 0,
                "top_overlaps": [],
            }

        # Count by severity
        high = sum(1 for o in overlaps if o.severity == OverlapSeverity.HIGH)
        medium = sum(1 for o in overlaps if o.severity == OverlapSeverity.MEDIUM)
        low = sum(1 for o in overlaps if o.severity == OverlapSeverity.LOW)

        # Count by type
        same_dir = sum(1 for o in overlaps if o.overlap_type == OverlapType.SAME_DIRECTION)
        opposing = sum(1 for o in overlaps if o.overlap_type == OverlapType.OPPOSING)

        # Count correlation concerns
        correlation_concerns = sum(1 for o in overlaps if o.correlation_concern)

        # Top 5 overlaps by severity/concentration
        top_overlaps = [o.to_dict() for o in overlaps[:5]]

        return {
            "tenant_id": str(tenant_id),
            "fund_id": str(fund_id) if fund_id else None,
            "total_overlaps": len(overlaps),
            "high_severity": high,
            "medium_severity": medium,
            "low_severity": low,
            "same_direction_count": same_dir,
            "opposing_count": opposing,
            "correlation_concerns": correlation_concerns,
            "top_overlaps": top_overlaps,
        }

    def get_pm_overlap_exposure(
        self,
        tenant_id: UUID,
        pm_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get overlap exposure for a specific PM.

        Shows which of a PM's positions overlap with other PMs.

        Args:
            tenant_id: Tenant ID
            pm_id: PM user ID

        Returns:
            PM's overlap exposure details
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get PM's securities
        cur.execute("""
            SELECT DISTINCT p.security_id
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
        """, (str(tenant_id), str(pm_id)))

        pm_securities = [row["security_id"] for row in cur.fetchall()]

        # Check each for overlaps with other PMs
        overlapping_securities = []
        for sec_id in pm_securities:
            # Count other PMs with this security
            cur.execute("""
                SELECT COUNT(DISTINCT b.pm_id) as other_pm_count
                FROM positions p
                JOIN books b ON p.book_id = b.id
                WHERE p.tenant_id = %s
                  AND p.security_id = %s
                  AND b.pm_id != %s
                  AND b.pm_id IS NOT NULL
            """, (str(tenant_id), str(sec_id), str(pm_id)))

            other_pms = cur.fetchone()["other_pm_count"]
            if other_pms > 0:
                overlapping_securities.append(sec_id)

        return {
            "pm_id": str(pm_id),
            "total_securities": len(pm_securities),
            "overlapping_securities": len(overlapping_securities),
            "overlap_pct": round(
                len(overlapping_securities) / len(pm_securities) * 100
                if pm_securities else 0, 2
            ),
            "overlapping_security_ids": [str(s) for s in overlapping_securities],
        }

    def detect_concentration_risks(
        self,
        tenant_id: UUID,
        threshold_pct: float = 5.0,
        fund_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect concentration risks (same-direction overlaps above threshold).

        These are securities where multiple PMs are all in the same direction,
        creating correlated risk.

        Args:
            tenant_id: Tenant ID
            threshold_pct: Minimum concentration % to flag (default 5%)
            fund_id: Optional fund filter

        Returns:
            List of concentration risks
        """
        overlaps = self.detect_overlaps(tenant_id, fund_id)

        # Filter to same-direction overlaps above threshold
        concentration_risks = [
            o.to_dict()
            for o in overlaps
            if o.overlap_type == OverlapType.SAME_DIRECTION
            and o.concentration_pct >= threshold_pct
        ]

        return concentration_risks

    def detect_netting_opportunities(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect netting opportunities (opposing overlaps).

        These are securities where PMs have opposing positions,
        which could be netted for capital efficiency.

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            List of netting opportunities with potential benefit
        """
        overlaps = self.detect_overlaps(tenant_id, fund_id)

        # Filter to opposing overlaps
        opportunities = []
        for o in overlaps:
            if o.overlap_type == OverlapType.OPPOSING:
                # Calculate netting benefit (how much could be offset)
                offset_value = min(
                    float(o.total_long_value),
                    float(o.total_short_value)
                )
                opportunities.append({
                    **o.to_dict(),
                    "netting_potential": offset_value * 2,  # Both sides freed up
                })

        # Sort by netting potential
        opportunities.sort(key=lambda x: x["netting_potential"], reverse=True)

        return opportunities
