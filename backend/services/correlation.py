# RISKCORE Correlation Service
# Cross-pod correlation matrix and firm-level VaR calculation
# THE CORE - Week 4 Aggregation Engine

from typing import Dict, Tuple, Optional, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
import math
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from .riskpod import RiskPod, RiskPodService

logger = logging.getLogger(__name__)


# Default cross-asset correlations (based on historical market behavior)
# These are typical values; can be overridden with firm-specific estimates
# Keys are sorted alphabetically for consistent lookup
DEFAULT_CORRELATIONS: Dict[Tuple[str, str], float] = {
    # Equity correlations (credit < equity < fx < other < rates alphabetically)
    ('credit', 'equity'): 0.40,     # Equity-Credit: positive (risk-on correlation)
    ('equity', 'fx'): 0.15,         # Equity-FX: mild positive
    ('equity', 'other'): 0.25,      # Equity-Other: moderate positive
    ('equity', 'rates'): -0.20,     # Equity-Rates: negative (flight to quality)
    # Rates correlations
    ('credit', 'rates'): 0.30,      # Rates-Credit: positive (spread compression)
    ('fx', 'rates'): 0.10,          # Rates-FX: mild positive
    ('other', 'rates'): -0.05,      # Rates-Other: near zero
    # Credit correlations
    ('credit', 'fx'): 0.20,         # Credit-FX: moderate positive
    ('credit', 'other'): 0.15,      # Credit-Other: mild positive
    # FX correlations
    ('fx', 'other'): 0.30,          # FX-Other: moderate positive (commodity currencies)
}

# Crisis mode correlations (correlations spike toward 1.0 in stress)
# Keys are sorted alphabetically for consistent lookup
CRISIS_CORRELATIONS: Dict[Tuple[str, str], float] = {
    ('credit', 'equity'): 0.80,     # Contagion
    ('equity', 'fx'): 0.50,         # Risk-off
    ('equity', 'other'): 0.60,      # Correlation spike
    ('equity', 'rates'): 0.10,      # Less negative in crisis
    ('credit', 'rates'): 0.50,
    ('fx', 'rates'): 0.30,
    ('other', 'rates'): 0.20,
    ('credit', 'fx'): 0.50,
    ('credit', 'other'): 0.40,
    ('fx', 'other'): 0.50,
}


def get_correlation(pod1: RiskPod, pod2: RiskPod, crisis_mode: bool = False) -> float:
    """
    Get correlation between two RiskPods.

    Args:
        pod1: First RiskPod
        pod2: Second RiskPod
        crisis_mode: If True, use crisis correlations (higher)

    Returns:
        Correlation coefficient between -1 and 1
    """
    if pod1 == pod2:
        return 1.0

    # Sort to ensure consistent key lookup
    key = tuple(sorted([pod1.value, pod2.value]))

    correlations = CRISIS_CORRELATIONS if crisis_mode else DEFAULT_CORRELATIONS
    return correlations.get(key, 0.0)


def build_correlation_matrix(crisis_mode: bool = False) -> Dict[str, Dict[str, float]]:
    """
    Build full correlation matrix for all RiskPods.

    Args:
        crisis_mode: If True, use crisis correlations

    Returns:
        Nested dict with correlations[pod1][pod2] = correlation
    """
    pods = list(RiskPod)
    matrix = {}

    for pod1 in pods:
        matrix[pod1.value] = {}
        for pod2 in pods:
            matrix[pod1.value][pod2.value] = get_correlation(pod1, pod2, crisis_mode)

    return matrix


@dataclass
class FirmVaRResult:
    """Result of firm-level VaR calculation with diversification."""

    # Pod-level VaRs
    pod_vars: Dict[str, float]

    # Aggregation
    sum_of_pod_vars: float          # Simple sum (no correlation)
    firm_var_correlated: float      # Correlation-adjusted firm VaR
    diversification_benefit: float  # Sum - Correlated ($ saved)
    diversification_pct: float      # % reduction from diversification

    # Methodology
    crisis_mode: bool
    var_confidence: float           # e.g., 0.95 for 95% VaR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "pod_vars": self.pod_vars,
            "sum_of_pod_vars": round(self.sum_of_pod_vars, 2),
            "firm_var_correlated": round(self.firm_var_correlated, 2),
            "diversification_benefit": round(self.diversification_benefit, 2),
            "diversification_pct": round(self.diversification_pct, 2),
            "crisis_mode": self.crisis_mode,
            "var_confidence": self.var_confidence,
            "methodology": "variance_covariance",
            "note": "Diversification benefit = Sum of Pod VaRs - Firm VaR",
        }


class CorrelationService:
    """
    Service for cross-pod correlation analysis and firm-level VaR.

    The correlation-adjusted firm VaR is a key RISKCORE differentiator:
    - Aggregates risk across pods while accounting for diversification
    - Shows how much risk is "saved" from cross-pod correlations
    - Supports normal and crisis mode correlations
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """Initialize with database connection."""
        self.conn = conn
        self.riskpod_service = RiskPodService(conn)

    def get_correlation_matrix(
        self,
        tenant_id: UUID,
        crisis_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Get correlation matrix for all RiskPods.

        Args:
            tenant_id: Tenant ID (for potential tenant-specific correlations)
            crisis_mode: Use crisis correlations if True

        Returns:
            Correlation matrix with metadata
        """
        matrix = build_correlation_matrix(crisis_mode)

        return {
            "matrix": matrix,
            "pods": [pod.value for pod in RiskPod],
            "crisis_mode": crisis_mode,
            "source": "default_estimates",
            "note": "Default correlations based on historical market behavior. "
                    "Crisis mode shows elevated correlations during market stress.",
        }

    def calculate_firm_var_correlated(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
        crisis_mode: bool = False,
        var_confidence: float = 0.95,
    ) -> FirmVaRResult:
        """
        Calculate firm-level VaR with cross-pod correlation adjustment.

        Uses variance-covariance approach:
        Firm VaR = sqrt(sum of variances + 2*sum of covariances)

        Where:
        - Variance for pod i = VaR_i^2
        - Covariance for pods i,j = VaR_i * VaR_j * Correlation(i,j)

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter
            crisis_mode: Use crisis correlations if True
            var_confidence: VaR confidence level (default 0.95)

        Returns:
            FirmVaRResult with pod VaRs, firm VaR, and diversification benefit
        """
        # Get VaR for each pod
        var_breakdown = self.riskpod_service.get_pod_var_breakdown(tenant_id, fund_id)
        pod_var_data = var_breakdown.get('pod_vars', {})

        # Extract VaR values (only for pods with exposure)
        pod_vars: Dict[str, float] = {}
        for pod_name, data in pod_var_data.items():
            if data['var_95_estimate'] > 0:
                pod_vars[pod_name] = data['var_95_estimate']

        if not pod_vars:
            return FirmVaRResult(
                pod_vars={},
                sum_of_pod_vars=0.0,
                firm_var_correlated=0.0,
                diversification_benefit=0.0,
                diversification_pct=0.0,
                crisis_mode=crisis_mode,
                var_confidence=var_confidence,
            )

        # Sum of pod VaRs (undiversified)
        sum_of_vars = sum(pod_vars.values())

        # Calculate variance-covariance firm VaR
        # Formula: sqrt(sum_i(VaR_i^2) + 2*sum_{i<j}(VaR_i*VaR_j*Corr(i,j)))
        variance_sum = 0.0
        covariance_sum = 0.0

        pods_with_exposure = list(pod_vars.keys())

        for i, pod1 in enumerate(pods_with_exposure):
            var1 = pod_vars[pod1]
            variance_sum += var1 ** 2

            for pod2 in pods_with_exposure[i+1:]:
                var2 = pod_vars[pod2]
                corr = get_correlation(
                    RiskPod(pod1),
                    RiskPod(pod2),
                    crisis_mode
                )
                covariance_sum += var1 * var2 * corr

        firm_var_squared = variance_sum + 2 * covariance_sum

        # Handle numerical issues (can be slightly negative due to floating point)
        firm_var_correlated = math.sqrt(max(0, firm_var_squared))

        # Diversification benefit
        diversification_benefit = sum_of_vars - firm_var_correlated
        diversification_pct = (diversification_benefit / sum_of_vars * 100) if sum_of_vars > 0 else 0.0

        return FirmVaRResult(
            pod_vars=pod_vars,
            sum_of_pod_vars=sum_of_vars,
            firm_var_correlated=firm_var_correlated,
            diversification_benefit=diversification_benefit,
            diversification_pct=diversification_pct,
            crisis_mode=crisis_mode,
            var_confidence=var_confidence,
        )

    def compare_normal_vs_crisis(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Compare firm VaR under normal vs crisis correlations.

        Shows how much additional risk emerges when correlations spike.

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            Comparison of normal vs crisis VaR
        """
        normal = self.calculate_firm_var_correlated(tenant_id, fund_id, crisis_mode=False)
        crisis = self.calculate_firm_var_correlated(tenant_id, fund_id, crisis_mode=True)

        crisis_impact = crisis.firm_var_correlated - normal.firm_var_correlated
        crisis_impact_pct = (crisis_impact / normal.firm_var_correlated * 100) if normal.firm_var_correlated > 0 else 0

        return {
            "normal_mode": normal.to_dict(),
            "crisis_mode": crisis.to_dict(),
            "crisis_impact": {
                "additional_var": round(crisis_impact, 2),
                "additional_var_pct": round(crisis_impact_pct, 2),
                "diversification_lost_pct": round(
                    normal.diversification_pct - crisis.diversification_pct, 2
                ),
            },
            "interpretation": (
                f"In crisis mode, firm VaR increases by ${round(crisis_impact/1e6, 2)}M "
                f"({round(crisis_impact_pct, 1)}%) as correlations spike. "
                f"Diversification benefit drops from {round(normal.diversification_pct, 1)}% "
                f"to {round(crisis.diversification_pct, 1)}%."
                if crisis_impact > 0 else
                "No material change between normal and crisis modes."
            ),
        }

    def get_cross_pod_exposure_matrix(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get cross-pod exposure matrix showing PM exposure across pods.

        Useful for identifying PMs with exposure across multiple pods
        (which adds diversification benefit).

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            Matrix of PM exposure by pod
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        fund_filter = ""
        params = [str(tenant_id)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT
                b.pm_id,
                u.name as pm_name,
                s.asset_class,
                SUM(ABS(COALESCE(p.market_value_base, p.market_value, 0))) as gross_exposure
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            LEFT JOIN users u ON b.pm_id = u.id
            WHERE p.tenant_id = %s
              {fund_filter}
              AND b.pm_id IS NOT NULL
            GROUP BY b.pm_id, u.name, s.asset_class
        """, params)

        results = cur.fetchall()

        # Build PM x Pod matrix
        pm_exposures: Dict[str, Dict[str, float]] = {}
        pm_names: Dict[str, str] = {}

        from .riskpod import get_riskpod

        for row in results:
            pm_id = str(row['pm_id'])
            pm_names[pm_id] = row['pm_name'] or 'Unknown'
            pod = get_riskpod(row['asset_class']).value

            if pm_id not in pm_exposures:
                pm_exposures[pm_id] = {p.value: 0.0 for p in RiskPod}

            pm_exposures[pm_id][pod] += float(row['gross_exposure'])

        # Calculate diversity score (how many pods does PM have exposure to)
        pm_matrix = []
        for pm_id, exposures in pm_exposures.items():
            active_pods = sum(1 for v in exposures.values() if v > 0)
            total_exposure = sum(exposures.values())

            pm_matrix.append({
                'pm_id': pm_id,
                'pm_name': pm_names[pm_id],
                'exposures_by_pod': exposures,
                'total_exposure': total_exposure,
                'active_pods': active_pods,
                'diversity_score': active_pods / len(RiskPod),
            })

        # Sort by total exposure
        pm_matrix.sort(key=lambda x: x['total_exposure'], reverse=True)

        return {
            'pm_matrix': pm_matrix,
            'pods': [p.value for p in RiskPod],
            'total_pms': len(pm_matrix),
            'multi_pod_pms': sum(1 for pm in pm_matrix if pm['active_pods'] > 1),
        }
