"""
Tests for Returns and Correlation Services

Tests:
- ReturnsService: capture returns, aggregate, get summaries
- RealizedCorrelationService: PM correlations, implied correlations, matrix
- Correlation calculation utilities
"""

import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List
from unittest.mock import Mock, patch
import math

# Import service classes and functions
from backend.services.returns import (
    ReturnsService,
    ReturnWindow,
    DailyReturn,
    ReturnSeries,
)
from backend.services.realized_correlation import (
    RealizedCorrelationService,
    CorrelationEntityType,
    CorrelationType,
    CorrelationResult,
    PMCorrelationMatrix,
    calculate_pearson_correlation,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_conn():
    """Create a mock database connection."""
    conn = Mock()
    conn.cursor.return_value = Mock()
    return conn


@pytest.fixture
def sample_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def sample_pm_ids():
    return [uuid.uuid4() for _ in range(5)]


@pytest.fixture
def sample_book_ids():
    return [uuid.uuid4() for _ in range(5)]


# =============================================================================
# RETURN WINDOW TESTS
# =============================================================================

class TestReturnWindow:
    """Test ReturnWindow enum."""

    def test_return_window_values(self):
        """Test ReturnWindow enum has expected values."""
        assert ReturnWindow.DAY_1.value == "1d"
        assert ReturnWindow.DAY_5.value == "5d"
        assert ReturnWindow.DAY_21.value == "21d"
        assert ReturnWindow.DAY_63.value == "63d"
        assert ReturnWindow.DAY_252.value == "252d"

    def test_return_window_from_string(self):
        """Test creating ReturnWindow from string."""
        assert ReturnWindow("1d") == ReturnWindow.DAY_1
        assert ReturnWindow("5d") == ReturnWindow.DAY_5
        assert ReturnWindow("21d") == ReturnWindow.DAY_21
        assert ReturnWindow("63d") == ReturnWindow.DAY_63
        assert ReturnWindow("252d") == ReturnWindow.DAY_252

    def test_return_window_invalid_value(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            ReturnWindow("invalid")

        with pytest.raises(ValueError):
            ReturnWindow("30d")


# =============================================================================
# DAILY RETURN TESTS
# =============================================================================

class TestDailyReturn:
    """Test DailyReturn dataclass."""

    def test_daily_return_creation(self):
        """Test creating DailyReturn."""
        entity_id = uuid.uuid4()
        return_date = date.today()
        dr = DailyReturn(
            entity_id=entity_id,
            entity_name="Test Book",
            return_date=return_date,
            daily_pnl=Decimal("10000.00"),
            daily_return_pct=Decimal("0.5"),
            start_nav=Decimal("2000000.00"),
            end_nav=Decimal("2010000.00"),
        )

        assert dr.return_date == return_date
        assert dr.daily_pnl == Decimal("10000.00")
        assert dr.daily_return_pct == Decimal("0.5")
        assert dr.start_nav == Decimal("2000000.00")
        assert dr.end_nav == Decimal("2010000.00")

    def test_daily_return_to_dict(self):
        """Test DailyReturn serialization."""
        entity_id = uuid.uuid4()
        return_date = date.today()
        dr = DailyReturn(
            entity_id=entity_id,
            entity_name="Test Book",
            return_date=return_date,
            daily_pnl=Decimal("10000.00"),
            daily_return_pct=Decimal("0.5"),
            start_nav=Decimal("2000000.00"),
            end_nav=Decimal("2010000.00"),
        )

        result = dr.to_dict()
        assert result["return_date"] == return_date.isoformat()
        assert result["daily_pnl"] == 10000.00
        assert result["daily_return_pct"] == 0.5


# =============================================================================
# RETURN SERIES TESTS
# =============================================================================

class TestReturnSeries:
    """Test ReturnSeries dataclass."""

    def test_return_series_creation(self):
        """Test creating ReturnSeries."""
        entity_id = uuid.uuid4()
        returns = [
            DailyReturn(
                entity_id=entity_id,
                entity_name="Test PM",
                return_date=date.today() - timedelta(days=i),
                daily_pnl=Decimal(str(100 * (i + 1))),
                daily_return_pct=Decimal("0.5"),
                start_nav=Decimal("2000000.00"),
                end_nav=Decimal("2010000.00"),
            )
            for i in range(5)
        ]

        series = ReturnSeries(
            entity_id=entity_id,
            entity_name="Test PM",
            entity_type="pm",
            window=ReturnWindow.DAY_5,
            returns=returns,
        )

        assert series.entity_name == "Test PM"
        assert series.entity_type == "pm"
        assert series.window == ReturnWindow.DAY_5
        assert len(series.returns) == 5

    def test_return_series_statistics(self):
        """Test ReturnSeries statistics calculation."""
        entity_id = uuid.uuid4()
        returns = [
            DailyReturn(
                entity_id=entity_id,
                entity_name="Test PM",
                return_date=date.today() - timedelta(days=i),
                daily_pnl=Decimal(str(1000 * (i + 1))),
                daily_return_pct=Decimal(str(0.5 * (i + 1))),
                start_nav=Decimal("2000000.00"),
                end_nav=Decimal("2010000.00"),
            )
            for i in range(5)
        ]

        series = ReturnSeries(
            entity_id=entity_id,
            entity_name="Test PM",
            entity_type="pm",
            window=ReturnWindow.DAY_5,
            returns=returns,
        )

        result = series.to_dict()

        # Total P&L = 1000 + 2000 + 3000 + 4000 + 5000 = 15000
        assert result["total_pnl"] == 15000.0
        assert result["data_points"] == 5

    def test_return_series_return_values(self):
        """Test ReturnSeries return_values property."""
        entity_id = uuid.uuid4()
        returns = [
            DailyReturn(
                entity_id=entity_id,
                entity_name="Test PM",
                return_date=date.today() - timedelta(days=i),
                daily_pnl=Decimal("1000"),
                daily_return_pct=Decimal(str(0.1 * (i + 1))),
                start_nav=Decimal("2000000.00"),
                end_nav=Decimal("2010000.00"),
            )
            for i in range(3)
        ]

        series = ReturnSeries(
            entity_id=entity_id,
            entity_name="Test PM",
            entity_type="pm",
            window=ReturnWindow.DAY_5,
            returns=returns,
        )

        # return_values should extract daily_return_pct as floats
        values = series.return_values
        assert len(values) == 3
        assert abs(values[0] - 0.1) < 0.0001
        assert abs(values[1] - 0.2) < 0.0001
        assert abs(values[2] - 0.3) < 0.0001


# =============================================================================
# PEARSON CORRELATION TESTS
# =============================================================================

class TestPearsonCorrelation:
    """Test Pearson correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test perfectly correlated series returns 1.0."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert abs(corr - 1.0) < 0.0001
        assert n == 5

    def test_perfect_negative_correlation(self):
        """Test perfectly negatively correlated series returns -1.0."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert abs(corr - (-1.0)) < 0.0001
        assert n == 5

    def test_zero_correlation(self):
        """Test uncorrelated series returns near 0."""
        # These are designed to be uncorrelated
        x = [1.0, -1.0, 1.0, -1.0]
        y = [1.0, 1.0, -1.0, -1.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert abs(corr) < 0.0001
        assert n == 4

    def test_unequal_length_series(self):
        """Test with unequal length series (uses minimum)."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0]  # Shorter

        corr, n = calculate_pearson_correlation(x, y)
        assert abs(corr - 1.0) < 0.0001
        assert n == 3  # Uses minimum length

    def test_single_point_series(self):
        """Test with single point returns 0."""
        x = [1.0]
        y = [2.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert corr == 0.0
        assert n == 1

    def test_empty_series(self):
        """Test with empty series returns 0."""
        x = []
        y = []

        corr, n = calculate_pearson_correlation(x, y)
        assert corr == 0.0
        assert n == 0

    def test_constant_series(self):
        """Test with constant series returns 0 (no variance)."""
        x = [5.0, 5.0, 5.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert corr == 0.0  # No variance in x

    def test_moderate_correlation(self):
        """Test with realistic moderate correlation."""
        # Simulate two PMs with moderate positive correlation
        x = [0.01, -0.02, 0.015, -0.005, 0.02, -0.01, 0.025, -0.015]
        y = [0.008, -0.015, 0.012, -0.003, 0.018, -0.008, 0.02, -0.012]

        corr, n = calculate_pearson_correlation(x, y)
        # Should be positive and significant
        assert 0.8 < corr < 1.0
        assert n == 8


# =============================================================================
# CORRELATION RESULT TESTS
# =============================================================================

class TestCorrelationResult:
    """Test CorrelationResult dataclass."""

    def test_correlation_result_creation(self):
        """Test creating CorrelationResult."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.65,
            data_points=21,
        )

        assert result.entity1_name == "PM Alpha"
        assert result.entity2_name == "PM Beta"
        assert result.correlation == 0.65
        assert result.data_points == 21

    def test_correlation_strength_strong(self):
        """Test strong correlation classification."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.75,
            data_points=21,
        )

        assert result.strength == "strong"
        assert result.is_concerning is True

    def test_correlation_strength_moderate(self):
        """Test moderate correlation classification."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.55,
            data_points=21,
        )

        assert result.strength == "moderate"
        assert result.is_concerning is False

    def test_correlation_strength_weak(self):
        """Test weak correlation classification."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.25,
            data_points=21,
        )

        assert result.strength == "weak"
        assert result.is_concerning is False

    def test_correlation_strength_negligible(self):
        """Test negligible correlation classification."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.05,
            data_points=21,
        )

        assert result.strength == "negligible"
        assert result.is_concerning is False

    def test_correlation_strength_negative(self):
        """Test negative correlation uses absolute value."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=-0.85,
            data_points=21,
        )

        assert result.strength == "strong"
        assert result.is_concerning is True  # Strong negative is also concerning

    def test_correlation_result_to_dict(self):
        """Test CorrelationResult serialization."""
        id1, id2 = str(uuid.uuid4()), str(uuid.uuid4())
        result = CorrelationResult(
            entity1_id=id1,
            entity1_name="PM Alpha",
            entity2_id=id2,
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.65,
            data_points=21,
        )

        d = result.to_dict()
        assert d["entity1_id"] == id1
        assert d["entity2_id"] == id2
        assert d["entity1_name"] == "PM Alpha"
        assert d["entity2_name"] == "PM Beta"
        assert d["entity_type"] == "pm"
        assert d["correlation_type"] == "realized"
        assert d["window"] == "21d"
        assert d["correlation"] == 0.65
        assert d["strength"] == "moderate"
        assert d["is_concerning"] is False
        assert d["data_points"] == 21


# =============================================================================
# PM CORRELATION MATRIX TESTS
# =============================================================================

class TestPMCorrelationMatrix:
    """Test PMCorrelationMatrix dataclass."""

    def test_pm_correlation_matrix_creation(self):
        """Test creating PMCorrelationMatrix."""
        pm_ids = [str(uuid.uuid4()) for _ in range(3)]
        pm_names = ["PM Alpha", "PM Beta", "PM Gamma"]

        matrix = PMCorrelationMatrix(
            tenant_id=uuid.uuid4(),
            window=ReturnWindow.DAY_21,
            correlation_type=CorrelationType.REALIZED,
            pm_ids=pm_ids,
            pm_names=pm_names,
            matrix=[
                [1.0, 0.5, 0.3],
                [0.5, 1.0, 0.2],
                [0.3, 0.2, 1.0],
            ],
            as_of_date=date.today(),
            high_correlation_pairs=[],
        )

        assert len(matrix.pm_names) == 3
        assert len(matrix.matrix) == 3
        assert all(len(row) == 3 for row in matrix.matrix)

    def test_pm_correlation_matrix_diagonal(self):
        """Test diagonal values are 1.0 (self-correlation)."""
        pm_ids = [str(uuid.uuid4()) for _ in range(2)]
        pm_names = ["PM Alpha", "PM Beta"]

        matrix = PMCorrelationMatrix(
            tenant_id=uuid.uuid4(),
            window=ReturnWindow.DAY_21,
            correlation_type=CorrelationType.REALIZED,
            pm_ids=pm_ids,
            pm_names=pm_names,
            matrix=[
                [1.0, 0.5],
                [0.5, 1.0],
            ],
            as_of_date=date.today(),
            high_correlation_pairs=[],
        )

        # Diagonal should be 1.0
        assert matrix.matrix[0][0] == 1.0
        assert matrix.matrix[1][1] == 1.0

    def test_pm_correlation_matrix_symmetric(self):
        """Test matrix is symmetric."""
        pm_ids = [str(uuid.uuid4()) for _ in range(3)]
        pm_names = ["PM Alpha", "PM Beta", "PM Gamma"]

        matrix = PMCorrelationMatrix(
            tenant_id=uuid.uuid4(),
            window=ReturnWindow.DAY_21,
            correlation_type=CorrelationType.REALIZED,
            pm_ids=pm_ids,
            pm_names=pm_names,
            matrix=[
                [1.0, 0.5, 0.3],
                [0.5, 1.0, 0.2],
                [0.3, 0.2, 1.0],
            ],
            as_of_date=date.today(),
            high_correlation_pairs=[],
        )

        # Check symmetry
        for i in range(3):
            for j in range(3):
                assert matrix.matrix[i][j] == matrix.matrix[j][i]

    def test_pm_correlation_matrix_to_dict(self):
        """Test PMCorrelationMatrix serialization."""
        tenant_id = uuid.uuid4()
        pm_ids = [str(uuid.uuid4()) for _ in range(2)]
        pm_names = ["PM Alpha", "PM Beta"]

        high_pair = CorrelationResult(
            entity1_id=pm_ids[0],
            entity1_name="PM Alpha",
            entity2_id=pm_ids[1],
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.85,
            data_points=21,
        )

        matrix = PMCorrelationMatrix(
            tenant_id=tenant_id,
            window=ReturnWindow.DAY_21,
            correlation_type=CorrelationType.REALIZED,
            pm_ids=pm_ids,
            pm_names=pm_names,
            matrix=[
                [1.0, 0.85],
                [0.85, 1.0],
            ],
            as_of_date=date.today(),
            high_correlation_pairs=[high_pair],
        )

        d = matrix.to_dict()
        assert d["tenant_id"] == str(tenant_id)
        assert d["window"] == "21d"
        assert d["correlation_type"] == "realized"
        assert d["pm_count"] == 2
        assert d["pm_names"] == ["PM Alpha", "PM Beta"]
        assert len(d["high_correlation_pairs"]) == 1
        assert d["high_correlation_count"] == 1


# =============================================================================
# RETURNS SERVICE TESTS (with mocked DB)
# =============================================================================

class TestReturnsService:
    """Test ReturnsService with mocked database."""

    def test_returns_service_creation(self, mock_conn):
        """Test creating ReturnsService."""
        service = ReturnsService(mock_conn)
        assert service.conn == mock_conn

    def test_window_values_mapping(self, mock_conn):
        """Test that return window values are consistent."""
        # Window values should map to trading days
        windows = {
            ReturnWindow.DAY_1: 1,
            ReturnWindow.DAY_5: 5,
            ReturnWindow.DAY_21: 21,
            ReturnWindow.DAY_63: 63,
            ReturnWindow.DAY_252: 252,
        }

        for window, expected_days in windows.items():
            # Extract numeric value from window
            days_str = window.value.replace('d', '')
            assert int(days_str) == expected_days


# =============================================================================
# REALIZED CORRELATION SERVICE TESTS (with mocked DB)
# =============================================================================

class TestRealizedCorrelationService:
    """Test RealizedCorrelationService with mocked database."""

    def test_service_creation(self, mock_conn):
        """Test creating RealizedCorrelationService."""
        service = RealizedCorrelationService(mock_conn)
        assert service.conn == mock_conn


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_correlation_with_insufficient_data(self):
        """Test correlation calculation with too few data points."""
        x = [1.0]
        y = [2.0]

        corr, n = calculate_pearson_correlation(x, y)
        assert corr == 0.0  # Should return 0 for insufficient data
        assert n == 1

    def test_correlation_result_self_correlation(self):
        """Test that self-correlation is always 1.0."""
        id1 = str(uuid.uuid4())
        result = CorrelationResult(
            entity1_id=id1,
            entity1_name="PM Alpha",
            entity2_id=id1,  # Same ID
            entity2_name="PM Alpha",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=1.0,
            data_points=21,
        )

        # Self-correlation should be 1.0
        assert result.correlation == 1.0

    def test_all_return_windows(self):
        """Test all return window values are valid."""
        windows = [
            ReturnWindow.DAY_1,
            ReturnWindow.DAY_5,
            ReturnWindow.DAY_21,
            ReturnWindow.DAY_63,
            ReturnWindow.DAY_252,
        ]

        for window in windows:
            assert window.value in ["1d", "5d", "21d", "63d", "252d"]


# =============================================================================
# CORRELATION TYPE TESTS
# =============================================================================

class TestCorrelationType:
    """Test CorrelationType enum."""

    def test_correlation_type_values(self):
        """Test CorrelationType enum has expected values."""
        assert CorrelationType.REALIZED.value == "realized"
        assert CorrelationType.IMPLIED.value == "implied"

    def test_correlation_entity_type_values(self):
        """Test CorrelationEntityType enum has expected values."""
        assert CorrelationEntityType.PM.value == "pm"
        assert CorrelationEntityType.BOOK.value == "book"
        assert CorrelationEntityType.POD.value == "pod"
        assert CorrelationEntityType.FUND.value == "fund"


# =============================================================================
# STATISTICAL PROPERTIES TESTS
# =============================================================================

class TestStatisticalProperties:
    """Test statistical properties of correlation calculations."""

    def test_correlation_bounds(self):
        """Test correlation is always between -1 and 1."""
        # Generate random data
        import random
        random.seed(42)

        for _ in range(100):
            x = [random.gauss(0, 1) for _ in range(50)]
            y = [random.gauss(0, 1) for _ in range(50)]

            corr, _ = calculate_pearson_correlation(x, y)
            assert -1.0 <= corr <= 1.0

    def test_correlation_symmetry(self):
        """Test correlation(x, y) == correlation(y, x)."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        y = [2.1, 3.9, 6.2, 7.8, 10.1, 12.0, 13.9, 16.2]

        corr_xy, _ = calculate_pearson_correlation(x, y)
        corr_yx, _ = calculate_pearson_correlation(y, x)

        assert abs(corr_xy - corr_yx) < 0.0001

    def test_correlation_scaling_invariant(self):
        """Test correlation is invariant to linear scaling."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]

        # Scale x by 2 and shift by 100
        x_scaled = [2 * xi + 100 for xi in x]

        corr1, _ = calculate_pearson_correlation(x, y)
        corr2, _ = calculate_pearson_correlation(x_scaled, y)

        assert abs(corr1 - corr2) < 0.0001


# =============================================================================
# INTEGRATION-STYLE TESTS (without DB)
# =============================================================================

class TestIntegrationStyle:
    """Integration-style tests with realistic data patterns."""

    def test_correlation_realistic_returns(self):
        """Test correlation with realistic daily return patterns."""
        # Simulate two PMs over 21 trading days
        # PM1: Equity long/short
        pm1_returns = [
            0.012, -0.008, 0.015, -0.002, 0.009,
            -0.011, 0.007, 0.003, -0.005, 0.018,
            -0.003, 0.010, -0.007, 0.004, 0.012,
            -0.006, 0.008, -0.001, 0.015, -0.009,
            0.006
        ]

        # PM2: Similar strategy with some correlation
        pm2_returns = [
            0.009, -0.006, 0.012, 0.001, 0.007,
            -0.008, 0.005, 0.002, -0.003, 0.015,
            -0.001, 0.008, -0.005, 0.003, 0.010,
            -0.004, 0.006, 0.001, 0.012, -0.007,
            0.004
        ]

        corr, n = calculate_pearson_correlation(pm1_returns, pm2_returns)

        # Should have positive correlation (similar strategies)
        assert corr > 0.7
        assert n == 21

    def test_correlation_uncorrelated_strategies(self):
        """Test correlation between fundamentally different strategies."""
        # PM1: Trending returns (up-down-up-down pattern)
        pm1_returns = [0.01, -0.01, 0.02, -0.02, 0.015, -0.015, 0.01, -0.01]

        # PM2: Independent random-walk style (no pattern relationship)
        pm2_returns = [0.005, 0.008, -0.003, 0.007, -0.002, 0.004, 0.001, -0.006]

        corr, n = calculate_pearson_correlation(pm1_returns, pm2_returns)

        # These should have weak/moderate correlation (not highly correlated)
        # The key is they're designed to not move together
        assert abs(corr) < 0.7  # Not highly correlated
        assert n == 8

    def test_correlation_result_boundary_thresholds(self):
        """Test correlation result boundary thresholds."""
        # Test exactly at threshold boundary (0.7)
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.7,
            data_points=21,
        )
        assert result.strength == "strong"
        assert result.is_concerning is True

        # Just below threshold (0.69)
        result2 = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.REALIZED,
            window=ReturnWindow.DAY_21,
            correlation=0.69,
            data_points=21,
        )
        assert result2.strength == "moderate"
        assert result2.is_concerning is False

    def test_correlation_type_implied(self):
        """Test implied correlation type."""
        result = CorrelationResult(
            entity1_id=str(uuid.uuid4()),
            entity1_name="PM Alpha",
            entity2_id=str(uuid.uuid4()),
            entity2_name="PM Beta",
            entity_type=CorrelationEntityType.PM,
            correlation_type=CorrelationType.IMPLIED,
            window=ReturnWindow.DAY_21,
            correlation=0.65,
            data_points=0,  # Implied doesn't have data points
        )

        d = result.to_dict()
        assert d["correlation_type"] == "implied"
        assert d["data_points"] == 0
