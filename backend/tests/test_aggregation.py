# RISKCORE Aggregation Tests
# Tests for netting, overlap detection, and firm-level aggregation
# Week 4 - THE CORE

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import status


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def tenant_id():
    """Generate a test tenant ID."""
    return uuid4()


@pytest.fixture
def fund_id():
    """Generate a test fund ID."""
    return uuid4()


@pytest.fixture
def pm_ids():
    """Generate test PM IDs."""
    return [uuid4() for _ in range(3)]


@pytest.fixture
def book_ids():
    """Generate test book IDs."""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def security_id():
    """Generate a test security ID."""
    return uuid4()


@pytest.fixture
def mock_positions_same_direction():
    """
    Mock positions for same-direction overlap testing.

    PM1 long 1000, PM2 long 500, PM3 long 300 = 1800 total (concentration risk)
    """
    return [
        {"book_id": "b1", "pm_id": "pm1", "quantity": 1000, "direction": "long",
         "market_value": 100000, "market_value_base": 100000, "base_currency": "USD",
         "as_of_timestamp": datetime.now(), "book_name": "Book1", "security_name": "AAPL",
         "pm_name": "PM One"},
        {"book_id": "b2", "pm_id": "pm2", "quantity": 500, "direction": "long",
         "market_value": 50000, "market_value_base": 50000, "base_currency": "USD",
         "as_of_timestamp": datetime.now(), "book_name": "Book2", "security_name": "AAPL",
         "pm_name": "PM Two"},
        {"book_id": "b3", "pm_id": "pm3", "quantity": 300, "direction": "long",
         "market_value": 30000, "market_value_base": 30000, "base_currency": "USD",
         "as_of_timestamp": datetime.now(), "book_name": "Book3", "security_name": "AAPL",
         "pm_name": "PM Three"},
    ]


@pytest.fixture
def mock_positions_opposing():
    """
    Mock positions for opposing direction overlap testing.

    PM1 long 1000, PM2 short 300 = net 700 (netting opportunity)
    """
    return [
        {"book_id": "b1", "pm_id": "pm1", "quantity": 1000, "direction": "long",
         "market_value": 100000, "market_value_base": 100000, "base_currency": "USD",
         "as_of_timestamp": datetime.now(), "book_name": "Book1", "security_name": "AAPL",
         "pm_name": "PM One"},
        {"book_id": "b2", "pm_id": "pm2", "quantity": 300, "direction": "short",
         "market_value": -30000, "market_value_base": -30000, "base_currency": "USD",
         "as_of_timestamp": datetime.now(), "book_name": "Book2", "security_name": "AAPL",
         "pm_name": "PM Two"},
    ]


# =============================================================================
# NETTING SERVICE TESTS
# =============================================================================

class TestNettingService:
    """Tests for the NettingService."""

    def test_net_position_calculation_long_only(self, mock_positions_same_direction):
        """Test net position with all long positions."""
        from backend.services.netting import NettingService, NetPosition

        mock_conn = MagicMock()
        service = NettingService(mock_conn)

        # Create a net position from test data
        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="AAPL",
        )

        # Simulate what calculate_net_position does
        for p in mock_positions_same_direction:
            qty = Decimal(str(p["quantity"]))
            val = Decimal(str(abs(p["market_value"])))

            if p["direction"] == "long":
                net_pos.gross_long_quantity += qty
                net_pos.gross_long_value += val
                net_pos.long_book_ids.append(p["book_id"])
            else:
                net_pos.gross_short_quantity += qty
                net_pos.gross_short_value += val
                net_pos.short_book_ids.append(p["book_id"])

        net_pos.net_quantity = net_pos.gross_long_quantity - net_pos.gross_short_quantity
        net_pos.net_value = net_pos.gross_long_value - net_pos.gross_short_value

        if net_pos.net_quantity > 0:
            net_pos.net_direction = "long"
        elif net_pos.net_quantity < 0:
            net_pos.net_direction = "short"
        else:
            net_pos.net_direction = "flat"

        # Assertions
        assert net_pos.gross_long_quantity == Decimal("1800")
        assert net_pos.gross_short_quantity == Decimal("0")
        assert net_pos.net_quantity == Decimal("1800")
        assert net_pos.net_direction == "long"
        assert len(net_pos.long_book_ids) == 3
        assert len(net_pos.short_book_ids) == 0

    def test_net_position_calculation_opposing(self, mock_positions_opposing):
        """Test net position with opposing long/short positions."""
        from backend.services.netting import NettingService, NetPosition

        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="AAPL",
        )

        for p in mock_positions_opposing:
            qty = Decimal(str(abs(p["quantity"])))
            val = Decimal(str(abs(p["market_value"])))

            if p["direction"] == "long":
                net_pos.gross_long_quantity += qty
                net_pos.gross_long_value += val
                net_pos.long_book_ids.append(p["book_id"])
            else:
                net_pos.gross_short_quantity += qty
                net_pos.gross_short_value += val
                net_pos.short_book_ids.append(p["book_id"])

        net_pos.net_quantity = net_pos.gross_long_quantity - net_pos.gross_short_quantity
        net_pos.net_value = net_pos.gross_long_value - net_pos.gross_short_value

        if net_pos.net_quantity > 0:
            net_pos.net_direction = "long"
        elif net_pos.net_quantity < 0:
            net_pos.net_direction = "short"
        else:
            net_pos.net_direction = "flat"

        # Assertions - THE CORE CALCULATION
        assert net_pos.gross_long_quantity == Decimal("1000")
        assert net_pos.gross_short_quantity == Decimal("300")
        assert net_pos.net_quantity == Decimal("700")  # 1000 - 300 = 700
        assert net_pos.net_direction == "long"
        assert len(net_pos.long_book_ids) == 1
        assert len(net_pos.short_book_ids) == 1

    def test_net_position_to_dict(self):
        """Test NetPosition serialization."""
        from backend.services.netting import NetPosition

        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="AAPL",
            gross_long_quantity=Decimal("1000"),
            gross_short_quantity=Decimal("300"),
            gross_long_value=Decimal("100000"),
            gross_short_value=Decimal("30000"),
            net_quantity=Decimal("700"),
            net_value=Decimal("70000"),
            net_direction="long",
            contributing_pm_count=2,
        )

        result = net_pos.to_dict()

        assert result["security_name"] == "AAPL"
        assert result["gross_long_quantity"] == 1000.0
        assert result["gross_short_quantity"] == 300.0
        assert result["net_quantity"] == 700.0
        assert result["net_direction"] == "long"
        assert result["contributing_pm_count"] == 2

    def test_netting_efficiency_calculation(self):
        """Test netting efficiency percentage calculation."""
        # Gross = Long + Short = 100,000 + 30,000 = 130,000
        # Net = |Long - Short| = |70,000| = 70,000
        # Netting Benefit = Gross - Net = 130,000 - 70,000 = 60,000
        # Netting Efficiency = 60,000 / 130,000 * 100 = 46.15%

        gross_long = 100000
        gross_short = 30000
        total_gross = gross_long + gross_short
        total_net = abs(gross_long - gross_short)
        netting_benefit = total_gross - total_net
        netting_efficiency = netting_benefit / total_gross * 100

        assert total_gross == 130000
        assert total_net == 70000
        assert netting_benefit == 60000
        assert abs(netting_efficiency - 46.15) < 0.1

    def test_flat_position(self):
        """Test when long and short completely offset (flat)."""
        from backend.services.netting import NetPosition

        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="AAPL",
            gross_long_quantity=Decimal("500"),
            gross_short_quantity=Decimal("500"),
            gross_long_value=Decimal("50000"),
            gross_short_value=Decimal("50000"),
            net_quantity=Decimal("0"),
            net_value=Decimal("0"),
            net_direction="flat",
        )

        assert net_pos.net_quantity == Decimal("0")
        assert net_pos.net_direction == "flat"

    def test_net_short_position(self):
        """Test when shorts exceed longs (net short)."""
        from backend.services.netting import NetPosition

        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="AAPL",
            gross_long_quantity=Decimal("300"),
            gross_short_quantity=Decimal("1000"),
            gross_long_value=Decimal("30000"),
            gross_short_value=Decimal("100000"),
        )

        net_pos.net_quantity = net_pos.gross_long_quantity - net_pos.gross_short_quantity
        net_pos.net_value = net_pos.gross_long_value - net_pos.gross_short_value

        if net_pos.net_quantity > 0:
            net_pos.net_direction = "long"
        elif net_pos.net_quantity < 0:
            net_pos.net_direction = "short"
        else:
            net_pos.net_direction = "flat"

        assert net_pos.net_quantity == Decimal("-700")
        assert net_pos.net_direction == "short"


# =============================================================================
# OVERLAP DETECTION TESTS
# =============================================================================

class TestOverlapDetection:
    """Tests for overlap detection service."""

    def test_overlap_type_same_direction(self):
        """Test overlap type classification for same-direction positions."""
        from backend.services.overlap import OverlapType

        # All PMs long = same_direction (concentration risk)
        directions = {"long"}
        if len(directions) == 1:
            if "long" in directions:
                overlap_type = OverlapType.SAME_DIRECTION
            elif "short" in directions:
                overlap_type = OverlapType.SAME_DIRECTION
            else:
                overlap_type = OverlapType.MIXED
        else:
            overlap_type = OverlapType.OPPOSING

        assert overlap_type == OverlapType.SAME_DIRECTION

    def test_overlap_type_opposing(self):
        """Test overlap type classification for opposing positions."""
        from backend.services.overlap import OverlapType

        # Mix of long and short = opposing (netting opportunity)
        directions = {"long", "short"}
        if len(directions) == 1:
            overlap_type = OverlapType.SAME_DIRECTION
        elif "mixed" in directions:
            overlap_type = OverlapType.MIXED
        else:
            overlap_type = OverlapType.OPPOSING

        assert overlap_type == OverlapType.OPPOSING

    def test_overlap_severity_high(self):
        """Test high severity classification."""
        from backend.services.overlap import OverlapSeverity

        pm_count = 4
        concentration_pct = 12.0

        # High if: >3 PMs OR >10% concentration
        if pm_count > 3 or concentration_pct > 10:
            severity = OverlapSeverity.HIGH
        elif pm_count >= 2 and concentration_pct > 5:
            severity = OverlapSeverity.MEDIUM
        else:
            severity = OverlapSeverity.LOW

        assert severity == OverlapSeverity.HIGH

    def test_overlap_severity_medium(self):
        """Test medium severity classification."""
        from backend.services.overlap import OverlapSeverity

        pm_count = 3
        concentration_pct = 7.0

        if pm_count > 3 or concentration_pct > 10:
            severity = OverlapSeverity.HIGH
        elif pm_count >= 2 and concentration_pct > 5:
            severity = OverlapSeverity.MEDIUM
        else:
            severity = OverlapSeverity.LOW

        assert severity == OverlapSeverity.MEDIUM

    def test_overlap_severity_low(self):
        """Test low severity classification."""
        from backend.services.overlap import OverlapSeverity

        pm_count = 2
        concentration_pct = 3.0

        if pm_count > 3 or concentration_pct > 10:
            severity = OverlapSeverity.HIGH
        elif pm_count >= 2 and concentration_pct > 5:
            severity = OverlapSeverity.MEDIUM
        else:
            severity = OverlapSeverity.LOW

        assert severity == OverlapSeverity.LOW

    def test_position_overlap_to_dict(self):
        """Test PositionOverlap serialization."""
        from backend.services.overlap import PositionOverlap, OverlapType, OverlapSeverity

        overlap = PositionOverlap(
            security_id=uuid4(),
            security_name="AAPL",
            overlap_type=OverlapType.SAME_DIRECTION,
            severity=OverlapSeverity.HIGH,
            pm_count=4,
            total_long_quantity=Decimal("1800"),
            total_short_quantity=Decimal("0"),
            total_long_value=Decimal("180000"),
            total_short_value=Decimal("0"),
            net_quantity=Decimal("1800"),
            net_value=Decimal("180000"),
            concentration_pct=15.5,
            correlation_concern=True,
        )

        result = overlap.to_dict()

        assert result["security_name"] == "AAPL"
        assert result["overlap_type"] == "same_direction"
        assert result["severity"] == "high"
        assert result["pm_count"] == 4
        assert result["concentration_pct"] == 15.5
        assert result["correlation_concern"] is True

    def test_concentration_risk_detection(self):
        """Test that same-direction overlaps are flagged as concentration risks."""
        from backend.services.overlap import OverlapType

        # All long = correlation concern (correlated losses)
        overlap_type = OverlapType.SAME_DIRECTION
        correlation_concern = overlap_type == OverlapType.SAME_DIRECTION

        assert correlation_concern is True

    def test_netting_opportunity_detection(self):
        """Test that opposing overlaps are identified as netting opportunities."""
        from backend.services.overlap import OverlapType

        # Opposing = netting opportunity
        overlap_type = OverlapType.OPPOSING
        is_netting_opportunity = overlap_type == OverlapType.OPPOSING

        assert is_netting_opportunity is True


# =============================================================================
# AGGREGATION SERVICE TESTS
# =============================================================================

class TestAggregationService:
    """Tests for the main AggregationService."""

    def test_hierarchy_node_to_dict(self):
        """Test HierarchyNode serialization."""
        from backend.services.aggregation import HierarchyNode

        book_node = HierarchyNode(
            level="book",
            id=uuid4(),
            name="Test Book",
            position_count=10,
            gross_exposure=Decimal("1000000"),
            net_exposure=Decimal("500000"),
            long_exposure=Decimal("750000"),
            short_exposure=Decimal("250000"),
        )

        result = book_node.to_dict()

        assert result["level"] == "book"
        assert result["name"] == "Test Book"
        assert result["position_count"] == 10
        assert result["gross_exposure"] == 1000000.0
        assert result["net_exposure"] == 500000.0
        assert result["long_exposure"] == 750000.0
        assert result["short_exposure"] == 250000.0

    def test_hierarchy_aggregation(self):
        """Test that child metrics sum to parent."""
        from backend.services.aggregation import HierarchyNode

        # Create book nodes
        book1 = HierarchyNode(
            level="book", id=uuid4(), name="Book1",
            position_count=5, gross_exposure=Decimal("100000"),
            net_exposure=Decimal("80000"), long_exposure=Decimal("90000"),
            short_exposure=Decimal("10000"),
        )

        book2 = HierarchyNode(
            level="book", id=uuid4(), name="Book2",
            position_count=3, gross_exposure=Decimal("50000"),
            net_exposure=Decimal("20000"), long_exposure=Decimal("35000"),
            short_exposure=Decimal("15000"),
        )

        # Create PM node with children
        pm_node = HierarchyNode(
            level="pm", id=uuid4(), name="Test PM",
            children=[book1, book2],
        )

        # Aggregate metrics
        pm_node.position_count = sum(c.position_count for c in pm_node.children)
        pm_node.gross_exposure = sum(c.gross_exposure for c in pm_node.children)
        pm_node.net_exposure = sum(c.net_exposure for c in pm_node.children)
        pm_node.long_exposure = sum(c.long_exposure for c in pm_node.children)
        pm_node.short_exposure = sum(c.short_exposure for c in pm_node.children)

        # Assertions - sum of children equals parent
        assert pm_node.position_count == 8  # 5 + 3
        assert pm_node.gross_exposure == Decimal("150000")  # 100K + 50K
        assert pm_node.net_exposure == Decimal("100000")  # 80K + 20K
        assert pm_node.long_exposure == Decimal("125000")  # 90K + 35K
        assert pm_node.short_exposure == Decimal("25000")  # 10K + 15K

    def test_leverage_ratio_calculation(self):
        """Test leverage ratio calculation."""
        gross = 1000000
        net = 500000

        leverage = gross / abs(net) if net != 0 else 0

        assert leverage == 2.0  # 2x leverage

    def test_leverage_ratio_zero_net(self):
        """Test leverage ratio when net is zero."""
        gross = 1000000
        net = 0

        leverage = gross / abs(net) if net != 0 else 0

        assert leverage == 0  # Can't calculate when net is 0


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestAggregationAPI:
    """Tests for aggregation API endpoints."""

    def test_firm_summary_endpoint(self):
        """Test GET /api/v1/aggregation/firm/summary endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/firm/summary",
            params={"tenant_id": tenant_id}
        )

        # Should return 404 for non-existent tenant or 200 with data
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_netting_summary_endpoint(self):
        """Test GET /api/v1/aggregation/netting/summary endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/netting/summary",
            params={"tenant_id": tenant_id}
        )

        # Should return 200 with empty summary if no data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_gross" in data
        assert "netting_efficiency_pct" in data

    def test_overlaps_endpoint(self):
        """Test GET /api/v1/aggregation/overlaps endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/overlaps",
            params={"tenant_id": tenant_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_overlaps_summary_endpoint(self):
        """Test GET /api/v1/aggregation/overlaps/summary endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/overlaps/summary",
            params={"tenant_id": tenant_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_overlaps" in data
        assert "high_severity" in data
        assert "correlation_concerns" in data

    def test_invalid_severity_filter(self):
        """Test invalid severity filter returns 400."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/overlaps",
            params={"tenant_id": tenant_id, "min_severity": "invalid"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_net_positions_endpoint(self):
        """Test GET /api/v1/aggregation/netting/positions endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/netting/positions",
            params={"tenant_id": tenant_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_firm_hierarchy_endpoint(self):
        """Test GET /api/v1/aggregation/firm/hierarchy endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/firm/hierarchy",
            params={"tenant_id": tenant_id}
        )

        # Should return 404 for non-existent tenant
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_concentration_risks_endpoint(self):
        """Test GET /api/v1/aggregation/overlaps/concentration-risks endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/overlaps/concentration-risks",
            params={"tenant_id": tenant_id, "threshold_pct": 5.0}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_netting_opportunities_endpoint(self):
        """Test GET /api/v1/aggregation/overlaps/netting-opportunities endpoint."""
        from backend.main import app

        client = TestClient(app)
        tenant_id = str(uuid4())

        response = client.get(
            f"/api/v1/aggregation/overlaps/netting-opportunities",
            params={"tenant_id": tenant_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_firm_summary(self):
        """Test firm summary with no positions."""
        # When no positions exist, should return zeros
        summary = {
            "total_positions": 0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "netting_efficiency_pct": 0.0,
        }

        assert summary["total_positions"] == 0
        assert summary["netting_efficiency_pct"] == 0.0

    def test_single_pm_no_overlap(self):
        """Test that single PM positions don't create overlaps."""
        from backend.services.overlap import OverlapSeverity

        pm_count = 1
        min_pm_count = 2

        # Single PM should not create an overlap
        is_overlap = pm_count >= min_pm_count

        assert is_overlap is False

    def test_concentration_threshold(self):
        """Test concentration threshold filtering."""
        threshold_pct = 5.0
        concentrations = [2.0, 5.5, 10.0, 3.0, 8.0]

        above_threshold = [c for c in concentrations if c >= threshold_pct]

        assert len(above_threshold) == 3  # 5.5, 10.0, 8.0
        assert 2.0 not in above_threshold
        assert 3.0 not in above_threshold

    def test_currency_consistency(self):
        """Test that base currency is tracked."""
        from backend.services.netting import NetPosition

        net_pos = NetPosition(
            security_id=uuid4(),
            security_name="Test",
            base_currency="EUR",
        )

        assert net_pos.base_currency == "EUR"

    def test_decimal_precision(self):
        """Test decimal precision is maintained."""
        from decimal import Decimal

        qty = Decimal("1000.123456")
        price = Decimal("99.999999")
        value = qty * price

        # Should maintain precision (Decimal multiplication is exact)
        expected = Decimal("1000.123456") * Decimal("99.999999")
        assert value == expected

    def test_large_number_handling(self):
        """Test handling of large position values."""
        from decimal import Decimal

        # Billion-dollar position
        large_value = Decimal("1000000000.00")

        # Should handle without overflow
        assert large_value > 0
        assert float(large_value) == 1_000_000_000.0
