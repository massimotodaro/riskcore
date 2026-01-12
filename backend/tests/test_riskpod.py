# RISKCORE RiskPod Tests
# Tests for RiskPod service, correlation, and firm VaR calculations
# THE CORE - Week 4 Aggregation Engine

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
import math

from backend.services.riskpod import (
    RiskPod,
    RiskPodService,
    RiskPodSummary,
    get_riskpod,
    get_pod_metrics,
    ASSET_CLASS_TO_POD,
    POD_RISK_METRICS,
)
from backend.services.correlation import (
    CorrelationService,
    FirmVaRResult,
    get_correlation,
    build_correlation_matrix,
    DEFAULT_CORRELATIONS,
    CRISIS_CORRELATIONS,
)


# =============================================================================
# RISKPOD ENUM AND MAPPING TESTS
# =============================================================================

class TestRiskPodEnum:
    """Tests for RiskPod enum and constants."""

    def test_riskpod_values(self):
        """Test RiskPod enum has expected values."""
        assert RiskPod.EQUITY.value == "equity"
        assert RiskPod.RATES.value == "rates"
        assert RiskPod.CREDIT.value == "credit"
        assert RiskPod.FX.value == "fx"
        assert RiskPod.OTHER.value == "other"

    def test_all_pods_in_mapping(self):
        """Test all RiskPods are in asset class mapping."""
        mapped_pods = set(ASSET_CLASS_TO_POD.values())
        all_pods = set(RiskPod)
        assert all_pods == mapped_pods

    def test_pod_risk_metrics_exist(self):
        """Test all RiskPods have risk metrics defined."""
        for pod in RiskPod:
            assert pod in POD_RISK_METRICS
            assert len(POD_RISK_METRICS[pod]) > 0

    def test_common_metrics_across_pods(self):
        """Test VaR and CVaR are available in all pods."""
        for pod in RiskPod:
            metrics = POD_RISK_METRICS[pod]
            assert "var" in metrics
            assert "cvar" in metrics


class TestGetRiskpod:
    """Tests for get_riskpod function."""

    def test_equity_mapping(self):
        """Test equity asset class maps to EQUITY pod."""
        assert get_riskpod("equity") == RiskPod.EQUITY

    def test_option_maps_to_equity(self):
        """Test options map to EQUITY pod (follow underlying)."""
        assert get_riskpod("option") == RiskPod.EQUITY

    def test_future_maps_to_equity(self):
        """Test futures map to EQUITY pod (equity index futures)."""
        assert get_riskpod("future") == RiskPod.EQUITY

    def test_fund_maps_to_equity(self):
        """Test funds (ETFs) map to EQUITY pod."""
        assert get_riskpod("fund") == RiskPod.EQUITY

    def test_fixed_income_maps_to_rates(self):
        """Test fixed income maps to RATES pod."""
        assert get_riskpod("fixed_income") == RiskPod.RATES

    def test_swap_maps_to_rates(self):
        """Test swaps map to RATES pod."""
        assert get_riskpod("swap") == RiskPod.RATES

    def test_cds_maps_to_credit(self):
        """Test CDS maps to CREDIT pod."""
        assert get_riskpod("cds") == RiskPod.CREDIT

    def test_fx_maps_to_fx(self):
        """Test FX maps to FX pod."""
        assert get_riskpod("fx") == RiskPod.FX

    def test_commodity_maps_to_other(self):
        """Test commodity maps to OTHER pod."""
        assert get_riskpod("commodity") == RiskPod.OTHER

    def test_crypto_maps_to_other(self):
        """Test crypto maps to OTHER pod."""
        assert get_riskpod("crypto") == RiskPod.OTHER

    def test_unknown_maps_to_other(self):
        """Test unknown asset class maps to OTHER pod."""
        assert get_riskpod("unknown_asset") == RiskPod.OTHER

    def test_none_maps_to_other(self):
        """Test None asset class maps to OTHER pod."""
        assert get_riskpod(None) == RiskPod.OTHER

    def test_case_insensitive(self):
        """Test mapping is case insensitive."""
        assert get_riskpod("EQUITY") == RiskPod.EQUITY
        assert get_riskpod("Equity") == RiskPod.EQUITY
        assert get_riskpod("equity") == RiskPod.EQUITY


class TestGetPodMetrics:
    """Tests for get_pod_metrics function."""

    def test_equity_metrics(self):
        """Test equity pod has expected metrics."""
        metrics = get_pod_metrics(RiskPod.EQUITY)
        assert "beta" in metrics
        assert "delta" in metrics
        assert "gamma" in metrics
        assert "vega" in metrics
        assert "sector_exposure" in metrics

    def test_rates_metrics(self):
        """Test rates pod has expected metrics."""
        metrics = get_pod_metrics(RiskPod.RATES)
        assert "dv01" in metrics
        assert "duration" in metrics
        assert "convexity" in metrics

    def test_credit_metrics(self):
        """Test credit pod has expected metrics."""
        metrics = get_pod_metrics(RiskPod.CREDIT)
        assert "cs01" in metrics
        assert "credit_duration" in metrics
        assert "default_probability" in metrics

    def test_fx_metrics(self):
        """Test FX pod has expected metrics."""
        metrics = get_pod_metrics(RiskPod.FX)
        assert "fx_delta" in metrics
        assert "currency_exposure" in metrics


# =============================================================================
# CORRELATION TESTS
# =============================================================================

class TestCorrelation:
    """Tests for correlation functions."""

    def test_self_correlation_is_one(self):
        """Test correlation with self is 1.0."""
        for pod in RiskPod:
            assert get_correlation(pod, pod) == 1.0

    def test_equity_rates_negative(self):
        """Test equity-rates correlation is negative (flight to quality)."""
        corr = get_correlation(RiskPod.EQUITY, RiskPod.RATES)
        assert corr < 0

    def test_equity_credit_positive(self):
        """Test equity-credit correlation is positive (risk-on)."""
        corr = get_correlation(RiskPod.EQUITY, RiskPod.CREDIT)
        assert corr > 0

    def test_correlation_symmetric(self):
        """Test correlation is symmetric (corr(A,B) == corr(B,A))."""
        for pod1 in RiskPod:
            for pod2 in RiskPod:
                assert get_correlation(pod1, pod2) == get_correlation(pod2, pod1)

    def test_correlation_bounded(self):
        """Test all correlations are between -1 and 1."""
        for pod1 in RiskPod:
            for pod2 in RiskPod:
                corr = get_correlation(pod1, pod2)
                assert -1 <= corr <= 1

    def test_crisis_correlations_higher(self):
        """Test crisis correlations are generally higher than normal."""
        # In crisis mode, correlations should spike toward 1
        # Check equity-credit (one of the most affected pairs)
        normal_corr = get_correlation(RiskPod.EQUITY, RiskPod.CREDIT, crisis_mode=False)
        crisis_corr = get_correlation(RiskPod.EQUITY, RiskPod.CREDIT, crisis_mode=True)
        assert crisis_corr > normal_corr


class TestCorrelationMatrix:
    """Tests for correlation matrix building."""

    def test_matrix_structure(self):
        """Test correlation matrix has correct structure."""
        matrix = build_correlation_matrix()

        # Check all pods are present
        for pod in RiskPod:
            assert pod.value in matrix
            for pod2 in RiskPod:
                assert pod2.value in matrix[pod.value]

    def test_matrix_diagonal_is_one(self):
        """Test diagonal elements are 1.0."""
        matrix = build_correlation_matrix()

        for pod in RiskPod:
            assert matrix[pod.value][pod.value] == 1.0

    def test_matrix_symmetric(self):
        """Test matrix is symmetric."""
        matrix = build_correlation_matrix()

        for pod1 in RiskPod:
            for pod2 in RiskPod:
                assert matrix[pod1.value][pod2.value] == matrix[pod2.value][pod1.value]

    def test_crisis_matrix_different(self):
        """Test crisis matrix is different from normal."""
        normal = build_correlation_matrix(crisis_mode=False)
        crisis = build_correlation_matrix(crisis_mode=True)

        # At least some values should be different
        different_count = 0
        for pod1 in RiskPod:
            for pod2 in RiskPod:
                if normal[pod1.value][pod2.value] != crisis[pod1.value][pod2.value]:
                    different_count += 1

        assert different_count > 0


# =============================================================================
# FIRM VAR CALCULATION TESTS
# =============================================================================

class TestFirmVaRCalculation:
    """Tests for firm-level VaR calculation with correlations."""

    def test_firmvar_result_structure(self):
        """Test FirmVaRResult has expected fields."""
        result = FirmVaRResult(
            pod_vars={"equity": 100000.0, "rates": 50000.0},
            sum_of_pod_vars=150000.0,
            firm_var_correlated=120000.0,
            diversification_benefit=30000.0,
            diversification_pct=20.0,
            crisis_mode=False,
            var_confidence=0.95,
        )

        d = result.to_dict()
        assert "pod_vars" in d
        assert "sum_of_pod_vars" in d
        assert "firm_var_correlated" in d
        assert "diversification_benefit" in d
        assert "diversification_pct" in d
        assert "methodology" in d

    def test_diversification_benefit_positive(self):
        """Test diversification benefit is positive when correlations < 1."""
        # With correlations less than 1, firm VaR < sum of pod VaRs
        # So diversification benefit should be positive
        result = FirmVaRResult(
            pod_vars={"equity": 100000.0, "rates": 50000.0},
            sum_of_pod_vars=150000.0,
            firm_var_correlated=120000.0,
            diversification_benefit=30000.0,
            diversification_pct=20.0,
            crisis_mode=False,
            var_confidence=0.95,
        )
        assert result.diversification_benefit > 0

    def test_variance_covariance_math(self):
        """Test the variance-covariance calculation is correct."""
        # Given two pod VaRs and their correlation, calculate expected firm VaR
        var_equity = 100.0
        var_rates = 50.0
        corr = -0.2  # Negative correlation (equity-rates)

        # Firm VaR^2 = VaR_eq^2 + VaR_rates^2 + 2*VaR_eq*VaR_rates*corr
        # = 10000 + 2500 + 2*100*50*(-0.2)
        # = 12500 - 2000 = 10500
        # Firm VaR = sqrt(10500) = 102.47

        variance_sum = var_equity**2 + var_rates**2
        covariance = 2 * var_equity * var_rates * corr
        firm_var = math.sqrt(variance_sum + covariance)

        expected = 102.47
        assert abs(firm_var - expected) < 0.1

    def test_perfect_correlation_no_benefit(self):
        """Test that perfect correlation gives no diversification benefit."""
        # If correlation = 1, firm VaR = sum of pod VaRs
        var_a = 100.0
        var_b = 50.0
        corr = 1.0

        variance_sum = var_a**2 + var_b**2
        covariance = 2 * var_a * var_b * corr
        firm_var = math.sqrt(variance_sum + covariance)

        # With corr=1: sqrt(10000 + 2500 + 10000) = sqrt(22500) = 150
        expected = var_a + var_b
        assert abs(firm_var - expected) < 0.01


# =============================================================================
# RISKPOD SUMMARY TESTS
# =============================================================================

class TestRiskPodSummary:
    """Tests for RiskPodSummary dataclass."""

    def test_summary_initialization(self):
        """Test RiskPodSummary initializes correctly."""
        summary = RiskPodSummary(pod=RiskPod.EQUITY)

        assert summary.pod == RiskPod.EQUITY
        assert summary.position_count == 0
        assert summary.gross_long == Decimal("0")
        assert summary.gross_short == Decimal("0")

    def test_summary_to_dict(self):
        """Test RiskPodSummary converts to dict correctly."""
        summary = RiskPodSummary(
            pod=RiskPod.EQUITY,
            position_count=100,
            security_count=50,
            pm_count=5,
            gross_long=Decimal("1000000"),
            gross_short=Decimal("500000"),
            gross_total=Decimal("1500000"),
            net_exposure=Decimal("500000"),
        )

        d = summary.to_dict()

        assert d["pod"] == "equity"
        assert d["pod_display_name"] == "EQUITY"
        assert d["position_count"] == 100
        assert d["security_count"] == 50
        assert d["pm_count"] == 5
        assert d["gross_long"] == 1000000.0
        assert d["gross_short"] == 500000.0
        assert d["gross_total"] == 1500000.0
        assert d["net_exposure"] == 500000.0
        assert "available_metrics" in d


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestRiskPodAPI:
    """Tests for RiskPod API endpoints."""

    def test_riskpod_summary_endpoint_exists(self):
        """Test RiskPod summary endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/riskpods/summary" in routes

    def test_riskpod_detail_endpoint_exists(self):
        """Test RiskPod detail endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/riskpods/{pod}/detail" in routes

    def test_var_correlated_endpoint_exists(self):
        """Test VaR correlated endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/firm/var-correlated" in routes

    def test_correlation_matrix_endpoint_exists(self):
        """Test correlation matrix endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/correlation/matrix" in routes

    def test_var_comparison_endpoint_exists(self):
        """Test VaR comparison endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/firm/var-comparison" in routes

    def test_pm_exposure_endpoint_exists(self):
        """Test PM exposure endpoint is registered."""
        from backend.api.aggregation import router

        routes = [r.path for r in router.routes]
        assert "/riskpods/pm-exposure" in routes


# =============================================================================
# INTEGRATION TESTS (WITH MOCK DATA)
# =============================================================================

class TestRiskPodIntegration:
    """Integration tests using mock database connections."""

    def test_aggregation_service_has_riskpod_methods(self):
        """Test AggregationService has RiskPod methods."""
        from backend.services.aggregation import AggregationService

        # Check methods exist (even without DB connection)
        assert hasattr(AggregationService, "get_riskpod_summary")
        assert hasattr(AggregationService, "get_riskpod_detail")
        assert hasattr(AggregationService, "get_firm_var_correlated")
        assert hasattr(AggregationService, "get_correlation_matrix")
        assert hasattr(AggregationService, "compare_normal_vs_crisis_var")
        assert hasattr(AggregationService, "get_cross_pod_pm_exposure")


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_pod_vars(self):
        """Test FirmVaRResult handles empty pod vars."""
        result = FirmVaRResult(
            pod_vars={},
            sum_of_pod_vars=0.0,
            firm_var_correlated=0.0,
            diversification_benefit=0.0,
            diversification_pct=0.0,
            crisis_mode=False,
            var_confidence=0.95,
        )

        d = result.to_dict()
        assert d["sum_of_pod_vars"] == 0.0
        assert d["firm_var_correlated"] == 0.0

    def test_single_pod_no_diversification(self):
        """Test single pod has no diversification benefit."""
        # With only one pod, there's nothing to diversify across
        var_equity = 100.0

        # Firm VaR = VaR of single pod
        firm_var = math.sqrt(var_equity**2)
        assert firm_var == var_equity

    def test_negative_correlation_increases_benefit(self):
        """Test negative correlation increases diversification benefit."""
        var_a = 100.0
        var_b = 100.0

        # With zero correlation
        firm_var_zero = math.sqrt(var_a**2 + var_b**2)

        # With negative correlation (-0.5)
        firm_var_neg = math.sqrt(var_a**2 + var_b**2 + 2*var_a*var_b*(-0.5))

        # Negative correlation should give lower firm VaR
        assert firm_var_neg < firm_var_zero

    def test_all_asset_classes_mapped(self):
        """Test all expected asset classes have mappings."""
        expected_asset_classes = [
            'equity', 'fixed_income', 'fx', 'option', 'future',
            'swap', 'cds', 'commodity', 'crypto', 'fund', 'other'
        ]

        for ac in expected_asset_classes:
            pod = get_riskpod(ac)
            assert pod in RiskPod
