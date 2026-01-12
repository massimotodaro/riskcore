# RISKCORE Risk Engine
# VaR, CVaR, and risk metric calculations
# Uses numpy/scipy for calculations (riskfolio-lib has Windows build issues)

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
import logging

import numpy as np
from scipy import stats
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class VaRMethod(str, Enum):
    """VaR calculation methods."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class RiskMetricType(str, Enum):
    """Risk metric types matching database enum."""
    VAR_95 = "var_95"
    VAR_99 = "var_99"
    VAR_95_1D = "var_95_1d"
    VAR_99_1D = "var_99_1d"
    VAR_95_10D = "var_95_10d"
    VAR_99_10D = "var_99_10d"
    CVAR_95 = "cvar_95"
    CVAR_99 = "cvar_99"
    GROSS_EXPOSURE = "gross_exposure"
    NET_EXPOSURE = "net_exposure"
    LONG_EXPOSURE = "long_exposure"
    SHORT_EXPOSURE = "short_exposure"
    NET_DELTA = "net_delta"
    NET_GAMMA = "net_gamma"
    NET_VEGA = "net_vega"
    NET_THETA = "net_theta"
    NET_RHO = "net_rho"
    TOTAL_DV01 = "total_dv01"
    TOTAL_CS01 = "total_cs01"
    TOTAL_CONVEXITY = "total_convexity"
    TOP_10_CONCENTRATION = "top_10_concentration"
    SECTOR_CONCENTRATION = "sector_concentration"
    SINGLE_NAME_MAX = "single_name_max"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    PORTFOLIO_BETA = "portfolio_beta"
    CUSTOM = "custom"


class MetricLevel(str, Enum):
    """Metric aggregation levels."""
    POSITION = "position"
    BOOK = "book"
    FUND = "fund"
    TENANT = "tenant"


class RiskEngine:
    """
    Risk calculation engine for RISKCORE.

    Provides:
    - VaR (Value at Risk) at 95% and 99% confidence
    - CVaR (Conditional VaR / Expected Shortfall)
    - Multiple calculation methods (historical, parametric, Monte Carlo)
    - Scaling for different time horizons (1-day, 10-day)

    Uses numpy/scipy for calculations.
    All data stays on-premises - no cloud storage.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    # =========================================================================
    # VaR Calculations
    # =========================================================================

    def calculate_historical_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
    ) -> float:
        """
        Calculate Historical VaR.

        Historical VaR uses actual historical returns to estimate risk.
        It's the percentile of historical returns at the confidence level.

        Args:
            returns: Array of historical returns (daily)
            confidence_level: Confidence level (0.95 or 0.99)
            horizon_days: Time horizon in days (1 or 10)

        Returns:
            VaR as a positive number (loss)
        """
        if len(returns) == 0:
            return 0.0

        # VaR is the negative of the percentile (since losses are negative returns)
        var_1d = -np.percentile(returns, (1 - confidence_level) * 100)

        # Scale for time horizon using square root of time
        var = var_1d * np.sqrt(horizon_days)

        return float(var)

    def calculate_parametric_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
    ) -> float:
        """
        Calculate Parametric (Variance-Covariance) VaR.

        Assumes returns are normally distributed.
        VaR = μ - σ * z_α

        Args:
            returns: Array of historical returns (daily)
            confidence_level: Confidence level (0.95 or 0.99)
            horizon_days: Time horizon in days (1 or 10)

        Returns:
            VaR as a positive number (loss)
        """
        if len(returns) == 0:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)  # Sample std dev

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR (negative because we want loss as positive)
        var_1d = -(mean + z_score * std)

        # Scale for time horizon
        var = var_1d * np.sqrt(horizon_days)

        return float(max(0, var))  # VaR should be positive

    def calculate_monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
        n_simulations: int = 10000,
    ) -> float:
        """
        Calculate Monte Carlo VaR.

        Simulates future returns based on historical distribution.

        Args:
            returns: Array of historical returns (daily)
            confidence_level: Confidence level (0.95 or 0.99)
            horizon_days: Time horizon in days (1 or 10)
            n_simulations: Number of Monte Carlo simulations

        Returns:
            VaR as a positive number (loss)
        """
        if len(returns) == 0:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        # Generate random returns
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(mean, std, (n_simulations, horizon_days))

        # Sum returns over horizon
        portfolio_returns = np.sum(simulated_returns, axis=1)

        # VaR is the negative of the percentile
        var = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)

        return float(max(0, var))

    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> float:
        """
        Calculate VaR using specified method.

        Args:
            returns: Array of historical returns
            confidence_level: 0.95 or 0.99
            horizon_days: 1 or 10
            method: Calculation method

        Returns:
            VaR as a positive number
        """
        if method == VaRMethod.HISTORICAL:
            return self.calculate_historical_var(returns, confidence_level, horizon_days)
        elif method == VaRMethod.PARAMETRIC:
            return self.calculate_parametric_var(returns, confidence_level, horizon_days)
        elif method == VaRMethod.MONTE_CARLO:
            return self.calculate_monte_carlo_var(returns, confidence_level, horizon_days)
        else:
            raise ValueError(f"Unknown VaR method: {method}")

    # =========================================================================
    # CVaR (Expected Shortfall) Calculations
    # =========================================================================

    def calculate_cvar(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
    ) -> float:
        """
        Calculate CVaR (Conditional VaR / Expected Shortfall).

        CVaR is the expected loss given that the loss exceeds VaR.
        It's the average of all returns below the VaR threshold.

        Args:
            returns: Array of historical returns (daily)
            confidence_level: Confidence level (0.95 or 0.99)
            horizon_days: Time horizon in days

        Returns:
            CVaR as a positive number (expected loss in tail)
        """
        if len(returns) == 0:
            return 0.0

        # Scale returns for horizon
        if horizon_days > 1:
            # Simple scaling (more sophisticated would use rolling windows)
            scaled_returns = returns * np.sqrt(horizon_days)
        else:
            scaled_returns = returns

        # Find the VaR threshold
        var_threshold = np.percentile(scaled_returns, (1 - confidence_level) * 100)

        # CVaR is the mean of returns below VaR threshold
        tail_returns = scaled_returns[scaled_returns <= var_threshold]

        if len(tail_returns) == 0:
            return self.calculate_historical_var(returns, confidence_level, horizon_days)

        cvar = -np.mean(tail_returns)

        return float(max(0, cvar))

    # =========================================================================
    # Portfolio-Level Risk Calculations
    # =========================================================================

    def calculate_book_var(
        self,
        book_id: UUID,
        tenant_id: UUID,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
        method: VaRMethod = VaRMethod.HISTORICAL,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Calculate VaR for a book.

        Uses position market values and historical price data to compute
        portfolio returns, then calculates VaR.

        Args:
            book_id: Book ID
            tenant_id: Tenant ID
            confidence_level: 0.95 or 0.99
            horizon_days: 1 or 10
            method: VaR calculation method
            lookback_days: Historical days for calculation

        Returns:
            Dict with VaR metrics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get positions with market values
        cur.execute("""
            SELECT
                p.id,
                p.security_id,
                p.quantity,
                p.market_value,
                p.direction,
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
                "var": 0.0,
                "cvar": 0.0,
                "confidence_level": confidence_level,
                "horizon_days": horizon_days,
                "method": method.value,
                "position_count": 0,
                "total_market_value": 0.0,
                "error": "No positions with market values found",
            }

        # Calculate total market value
        total_mv = sum(float(p["market_value"]) for p in positions)

        # Get historical returns for each security
        security_ids = [str(p["security_id"]) for p in positions]
        weights = [float(p["market_value"]) / total_mv for p in positions]

        # Get historical prices
        cur.execute("""
            SELECT
                security_id,
                price_date,
                close_price
            FROM security_prices
            WHERE security_id = ANY(%s)
              AND price_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY security_id, price_date
        """, (security_ids, lookback_days))

        price_data = cur.fetchall()

        # Build returns matrix
        # For MVP, use simple approach: if no price data, use synthetic returns
        if not price_data:
            logger.warning(f"No historical prices for book {book_id}, using synthetic returns")
            # Generate synthetic returns based on typical equity volatility (~20% annual)
            daily_vol = 0.20 / np.sqrt(252)
            synthetic_returns = np.random.normal(0, daily_vol, lookback_days)

            var = self.calculate_var(synthetic_returns, confidence_level, horizon_days, method)
            cvar = self.calculate_cvar(synthetic_returns, confidence_level, horizon_days)

            return {
                "book_id": str(book_id),
                "var": var * total_mv,
                "var_pct": var * 100,
                "cvar": cvar * total_mv,
                "cvar_pct": cvar * 100,
                "confidence_level": confidence_level,
                "horizon_days": horizon_days,
                "method": method.value,
                "position_count": len(positions),
                "total_market_value": total_mv,
                "note": "Using synthetic returns (no historical price data)",
            }

        # Process actual price data into returns
        returns_by_security = {}
        for row in price_data:
            sec_id = str(row["security_id"])
            if sec_id not in returns_by_security:
                returns_by_security[sec_id] = []
            returns_by_security[sec_id].append(float(row["close_price"]))

        # Calculate returns for each security
        security_returns = {}
        for sec_id, prices in returns_by_security.items():
            if len(prices) > 1:
                prices_arr = np.array(prices)
                returns = np.diff(prices_arr) / prices_arr[:-1]
                security_returns[sec_id] = returns

        # Calculate weighted portfolio returns
        if not security_returns:
            logger.warning(f"Insufficient price data for book {book_id}")
            return {
                "book_id": str(book_id),
                "var": 0.0,
                "cvar": 0.0,
                "confidence_level": confidence_level,
                "horizon_days": horizon_days,
                "method": method.value,
                "position_count": len(positions),
                "total_market_value": total_mv,
                "error": "Insufficient price data for return calculation",
            }

        # Find common length for returns
        min_len = min(len(r) for r in security_returns.values())

        # Calculate weighted returns
        portfolio_returns = np.zeros(min_len)
        for i, p in enumerate(positions):
            sec_id = str(p["security_id"])
            if sec_id in security_returns:
                sec_returns = security_returns[sec_id][-min_len:]
                portfolio_returns += weights[i] * np.array(sec_returns)

        # Calculate VaR and CVaR
        var = self.calculate_var(portfolio_returns, confidence_level, horizon_days, method)
        cvar = self.calculate_cvar(portfolio_returns, confidence_level, horizon_days)

        return {
            "book_id": str(book_id),
            "var": var * total_mv,
            "var_pct": var * 100,
            "cvar": cvar * total_mv,
            "cvar_pct": cvar * 100,
            "confidence_level": confidence_level,
            "horizon_days": horizon_days,
            "method": method.value,
            "position_count": len(positions),
            "total_market_value": total_mv,
            "lookback_days": min_len,
        }

    # =========================================================================
    # Risk Metric Persistence
    # =========================================================================

    def save_risk_metric(
        self,
        tenant_id: UUID,
        metric_type: RiskMetricType,
        value: float,
        level: MetricLevel = MetricLevel.BOOK,
        book_id: Optional[UUID] = None,
        fund_id: Optional[UUID] = None,
        position_id: Optional[UUID] = None,
        unit: Optional[str] = None,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None,
        calculation_method: Optional[str] = None,
        calculation_params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Save a risk metric to the database.

        Args:
            tenant_id: Tenant ID
            metric_type: Type of risk metric
            value: Metric value
            level: Aggregation level
            book_id: Optional book ID
            fund_id: Optional fund ID
            position_id: Optional position ID
            unit: Unit of measurement (%, $, bps)
            dimension: Optional breakdown dimension
            dimension_value: Optional dimension value
            calculation_method: Method used (historical, parametric, etc.)
            calculation_params: Parameters used in calculation

        Returns:
            Created metric record
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        import json
        params_json = json.dumps(calculation_params) if calculation_params else None

        cur.execute("""
            INSERT INTO risk_metrics (
                tenant_id, level, book_id, fund_id, position_id,
                metric_type, value, unit, dimension, dimension_value,
                calculation_method, calculation_params, as_of_timestamp
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, NOW()
            )
            RETURNING *
        """, (
            str(tenant_id), level.value,
            str(book_id) if book_id else None,
            str(fund_id) if fund_id else None,
            str(position_id) if position_id else None,
            metric_type.value, value, unit, dimension, dimension_value,
            calculation_method, params_json,
        ))

        result = cur.fetchone()
        self.conn.commit()

        return dict(result)

    def get_latest_risk_metrics(
        self,
        tenant_id: UUID,
        book_id: Optional[UUID] = None,
        metric_types: Optional[List[RiskMetricType]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the latest risk metrics for a book or tenant.

        Args:
            tenant_id: Tenant ID
            book_id: Optional book ID (if None, gets tenant-level metrics)
            metric_types: Optional list of metric types to filter

        Returns:
            List of latest metrics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        conditions = ["tenant_id = %s"]
        params = [str(tenant_id)]

        if book_id:
            conditions.append("book_id = %s")
            params.append(str(book_id))

        if metric_types:
            placeholders = ", ".join(["%s"] * len(metric_types))
            conditions.append(f"metric_type IN ({placeholders})")
            params.extend([mt.value for mt in metric_types])

        where_clause = " AND ".join(conditions)

        # Get latest metric of each type
        cur.execute(f"""
            SELECT DISTINCT ON (metric_type) *
            FROM risk_metrics
            WHERE {where_clause}
            ORDER BY metric_type, as_of_timestamp DESC
        """, params)

        return [dict(row) for row in cur.fetchall()]

    def calculate_and_save_all_var_metrics(
        self,
        book_id: UUID,
        tenant_id: UUID,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> Dict[str, Any]:
        """
        Calculate all VaR/CVaR metrics for a book and save them.

        Calculates:
        - VaR 95% (1-day, 10-day)
        - VaR 99% (1-day, 10-day)
        - CVaR 95%, CVaR 99%

        Args:
            book_id: Book ID
            tenant_id: Tenant ID
            method: VaR calculation method

        Returns:
            Dict with all calculated metrics
        """
        results = {}

        # VaR 95% 1-day
        var_95_1d = self.calculate_book_var(
            book_id, tenant_id, 0.95, 1, method
        )
        self.save_risk_metric(
            tenant_id, RiskMetricType.VAR_95_1D, var_95_1d["var"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.95, "horizon": 1}
        )
        results["var_95_1d"] = var_95_1d

        # VaR 99% 1-day
        var_99_1d = self.calculate_book_var(
            book_id, tenant_id, 0.99, 1, method
        )
        self.save_risk_metric(
            tenant_id, RiskMetricType.VAR_99_1D, var_99_1d["var"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.99, "horizon": 1}
        )
        results["var_99_1d"] = var_99_1d

        # VaR 95% 10-day
        var_95_10d = self.calculate_book_var(
            book_id, tenant_id, 0.95, 10, method
        )
        self.save_risk_metric(
            tenant_id, RiskMetricType.VAR_95_10D, var_95_10d["var"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.95, "horizon": 10}
        )
        results["var_95_10d"] = var_95_10d

        # VaR 99% 10-day
        var_99_10d = self.calculate_book_var(
            book_id, tenant_id, 0.99, 10, method
        )
        self.save_risk_metric(
            tenant_id, RiskMetricType.VAR_99_10D, var_99_10d["var"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.99, "horizon": 10}
        )
        results["var_99_10d"] = var_99_10d

        # CVaR 95%
        self.save_risk_metric(
            tenant_id, RiskMetricType.CVAR_95, var_95_1d["cvar"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.95}
        )
        results["cvar_95"] = var_95_1d["cvar"]

        # CVaR 99%
        self.save_risk_metric(
            tenant_id, RiskMetricType.CVAR_99, var_99_1d["cvar"],
            MetricLevel.BOOK, book_id, unit="$",
            calculation_method=method.value,
            calculation_params={"confidence": 0.99}
        )
        results["cvar_99"] = var_99_1d["cvar"]

        return results
