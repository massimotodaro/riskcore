# RISKCORE Exposure Calculations
# Sector, geography, and asset class breakdown

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from enum import Enum
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class ExposureDimension(str, Enum):
    """Dimensions for exposure breakdown."""
    SECTOR = "sector"
    GEOGRAPHY = "geography"
    ASSET_CLASS = "asset_class"
    CURRENCY = "currency"
    INDUSTRY = "industry"
    COUNTRY = "country"


class ExposureService:
    """
    Service for calculating exposure breakdowns.

    Provides:
    - Sector exposure breakdown
    - Geography/country exposure
    - Asset class breakdown
    - Currency exposure
    - Concentration metrics

    All data stays on-premises.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    def calculate_exposure_breakdown(
        self,
        book_id: UUID,
        tenant_id: UUID,
        dimension: ExposureDimension,
    ) -> Dict[str, Any]:
        """
        Calculate exposure breakdown by a dimension.

        Args:
            book_id: Book ID
            tenant_id: Tenant ID
            dimension: Dimension to break down by (sector, geography, etc.)

        Returns:
            Dict with exposure breakdown
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Map dimension to security table column
        dimension_column = self._get_dimension_column(dimension)

        # Get positions with security details
        cur.execute(f"""
            SELECT
                p.id as position_id,
                p.quantity,
                p.market_value,
                p.direction,
                s.{dimension_column} as dimension_value,
                s.ticker,
                s.name as security_name
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = %s AND p.tenant_id = %s
              AND p.market_value IS NOT NULL
        """, (str(book_id), str(tenant_id)))

        positions = cur.fetchall()

        if not positions:
            return {
                "book_id": str(book_id),
                "dimension": dimension.value,
                "breakdown": [],
                "total_exposure": 0.0,
                "position_count": 0,
                "error": "No positions found",
            }

        # Calculate total market value
        total_mv = sum(abs(float(p["market_value"])) for p in positions)

        # Group by dimension
        breakdown = {}
        for p in positions:
            dim_value = p["dimension_value"] or "Unknown"
            mv = float(p["market_value"])

            # Handle long/short separately
            direction = p["direction"]

            if dim_value not in breakdown:
                breakdown[dim_value] = {
                    "dimension_value": dim_value,
                    "long_value": 0.0,
                    "short_value": 0.0,
                    "net_value": 0.0,
                    "gross_value": 0.0,
                    "position_count": 0,
                }

            breakdown[dim_value]["position_count"] += 1

            if direction == "long":
                breakdown[dim_value]["long_value"] += mv
            else:
                breakdown[dim_value]["short_value"] += abs(mv)

            breakdown[dim_value]["net_value"] += mv if direction == "long" else -abs(mv)
            breakdown[dim_value]["gross_value"] += abs(mv)

        # Calculate percentages
        result_breakdown = []
        for dim_value, data in breakdown.items():
            data["gross_pct"] = (data["gross_value"] / total_mv * 100) if total_mv > 0 else 0
            data["net_pct"] = (data["net_value"] / total_mv * 100) if total_mv > 0 else 0
            result_breakdown.append(data)

        # Sort by gross exposure descending
        result_breakdown.sort(key=lambda x: x["gross_value"], reverse=True)

        return {
            "book_id": str(book_id),
            "dimension": dimension.value,
            "breakdown": result_breakdown,
            "total_exposure": total_mv,
            "position_count": len(positions),
        }

    def _get_dimension_column(self, dimension: ExposureDimension) -> str:
        """Map dimension enum to database column."""
        mapping = {
            ExposureDimension.SECTOR: "sector",
            ExposureDimension.GEOGRAPHY: "country_of_risk",
            ExposureDimension.ASSET_CLASS: "asset_class",
            ExposureDimension.CURRENCY: "currency",
            ExposureDimension.INDUSTRY: "industry_group",
            ExposureDimension.COUNTRY: "country_of_risk",
        }
        return mapping.get(dimension, "sector")

    def calculate_sector_exposure(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate sector exposure breakdown."""
        return self.calculate_exposure_breakdown(
            book_id, tenant_id, ExposureDimension.SECTOR
        )

    def calculate_geography_exposure(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate geography/country exposure breakdown."""
        return self.calculate_exposure_breakdown(
            book_id, tenant_id, ExposureDimension.GEOGRAPHY
        )

    def calculate_asset_class_exposure(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate asset class exposure breakdown."""
        return self.calculate_exposure_breakdown(
            book_id, tenant_id, ExposureDimension.ASSET_CLASS
        )

    def calculate_currency_exposure(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate currency exposure breakdown."""
        return self.calculate_exposure_breakdown(
            book_id, tenant_id, ExposureDimension.CURRENCY
        )

    def calculate_all_exposures(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate all exposure breakdowns for a book.

        Returns:
            Dict with all exposure breakdowns
        """
        return {
            "book_id": str(book_id),
            "sector": self.calculate_sector_exposure(book_id, tenant_id),
            "geography": self.calculate_geography_exposure(book_id, tenant_id),
            "asset_class": self.calculate_asset_class_exposure(book_id, tenant_id),
            "currency": self.calculate_currency_exposure(book_id, tenant_id),
        }

    # =========================================================================
    # Concentration Metrics
    # =========================================================================

    def calculate_concentration_metrics(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate concentration metrics for a book.

        Metrics:
        - Top 10 position concentration
        - Single name maximum exposure
        - Sector concentration (HHI)

        Returns:
            Dict with concentration metrics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get positions sorted by market value
        cur.execute("""
            SELECT
                p.id,
                p.security_id,
                p.market_value,
                p.direction,
                s.ticker,
                s.name as security_name,
                s.sector
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = %s AND p.tenant_id = %s
              AND p.market_value IS NOT NULL
            ORDER BY ABS(p.market_value) DESC
        """, (str(book_id), str(tenant_id)))

        positions = cur.fetchall()

        if not positions:
            return {
                "book_id": str(book_id),
                "top_10_concentration": 0.0,
                "single_name_max": 0.0,
                "sector_hhi": 0.0,
                "position_count": 0,
            }

        # Total market value (gross)
        total_mv = sum(abs(float(p["market_value"])) for p in positions)

        # Top 10 concentration
        top_10_mv = sum(abs(float(p["market_value"])) for p in positions[:10])
        top_10_concentration = (top_10_mv / total_mv * 100) if total_mv > 0 else 0

        # Single name maximum
        single_name_max = (abs(float(positions[0]["market_value"])) / total_mv * 100) if total_mv > 0 else 0

        # Sector HHI (Herfindahl-Hirschman Index)
        sector_exposure = {}
        for p in positions:
            sector = p["sector"] or "Unknown"
            mv = abs(float(p["market_value"]))
            sector_exposure[sector] = sector_exposure.get(sector, 0) + mv

        sector_hhi = 0
        for sector, mv in sector_exposure.items():
            share = (mv / total_mv) if total_mv > 0 else 0
            sector_hhi += share ** 2

        # HHI ranges from 0 to 1, multiply by 10000 for standard HHI scale
        sector_hhi *= 10000

        return {
            "book_id": str(book_id),
            "top_10_concentration": round(top_10_concentration, 2),
            "single_name_max": round(single_name_max, 2),
            "single_name_max_ticker": positions[0]["ticker"] if positions else None,
            "sector_hhi": round(sector_hhi, 2),
            "position_count": len(positions),
            "total_gross_exposure": total_mv,
        }

    # =========================================================================
    # Exposure Summary
    # =========================================================================

    def calculate_exposure_summary(
        self,
        book_id: UUID,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate summary exposure metrics for a book.

        Returns:
            Dict with gross, net, long, short exposures
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                COUNT(*) as position_count,
                COALESCE(SUM(CASE WHEN direction = 'long' THEN market_value ELSE 0 END), 0) as long_exposure,
                COALESCE(SUM(CASE WHEN direction = 'short' THEN ABS(market_value) ELSE 0 END), 0) as short_exposure,
                COALESCE(SUM(market_value), 0) as net_exposure,
                COALESCE(SUM(ABS(market_value)), 0) as gross_exposure
            FROM positions
            WHERE book_id = %s AND tenant_id = %s
              AND market_value IS NOT NULL
        """, (str(book_id), str(tenant_id)))

        result = cur.fetchone()

        long_exp = float(result["long_exposure"])
        short_exp = float(result["short_exposure"])
        net_exp = float(result["net_exposure"])
        gross_exp = float(result["gross_exposure"])

        # Calculate leverage ratio (gross / net)
        leverage = (gross_exp / abs(net_exp)) if net_exp != 0 else 0

        return {
            "book_id": str(book_id),
            "long_exposure": long_exp,
            "short_exposure": short_exp,
            "net_exposure": net_exp,
            "gross_exposure": gross_exp,
            "long_short_ratio": (long_exp / short_exp) if short_exp > 0 else None,
            "leverage_ratio": round(leverage, 2),
            "position_count": result["position_count"],
        }
