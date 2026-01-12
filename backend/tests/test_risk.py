# RISKCORE Risk Tests
# Tests for VaR, CVaR, exposures, and Greeks

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import date, datetime

from fastapi.testclient import TestClient
from fastapi import status


class TestVaRCalculations:
    """Tests for VaR calculation methods."""

    def test_historical_var_95(self):
        """Test historical VaR at 95% confidence."""
        from backend.services.risk_engine import RiskEngine

        # Create mock connection
        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        # Generate sample returns (normal distribution, ~20% annual vol)
        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)  # 252 trading days

        var = engine.calculate_historical_var(daily_returns, 0.95, 1)

        # VaR should be positive and reasonable
        assert var > 0
        assert var < 0.10  # Should be less than 10% for daily

    def test_historical_var_99(self):
        """Test historical VaR at 99% confidence."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        var_95 = engine.calculate_historical_var(daily_returns, 0.95, 1)
        var_99 = engine.calculate_historical_var(daily_returns, 0.99, 1)

        # 99% VaR should be higher than 95% VaR
        assert var_99 > var_95

    def test_var_horizon_scaling(self):
        """Test VaR scales with square root of time."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        var_1d = engine.calculate_historical_var(daily_returns, 0.95, 1)
        var_10d = engine.calculate_historical_var(daily_returns, 0.95, 10)

        # 10-day VaR should be approximately sqrt(10) times 1-day VaR
        expected_ratio = np.sqrt(10)
        actual_ratio = var_10d / var_1d

        assert abs(actual_ratio - expected_ratio) < 0.01

    def test_parametric_var(self):
        """Test parametric (variance-covariance) VaR."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        var = engine.calculate_parametric_var(daily_returns, 0.95, 1)

        assert var > 0
        assert var < 0.10

    def test_monte_carlo_var(self):
        """Test Monte Carlo VaR."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        var = engine.calculate_monte_carlo_var(daily_returns, 0.95, 1, n_simulations=1000)

        assert var > 0
        assert var < 0.10

    def test_var_empty_returns(self):
        """Test VaR with empty returns array."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        empty_returns = np.array([])

        var = engine.calculate_historical_var(empty_returns, 0.95, 1)

        assert var == 0.0


class TestCVaRCalculations:
    """Tests for CVaR (Expected Shortfall) calculations."""

    def test_cvar_95(self):
        """Test CVaR at 95% confidence."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        cvar = engine.calculate_cvar(daily_returns, 0.95, 1)

        # CVaR should be positive
        assert cvar > 0

    def test_cvar_greater_than_var(self):
        """Test CVaR is greater than or equal to VaR."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        daily_returns = np.random.normal(0, 0.01, 252)

        var = engine.calculate_historical_var(daily_returns, 0.95, 1)
        cvar = engine.calculate_cvar(daily_returns, 0.95, 1)

        # CVaR should always be >= VaR
        assert cvar >= var

    def test_cvar_empty_returns(self):
        """Test CVaR with empty returns array."""
        from backend.services.risk_engine import RiskEngine

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        empty_returns = np.array([])

        cvar = engine.calculate_cvar(empty_returns, 0.95, 1)

        assert cvar == 0.0


class TestGreeksCalculations:
    """Tests for options Greeks calculations."""

    def test_call_delta_atm(self):
        """Test call delta is approximately 0.5 at the money."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        # ATM call: spot = strike
        delta = greeks.calculate_delta(
            spot_price=100,
            strike_price=100,
            time_to_expiry=0.25,  # 3 months
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        # ATM call delta should be close to 0.5 (slightly higher due to drift)
        assert 0.45 < delta < 0.65

    def test_put_delta_atm(self):
        """Test put delta is approximately -0.5 at the money."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        delta = greeks.calculate_delta(
            spot_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.PUT,
        )

        # ATM put delta should be close to -0.5
        assert -0.55 < delta < -0.35

    def test_itm_call_delta(self):
        """Test ITM call delta is close to 1."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        # Deep ITM call
        delta = greeks.calculate_delta(
            spot_price=150,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        assert delta > 0.95

    def test_otm_call_delta(self):
        """Test OTM call delta is close to 0."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        # Deep OTM call
        delta = greeks.calculate_delta(
            spot_price=50,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        assert delta < 0.05

    def test_gamma_positive(self):
        """Test gamma is always positive."""
        from backend.services.greeks import GreeksService

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        gamma = greeks.calculate_gamma(
            spot_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
        )

        assert gamma > 0

    def test_gamma_highest_atm(self):
        """Test gamma is highest at the money."""
        from backend.services.greeks import GreeksService

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        gamma_atm = greeks.calculate_gamma(100, 100, 0.25, 0.05, 0.20)
        gamma_itm = greeks.calculate_gamma(120, 100, 0.25, 0.05, 0.20)
        gamma_otm = greeks.calculate_gamma(80, 100, 0.25, 0.05, 0.20)

        assert gamma_atm > gamma_itm
        assert gamma_atm > gamma_otm

    def test_vega_positive(self):
        """Test vega is always positive."""
        from backend.services.greeks import GreeksService

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        vega = greeks.calculate_vega(100, 100, 0.25, 0.05, 0.20)

        assert vega > 0

    def test_theta_negative_long(self):
        """Test theta is negative for long options (time decay)."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        theta_call = greeks.calculate_theta(100, 100, 0.25, 0.05, 0.20, OptionType.CALL)
        theta_put = greeks.calculate_theta(100, 100, 0.25, 0.05, 0.20, OptionType.PUT)

        # Theta should be negative (options lose value over time)
        assert theta_call < 0
        assert theta_put < 0

    def test_all_greeks_structure(self):
        """Test calculate_all_greeks returns correct structure."""
        from backend.services.greeks import GreeksService, OptionType

        mock_conn = MagicMock()
        greeks = GreeksService(mock_conn)

        result = greeks.calculate_all_greeks(
            spot_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        assert "delta" in result
        assert "gamma" in result
        assert "vega" in result
        assert "theta" in result
        assert "rho" in result
        assert result["option_type"] == "call"


class TestExposureCalculations:
    """Tests for exposure breakdown calculations."""

    def test_exposure_dimension_enum(self):
        """Test ExposureDimension enum values."""
        from backend.services.exposures import ExposureDimension

        assert ExposureDimension.SECTOR.value == "sector"
        assert ExposureDimension.GEOGRAPHY.value == "geography"
        assert ExposureDimension.ASSET_CLASS.value == "asset_class"

    def test_exposure_service_initialization(self):
        """Test ExposureService can be initialized."""
        from backend.services.exposures import ExposureService

        mock_conn = MagicMock()
        service = ExposureService(mock_conn)

        assert service.conn == mock_conn


class TestRiskAPIEndpoints:
    """Tests for Risk API endpoints."""

    def test_var_endpoint_validation(self, client):
        """Test VaR endpoint parameter validation."""
        book_id = uuid4()
        tenant_id = uuid4()

        # Invalid confidence level
        response = client.get(
            f"/api/v1/risk/var/{book_id}?tenant_id={tenant_id}&confidence_level=0.50"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_var_endpoint_invalid_method(self, client):
        """Test VaR endpoint rejects invalid method."""
        book_id = uuid4()
        tenant_id = uuid4()

        response = client.get(
            f"/api/v1/risk/var/{book_id}?tenant_id={tenant_id}&method=invalid"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_exposure_endpoint_validation(self, client):
        """Test exposure endpoint parameter validation."""
        book_id = uuid4()
        tenant_id = uuid4()

        # Invalid dimension
        response = client.get(
            f"/api/v1/risk/exposures/{book_id}?tenant_id={tenant_id}&dimension=invalid"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_greeks_calculate_endpoint(self, client):
        """Test Greeks calculation endpoint."""
        response = client.post(
            "/api/v1/risk/greeks/calculate",
            json={
                "spot_price": 100.0,
                "strike_price": 100.0,
                "time_to_expiry": 0.25,
                "volatility": 0.20,
                "risk_free_rate": 0.05,
                "option_type": "call",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "delta" in data
        assert "gamma" in data
        assert "vega" in data
        assert "theta" in data
        assert "rho" in data

    def test_greeks_calculate_put(self, client):
        """Test Greeks calculation for put option."""
        response = client.post(
            "/api/v1/risk/greeks/calculate",
            json={
                "spot_price": 100.0,
                "strike_price": 100.0,
                "time_to_expiry": 0.25,
                "volatility": 0.20,
                "risk_free_rate": 0.05,
                "option_type": "put",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["delta"] < 0  # Put delta is negative
        assert data["option_type"] == "put"

    def test_greeks_calculate_invalid_spot(self, client):
        """Test Greeks calculation rejects invalid spot price."""
        response = client.post(
            "/api/v1/risk/greeks/calculate",
            json={
                "spot_price": -100.0,  # Invalid
                "strike_price": 100.0,
                "time_to_expiry": 0.25,
                "volatility": 0.20,
                "risk_free_rate": 0.05,
                "option_type": "call",
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_greeks_calculate_invalid_volatility(self, client):
        """Test Greeks calculation rejects invalid volatility."""
        response = client.post(
            "/api/v1/risk/greeks/calculate",
            json={
                "spot_price": 100.0,
                "strike_price": 100.0,
                "time_to_expiry": 0.25,
                "volatility": 3.0,  # Too high (max 2.0 = 200%)
                "risk_free_rate": 0.05,
                "option_type": "call",
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRiskMetricTypes:
    """Tests for risk metric type enums."""

    def test_risk_metric_type_enum(self):
        """Test RiskMetricType enum values."""
        from backend.services.risk_engine import RiskMetricType

        assert RiskMetricType.VAR_95.value == "var_95"
        assert RiskMetricType.VAR_99.value == "var_99"
        assert RiskMetricType.CVAR_95.value == "cvar_95"
        assert RiskMetricType.NET_DELTA.value == "net_delta"

    def test_metric_level_enum(self):
        """Test MetricLevel enum values."""
        from backend.services.risk_engine import MetricLevel

        assert MetricLevel.POSITION.value == "position"
        assert MetricLevel.BOOK.value == "book"
        assert MetricLevel.FUND.value == "fund"
        assert MetricLevel.TENANT.value == "tenant"

    def test_var_method_enum(self):
        """Test VaRMethod enum values."""
        from backend.services.risk_engine import VaRMethod

        assert VaRMethod.HISTORICAL.value == "historical"
        assert VaRMethod.PARAMETRIC.value == "parametric"
        assert VaRMethod.MONTE_CARLO.value == "monte_carlo"


class TestRiskEngineIntegration:
    """Integration tests for risk engine."""

    def test_var_calculation_with_method(self):
        """Test VaR calculation with different methods produces similar results."""
        from backend.services.risk_engine import RiskEngine, VaRMethod

        mock_conn = MagicMock()
        engine = RiskEngine(mock_conn)

        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 500)

        var_hist = engine.calculate_var(returns, 0.95, 1, VaRMethod.HISTORICAL)
        var_param = engine.calculate_var(returns, 0.95, 1, VaRMethod.PARAMETRIC)
        var_mc = engine.calculate_var(returns, 0.95, 1, VaRMethod.MONTE_CARLO)

        # All methods should produce similar results (within 50%)
        assert abs(var_hist - var_param) / var_hist < 0.5
        assert abs(var_hist - var_mc) / var_hist < 0.5
