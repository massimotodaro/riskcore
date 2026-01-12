# RISKCORE Aggregation Service
# Main orchestrator for cross-PM aggregation
# THE CORE - Week 4 Aggregation Engine

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from .netting import NettingService, NetPosition
from .overlap import OverlapDetectionService, OverlapSeverity

logger = logging.getLogger(__name__)


@dataclass
class HierarchyNode:
    """
    Represents a node in the firm hierarchy.

    Hierarchy: Firm → Fund → PM → Book → Position
    """
    level: str  # firm, fund, pm, book
    id: Optional[UUID]
    name: str
    children: List["HierarchyNode"] = None

    # Aggregated metrics
    position_count: int = 0
    gross_exposure: Decimal = Decimal("0")
    net_exposure: Decimal = Decimal("0")
    long_exposure: Decimal = Decimal("0")
    short_exposure: Decimal = Decimal("0")

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "level": self.level,
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "position_count": self.position_count,
            "gross_exposure": float(self.gross_exposure),
            "net_exposure": float(self.net_exposure),
            "long_exposure": float(self.long_exposure),
            "short_exposure": float(self.short_exposure),
            "children": [c.to_dict() for c in self.children] if self.children else [],
        }


class AggregationService:
    """
    Main orchestrator for RISKCORE's aggregation engine.

    This is THE CORE of RISKCORE - what makes it unique:
    1. Cross-PM netting calculations
    2. Overlap detection and concentration risk
    3. Hierarchy navigation (Firm → Fund → PM → Book)
    4. Firm-level position rollup

    All data stays on-premises - no cloud storage.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn
        self.netting_service = NettingService(conn)
        self.overlap_service = OverlapDetectionService(conn)

    # =========================================================================
    # HIERARCHY NAVIGATION
    # =========================================================================

    def get_firm_hierarchy(
        self,
        tenant_id: UUID,
        include_metrics: bool = True,
    ) -> HierarchyNode:
        """
        Get the complete firm hierarchy with optional metrics.

        Hierarchy: Firm → Fund → PM → Book

        Args:
            tenant_id: Tenant ID (firm-level)
            include_metrics: Whether to include exposure metrics

        Returns:
            HierarchyNode representing the firm
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get tenant info
        cur.execute("""
            SELECT id, name FROM tenants WHERE id = %s
        """, (str(tenant_id),))
        tenant = cur.fetchone()

        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Build firm node
        firm = HierarchyNode(
            level="firm",
            id=UUID(tenant["id"]),
            name=tenant["name"],
        )

        # Get funds
        cur.execute("""
            SELECT id, name FROM funds
            WHERE tenant_id = %s AND is_active = TRUE
            ORDER BY name
        """, (str(tenant_id),))
        funds = cur.fetchall()

        for fund_row in funds:
            fund_node = HierarchyNode(
                level="fund",
                id=UUID(fund_row["id"]),
                name=fund_row["name"],
            )

            # Get PMs with books in this fund
            cur.execute("""
                SELECT DISTINCT b.pm_id, u.name as pm_name
                FROM books b
                LEFT JOIN users u ON b.pm_id = u.id
                WHERE b.fund_id = %s AND b.is_active = TRUE
                ORDER BY u.name
            """, (str(fund_row["id"]),))
            pms = cur.fetchall()

            for pm_row in pms:
                pm_id = pm_row["pm_id"]
                pm_name = pm_row["pm_name"] or "Unassigned"

                pm_node = HierarchyNode(
                    level="pm",
                    id=UUID(pm_id) if pm_id else None,
                    name=pm_name,
                )

                # Get books for this PM in this fund
                if pm_id:
                    cur.execute("""
                        SELECT id, name, strategy
                        FROM books
                        WHERE fund_id = %s AND pm_id = %s AND is_active = TRUE
                        ORDER BY name
                    """, (str(fund_row["id"]), str(pm_id)))
                else:
                    cur.execute("""
                        SELECT id, name, strategy
                        FROM books
                        WHERE fund_id = %s AND pm_id IS NULL AND is_active = TRUE
                        ORDER BY name
                    """, (str(fund_row["id"]),))

                books = cur.fetchall()

                for book_row in books:
                    book_node = HierarchyNode(
                        level="book",
                        id=UUID(book_row["id"]),
                        name=book_row["name"],
                    )

                    if include_metrics:
                        self._populate_book_metrics(book_node, tenant_id)

                    pm_node.children.append(book_node)

                if include_metrics:
                    self._aggregate_metrics(pm_node)

                fund_node.children.append(pm_node)

            if include_metrics:
                self._aggregate_metrics(fund_node)

            firm.children.append(fund_node)

        # Also get books without fund
        cur.execute("""
            SELECT DISTINCT b.pm_id, u.name as pm_name
            FROM books b
            LEFT JOIN users u ON b.pm_id = u.id
            WHERE b.tenant_id = %s AND b.fund_id IS NULL AND b.is_active = TRUE
            ORDER BY u.name
        """, (str(tenant_id),))
        orphan_pms = cur.fetchall()

        if orphan_pms:
            no_fund_node = HierarchyNode(
                level="fund",
                id=None,
                name="(No Fund)",
            )

            for pm_row in orphan_pms:
                pm_id = pm_row["pm_id"]
                pm_name = pm_row["pm_name"] or "Unassigned"

                pm_node = HierarchyNode(
                    level="pm",
                    id=UUID(pm_id) if pm_id else None,
                    name=pm_name,
                )

                if pm_id:
                    cur.execute("""
                        SELECT id, name, strategy
                        FROM books
                        WHERE tenant_id = %s AND fund_id IS NULL AND pm_id = %s AND is_active = TRUE
                        ORDER BY name
                    """, (str(tenant_id), str(pm_id)))
                else:
                    cur.execute("""
                        SELECT id, name, strategy
                        FROM books
                        WHERE tenant_id = %s AND fund_id IS NULL AND pm_id IS NULL AND is_active = TRUE
                        ORDER BY name
                    """, (str(tenant_id),))

                books = cur.fetchall()

                for book_row in books:
                    book_node = HierarchyNode(
                        level="book",
                        id=UUID(book_row["id"]),
                        name=book_row["name"],
                    )

                    if include_metrics:
                        self._populate_book_metrics(book_node, tenant_id)

                    pm_node.children.append(book_node)

                if include_metrics:
                    self._aggregate_metrics(pm_node)

                no_fund_node.children.append(pm_node)

            if include_metrics:
                self._aggregate_metrics(no_fund_node)

            firm.children.append(no_fund_node)

        if include_metrics:
            self._aggregate_metrics(firm)

        return firm

    def _populate_book_metrics(self, node: HierarchyNode, tenant_id: UUID):
        """Populate exposure metrics for a book node."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                COUNT(*) as position_count,
                COALESCE(SUM(ABS(market_value)), 0) as gross,
                COALESCE(SUM(market_value), 0) as net,
                COALESCE(SUM(CASE WHEN direction = 'long' THEN market_value ELSE 0 END), 0) as long_val,
                COALESCE(SUM(CASE WHEN direction = 'short' THEN ABS(market_value) ELSE 0 END), 0) as short_val
            FROM positions
            WHERE book_id = %s AND tenant_id = %s
        """, (str(node.id), str(tenant_id)))

        result = cur.fetchone()
        node.position_count = result["position_count"]
        node.gross_exposure = Decimal(str(result["gross"]))
        node.net_exposure = Decimal(str(result["net"]))
        node.long_exposure = Decimal(str(result["long_val"]))
        node.short_exposure = Decimal(str(result["short_val"]))

    def _aggregate_metrics(self, node: HierarchyNode):
        """Aggregate metrics from children to parent."""
        node.position_count = sum(c.position_count for c in node.children)
        node.gross_exposure = sum(c.gross_exposure for c in node.children)
        node.net_exposure = sum(c.net_exposure for c in node.children)
        node.long_exposure = sum(c.long_exposure for c in node.children)
        node.short_exposure = sum(c.short_exposure for c in node.children)

    # =========================================================================
    # FIRM-LEVEL AGGREGATION
    # =========================================================================

    def get_firm_summary(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get firm-wide aggregated summary.

        Combines:
        - Exposure metrics
        - Netting summary
        - Overlap summary
        - Hierarchy counts

        Args:
            tenant_id: Tenant ID

        Returns:
            Comprehensive firm summary
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get basic exposure metrics
        cur.execute("""
            SELECT
                COUNT(*) as total_positions,
                COUNT(DISTINCT p.security_id) as unique_securities,
                COUNT(DISTINCT p.book_id) as total_books,
                COALESCE(SUM(ABS(p.market_value)), 0) as gross_exposure,
                COALESCE(SUM(p.market_value), 0) as net_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE 0 END), 0) as long_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'short' THEN ABS(p.market_value) ELSE 0 END), 0) as short_exposure
            FROM positions p
            WHERE p.tenant_id = %s
        """, (str(tenant_id),))

        exposure = cur.fetchone()

        # Get PM and fund counts
        cur.execute("""
            SELECT
                COUNT(DISTINCT fund_id) FILTER (WHERE fund_id IS NOT NULL) as fund_count,
                COUNT(DISTINCT pm_id) FILTER (WHERE pm_id IS NOT NULL) as pm_count
            FROM books
            WHERE tenant_id = %s AND is_active = TRUE
        """, (str(tenant_id),))

        counts = cur.fetchone()

        # Get netting summary
        netting_summary = self.netting_service.get_firm_netting_summary(tenant_id)

        # Get overlap summary
        overlap_summary = self.overlap_service.get_overlap_summary(tenant_id)

        gross = float(exposure["gross_exposure"])
        net = float(exposure["net_exposure"])
        long_val = float(exposure["long_exposure"])
        short_val = float(exposure["short_exposure"])

        return {
            "tenant_id": str(tenant_id),
            "as_of": datetime.now(timezone.utc).isoformat(),

            # Exposure metrics
            "total_positions": exposure["total_positions"],
            "unique_securities": exposure["unique_securities"],
            "gross_exposure": gross,
            "net_exposure": net,
            "long_exposure": long_val,
            "short_exposure": short_val,
            "leverage_ratio": round(gross / abs(net), 2) if net != 0 else 0,
            "long_short_ratio": round(long_val / short_val, 2) if short_val > 0 else None,

            # Structure counts
            "fund_count": counts["fund_count"],
            "pm_count": counts["pm_count"],
            "book_count": exposure["total_books"],

            # Netting metrics
            "netting": {
                "total_gross": netting_summary["total_gross"],
                "total_net": netting_summary["total_net"],
                "netting_benefit": netting_summary["netting_benefit"],
                "netting_efficiency_pct": netting_summary["netting_efficiency_pct"],
                "securities_with_offsetting": netting_summary["securities_with_offsetting"],
            },

            # Overlap metrics
            "overlaps": {
                "total_overlaps": overlap_summary["total_overlaps"],
                "high_severity": overlap_summary["high_severity"],
                "medium_severity": overlap_summary["medium_severity"],
                "correlation_concerns": overlap_summary["correlation_concerns"],
            },
        }

    def get_firm_positions(
        self,
        tenant_id: UUID,
        netted: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get firm-level positions (optionally netted across PMs).

        Args:
            tenant_id: Tenant ID
            netted: If True, return net positions; if False, return all raw positions
            page: Page number
            page_size: Items per page

        Returns:
            Paginated position list
        """
        if netted:
            # Get netted positions
            all_net = self.netting_service.calculate_all_net_positions(tenant_id)

            # Paginate
            total = len(all_net)
            start = (page - 1) * page_size
            end = start + page_size
            page_items = all_net[start:end]

            return {
                "items": [p.to_dict() for p in page_items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "netted": True,
            }
        else:
            # Get raw positions
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get count
            cur.execute("""
                SELECT COUNT(*) as total FROM positions WHERE tenant_id = %s
            """, (str(tenant_id),))
            total = cur.fetchone()["total"]

            # Get page
            offset = (page - 1) * page_size
            cur.execute("""
                SELECT
                    p.id, p.book_id, p.security_id, p.quantity, p.direction,
                    p.market_value, p.as_of_timestamp,
                    s.name as security_name,
                    b.name as book_name,
                    u.name as pm_name
                FROM positions p
                JOIN securities s ON p.security_id = s.id
                JOIN books b ON p.book_id = b.id
                LEFT JOIN users u ON b.pm_id = u.id
                WHERE p.tenant_id = %s
                ORDER BY ABS(p.market_value) DESC
                LIMIT %s OFFSET %s
            """, (str(tenant_id), page_size, offset))

            items = [dict(row) for row in cur.fetchall()]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "netted": False,
            }

    # =========================================================================
    # FUND-LEVEL AGGREGATION
    # =========================================================================

    def get_fund_summary(
        self,
        tenant_id: UUID,
        fund_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get fund-level aggregated summary.

        Args:
            tenant_id: Tenant ID
            fund_id: Fund ID

        Returns:
            Fund summary with exposure and netting metrics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get fund info
        cur.execute("""
            SELECT id, name FROM funds
            WHERE id = %s AND tenant_id = %s
        """, (str(fund_id), str(tenant_id)))

        fund = cur.fetchone()
        if not fund:
            raise ValueError(f"Fund {fund_id} not found")

        # Get exposure metrics
        cur.execute("""
            SELECT
                COUNT(*) as total_positions,
                COUNT(DISTINCT p.security_id) as unique_securities,
                COUNT(DISTINCT p.book_id) as total_books,
                COUNT(DISTINCT b.pm_id) FILTER (WHERE b.pm_id IS NOT NULL) as pm_count,
                COALESCE(SUM(ABS(p.market_value)), 0) as gross_exposure,
                COALESCE(SUM(p.market_value), 0) as net_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE 0 END), 0) as long_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'short' THEN ABS(p.market_value) ELSE 0 END), 0) as short_exposure
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s AND b.fund_id = %s
        """, (str(tenant_id), str(fund_id)))

        exposure = cur.fetchone()

        # Get netting summary for fund
        netting_summary = self.netting_service.get_firm_netting_summary(tenant_id, fund_id)

        # Get overlap summary for fund
        overlap_summary = self.overlap_service.get_overlap_summary(tenant_id, fund_id)

        return {
            "fund_id": str(fund_id),
            "fund_name": fund["name"],
            "tenant_id": str(tenant_id),
            "total_positions": exposure["total_positions"],
            "unique_securities": exposure["unique_securities"],
            "book_count": exposure["total_books"],
            "pm_count": exposure["pm_count"],
            "gross_exposure": float(exposure["gross_exposure"]),
            "net_exposure": float(exposure["net_exposure"]),
            "long_exposure": float(exposure["long_exposure"]),
            "short_exposure": float(exposure["short_exposure"]),
            "netting": netting_summary,
            "overlaps": overlap_summary,
        }

    # =========================================================================
    # PM-LEVEL AGGREGATION
    # =========================================================================

    def get_pm_summary(
        self,
        tenant_id: UUID,
        pm_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get PM-level aggregated summary.

        Args:
            tenant_id: Tenant ID
            pm_id: PM user ID

        Returns:
            PM summary with exposure and contribution to firm
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get PM info
        cur.execute("""
            SELECT id, name FROM users
            WHERE id = %s AND tenant_id = %s
        """, (str(pm_id), str(tenant_id)))

        pm = cur.fetchone()
        if not pm:
            raise ValueError(f"PM {pm_id} not found")

        # Get PM's exposure metrics
        cur.execute("""
            SELECT
                COUNT(*) as total_positions,
                COUNT(DISTINCT p.security_id) as unique_securities,
                COUNT(DISTINCT p.book_id) as total_books,
                COALESCE(SUM(ABS(p.market_value)), 0) as gross_exposure,
                COALESCE(SUM(p.market_value), 0) as net_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE 0 END), 0) as long_exposure,
                COALESCE(SUM(CASE WHEN p.direction = 'short' THEN ABS(p.market_value) ELSE 0 END), 0) as short_exposure
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
        """, (str(tenant_id), str(pm_id)))

        exposure = cur.fetchone()

        # Get PM's contribution to netting
        netting_contrib = self.netting_service.get_pm_contribution_to_netting(tenant_id, pm_id)

        # Get PM's overlap exposure
        overlap_exposure = self.overlap_service.get_pm_overlap_exposure(tenant_id, pm_id)

        # Get firm total for % calculation
        cur.execute("""
            SELECT COALESCE(SUM(ABS(market_value)), 0) as firm_gross
            FROM positions WHERE tenant_id = %s
        """, (str(tenant_id),))
        firm_gross = float(cur.fetchone()["firm_gross"])

        pm_gross = float(exposure["gross_exposure"])
        firm_pct = (pm_gross / firm_gross * 100) if firm_gross > 0 else 0

        return {
            "pm_id": str(pm_id),
            "pm_name": pm["name"],
            "tenant_id": str(tenant_id),
            "total_positions": exposure["total_positions"],
            "unique_securities": exposure["unique_securities"],
            "book_count": exposure["total_books"],
            "gross_exposure": pm_gross,
            "net_exposure": float(exposure["net_exposure"]),
            "long_exposure": float(exposure["long_exposure"]),
            "short_exposure": float(exposure["short_exposure"]),
            "firm_exposure_pct": round(firm_pct, 2),
            "netting_contribution": netting_contrib,
            "overlap_exposure": overlap_exposure,
        }

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def get_net_positions(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get all net positions."""
        net_positions = self.netting_service.calculate_all_net_positions(tenant_id, fund_id)
        return [p.to_dict() for p in net_positions]

    def get_overlaps(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
        min_severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all overlaps."""
        severity = None
        if min_severity:
            severity = OverlapSeverity(min_severity)

        overlaps = self.overlap_service.detect_overlaps(
            tenant_id, fund_id, min_severity=severity
        )
        return [o.to_dict() for o in overlaps]

    def get_concentration_risks(
        self,
        tenant_id: UUID,
        threshold_pct: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """Get concentration risks."""
        return self.overlap_service.detect_concentration_risks(tenant_id, threshold_pct)

    def get_netting_opportunities(
        self,
        tenant_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get netting opportunities."""
        return self.overlap_service.detect_netting_opportunities(tenant_id)
