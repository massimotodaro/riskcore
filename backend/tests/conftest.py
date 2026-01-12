# RISKCORE Test Configuration
# On-premises PostgreSQL - psycopg2

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient


@pytest.fixture
def mock_db_connection():
    """Create a mock psycopg2 connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Default cursor behavior
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    return mock_conn


@pytest.fixture
def mock_db():
    """Legacy fixture name - alias for mock_db_connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID for tests."""
    return uuid4()


@pytest.fixture
def sample_book_id():
    """Sample book ID for tests."""
    return uuid4()


@pytest.fixture
def sample_security_id():
    """Sample security ID for tests."""
    return uuid4()


@pytest.fixture
def sample_position_data(sample_tenant_id, sample_book_id, sample_security_id):
    """Sample position data for creating positions."""
    return {
        "tenant_id": str(sample_tenant_id),
        "book_id": str(sample_book_id),
        "security_id": str(sample_security_id),
        "quantity": "1000",
        "direction": "long",
        "source": "api",
        "as_of_timestamp": datetime.utcnow().isoformat(),
        "price": "150.50",
        "local_currency": "USD",
        "base_currency": "USD",
    }


@pytest.fixture
def sample_position_response(sample_tenant_id, sample_book_id, sample_security_id):
    """Sample position response from database."""
    return {
        "id": str(uuid4()),
        "tenant_id": str(sample_tenant_id),
        "book_id": str(sample_book_id),
        "security_id": str(sample_security_id),
        "quantity": 1000.0,
        "direction": "long",
        "market_value": 150500.0,
        "cost_basis": 140000.0,
        "unrealized_pnl": 10500.0,
        "price": 150.50,
        "price_source": "market",
        "price_as_of": datetime.utcnow().isoformat(),
        "local_currency": "USD",
        "base_currency": "USD",
        "fx_rate": None,
        "market_value_base": 150500.0,
        "beta": None,
        "delta": None,
        "gamma": None,
        "vega": None,
        "theta": None,
        "rho": None,
        "dv01": None,
        "cs01": None,
        "source": "api",
        "source_reference": None,
        "as_of_timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from backend.main import app

    return TestClient(app)
