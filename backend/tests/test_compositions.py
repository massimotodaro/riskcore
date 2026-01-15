"""
Unit Tests for Composition Service

Tests for structured note component breakdown, risk attribution,
and composition management.
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.composition_service import (
    CompositionService,
    CompositionData,
    ComponentData,
    RiskAttribution,
)


# ============================================
# DATA CLASS TESTS (No DB needed)
# ============================================

class TestComponentData:
    """Test ComponentData dataclass."""

    def test_component_creation(self):
        """Test creating a component."""
        component = ComponentData(
            id="comp-1",
            component_name="S&P 500 Future Mar 2025",
            instrument_type_id="type-1",
            instrument_type_code="FUTURE",
            riskpod="equity",
            allocation_type="percentage",
            allocation_value=Decimal("33.33"),
            security_id=None,
            delta=Decimal("1.0"),
            gamma=None,
            vega=None,
            theta=None,
            rho=None,
            duration=None,
            convexity=None,
            dv01=None,
            order_num=0,
        )
        assert component.component_name == "S&P 500 Future Mar 2025"
        assert component.riskpod == "equity"
        assert component.allocation_value == Decimal("33.33")

    def test_component_to_dict(self):
        """Test converting component to dict."""
        component = ComponentData(
            id="comp-1",
            component_name="Test Component",
            instrument_type_id="type-1",
            instrument_type_code="FUTURE",
            riskpod="equity",
            allocation_type="percentage",
            allocation_value=Decimal("50.00"),
            security_id=None,
            delta=Decimal("0.5"),
            gamma=None,
            vega=None,
            theta=None,
            rho=None,
            duration=None,
            convexity=None,
            dv01=None,
            order_num=0,
        )
        d = component.to_dict()
        assert d["component_name"] == "Test Component"
        assert d["allocation_value"] == 50.0
        assert d["delta"] == 0.5
        assert d["gamma"] is None


class TestCompositionData:
    """Test CompositionData dataclass."""

    def test_composition_creation(self):
        """Test creating a composition."""
        now = datetime.now()
        composition = CompositionData(
            id="comp-1",
            tenant_id="tenant-1",
            name="ABC Structured Note",
            name_normalized="abc structured note",
            description="Test composition",
            is_template=True,
            is_active=True,
            components=[],
            created_by="user-1",
            created_at=now,
            updated_at=now,
        )
        assert composition.name == "ABC Structured Note"
        assert composition.is_template is True

    def test_composition_with_components(self):
        """Test composition with components."""
        now = datetime.now()
        components = [
            ComponentData(
                id="c1", component_name="Future", instrument_type_id=None,
                instrument_type_code="FUTURE", riskpod="equity",
                allocation_type="percentage", allocation_value=Decimal("50"),
                security_id=None, delta=None, gamma=None, vega=None,
                theta=None, rho=None, duration=None, convexity=None,
                dv01=None, order_num=0
            ),
            ComponentData(
                id="c2", component_name="Bond", instrument_type_id=None,
                instrument_type_code="CORPBOND", riskpod="credit",
                allocation_type="percentage", allocation_value=Decimal("50"),
                security_id=None, delta=None, gamma=None, vega=None,
                theta=None, rho=None, duration=None, convexity=None,
                dv01=None, order_num=1
            ),
        ]
        composition = CompositionData(
            id="comp-1", tenant_id="tenant-1", name="Test",
            name_normalized="test", description=None, is_template=True,
            is_active=True, components=components, created_by=None,
            created_at=now, updated_at=now
        )
        d = composition.to_dict()
        assert d["component_count"] == 2
        assert d["total_allocation"] == Decimal("100")

    def test_composition_to_dict(self):
        """Test converting composition to dict."""
        now = datetime.now()
        composition = CompositionData(
            id="comp-1", tenant_id="tenant-1", name="Test",
            name_normalized="test", description="Description",
            is_template=True, is_active=True, components=[],
            created_by="user-1", created_at=now, updated_at=now
        )
        d = composition.to_dict()
        assert isinstance(d, dict)
        assert d["name"] == "Test"
        assert d["is_template"] is True
        assert d["component_count"] == 0


class TestRiskAttribution:
    """Test RiskAttribution dataclass."""

    def test_risk_attribution_creation(self):
        """Test creating risk attribution."""
        attribution = RiskAttribution(
            position_id="pos-1",
            total_value=Decimal("30000000"),
            equity=Decimal("20000000"),
            rates=Decimal("0"),
            credit=Decimal("10000000"),
            fx=Decimal("0"),
            other=Decimal("0"),
            components=[
                {"name": "Future", "value": 10000000, "riskpod": "equity"},
                {"name": "Option", "value": 10000000, "riskpod": "equity"},
                {"name": "Bond", "value": 10000000, "riskpod": "credit"},
            ],
        )
        assert attribution.total_value == Decimal("30000000")
        assert attribution.equity == Decimal("20000000")
        assert attribution.credit == Decimal("10000000")

    def test_risk_attribution_to_dict(self):
        """Test converting attribution to dict."""
        attribution = RiskAttribution(
            position_id="pos-1",
            total_value=Decimal("100000"),
            equity=Decimal("60000"),
            rates=Decimal("0"),
            credit=Decimal("40000"),
            fx=Decimal("0"),
            other=Decimal("0"),
            components=[],
        )
        d = attribution.to_dict()
        assert d["total_value"] == 100000
        assert d["attribution"]["equity"] == 60000
        assert d["attribution"]["credit"] == 40000
        assert d["attribution"]["rates"] == 0


# ============================================
# SERVICE TESTS (Mocked DB)
# ============================================

class TestCompositionServiceInit:
    """Test service initialization."""

    def test_init_with_tenant(self):
        """Test initializing with tenant ID."""
        mock_conn = Mock()
        service = CompositionService(mock_conn, "tenant-123")
        assert service.conn == mock_conn
        assert service.tenant_id == "tenant-123"

    def test_init_without_tenant(self):
        """Test initializing without tenant ID."""
        mock_conn = Mock()
        service = CompositionService(mock_conn)
        assert service.tenant_id is None


class TestNormalizeName:
    """Test name normalization."""

    def test_normalize_simple(self):
        """Test simple name normalization."""
        mock_conn = Mock()
        service = CompositionService(mock_conn)
        assert service._normalize_name("Test Name") == "test name"

    def test_normalize_with_extra_spaces(self):
        """Test normalizing name with extra spaces."""
        mock_conn = Mock()
        service = CompositionService(mock_conn)
        assert service._normalize_name("  Test   Name  ") == "test name"

    def test_normalize_empty(self):
        """Test normalizing empty string."""
        mock_conn = Mock()
        service = CompositionService(mock_conn)
        assert service._normalize_name("") == ""

    def test_normalize_none(self):
        """Test normalizing None."""
        mock_conn = Mock()
        service = CompositionService(mock_conn)
        assert service._normalize_name(None) == ""


# ============================================
# INTEGRATION TESTS (Require DB)
# ============================================

@pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Database tests skipped. Set RUN_DB_TESTS=1 to run."
)
class TestCompositionServiceDB:
    """Integration tests requiring actual database."""

    @pytest.fixture
    def db_connection(self):
        """Create actual database connection."""
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        )
        yield conn
        conn.close()

    @pytest.fixture
    def tenant_id(self, db_connection):
        """Get or create a test tenant."""
        cur = db_connection.cursor()
        cur.execute("SELECT id FROM tenants LIMIT 1")
        row = cur.fetchone()
        if row:
            return str(row[0])
        # Create test tenant if none exists
        cur.execute("""
            INSERT INTO tenants (name) VALUES ('Test Tenant')
            RETURNING id
        """)
        tenant_id = str(cur.fetchone()[0])
        db_connection.commit()
        return tenant_id

    def test_create_composition(self, db_connection, tenant_id):
        """Test creating a composition."""
        service = CompositionService(db_connection, tenant_id)

        components = [
            {"name": "Test Future", "type_code": "FUTURE", "allocation": 50.0},
            {"name": "Test Bond", "type_code": "CORPBOND", "allocation": 50.0},
        ]

        comp_id = service.create_composition(
            name="Test Structured Note",
            components=components,
            description="Test composition",
            is_template=True,
        )

        assert comp_id is not None

        # Verify it was created
        composition = service.get_composition(comp_id)
        assert composition is not None
        assert composition.name == "Test Structured Note"
        assert len(composition.components) == 2

        # Cleanup
        service.delete_composition(comp_id)

    def test_list_compositions(self, db_connection, tenant_id):
        """Test listing compositions."""
        service = CompositionService(db_connection, tenant_id)

        # Create a test composition
        comp_id = service.create_composition(
            name="List Test Composition",
            components=[{"name": "Test", "type_code": "EQUITY", "allocation": 100}],
        )

        compositions = service.list_compositions()
        assert len(compositions) >= 1

        # Cleanup
        service.delete_composition(comp_id)

    def test_update_composition(self, db_connection, tenant_id):
        """Test updating a composition."""
        service = CompositionService(db_connection, tenant_id)

        comp_id = service.create_composition(
            name="Update Test",
            components=[{"name": "Test", "type_code": "EQUITY", "allocation": 100}],
        )

        success = service.update_composition(
            comp_id,
            name="Updated Name",
            description="Updated description",
        )
        assert success is True

        composition = service.get_composition(comp_id)
        assert composition.name == "Updated Name"
        assert composition.description == "Updated description"

        # Cleanup
        service.delete_composition(comp_id)

    def test_add_remove_component(self, db_connection, tenant_id):
        """Test adding and removing components."""
        service = CompositionService(db_connection, tenant_id)

        comp_id = service.create_composition(
            name="Component Test",
            components=[{"name": "Initial", "type_code": "EQUITY", "allocation": 50}],
        )

        # Add component
        component_id = service.add_component(
            comp_id,
            {"name": "Added Component", "type_code": "FUTURE", "allocation": 50},
        )
        assert component_id is not None

        composition = service.get_composition(comp_id)
        assert len(composition.components) == 2

        # Remove component
        success = service.remove_component(component_id)
        assert success is True

        composition = service.get_composition(comp_id)
        assert len(composition.components) == 1

        # Cleanup
        service.delete_composition(comp_id)

    def test_find_by_name(self, db_connection, tenant_id):
        """Test finding composition by name."""
        service = CompositionService(db_connection, tenant_id)

        comp_id = service.create_composition(
            name="Unique Name ABC123",
            components=[{"name": "Test", "type_code": "EQUITY", "allocation": 100}],
            is_template=True,
        )

        found = service.find_composition_by_name("Unique Name ABC123")
        assert found is not None
        assert found.id == comp_id

        # Test case insensitive
        found = service.find_composition_by_name("unique name abc123")
        assert found is not None

        # Test not found
        not_found = service.find_composition_by_name("Nonexistent XYZ")
        assert not_found is None

        # Cleanup
        service.delete_composition(comp_id)


# ============================================
# RISK ATTRIBUTION CALCULATION TESTS
# ============================================

class TestRiskAttributionCalculations:
    """Test risk attribution calculation logic."""

    def test_percentage_allocation(self):
        """Test percentage-based allocation calculation."""
        # Mock position value: $30M
        total_value = Decimal("30000000")

        # Components: 33.33% each
        allocations = [
            {"allocation": Decimal("33.33"), "riskpod": "equity"},
            {"allocation": Decimal("33.33"), "riskpod": "equity"},
            {"allocation": Decimal("33.34"), "riskpod": "credit"},
        ]

        equity_value = Decimal(0)
        credit_value = Decimal(0)

        for alloc in allocations:
            value = total_value * (alloc["allocation"] / Decimal(100))
            if alloc["riskpod"] == "equity":
                equity_value += value
            elif alloc["riskpod"] == "credit":
                credit_value += value

        # Verify
        assert equity_value == Decimal("19998000")  # 66.66% of 30M
        assert credit_value == Decimal("10002000")  # 33.34% of 30M
        assert equity_value + credit_value == total_value

    def test_notional_allocation(self):
        """Test notional-based allocation calculation."""
        # Components with notional values
        allocations = [
            {"allocation": Decimal("10000000"), "type": "notional", "riskpod": "equity"},
            {"allocation": Decimal("10000000"), "type": "notional", "riskpod": "equity"},
            {"allocation": Decimal("10000000"), "type": "notional", "riskpod": "credit"},
        ]

        equity_value = Decimal(0)
        credit_value = Decimal(0)

        for alloc in allocations:
            if alloc["type"] == "notional":
                value = alloc["allocation"]
            if alloc["riskpod"] == "equity":
                equity_value += value
            elif alloc["riskpod"] == "credit":
                credit_value += value

        assert equity_value == Decimal("20000000")
        assert credit_value == Decimal("10000000")


# ============================================
# API REQUEST/RESPONSE MODEL TESTS
# ============================================

class TestAPIModels:
    """Test that API models work correctly."""

    def test_component_input_validation(self):
        """Test component input validation."""
        from pydantic import ValidationError

        # Import the model
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

        try:
            from backend.api.compositions import ComponentInput

            # Valid input
            valid = ComponentInput(
                name="Test",
                type_code="FUTURE",
                allocation=33.33,
            )
            assert valid.name == "Test"
            assert valid.allocation == 33.33
            assert valid.allocation_type == "percentage"

            # Invalid: negative allocation
            with pytest.raises(ValidationError):
                ComponentInput(
                    name="Test",
                    type_code="FUTURE",
                    allocation=-10,
                )

            # Invalid: empty name
            with pytest.raises(ValidationError):
                ComponentInput(
                    name="",
                    type_code="FUTURE",
                    allocation=50,
                )

        except ImportError:
            pytest.skip("API module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
