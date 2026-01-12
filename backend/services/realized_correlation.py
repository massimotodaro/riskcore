# RISKCORE Realized Correlation Service
# Calculates realized and implied correlations from return data
# Week 4 Enhancement: Foundation for AI-native queries

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
import math
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from .returns import ReturnsService, ReturnWindow, ReturnSeries
from .riskpod import RiskPod, RiskPodService

logger = logging.getLogger(__name__)


class CorrelationEntityType(str, Enum):
    """Types of entities that can be correlated."""
    BOOK = "book"
    PM = "pm"
    FUND = "fund"
    POD = "pod"


class CorrelationType(str, Enum):
    """Types of correlation calculations."""
    REALIZED = "realized"   # From historical returns
    IMPLIED = "implied"     # From current portfolio structure


@dataclass
class CorrelationResult:
    """Result of a correlation calculation."""
    entity1_id: str
    entity1_name: str
    entity2_id: str
    entity2_name: str
    entity_type: CorrelationEntityType
    correlation_type: CorrelationType
    window: ReturnWindow
    correlation: float
    data_points: int
    p_value: Optional[float] = None
    as_of_date: Optional[date] = None

    @property
    def strength(self) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(self.correlation)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "negligible"

    @property
    def is_concerning(self) -> bool:
        """Flag high correlations that might indicate concentration risk."""
        return abs(self.correlation) >= 0.7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity1_id": self.entity1_id,
            "entity1_name": self.entity1_name,
            "entity2_id": self.entity2_id,
            "entity2_name": self.entity2_name,
            "entity_type": self.entity_type.value,
            "correlation_type": self.correlation_type.value,
            "window": self.window.value,
            "correlation": round(self.correlation, 4),
            "strength": self.strength,
            "is_concerning": self.is_concerning,
            "data_points": self.data_points,
            "p_value": round(self.p_value, 6) if self.p_value else None,
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date else None,
        }


@dataclass
class PMCorrelationMatrix:
    """Full correlation matrix between PMs."""
    tenant_id: UUID
    window: ReturnWindow
    correlation_type: CorrelationType
    pm_names: List[str]
    pm_ids: List[str]
    matrix: List[List[float]]  # 2D correlation matrix
    as_of_date: date
    high_correlation_pairs: List[CorrelationResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "window": self.window.value,
            "correlation_type": self.correlation_type.value,
            "pm_count": len(self.pm_names),
            "pm_names": self.pm_names,
            "pm_ids": self.pm_ids,
            "matrix": self.matrix,
            "as_of_date": self.as_of_date.isoformat(),
            "high_correlation_count": len(self.high_correlation_pairs),
            "high_correlation_pairs": [p.to_dict() for p in self.high_correlation_pairs],
        }


def calculate_pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, int]:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x: First series
        y: Second series

    Returns:
        Tuple of (correlation, data_points)
    """
    n = min(len(x), len(y))
    if n < 2:
        return 0.0, n

    x = x[:n]
    y = y[:n]

    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate correlation components
    sum_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    sum_x2 = sum((xi - mean_x) ** 2 for xi in x)
    sum_y2 = sum((yi - mean_y) ** 2 for yi in y)

    # Avoid division by zero
    if sum_x2 == 0 or sum_y2 == 0:
        return 0.0, n

    correlation = sum_xy / math.sqrt(sum_x2 * sum_y2)
    return correlation, n


class RealizedCorrelationService:
    """
    Service for calculating realized and implied correlations.

    Provides:
    - PM-to-PM realized correlations
    - Pod-to-Pod realized correlations
    - Implied correlations from portfolio overlap
    - Correlation caching for efficient queries
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn
        self.returns_service = ReturnsService(conn)
        self.riskpod_service = RiskPodService(conn)

    # =========================================================================
    # REALIZED CORRELATIONS (from historical returns)
    # =========================================================================

    def calculate_pm_correlation(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> CorrelationResult:
        """
        Calculate realized correlation between two PMs.

        Args:
            tenant_id: Tenant ID
            pm1_id: First PM ID
            pm2_id: Second PM ID
            window: Time window for correlation
            end_date: End date (defaults to today)

        Returns:
            CorrelationResult
        """
        # Get return series for both PMs
        series1 = self.returns_service.get_pm_returns(tenant_id, pm1_id, window, end_date)
        series2 = self.returns_service.get_pm_returns(tenant_id, pm2_id, window, end_date)

        # Align dates and calculate correlation
        returns1, returns2 = self._align_return_series(series1, series2)

        correlation, n = calculate_pearson_correlation(returns1, returns2)

        return CorrelationResult(
            entity1_id=str(pm1_id),
            entity1_name=series1.entity_name,
            entity2_id=str(pm2_id),
            entity2_name=series2.entity_name,
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=window,
            correlation=correlation,
            data_points=n,
            as_of_date=end_date or date.today(),
        )

    def _align_return_series(
        self,
        series1: ReturnSeries,
        series2: ReturnSeries,
    ) -> Tuple[List[float], List[float]]:
        """Align two return series by date."""
        # Build date -> return mapping
        returns1_by_date = {r.return_date: r for r in series1.returns}
        returns2_by_date = {r.return_date: r for r in series2.returns}

        # Find common dates
        common_dates = set(returns1_by_date.keys()) & set(returns2_by_date.keys())
        common_dates = sorted(common_dates)

        # Extract aligned returns
        aligned1 = []
        aligned2 = []

        for d in common_dates:
            r1 = returns1_by_date[d]
            r2 = returns2_by_date[d]

            # Use return percentage if available, otherwise P&L
            val1 = float(r1.daily_return_pct) if r1.daily_return_pct else float(r1.daily_pnl)
            val2 = float(r2.daily_return_pct) if r2.daily_return_pct else float(r2.daily_pnl)

            aligned1.append(val1)
            aligned2.append(val2)

        return aligned1, aligned2

    def calculate_pm_correlation_all_windows(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
        end_date: Optional[date] = None,
    ) -> Dict[str, CorrelationResult]:
        """
        Calculate PM correlation for all standard windows.

        Args:
            tenant_id: Tenant ID
            pm1_id: First PM
            pm2_id: Second PM
            end_date: End date

        Returns:
            Dict mapping window to CorrelationResult
        """
        results = {}

        for window in [ReturnWindow.DAY_1, ReturnWindow.DAY_5,
                       ReturnWindow.DAY_21, ReturnWindow.DAY_63]:
            result = self.calculate_pm_correlation(
                tenant_id, pm1_id, pm2_id, window, end_date
            )
            results[window.value] = result

        return results

    def build_pm_correlation_matrix(
        self,
        tenant_id: UUID,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> PMCorrelationMatrix:
        """
        Build full PM correlation matrix.

        Args:
            tenant_id: Tenant ID
            window: Time window
            end_date: End date

        Returns:
            PMCorrelationMatrix with all PM-to-PM correlations
        """
        if end_date is None:
            end_date = date.today()

        # Get all PM return series
        all_pm_returns = self.returns_service.get_all_pm_returns(tenant_id, window, end_date)

        if not all_pm_returns:
            return PMCorrelationMatrix(
                tenant_id=tenant_id,
                window=window,
                correlation_type=CorrelationType.REALIZED,
                pm_names=[],
                pm_ids=[],
                matrix=[],
                as_of_date=end_date,
                high_correlation_pairs=[],
            )

        # Build matrix
        n = len(all_pm_returns)
        pm_names = [s.entity_name for s in all_pm_returns]
        pm_ids = [str(s.entity_id) for s in all_pm_returns]
        matrix = [[0.0] * n for _ in range(n)]
        high_correlations = []

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                elif i < j:
                    # Calculate correlation
                    returns1, returns2 = self._align_return_series(
                        all_pm_returns[i], all_pm_returns[j]
                    )
                    corr, data_points = calculate_pearson_correlation(returns1, returns2)
                    matrix[i][j] = corr
                    matrix[j][i] = corr  # Symmetric

                    # Track high correlations
                    if abs(corr) >= 0.7:
                        high_correlations.append(CorrelationResult(
                            entity1_id=pm_ids[i],
                            entity1_name=pm_names[i],
                            entity2_id=pm_ids[j],
                            entity2_name=pm_names[j],
                            entity_type=CorrelationEntityType.PM,
                            correlation_type=CorrelationType.REALIZED,
                            window=window,
                            correlation=corr,
                            data_points=data_points,
                            as_of_date=end_date,
                        ))

        # Sort high correlations by absolute value
        high_correlations.sort(key=lambda x: abs(x.correlation), reverse=True)

        return PMCorrelationMatrix(
            tenant_id=tenant_id,
            window=window,
            correlation_type=CorrelationType.REALIZED,
            pm_names=pm_names,
            pm_ids=pm_ids,
            matrix=matrix,
            as_of_date=end_date,
            high_correlation_pairs=high_correlations,
        )

    # =========================================================================
    # IMPLIED CORRELATIONS (from portfolio structure)
    # =========================================================================

    def calculate_implied_pm_correlation(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
    ) -> CorrelationResult:
        """
        Calculate implied correlation between two PMs based on portfolio overlap.

        Implied correlation is estimated from:
        1. Common security holdings (direct overlap)
        2. Common sector/industry exposure
        3. Common RiskPod exposure

        This forward-looking measure predicts future correlation based on
        current portfolio structure.

        Args:
            tenant_id: Tenant ID
            pm1_id: First PM
            pm2_id: Second PM

        Returns:
            CorrelationResult with implied correlation
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get PM names
        cur.execute("""
            SELECT id, name FROM users WHERE id IN (%s, %s)
        """, (str(pm1_id), str(pm2_id)))
        pm_rows = {str(r['id']): r['name'] for r in cur.fetchall()}
        pm1_name = pm_rows.get(str(pm1_id), 'Unknown')
        pm2_name = pm_rows.get(str(pm2_id), 'Unknown')

        # Component 1: Direct security overlap
        security_overlap_corr = self._calculate_security_overlap_correlation(
            tenant_id, pm1_id, pm2_id
        )

        # Component 2: RiskPod exposure similarity
        pod_similarity_corr = self._calculate_pod_similarity(
            tenant_id, pm1_id, pm2_id
        )

        # Combined implied correlation (weighted average)
        # Security overlap is more predictive, so weight it higher
        implied_corr = (
            0.7 * security_overlap_corr +
            0.3 * pod_similarity_corr
        )

        return CorrelationResult(
            entity1_id=str(pm1_id),
            entity1_name=pm1_name,
            entity2_id=str(pm2_id),
            entity2_name=pm2_name,
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.IMPLIED,
            window=ReturnWindow.DAY_21,  # Implied doesn't have a window
            correlation=implied_corr,
            data_points=0,  # Not applicable for implied
            as_of_date=date.today(),
        )

    def _calculate_security_overlap_correlation(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
    ) -> float:
        """Calculate correlation component from direct security overlap."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get securities held by PM1
        cur.execute("""
            SELECT DISTINCT p.security_id
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
        """, (str(tenant_id), str(pm1_id)))
        pm1_securities = {r['security_id'] for r in cur.fetchall()}

        # Get securities held by PM2
        cur.execute("""
            SELECT DISTINCT p.security_id
            FROM positions p
            JOIN books b ON p.book_id = b.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
        """, (str(tenant_id), str(pm2_id)))
        pm2_securities = {r['security_id'] for r in cur.fetchall()}

        if not pm1_securities or not pm2_securities:
            return 0.0

        # Jaccard similarity of security sets
        intersection = len(pm1_securities & pm2_securities)
        union = len(pm1_securities | pm2_securities)

        jaccard = intersection / union if union > 0 else 0

        # Scale Jaccard to correlation-like range
        # High overlap (Jaccard > 0.5) suggests high correlation
        return min(jaccard * 2, 1.0)

    def _calculate_pod_similarity(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
    ) -> float:
        """Calculate correlation component from RiskPod exposure similarity."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get pod exposure for PM1
        pm1_pod = self._get_pm_pod_weights(tenant_id, pm1_id)
        pm2_pod = self._get_pm_pod_weights(tenant_id, pm2_id)

        if not pm1_pod or not pm2_pod:
            return 0.0

        # Cosine similarity of pod weight vectors
        dot_product = sum(pm1_pod.get(pod, 0) * pm2_pod.get(pod, 0) for pod in RiskPod)
        norm1 = math.sqrt(sum(w ** 2 for w in pm1_pod.values()))
        norm2 = math.sqrt(sum(w ** 2 for w in pm2_pod.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _get_pm_pod_weights(
        self,
        tenant_id: UUID,
        pm_id: UUID,
    ) -> Dict[RiskPod, float]:
        """Get PM's exposure weights by RiskPod."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                s.asset_class,
                SUM(ABS(COALESCE(p.market_value_base, p.market_value, 0))) as exposure
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s AND b.pm_id = %s
            GROUP BY s.asset_class
        """, (str(tenant_id), str(pm_id)))

        total = 0.0
        pod_exposure = {pod: 0.0 for pod in RiskPod}

        from .riskpod import get_riskpod

        for row in cur.fetchall():
            if row['asset_class']:
                pod = get_riskpod(row['asset_class'])
                exposure = float(row['exposure'] or 0)
                pod_exposure[pod] += exposure
                total += exposure

        # Convert to weights
        if total > 0:
            return {pod: exp / total for pod, exp in pod_exposure.items()}

        return pod_exposure

    # =========================================================================
    # COMBINED ANALYSIS
    # =========================================================================

    def get_pm_correlation_analysis(
        self,
        tenant_id: UUID,
        pm1_id: UUID,
        pm2_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get comprehensive correlation analysis between two PMs.

        Combines realized correlations (multiple windows) with implied correlation.

        Args:
            tenant_id: Tenant ID
            pm1_id: First PM
            pm2_id: Second PM

        Returns:
            Complete correlation analysis for AI/dashboard display
        """
        # Get realized correlations for all windows
        realized = self.calculate_pm_correlation_all_windows(tenant_id, pm1_id, pm2_id)

        # Get implied correlation
        implied = self.calculate_implied_pm_correlation(tenant_id, pm1_id, pm2_id)

        # Get pod exposure breakdown for both PMs
        pm1_pods = self._get_pm_pod_weights(tenant_id, pm1_id)
        pm2_pods = self._get_pm_pod_weights(tenant_id, pm2_id)

        # Determine if there's a concerning pattern
        recent_corr = realized.get('5d')
        historical_corr = realized.get('21d')

        is_increasing = (
            recent_corr and historical_corr and
            recent_corr.correlation > historical_corr.correlation + 0.1
        )

        # Build analysis response
        return {
            "pm1": {
                "id": str(pm1_id),
                "name": implied.entity1_name,
                "pod_weights": {pod.value: round(w * 100, 1) for pod, w in pm1_pods.items()},
            },
            "pm2": {
                "id": str(pm2_id),
                "name": implied.entity2_name,
                "pod_weights": {pod.value: round(w * 100, 1) for pod, w in pm2_pods.items()},
            },
            "realized_correlations": {
                window: corr.to_dict() for window, corr in realized.items()
            },
            "implied_correlation": implied.to_dict(),
            "analysis": {
                "is_highly_correlated": any(
                    c.is_concerning for c in realized.values()
                ),
                "is_correlation_increasing": is_increasing,
                "highest_window": max(realized.items(), key=lambda x: abs(x[1].correlation))[0]
                    if realized else None,
                "recommendation": self._generate_correlation_recommendation(realized, implied),
            },
        }

    def _generate_correlation_recommendation(
        self,
        realized: Dict[str, CorrelationResult],
        implied: CorrelationResult,
    ) -> str:
        """Generate AI-style recommendation based on correlation analysis."""
        # Find the most recent realized correlation
        recent = realized.get('5d') or realized.get('1d')
        monthly = realized.get('21d')

        if not recent:
            return "Insufficient return data for correlation analysis."

        if recent.is_concerning and implied.is_concerning:
            return (
                f"HIGH ALERT: Both realized ({recent.correlation:.2f}) and implied "
                f"({implied.correlation:.2f}) correlations are elevated. "
                "These PMs have significant position overlap and recent returns are moving together. "
                "Consider reviewing for concentration risk."
            )
        elif recent.is_concerning:
            return (
                f"Recent correlation is elevated ({recent.correlation:.2f}) but implied correlation "
                f"({implied.correlation:.2f}) suggests different portfolio structures. "
                "This may be a temporary market-driven effect."
            )
        elif implied.is_concerning:
            return (
                f"Portfolio overlap is high (implied: {implied.correlation:.2f}) but "
                f"realized correlation is moderate ({recent.correlation:.2f}). "
                "Watch for correlation to increase as positions become more similar."
            )
        else:
            return (
                f"Correlation is within normal range (realized: {recent.correlation:.2f}, "
                f"implied: {implied.correlation:.2f}). "
                "These PMs provide diversification benefit."
            )

    # =========================================================================
    # CACHING
    # =========================================================================

    def cache_correlation(
        self,
        tenant_id: UUID,
        result: CorrelationResult,
    ):
        """Cache a correlation result for efficient future queries."""
        cur = self.conn.cursor()

        cur.execute("""
            INSERT INTO correlation_cache (
                tenant_id, entity_type, entity1_id, entity1_name,
                entity2_id, entity2_name, correlation_type, window,
                correlation_value, data_points, as_of_date
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (tenant_id, entity_type, entity1_id, entity2_id, correlation_type, window, as_of_date)
            DO UPDATE SET
                correlation_value = EXCLUDED.correlation_value,
                data_points = EXCLUDED.data_points,
                calculated_at = NOW()
        """, (
            str(tenant_id),
            result.entity_type.value,
            result.entity1_id,
            result.entity1_name,
            result.entity2_id,
            result.entity2_name,
            result.correlation_type.value,
            result.window.value,
            result.correlation,
            result.data_points,
            result.as_of_date,
        ))

        self.conn.commit()

    def get_cached_correlation(
        self,
        tenant_id: UUID,
        entity1_id: UUID,
        entity2_id: UUID,
        entity_type: CorrelationEntityType,
        correlation_type: CorrelationType,
        window: ReturnWindow,
        as_of_date: Optional[date] = None,
    ) -> Optional[CorrelationResult]:
        """Retrieve cached correlation if available."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if as_of_date is None:
            as_of_date = date.today()

        cur.execute("""
            SELECT * FROM correlation_cache
            WHERE tenant_id = %s
              AND entity_type = %s
              AND entity1_id = %s
              AND entity2_id = %s
              AND correlation_type = %s
              AND window = %s
              AND as_of_date = %s
        """, (
            str(tenant_id),
            entity_type.value,
            str(entity1_id),
            str(entity2_id),
            correlation_type.value,
            window.value,
            as_of_date,
        ))

        row = cur.fetchone()
        if not row:
            return None

        return CorrelationResult(
            entity1_id=row['entity1_id'],
            entity1_name=row['entity1_name'],
            entity2_id=row['entity2_id'],
            entity2_name=row['entity2_name'],
            entity_type=entity_type,
            correlation_type=correlation_type,
            window=window,
            correlation=float(row['correlation_value']),
            data_points=row['data_points'],
            as_of_date=row['as_of_date'],
        )

    def refresh_all_pm_correlations(
        self,
        tenant_id: UUID,
        as_of_date: Optional[date] = None,
    ):
        """Refresh all PM correlation cache for a tenant."""
        if as_of_date is None:
            as_of_date = date.today()

        for window in [ReturnWindow.DAY_1, ReturnWindow.DAY_5,
                       ReturnWindow.DAY_21, ReturnWindow.DAY_63]:
            matrix = self.build_pm_correlation_matrix(tenant_id, window, as_of_date)

            # Cache each pair
            n = len(matrix.pm_ids)
            for i in range(n):
                for j in range(i + 1, n):
                    result = CorrelationResult(
                        entity1_id=matrix.pm_ids[i],
                        entity1_name=matrix.pm_names[i],
                        entity2_id=matrix.pm_ids[j],
                        entity2_name=matrix.pm_names[j],
                        entity_type=CorrelationEntityType.PM,
                        correlation_type=CorrelationType.REALIZED,
                        window=window,
                        correlation=matrix.matrix[i][j],
                        data_points=21,  # Approximate
                        as_of_date=as_of_date,
                    )
                    self.cache_correlation(tenant_id, result)

        logger.info(f"Refreshed PM correlation cache for tenant {tenant_id}")
