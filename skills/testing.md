# Testing Skill

> Test patterns and conventions for RISKCORE

---

## Testing Stack

| Tool | Purpose | Install |
|------|---------|---------|
| **pytest** | Test runner | `pip install pytest` |
| **pytest-cov** | Coverage | `pip install pytest-cov` |
| **pytest-asyncio** | Async tests | `pip install pytest-asyncio` |
| **httpx** | Async HTTP client | `pip install httpx` |
| **factory-boy** | Test data factories | `pip install factory-boy` |

---

## Directory Structure

```
/backend
└── /tests
    ├── __init__.py
    ├── conftest.py           # Fixtures
    ├── /unit
    │   ├── test_aggregation.py
    │   ├── test_pricing.py
    │   └── test_risk.py
    ├── /integration
    │   ├── test_api_positions.py
    │   ├── test_api_risk.py
    │   └── test_database.py
    └── /factories
        ├── __init__.py
        ├── position_factory.py
        └── portfolio_factory.py
```

---

## Conftest (Shared Fixtures)

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

from main import app
from core.database import get_db

# === Test Client ===

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def async_client():
    """Async test client for async endpoints."""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")

# === Mock Database ===

@pytest.fixture
def mock_db():
    """Mock Supabase client."""
    mock = MagicMock()
    return mock

@pytest.fixture
def override_db(mock_db):
    """Override database dependency."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()

# === Sample Data ===

@pytest.fixture
def sample_returns():
    """Sample returns DataFrame for risk calculations."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    
    returns = pd.DataFrame(
        np.random.randn(252, 4) * 0.02,  # ~2% daily vol
        index=dates,
        columns=symbols
    )
    return returns

@pytest.fixture
def sample_weights():
    """Sample portfolio weights."""
    return pd.Series({
        'AAPL': 0.25,
        'MSFT': 0.25,
        'GOOGL': 0.25,
        'AMZN': 0.25
    })

@pytest.fixture
def sample_position():
    """Sample position dict."""
    return {
        'id': 'test-uuid-123',
        'portfolio_id': 'portfolio-uuid-456',
        'security_id': 'security-uuid-789',
        'ticker': 'AAPL',
        'quantity': 100,
        'market_value': 19500.00,
        'cost_basis': 18000.00,
        'currency': 'USD',
        'as_of_date': '2025-01-09'
    }

@pytest.fixture
def sample_portfolio():
    """Sample portfolio dict."""
    return {
        'id': 'portfolio-uuid-456',
        'name': 'Alpha Fund',
        'pm_name': 'John Smith',
        'strategy': 'Long/Short Equity',
        'nav': 10000000.00,
        'is_active': True
    }

@pytest.fixture
def sample_positions_list(sample_position):
    """List of sample positions."""
    return [
        {**sample_position, 'ticker': 'AAPL', 'quantity': 100, 'market_value': 19500},
        {**sample_position, 'ticker': 'MSFT', 'quantity': 50, 'market_value': 21000},
        {**sample_position, 'ticker': 'GOOGL', 'quantity': 30, 'market_value': 18000},
    ]
```

---

## Unit Test Patterns

### Testing Services

```python
# tests/unit/test_aggregation.py
import pytest
from services.aggregation import AggregationService

class TestAggregationService:
    
    def test_aggregate_positions_by_security(self, sample_positions_list):
        """Test position aggregation groups by security."""
        service = AggregationService()
        
        result = service.aggregate_by_security(sample_positions_list)
        
        assert len(result) == 3  # 3 unique securities
        assert result['AAPL']['quantity'] == 100
    
    def test_aggregate_positions_empty_list(self):
        """Test aggregation with empty list."""
        service = AggregationService()
        
        result = service.aggregate_by_security([])
        
        assert result == {}
    
    def test_calculate_net_exposure(self, sample_positions_list):
        """Test net exposure calculation."""
        service = AggregationService()
        
        # Add a short position
        positions = sample_positions_list + [
            {'ticker': 'AAPL', 'quantity': -50, 'market_value': -9750}
        ]
        
        result = service.aggregate_by_security(positions)
        
        assert result['AAPL']['quantity'] == 50  # 100 - 50
    
    def test_detect_overlaps(self, sample_positions_list):
        """Test overlap detection across portfolios."""
        service = AggregationService()
        
        # Positions from different portfolios
        portfolio_a = [{'portfolio_id': 'A', 'ticker': 'AAPL', 'quantity': 100}]
        portfolio_b = [{'portfolio_id': 'B', 'ticker': 'AAPL', 'quantity': -50}]
        
        overlaps = service.detect_overlaps(portfolio_a + portfolio_b)
        
        assert 'AAPL' in overlaps
        assert overlaps['AAPL']['portfolios'] == ['A', 'B']
```

### Testing Risk Calculations

```python
# tests/unit/test_risk.py
import pytest
import numpy as np
from services.risk_engine import calculate_portfolio_risk, risk_contribution

class TestRiskCalculations:
    
    def test_var_95_within_expected_range(self, sample_returns, sample_weights):
        """VaR 95 should be around 5th percentile."""
        result = calculate_portfolio_risk(sample_returns, sample_weights)
        
        # VaR should be negative (it's a loss)
        assert result['var_95'] < 0
        # Should be roughly 1.65 * volatility for normal distribution
        assert -0.10 < result['var_95'] < 0
    
    def test_cvar_worse_than_var(self, sample_returns, sample_weights):
        """CVaR should be worse (more negative) than VaR."""
        result = calculate_portfolio_risk(sample_returns, sample_weights)
        
        assert result['cvar_95'] < result['var_95']
    
    def test_risk_contributions_sum_to_total(self, sample_returns, sample_weights):
        """Risk contributions should sum to portfolio volatility."""
        contributions = risk_contribution(sample_returns, sample_weights)
        
        total_contrib = contributions['risk_contribution'].sum()
        port_vol = np.sqrt(sample_weights @ sample_returns.cov() @ sample_weights)
        
        assert abs(total_contrib - port_vol) < 0.0001  # Allow small floating point error
    
    def test_sharpe_ratio_calculation(self, sample_returns, sample_weights):
        """Test Sharpe ratio is reasonable."""
        result = calculate_portfolio_risk(sample_returns, sample_weights)
        
        # Sharpe should be between -5 and 5 for normal data
        assert -5 < result['sharpe_ratio'] < 5
    
    def test_max_drawdown_negative(self, sample_returns, sample_weights):
        """Max drawdown should be negative or zero."""
        result = calculate_portfolio_risk(sample_returns, sample_weights)
        
        assert result['max_drawdown'] <= 0
```

### Testing Pricing

```python
# tests/unit/test_pricing.py
import pytest
from services.pricing import price_equity_option, price_bond

class TestOptionPricing:
    
    def test_call_option_positive_value(self):
        """Call option should have positive value."""
        result = price_equity_option(
            spot_price=100,
            strike_price=100,
            expiry_date='2025-06-09',
            option_type='call',
            volatility=0.20
        )
        
        assert result['price'] > 0
    
    def test_call_delta_between_0_and_1(self):
        """Call delta should be between 0 and 1."""
        result = price_equity_option(
            spot_price=100,
            strike_price=100,
            expiry_date='2025-06-09',
            option_type='call',
            volatility=0.20
        )
        
        assert 0 < result['delta'] < 1
    
    def test_put_delta_negative(self):
        """Put delta should be negative."""
        result = price_equity_option(
            spot_price=100,
            strike_price=100,
            expiry_date='2025-06-09',
            option_type='put',
            volatility=0.20
        )
        
        assert result['delta'] < 0
    
    def test_atm_call_delta_around_half(self):
        """ATM call delta should be around 0.5."""
        result = price_equity_option(
            spot_price=100,
            strike_price=100,
            expiry_date='2025-06-09',
            option_type='call',
            volatility=0.20
        )
        
        assert 0.4 < result['delta'] < 0.6

class TestBondPricing:
    
    def test_bond_price_positive(self):
        """Bond price should be positive."""
        result = price_bond(
            issue_date='2020-01-15',
            maturity_date='2030-01-15',
            coupon_rate=0.05,
            settlement_date='2025-01-09',
            yield_to_maturity=0.04
        )
        
        assert result['clean_price'] > 0
    
    def test_premium_bond_above_par(self):
        """Bond with coupon > yield should trade above par."""
        result = price_bond(
            issue_date='2020-01-15',
            maturity_date='2030-01-15',
            coupon_rate=0.05,  # 5% coupon
            settlement_date='2025-01-09',
            yield_to_maturity=0.03  # 3% yield
        )
        
        assert result['clean_price'] > 100
    
    def test_dv01_positive(self):
        """DV01 should be positive."""
        result = price_bond(
            issue_date='2020-01-15',
            maturity_date='2030-01-15',
            coupon_rate=0.05,
            settlement_date='2025-01-09',
            yield_to_maturity=0.04
        )
        
        assert result['dv01'] > 0
```

---

## Integration Test Patterns

### API Tests

```python
# tests/integration/test_api_positions.py
import pytest

class TestPositionsAPI:
    
    def test_list_positions_returns_200(self, client, override_db, mock_db):
        """GET /positions returns 200."""
        mock_db.table.return_value.select.return_value.execute.return_value.data = []
        
        response = client.get("/api/v1/positions")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_position_returns_201(self, client, override_db, mock_db, sample_position):
        """POST /positions returns 201."""
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [sample_position]
        
        response = client.post("/api/v1/positions", json={
            'portfolio_id': sample_position['portfolio_id'],
            'security_id': sample_position['security_id'],
            'quantity': 100,
            'as_of_date': '2025-01-09'
        })
        
        assert response.status_code == 201
    
    def test_get_position_not_found_returns_404(self, client, override_db, mock_db):
        """GET /positions/{id} returns 404 when not found."""
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        response = client.get("/api/v1/positions/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_upload_csv_returns_success(self, client, override_db, mock_db):
        """POST /positions/upload handles CSV."""
        csv_content = b"ticker,quantity,market_value\nAAPL,100,19500"
        
        response = client.post(
            "/api/v1/positions/upload",
            files={"file": ("positions.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        assert 'positions_created' in response.json()
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific file
pytest tests/unit/test_risk.py

# Run specific test
pytest tests/unit/test_risk.py::TestRiskCalculations::test_var_95_within_expected_range

# Run with verbose output
pytest -v

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

---

## Markers

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

Usage:
```python
@pytest.mark.slow
def test_full_portfolio_analysis():
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_database_connection():
    """This test requires database."""
    pass
```

---

## Coverage Requirements

Minimum coverage targets:

| Module | Target |
|--------|--------|
| `services/aggregation.py` | 90% |
| `services/risk_engine.py` | 85% |
| `services/pricing.py` | 85% |
| `api/*` | 80% |
| Overall | 80% |

---

## Don't

- ❌ Don't test external APIs directly (mock them)
- ❌ Don't use production database in tests
- ❌ Don't hardcode test data (use fixtures)
- ❌ Don't write tests that depend on order
- ❌ Don't skip edge cases (empty lists, nulls)
- ❌ Don't test private methods directly

---

*Testing patterns for RISKCORE*
