# RISKCORE RiskPod Service
# Maps asset classes to RiskPods and defines pod-specific risk metrics
# THE CORE - Week 4 Aggregation Engine

from enum import Enum
from typing import Dict, List, Any, Optional, Set
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass, field
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class RiskPod(str, Enum):
    """
    RiskPod categories for firm-level risk organization.

    This mirrors how pod shops (Millennium, Citadel, Balyasny) organize:
    - Each pod has distinct risk characteristics
    - Options follow their underlying's pod
    - Enables correlation-adjusted firm VaR
    """
    EQUITY = "equity"      # Stocks, equity options, equity futures, ETFs
    RATES = "rates"        # Bonds, swaps, rate futures
    CREDIT = "credit"      # CDS, corporate bonds (credit spread focus)
    FX = "fx"              # Spot, forwards, FX options
    OTHER = "other"        # Commodities, crypto, alternatives


# Asset class to RiskPod mapping
ASSET_CLASS_TO_POD: Dict[str, RiskPod] = {
    'equity': RiskPod.EQUITY,
    'option': RiskPod.EQUITY,       # Options follow underlying (equity)
    'future': RiskPod.EQUITY,       # Equity index futures
    'fund': RiskPod.EQUITY,         # ETFs
    'fixed_income': RiskPod.RATES,  # Government bonds default to rates
    'swap': RiskPod.RATES,          # Interest rate swaps
    'cds': RiskPod.CREDIT,          # Credit default swaps
    'fx': RiskPod.FX,
    'commodity': RiskPod.OTHER,
    'crypto': RiskPod.OTHER,
    'other': RiskPod.OTHER,
}


# Risk metrics specific to each pod
POD_RISK_METRICS: Dict[RiskPod, List[str]] = {
    RiskPod.EQUITY: [
        "beta",              # Market sensitivity
        "delta",             # Price sensitivity (options)
        "gamma",             # Convexity of delta (options)
        "vega",              # Volatility sensitivity (options)
        "sector_exposure",   # % by GICS sector
        "concentration",     # Single-name %
        "var",               # Value at Risk
        "cvar",              # Conditional VaR
    ],
    RiskPod.RATES: [
        "dv01",              # Dollar value of 1bp
        "duration",          # Price sensitivity to rates
        "convexity",         # Curvature for large moves
        "key_rate_duration", # Sensitivity by tenor
        "yield",             # YTM, current yield
        "var",
        "cvar",
    ],
    RiskPod.CREDIT: [
        "cs01",              # Credit spread 01
        "credit_duration",   # Spread sensitivity
        "default_probability",  # PD from CDS spread
        "recovery_rate",     # LGD assumption
        "rating_exposure",   # % by rating (AAA to CCC)
        "var",
        "cvar",
    ],
    RiskPod.FX: [
        "fx_delta",          # Currency exposure
        "fx_vega",           # Volatility exposure (FX options)
        "basis_points",      # Forward spread risk
        "currency_exposure", # Net exposure by currency
        "var",
        "cvar",
    ],
    RiskPod.OTHER: [
        "price_sensitivity", # $ per unit move
        "basis_risk",        # Spot-futures spread
        "roll_yield",        # Contango/backwardation
        "var",
        "cvar",
    ],
}


@dataclass
class RiskPodSummary:
    """Summary statistics for a single RiskPod."""
    pod: RiskPod
    position_count: int = 0
    security_count: int = 0
    pm_count: int = 0

    # Exposure
    gross_long: Decimal = Decimal("0")
    gross_short: Decimal = Decimal("0")
    gross_total: Decimal = Decimal("0")
    net_exposure: Decimal = Decimal("0")

    # Risk metrics (pod-specific populated)
    var_95: Optional[Decimal] = None
    cvar_95: Optional[Decimal] = None

    # Pod-specific metrics (varies by pod)
    specific_metrics: Dict[str, Any] = field(default_factory=dict)

    # Breakdown
    top_securities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "pod": self.pod.value,
            "pod_display_name": self.pod.value.upper(),
            "position_count": self.position_count,
            "security_count": self.security_count,
            "pm_count": self.pm_count,
            "gross_long": float(self.gross_long),
            "gross_short": float(self.gross_short),
            "gross_total": float(self.gross_total),
            "net_exposure": float(self.net_exposure),
            "var_95": float(self.var_95) if self.var_95 else None,
            "cvar_95": float(self.cvar_95) if self.cvar_95 else None,
            "available_metrics": POD_RISK_METRICS.get(self.pod, []),
            "specific_metrics": self.specific_metrics,
            "top_securities": self.top_securities,
        }


def get_riskpod(asset_class: str, security_type: Optional[str] = None) -> RiskPod:
    """
    Determine RiskPod from asset class and optional security type.

    Args:
        asset_class: The asset_class enum value from database
        security_type: Optional security type for more granular mapping

    Returns:
        RiskPod enum value

    Example:
        get_riskpod('equity') -> RiskPod.EQUITY
        get_riskpod('option') -> RiskPod.EQUITY  # Options follow underlying
        get_riskpod('cds') -> RiskPod.CREDIT
    """
    if asset_class is None:
        return RiskPod.OTHER

    asset_class_lower = asset_class.lower()

    # Special handling for fixed_income based on security_type
    if asset_class_lower == 'fixed_income' and security_type:
        # Corporate bonds with credit spread focus go to CREDIT pod
        if security_type.lower() in ('corporate_bond', 'high_yield', 'investment_grade'):
            return RiskPod.CREDIT

    return ASSET_CLASS_TO_POD.get(asset_class_lower, RiskPod.OTHER)


def get_pod_metrics(pod: RiskPod) -> List[str]:
    """Get list of risk metrics relevant to a specific RiskPod."""
    return POD_RISK_METRICS.get(pod, [])


class RiskPodService:
    """
    Service for RiskPod-based aggregation and analysis.

    Organizes positions into RiskPods for:
    - Pod-level exposure analysis
    - Pod-specific risk metric calculation
    - Cross-pod correlation analysis
    - Firm-level aggregation with diversification benefit
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """Initialize with database connection."""
        self.conn = conn

    def get_position_pod(self, security_id: UUID) -> RiskPod:
        """
        Get the RiskPod for a security based on its asset class.

        Args:
            security_id: Security UUID

        Returns:
            RiskPod enum value
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT asset_class, security_type
            FROM securities
            WHERE id = %s
        """, (str(security_id),))

        result = cur.fetchone()
        if not result:
            return RiskPod.OTHER

        return get_riskpod(result['asset_class'], result.get('security_type'))

    def get_all_pod_summaries(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[RiskPod, RiskPodSummary]:
        """
        Get summary statistics for all RiskPods.

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            Dictionary mapping RiskPod to its summary
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Build query with optional fund filter
        fund_filter = ""
        params = [str(tenant_id)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        # Get all positions with security asset class
        cur.execute(f"""
            SELECT
                p.id as position_id,
                p.security_id,
                p.quantity,
                p.direction,
                p.market_value,
                p.market_value_base,
                s.asset_class,
                s.security_type,
                s.name as security_name,
                b.pm_id
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s
              {fund_filter}
        """, params)

        positions = cur.fetchall()

        # Initialize summaries for all pods
        summaries: Dict[RiskPod, RiskPodSummary] = {
            pod: RiskPodSummary(pod=pod) for pod in RiskPod
        }

        # Track unique items per pod
        pod_securities: Dict[RiskPod, Set[str]] = {pod: set() for pod in RiskPod}
        pod_pms: Dict[RiskPod, Set[str]] = {pod: set() for pod in RiskPod}
        pod_security_values: Dict[RiskPod, Dict[str, Dict[str, Any]]] = {
            pod: {} for pod in RiskPod
        }

        for p in positions:
            pod = get_riskpod(p['asset_class'], p.get('security_type'))
            summary = summaries[pod]

            value = Decimal(str(p['market_value_base'] or p['market_value'] or 0))
            quantity = Decimal(str(p['quantity'] or 0))

            summary.position_count += 1
            pod_securities[pod].add(str(p['security_id']))

            if p['pm_id']:
                pod_pms[pod].add(str(p['pm_id']))

            # Track by direction
            if p['direction'] == 'long':
                summary.gross_long += abs(value)
            else:
                summary.gross_short += abs(value)

            # Track security values for top securities
            sec_id = str(p['security_id'])
            if sec_id not in pod_security_values[pod]:
                pod_security_values[pod][sec_id] = {
                    'security_id': sec_id,
                    'security_name': p['security_name'],
                    'gross_value': Decimal("0"),
                }
            pod_security_values[pod][sec_id]['gross_value'] += abs(value)

        # Finalize summaries
        for pod in RiskPod:
            summary = summaries[pod]
            summary.security_count = len(pod_securities[pod])
            summary.pm_count = len(pod_pms[pod])
            summary.gross_total = summary.gross_long + summary.gross_short
            summary.net_exposure = summary.gross_long - summary.gross_short

            # Get top 5 securities by gross value
            securities_list = list(pod_security_values[pod].values())
            securities_list.sort(key=lambda x: x['gross_value'], reverse=True)
            summary.top_securities = [
                {
                    'security_id': s['security_id'],
                    'security_name': s['security_name'],
                    'gross_value': float(s['gross_value']),
                }
                for s in securities_list[:5]
            ]

        return summaries

    def get_pod_detail(
        self,
        tenant_id: UUID,
        pod: RiskPod,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown for a specific RiskPod.

        Args:
            tenant_id: Tenant ID
            pod: RiskPod to get details for
            fund_id: Optional fund filter

        Returns:
            Detailed breakdown including positions, PMs, and metrics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get asset classes for this pod
        pod_asset_classes = [
            ac for ac, p in ASSET_CLASS_TO_POD.items() if p == pod
        ]

        if not pod_asset_classes:
            return {
                "pod": pod.value,
                "positions": [],
                "pm_breakdown": [],
                "security_breakdown": [],
                "available_metrics": POD_RISK_METRICS.get(pod, []),
            }

        # Build query
        fund_filter = ""
        params = [str(tenant_id), tuple(pod_asset_classes)]

        if fund_id:
            fund_filter = "AND b.fund_id = %s"
            params.append(str(fund_id))

        cur.execute(f"""
            SELECT
                p.id as position_id,
                p.security_id,
                p.book_id,
                p.quantity,
                p.direction,
                p.market_value,
                p.market_value_base,
                s.name as security_name,
                s.ticker,
                s.asset_class,
                b.name as book_name,
                b.pm_id,
                u.name as pm_name
            FROM positions p
            JOIN books b ON p.book_id = b.id
            JOIN securities s ON p.security_id = s.id
            LEFT JOIN users u ON b.pm_id = u.id
            WHERE p.tenant_id = %s
              AND s.asset_class IN %s
              {fund_filter}
            ORDER BY ABS(COALESCE(p.market_value_base, p.market_value, 0)) DESC
        """, params)

        positions = cur.fetchall()

        # Build position list
        position_list = []
        pm_totals: Dict[str, Dict[str, Any]] = {}
        security_totals: Dict[str, Dict[str, Any]] = {}

        for p in positions:
            value = float(p['market_value_base'] or p['market_value'] or 0)

            position_list.append({
                'position_id': str(p['position_id']),
                'security_id': str(p['security_id']),
                'security_name': p['security_name'],
                'ticker': p['ticker'],
                'book_id': str(p['book_id']),
                'book_name': p['book_name'],
                'pm_id': str(p['pm_id']) if p['pm_id'] else None,
                'pm_name': p['pm_name'],
                'quantity': float(p['quantity']),
                'direction': p['direction'],
                'market_value': value,
            })

            # Aggregate by PM
            pm_key = str(p['pm_id']) if p['pm_id'] else 'unassigned'
            if pm_key not in pm_totals:
                pm_totals[pm_key] = {
                    'pm_id': pm_key,
                    'pm_name': p['pm_name'] or 'Unassigned',
                    'gross_long': 0.0,
                    'gross_short': 0.0,
                    'position_count': 0,
                }
            pm_totals[pm_key]['position_count'] += 1
            if p['direction'] == 'long':
                pm_totals[pm_key]['gross_long'] += abs(value)
            else:
                pm_totals[pm_key]['gross_short'] += abs(value)

            # Aggregate by security
            sec_key = str(p['security_id'])
            if sec_key not in security_totals:
                security_totals[sec_key] = {
                    'security_id': sec_key,
                    'security_name': p['security_name'],
                    'ticker': p['ticker'],
                    'gross_long': 0.0,
                    'gross_short': 0.0,
                    'position_count': 0,
                }
            security_totals[sec_key]['position_count'] += 1
            if p['direction'] == 'long':
                security_totals[sec_key]['gross_long'] += abs(value)
            else:
                security_totals[sec_key]['gross_short'] += abs(value)

        # Sort PM breakdown by total exposure
        pm_breakdown = list(pm_totals.values())
        pm_breakdown.sort(
            key=lambda x: x['gross_long'] + x['gross_short'],
            reverse=True
        )
        for pm in pm_breakdown:
            pm['gross_total'] = pm['gross_long'] + pm['gross_short']
            pm['net_exposure'] = pm['gross_long'] - pm['gross_short']

        # Sort security breakdown by total exposure
        security_breakdown = list(security_totals.values())
        security_breakdown.sort(
            key=lambda x: x['gross_long'] + x['gross_short'],
            reverse=True
        )
        for sec in security_breakdown:
            sec['gross_total'] = sec['gross_long'] + sec['gross_short']
            sec['net_exposure'] = sec['gross_long'] - sec['gross_short']

        return {
            "pod": pod.value,
            "pod_display_name": pod.value.upper(),
            "position_count": len(position_list),
            "pm_count": len(pm_breakdown),
            "security_count": len(security_breakdown),
            "positions": position_list[:100],  # Limit to top 100
            "pm_breakdown": pm_breakdown,
            "security_breakdown": security_breakdown[:50],  # Top 50
            "available_metrics": POD_RISK_METRICS.get(pod, []),
        }

    def get_pod_var_breakdown(
        self,
        tenant_id: UUID,
        fund_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get VaR breakdown by RiskPod.

        Note: This is a simplified calculation. In production, would use
        historical returns and proper VaR methodology.

        Args:
            tenant_id: Tenant ID
            fund_id: Optional fund filter

        Returns:
            VaR breakdown by pod with simplified estimates
        """
        summaries = self.get_all_pod_summaries(tenant_id, fund_id)

        # Simplified VaR estimate: 2.5% of gross exposure (rough 95% VaR)
        # In production, use proper historical VaR calculation
        VAR_FACTOR = Decimal("0.025")

        pod_vars = {}
        for pod, summary in summaries.items():
            if summary.gross_total > 0:
                var_estimate = summary.gross_total * VAR_FACTOR
                pod_vars[pod.value] = {
                    'pod': pod.value,
                    'gross_exposure': float(summary.gross_total),
                    'var_95_estimate': float(var_estimate),
                    'position_count': summary.position_count,
                }

        return {
            'pod_vars': pod_vars,
            'total_standalone_var': sum(v['var_95_estimate'] for v in pod_vars.values()),
            'note': 'Simplified VaR estimates. Production uses historical returns.',
        }

    # =========================================================================
    # Asset Class Based Methods (for CIO Dashboard)
    # =========================================================================

    def get_firm_risk_by_asset_class(
        self,
        tenant_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get firm-wide risk aggregated by asset class.
        Uses v_firm_risk_by_asset_class view.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of asset class risk summaries for the entire firm
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                asset_class,
                position_count,
                book_count,
                gross_exposure,
                net_exposure,
                total_delta,
                total_gamma,
                total_vega,
                total_theta,
                total_rho,
                total_dv01,
                total_cs01,
                total_convexity
            FROM v_firm_risk_by_asset_class
            WHERE tenant_id = %s
            ORDER BY gross_exposure DESC
        """, (str(tenant_id),))

        results = cur.fetchall()

        return [
            {
                'asset_class': r['asset_class'],
                'asset_class_display': self._format_asset_class(r['asset_class']),
                'position_count': r['position_count'],
                'book_count': r['book_count'],
                'gross_exposure': float(r['gross_exposure'] or 0),
                'net_exposure': float(r['net_exposure'] or 0),
                'delta': float(r['total_delta'] or 0),
                'gamma': float(r['total_gamma'] or 0),
                'vega': float(r['total_vega'] or 0),
                'theta': float(r['total_theta'] or 0),
                'rho': float(r['total_rho'] or 0),
                'dv01': float(r['total_dv01'] or 0),
                'cs01': float(r['total_cs01'] or 0),
                'convexity': float(r['total_convexity'] or 0),
                'primary_risk_metric': self._get_primary_metric(r['asset_class']),
                'primary_risk_value': self._get_primary_value(r),
            }
            for r in results
        ]

    def get_book_risk_by_asset_class(
        self,
        book_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get risk for a single book aggregated by asset class.
        Uses v_risk_by_asset_class view.

        Args:
            book_id: Book ID

        Returns:
            List of asset class risk summaries for the book
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                asset_class,
                position_count,
                book_name,
                book_type,
                gross_exposure,
                net_exposure,
                total_delta,
                total_gamma,
                total_vega,
                total_theta,
                total_rho,
                total_dv01,
                total_cs01,
                total_convexity
            FROM v_risk_by_asset_class
            WHERE book_id = %s
            ORDER BY gross_exposure DESC
        """, (str(book_id),))

        results = cur.fetchall()

        return [
            {
                'asset_class': r['asset_class'],
                'asset_class_display': self._format_asset_class(r['asset_class']),
                'book_name': r['book_name'],
                'book_type': r['book_type'],
                'position_count': r['position_count'],
                'gross_exposure': float(r['gross_exposure'] or 0),
                'net_exposure': float(r['net_exposure'] or 0),
                'delta': float(r['total_delta'] or 0),
                'gamma': float(r['total_gamma'] or 0),
                'vega': float(r['total_vega'] or 0),
                'theta': float(r['total_theta'] or 0),
                'rho': float(r['total_rho'] or 0),
                'dv01': float(r['total_dv01'] or 0),
                'cs01': float(r['total_cs01'] or 0),
                'convexity': float(r['total_convexity'] or 0),
                'primary_risk_metric': self._get_primary_metric(r['asset_class']),
                'primary_risk_value': self._get_primary_value(r),
            }
            for r in results
        ]

    def get_overlay_risk_by_asset_class(
        self,
        tenant_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get overlay book risk aggregated by asset class.
        Uses v_overlay_risk_by_asset_class view.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of asset class risk summaries for overlay book(s)
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                book_id,
                book_name,
                asset_class,
                position_count,
                gross_exposure,
                net_exposure,
                total_delta,
                total_gamma,
                total_vega,
                total_theta,
                total_rho,
                total_dv01,
                total_cs01,
                total_convexity
            FROM v_overlay_risk_by_asset_class
            WHERE tenant_id = %s
            ORDER BY gross_exposure DESC
        """, (str(tenant_id),))

        results = cur.fetchall()

        return [
            {
                'book_id': str(r['book_id']),
                'book_name': r['book_name'],
                'asset_class': r['asset_class'],
                'asset_class_display': self._format_asset_class(r['asset_class']),
                'position_count': r['position_count'],
                'gross_exposure': float(r['gross_exposure'] or 0),
                'net_exposure': float(r['net_exposure'] or 0),
                'delta': float(r['total_delta'] or 0),
                'gamma': float(r['total_gamma'] or 0),
                'vega': float(r['total_vega'] or 0),
                'theta': float(r['total_theta'] or 0),
                'rho': float(r['total_rho'] or 0),
                'dv01': float(r['total_dv01'] or 0),
                'cs01': float(r['total_cs01'] or 0),
                'convexity': float(r['total_convexity'] or 0),
                'primary_risk_metric': self._get_primary_metric(r['asset_class']),
                'primary_risk_value': self._get_primary_value(r),
            }
            for r in results
        ]

    def get_all_books(
        self,
        tenant_id: UUID,
        book_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all books for a tenant, optionally filtered by type.

        Args:
            tenant_id: Tenant ID
            book_type: Optional filter - 'trading' or 'overlay'

        Returns:
            List of book summaries
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        type_filter = ""
        params = [str(tenant_id)]

        if book_type:
            type_filter = "AND book_type = %s"
            params.append(book_type)

        cur.execute(f"""
            SELECT
                b.id,
                b.name,
                b.book_type,
                b.strategy,
                b.pm_id,
                u.name as pm_name,
                f.name as fund_name
            FROM books b
            LEFT JOIN users u ON b.pm_id = u.id
            LEFT JOIN funds f ON b.fund_id = f.id
            WHERE b.tenant_id = %s
              AND b.is_active = true
              {type_filter}
            ORDER BY b.name
        """, params)

        results = cur.fetchall()

        return [
            {
                'book_id': str(r['id']),
                'name': r['name'],
                'book_type': r['book_type'],
                'strategy': r['strategy'],
                'pm_id': str(r['pm_id']) if r['pm_id'] else None,
                'pm_name': r['pm_name'],
                'fund_name': r['fund_name'],
            }
            for r in results
        ]

    def get_overlay_books(
        self,
        tenant_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get overlay books for a tenant with their source book links.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of overlay book details with source books
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                b.id,
                b.name,
                b.strategy,
                b.pm_id,
                u.name as pm_name
            FROM books b
            LEFT JOIN users u ON b.pm_id = u.id
            WHERE b.tenant_id = %s
              AND b.book_type = 'overlay'
              AND b.is_active = true
        """, (str(tenant_id),))

        overlay_books = cur.fetchall()

        result = []
        for ob in overlay_books:
            # Get source books
            cur.execute("""
                SELECT
                    obs.source_book_id,
                    sb.name as source_book_name,
                    obs.hedge_weight,
                    obs.target_metric,
                    obs.is_active
                FROM overlay_book_sources obs
                JOIN books sb ON obs.source_book_id = sb.id
                WHERE obs.overlay_book_id = %s
                  AND obs.is_active = true
            """, (str(ob['id']),))

            sources = cur.fetchall()

            result.append({
                'book_id': str(ob['id']),
                'name': ob['name'],
                'strategy': ob['strategy'],
                'pm_id': str(ob['pm_id']) if ob['pm_id'] else None,
                'pm_name': ob['pm_name'],
                'source_books': [
                    {
                        'book_id': str(s['source_book_id']),
                        'name': s['source_book_name'],
                        'hedge_weight': float(s['hedge_weight']),
                        'target_metric': s['target_metric'],
                    }
                    for s in sources
                ],
                'source_count': len(sources),
            })

        return result

    def _format_asset_class(self, asset_class: str) -> str:
        """Format asset class for display."""
        display_names = {
            'equity': 'Equities',
            'fixed_income': 'Fixed Income',
            'option': 'Options',
            'future': 'Futures',
            'fx': 'FX',
            'swap': 'Swaps',
            'cds': 'Credit (CDS)',
            'commodity': 'Commodities',
            'crypto': 'Crypto',
            'fund': 'Funds',
            'other': 'Other',
        }
        return display_names.get(asset_class, asset_class.title() if asset_class else 'Unknown')

    def _get_primary_metric(self, asset_class: str) -> str:
        """Get the primary risk metric for an asset class."""
        primary_metrics = {
            'equity': 'delta',
            'option': 'delta',
            'fixed_income': 'dv01',
            'swap': 'dv01',
            'cds': 'cs01',
            'fx': 'delta',
            'future': 'delta',
        }
        return primary_metrics.get(asset_class, 'net_exposure')

    def _get_primary_value(self, row: Dict) -> float:
        """Get the primary risk value based on asset class."""
        asset_class = row.get('asset_class', '')
        if asset_class in ('equity', 'option', 'fx', 'future'):
            return float(row.get('total_delta') or 0)
        elif asset_class in ('fixed_income', 'swap'):
            return float(row.get('total_dv01') or 0)
        elif asset_class == 'cds':
            return float(row.get('total_cs01') or 0)
        else:
            return float(row.get('net_exposure') or 0)

    # =========================================================================
    # Riskboard Dashboard Methods (Multi-Book Aggregation)
    # =========================================================================

    def get_risk_by_asset_class_multi_book(
        self,
        book_ids: List[UUID],
    ) -> List[Dict[str, Any]]:
        """
        Get risk aggregated by asset class for multiple selected books.
        This is the core method for RiskPod cards in the dashboard.

        Args:
            book_ids: List of book IDs to aggregate

        Returns:
            List of asset class risk summaries aggregated across selected books
        """
        if not book_ids:
            return []

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Convert UUIDs to strings for query
        book_id_strs = [str(bid) for bid in book_ids]

        cur.execute("""
            SELECT
                s.asset_class,
                COUNT(*) as position_count,
                COUNT(DISTINCT p.book_id) as book_count,
                SUM(ABS(p.market_value)) as gross_exposure,
                SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,
                SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE 0 END) as long_exposure,
                SUM(CASE WHEN p.direction = 'short' THEN ABS(p.market_value) ELSE 0 END) as short_exposure,
                SUM(COALESCE(p.delta, 0)) as total_delta,
                SUM(COALESCE(p.gamma, 0)) as total_gamma,
                SUM(COALESCE(p.vega, 0)) as total_vega,
                SUM(COALESCE(p.theta, 0)) as total_theta,
                SUM(COALESCE(p.rho, 0)) as total_rho,
                SUM(COALESCE(p.dv01, 0)) as total_dv01,
                SUM(COALESCE(p.cs01, 0)) as total_cs01,
                SUM(COALESCE(p.convexity, 0)) as total_convexity
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = ANY(%s::uuid[])
              AND p.quantity != 0
            GROUP BY s.asset_class
            ORDER BY gross_exposure DESC
        """, (book_id_strs,))

        results = cur.fetchall()

        return [
            {
                'asset_class': r['asset_class'],
                'asset_class_display': self._format_asset_class(r['asset_class']),
                'position_count': r['position_count'],
                'book_count': r['book_count'],
                'gross_exposure': float(r['gross_exposure'] or 0),
                'net_exposure': float(r['net_exposure'] or 0),
                'long_exposure': float(r['long_exposure'] or 0),
                'short_exposure': float(r['short_exposure'] or 0),
                'delta': float(r['total_delta'] or 0),
                'gamma': float(r['total_gamma'] or 0),
                'vega': float(r['total_vega'] or 0),
                'theta': float(r['total_theta'] or 0),
                'rho': float(r['total_rho'] or 0),
                'dv01': float(r['total_dv01'] or 0),
                'cs01': float(r['total_cs01'] or 0),
                'convexity': float(r['total_convexity'] or 0),
                'primary_risk_metric': self._get_primary_metric(r['asset_class']),
                'primary_risk_value': self._get_primary_value(r),
            }
            for r in results
        ]

    def get_risk_summary(
        self,
        tenant_id: UUID,
        book_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Get risk summary for the Riskboard top bar.
        Uses v_risk_summary view or calculates from selected books.

        Args:
            tenant_id: Tenant ID
            book_ids: Optional list of book IDs to aggregate (None = all books)

        Returns:
            Summary with NAV, gross, net exposures, position counts
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if book_ids:
            # Calculate from selected books
            book_id_strs = [str(bid) for bid in book_ids]

            cur.execute("""
                SELECT
                    SUM(CASE WHEN direction = 'long' THEN market_value ELSE -market_value END) as nav,
                    SUM(ABS(market_value)) as gross_exposure,
                    SUM(CASE WHEN direction = 'long' THEN market_value ELSE -market_value END) as net_exposure,
                    SUM(CASE WHEN direction = 'long' THEN market_value ELSE 0 END) as long_exposure,
                    SUM(CASE WHEN direction = 'short' THEN ABS(market_value) ELSE 0 END) as short_exposure,
                    COUNT(*) as position_count,
                    COUNT(DISTINCT security_id) as security_count,
                    COUNT(DISTINCT book_id) as book_count,
                    SUM(COALESCE(delta, 0)) as total_delta,
                    SUM(COALESCE(dv01, 0)) as total_dv01,
                    SUM(COALESCE(cs01, 0)) as total_cs01
                FROM positions
                WHERE book_id = ANY(%s::uuid[])
                  AND quantity != 0
            """, (book_id_strs,))
        else:
            # Use the view for all tenant positions
            cur.execute("""
                SELECT
                    nav,
                    gross_exposure,
                    net_exposure,
                    long_exposure,
                    short_exposure,
                    position_count,
                    security_count,
                    book_count,
                    total_delta,
                    total_dv01,
                    total_cs01
                FROM v_risk_summary
                WHERE tenant_id = %s
            """, (str(tenant_id),))

        result = cur.fetchone()

        if not result or result['gross_exposure'] is None:
            return {
                'nav': 0.0,
                'gross_exposure': 0.0,
                'net_exposure': 0.0,
                'long_exposure': 0.0,
                'short_exposure': 0.0,
                'position_count': 0,
                'security_count': 0,
                'book_count': 0,
                'total_delta': 0.0,
                'total_dv01': 0.0,
                'total_cs01': 0.0,
                'last_priced': None,
            }

        # Get last pricing run timestamp
        cur.execute("""
            SELECT completed_at
            FROM pricing_runs
            WHERE tenant_id = %s
              AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
        """, (str(tenant_id),))

        pricing_result = cur.fetchone()
        last_priced = pricing_result['completed_at'].isoformat() if pricing_result and pricing_result['completed_at'] else None

        return {
            'nav': float(result['nav'] or 0),
            'gross_exposure': float(result['gross_exposure'] or 0),
            'net_exposure': float(result['net_exposure'] or 0),
            'long_exposure': float(result['long_exposure'] or 0),
            'short_exposure': float(result['short_exposure'] or 0),
            'position_count': result['position_count'] or 0,
            'security_count': result['security_count'] or 0,
            'book_count': result['book_count'] or 0,
            'total_delta': float(result['total_delta'] or 0),
            'total_dv01': float(result['total_dv01'] or 0),
            'total_cs01': float(result['total_cs01'] or 0),
            'last_priced': last_priced,
        }

    def get_position_overlap(
        self,
        tenant_id: UUID,
        book_ids: Optional[List[UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get position overlaps for correlation analysis.
        Uses v_position_overlap view.

        Args:
            tenant_id: Tenant ID
            book_ids: Optional filter to only show overlaps involving these books

        Returns:
            List of securities held by multiple books with netting opportunities
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if book_ids:
            # Filter overlaps to only those involving selected books
            book_id_strs = [str(bid) for bid in book_ids]

            cur.execute("""
                SELECT
                    security_id,
                    ticker,
                    security_name,
                    asset_class,
                    book_count,
                    books,
                    book_ids,
                    net_quantity,
                    gross_exposure,
                    net_exposure,
                    netting_opportunity,
                    net_delta,
                    net_dv01,
                    net_cs01
                FROM v_position_overlap
                WHERE tenant_id = %s
                  AND book_ids && %s::uuid[]
                ORDER BY netting_opportunity DESC
                LIMIT 50
            """, (str(tenant_id), book_id_strs))
        else:
            # All overlaps for tenant
            cur.execute("""
                SELECT
                    security_id,
                    ticker,
                    security_name,
                    asset_class,
                    book_count,
                    books,
                    book_ids,
                    net_quantity,
                    gross_exposure,
                    net_exposure,
                    netting_opportunity,
                    net_delta,
                    net_dv01,
                    net_cs01
                FROM v_position_overlap
                WHERE tenant_id = %s
                ORDER BY netting_opportunity DESC
                LIMIT 50
            """, (str(tenant_id),))

        results = cur.fetchall()

        return [
            {
                'security_id': str(r['security_id']),
                'ticker': r['ticker'],
                'security_name': r['security_name'],
                'asset_class': r['asset_class'],
                'book_count': r['book_count'],
                'books': r['books'],
                'book_ids': [str(bid) for bid in r['book_ids']] if r['book_ids'] else [],
                'net_quantity': float(r['net_quantity'] or 0),
                'gross_exposure': float(r['gross_exposure'] or 0),
                'net_exposure': float(r['net_exposure'] or 0),
                'netting_opportunity': float(r['netting_opportunity'] or 0),
                'net_delta': float(r['net_delta'] or 0),
                'net_dv01': float(r['net_dv01'] or 0),
                'net_cs01': float(r['net_cs01'] or 0),
            }
            for r in results
        ]

    def get_concentration_by_sector(
        self,
        tenant_id: UUID,
        book_ids: Optional[List[UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get sector concentration for correlation panel.
        Uses v_concentration_by_sector view or calculates from selected books.

        Args:
            tenant_id: Tenant ID
            book_ids: Optional list of book IDs to analyze

        Returns:
            List of sectors with exposure percentages and warning flags
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if book_ids:
            # Calculate from selected books
            book_id_strs = [str(bid) for bid in book_ids]

            # Get total for percentage calculation
            cur.execute("""
                SELECT SUM(ABS(market_value)) as total
                FROM positions
                WHERE book_id = ANY(%s::uuid[]) AND quantity != 0
            """, (book_id_strs,))

            total_result = cur.fetchone()
            total = float(total_result['total'] or 0) if total_result else 0

            if total == 0:
                return []

            cur.execute("""
                SELECT
                    s.sector,
                    COUNT(DISTINCT p.security_id) as security_count,
                    COUNT(DISTINCT p.book_id) as book_count,
                    SUM(ABS(p.market_value)) as gross_exposure,
                    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure
                FROM positions p
                JOIN securities s ON p.security_id = s.id
                WHERE p.book_id = ANY(%s::uuid[])
                  AND p.quantity != 0
                  AND s.sector IS NOT NULL
                GROUP BY s.sector
                ORDER BY gross_exposure DESC
            """, (book_id_strs,))

            results = cur.fetchall()

            return [
                {
                    'sector': r['sector'],
                    'security_count': r['security_count'],
                    'book_count': r['book_count'],
                    'gross_exposure': float(r['gross_exposure'] or 0),
                    'net_exposure': float(r['net_exposure'] or 0),
                    'percentage': round((float(r['gross_exposure'] or 0) / total) * 100, 2),
                    'is_warning': (float(r['gross_exposure'] or 0) / total) > 0.40,
                }
                for r in results
            ]
        else:
            # Use the view
            cur.execute("""
                SELECT
                    sector,
                    security_count,
                    book_count,
                    gross_exposure,
                    net_exposure,
                    percentage,
                    is_warning
                FROM v_concentration_by_sector
                WHERE tenant_id = %s
                ORDER BY gross_exposure DESC
            """, (str(tenant_id),))

            results = cur.fetchall()

            return [
                {
                    'sector': r['sector'],
                    'security_count': r['security_count'],
                    'book_count': r['book_count'],
                    'gross_exposure': float(r['gross_exposure'] or 0),
                    'net_exposure': float(r['net_exposure'] or 0),
                    'percentage': float(r['percentage'] or 0),
                    'is_warning': r['is_warning'],
                }
                for r in results
            ]

    def get_concentration_by_security(
        self,
        tenant_id: UUID,
        book_ids: Optional[List[UUID]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get single-name concentration for correlation panel.
        Uses v_concentration_by_security view or calculates from selected books.

        Args:
            tenant_id: Tenant ID
            book_ids: Optional list of book IDs to analyze
            limit: Max number of results

        Returns:
            List of securities with exposure percentages and warning flags
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if book_ids:
            # Calculate from selected books
            book_id_strs = [str(bid) for bid in book_ids]

            # Get total for percentage calculation
            cur.execute("""
                SELECT SUM(ABS(market_value)) as total
                FROM positions
                WHERE book_id = ANY(%s::uuid[]) AND quantity != 0
            """, (book_id_strs,))

            total_result = cur.fetchone()
            total = float(total_result['total'] or 0) if total_result else 0

            if total == 0:
                return []

            cur.execute("""
                SELECT
                    p.security_id,
                    COALESCE(si.identifier_value, s.figi) as ticker,
                    s.name as security_name,
                    s.sector,
                    s.asset_class,
                    COUNT(DISTINCT p.book_id) as book_count,
                    SUM(ABS(p.market_value)) as gross_exposure,
                    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure
                FROM positions p
                JOIN securities s ON p.security_id = s.id
                LEFT JOIN security_identifiers si ON p.security_id = si.security_id
                    AND si.identifier_type = 'ticker'
                WHERE p.book_id = ANY(%s::uuid[])
                  AND p.quantity != 0
                GROUP BY p.security_id, si.identifier_value, s.figi, s.name, s.sector, s.asset_class
                ORDER BY gross_exposure DESC
                LIMIT %s
            """, (book_id_strs, limit))

            results = cur.fetchall()

            return [
                {
                    'security_id': str(r['security_id']),
                    'ticker': r['ticker'],
                    'security_name': r['security_name'],
                    'sector': r['sector'],
                    'asset_class': r['asset_class'],
                    'book_count': r['book_count'],
                    'gross_exposure': float(r['gross_exposure'] or 0),
                    'net_exposure': float(r['net_exposure'] or 0),
                    'percentage': round((float(r['gross_exposure'] or 0) / total) * 100, 2),
                    'is_warning': (float(r['gross_exposure'] or 0) / total) > 0.10,
                }
                for r in results
            ]
        else:
            # Use the view
            cur.execute("""
                SELECT
                    security_id,
                    ticker,
                    security_name,
                    sector,
                    asset_class,
                    book_count,
                    gross_exposure,
                    net_exposure,
                    percentage,
                    is_warning
                FROM v_concentration_by_security
                WHERE tenant_id = %s
                ORDER BY gross_exposure DESC
                LIMIT %s
            """, (str(tenant_id), limit))

            results = cur.fetchall()

            return [
                {
                    'security_id': str(r['security_id']),
                    'ticker': r['ticker'],
                    'security_name': r['security_name'],
                    'sector': r['sector'],
                    'asset_class': r['asset_class'],
                    'book_count': r['book_count'],
                    'gross_exposure': float(r['gross_exposure'] or 0),
                    'net_exposure': float(r['net_exposure'] or 0),
                    'percentage': float(r['percentage'] or 0),
                    'is_warning': r['is_warning'],
                }
                for r in results
            ]

    def get_positions_by_asset_class(
        self,
        book_ids: List[UUID],
        asset_class: str,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get positions filtered by books and asset class.
        Used for the Trades drill-down page.

        Args:
            book_ids: List of book IDs
            asset_class: Asset class filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated list of positions with valuation info
        """
        if not book_ids:
            return {'positions': [], 'total': 0, 'page': page, 'page_size': page_size}

        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        book_id_strs = [str(bid) for bid in book_ids]
        offset = (page - 1) * page_size

        # Get total count
        cur.execute("""
            SELECT COUNT(*)
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = ANY(%s::uuid[])
              AND p.quantity != 0
              AND s.asset_class = %s
        """, (book_id_strs, asset_class))

        total = cur.fetchone()['count']

        # Get positions with details
        cur.execute("""
            SELECT
                p.id as position_id,
                p.book_id,
                b.name as book_name,
                p.security_id,
                COALESCE(si.identifier_value, s.figi) as ticker,
                s.name as security_name,
                s.asset_class,
                p.direction,
                p.quantity,
                p.cost_basis,
                p.price as current_price,
                p.market_value,
                p.unrealized_pnl,
                p.delta,
                p.gamma,
                p.vega,
                p.theta,
                p.dv01,
                p.cs01,
                COALESCE(p.price_source::text, sp.price_source) as price_source,
                COALESCE(p.price_as_of, sp.price_date) as price_date,
                sp.model_id IS NOT NULL as has_model_details
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            JOIN books b ON p.book_id = b.id
            LEFT JOIN security_identifiers si ON p.security_id = si.security_id
                AND si.identifier_type = 'ticker'
            LEFT JOIN LATERAL (
                SELECT source::text as price_source, price_date, model_id
                FROM security_prices
                WHERE security_id = p.security_id
                ORDER BY price_date DESC
                LIMIT 1
            ) sp ON true
            WHERE p.book_id = ANY(%s::uuid[])
              AND p.quantity != 0
              AND s.asset_class = %s
            ORDER BY ABS(p.market_value) DESC
            LIMIT %s OFFSET %s
        """, (book_id_strs, asset_class, page_size, offset))

        results = cur.fetchall()

        positions = [
            {
                'position_id': str(r['position_id']),
                'book_id': str(r['book_id']),
                'book_name': r['book_name'],
                'security_id': str(r['security_id']),
                'ticker': r['ticker'],
                'security_name': r['security_name'],
                'asset_class': r['asset_class'],
                'direction': r['direction'],
                'quantity': float(r['quantity'] or 0),
                'cost_basis': float(r['cost_basis'] or 0),
                'current_price': float(r['current_price'] or 0),
                'market_value': float(r['market_value'] or 0),
                'unrealized_pnl': float(r['unrealized_pnl'] or 0),
                'delta': float(r['delta'] or 0),
                'gamma': float(r['gamma'] or 0),
                'vega': float(r['vega'] or 0),
                'theta': float(r['theta'] or 0),
                'dv01': float(r['dv01'] or 0),
                'cs01': float(r['cs01'] or 0),
                'price_source': r['price_source'] or 'unknown',
                'price_date': r['price_date'].isoformat() if r['price_date'] else None,
                'has_model_details': r['has_model_details'] or False,
            }
            for r in results
        ]

        return {
            'positions': positions,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }
