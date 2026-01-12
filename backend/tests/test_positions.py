# RISKCORE Position API Tests

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from fastapi import status


class TestListPositions:
    """Tests for GET /api/v1/positions/"""

    def test_list_positions_empty(self, client):
        """Test listing positions returns empty list when no positions exist."""
        response = client.get("/api/v1/positions/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_list_positions_with_pagination(self, client):
        """Test pagination parameters are accepted."""
        response = client.get("/api/v1/positions/?page=2&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_list_positions_invalid_page_size(self, client):
        """Test that page_size > 100 is rejected."""
        response = client.get("/api/v1/positions/?page_size=200")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_positions_with_book_filter(self, client, sample_book_id):
        """Test filtering by book_id."""
        response = client.get(f"/api/v1/positions/?book_id={sample_book_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_list_positions_with_direction_filter(self, client):
        """Test filtering by direction."""
        response = client.get("/api/v1/positions/?direction=long")

        assert response.status_code == status.HTTP_200_OK


class TestGetPosition:
    """Tests for GET /api/v1/positions/{position_id}"""

    def test_get_position_not_found(self, client):
        """Test getting a non-existent position returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/positions/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_position_invalid_uuid(self, client):
        """Test getting a position with invalid UUID returns 422."""
        response = client.get("/api/v1/positions/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePosition:
    """Tests for POST /api/v1/positions/"""

    def test_create_position_missing_required_fields(self, client):
        """Test creating position without required fields fails."""
        response = client.post("/api/v1/positions/", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_position_invalid_direction(self, client, sample_position_data):
        """Test creating position with invalid direction fails."""
        sample_position_data["direction"] = "invalid"

        response = client.post("/api/v1/positions/", json=sample_position_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_position_invalid_source(self, client, sample_position_data):
        """Test creating position with invalid source fails."""
        sample_position_data["source"] = "invalid"

        response = client.post("/api/v1/positions/", json=sample_position_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_position_negative_quantity(self, client, sample_position_data):
        """Test creating position with negative quantity fails."""
        sample_position_data["quantity"] = "-100"

        response = client.post("/api/v1/positions/", json=sample_position_data)

        # Pydantic should reject this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_position_currency_validation(self, client, sample_position_data):
        """Test that currency codes are validated (3 chars)."""
        sample_position_data["local_currency"] = "INVALID"

        response = client.post("/api/v1/positions/", json=sample_position_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdatePosition:
    """Tests for PUT /api/v1/positions/{position_id}"""

    def test_update_position_not_found(self, client):
        """Test updating a non-existent position returns 404."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/positions/{fake_id}",
            json={"quantity": "2000"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_position_empty_body(self, client):
        """Test updating with empty body is allowed (no changes)."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/positions/{fake_id}",
            json={},
        )

        # Should return 404 since position doesn't exist, not validation error
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeletePosition:
    """Tests for DELETE /api/v1/positions/{position_id}"""

    def test_delete_position_not_found(self, client):
        """Test deleting a non-existent position returns 404."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/positions/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_position_invalid_uuid(self, client):
        """Test deleting with invalid UUID returns 422."""
        response = client.delete("/api/v1/positions/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPositionPnL:
    """Tests for GET /api/v1/positions/{position_id}/pnl"""

    def test_pnl_position_not_found(self, client):
        """Test P&L calculation for non-existent position returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/positions/{fake_id}/pnl")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pnl_with_price_override(self, client):
        """Test P&L calculation with price override parameter."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/positions/{fake_id}/pnl?current_price=175.00")

        # Should be 404 (position not found), not 422 (validation)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBulkCreatePositions:
    """Tests for POST /api/v1/positions/bulk"""

    def test_bulk_create_empty_list(self, client):
        """Test bulk create with empty list returns success."""
        response = client.post("/api/v1/positions/bulk", json=[])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created"] == 0
        assert data["failed"] == 0
        assert data["total"] == 0

    def test_bulk_create_invalid_positions(self, client):
        """Test bulk create with invalid positions reports failures."""
        invalid_positions = [
            {
                "tenant_id": str(uuid4()),
                "book_id": str(uuid4()),
                # Missing security_id and identifiers
                "quantity": "1000",
                "direction": "long",
                "source": "api",
                "as_of_timestamp": datetime.utcnow().isoformat(),
            }
        ]

        response = client.post("/api/v1/positions/bulk", json=invalid_positions)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["failed"] == 1
        assert data["errors"] is not None


class TestPositionModels:
    """Tests for Pydantic model validation."""

    def test_position_direction_enum(self):
        """Test that PositionDirection enum has correct values."""
        from backend.models.common import PositionDirection

        assert PositionDirection.LONG.value == "long"
        assert PositionDirection.SHORT.value == "short"
        assert PositionDirection.FLAT.value == "flat"

    def test_position_source_enum(self):
        """Test that PositionSource enum has correct values."""
        from backend.models.common import PositionSource

        assert PositionSource.FILE_UPLOAD.value == "file_upload"
        assert PositionSource.API.value == "api"
        assert PositionSource.FIX.value == "fix"
        assert PositionSource.CALCULATED.value == "calculated"

    def test_price_source_enum(self):
        """Test that PriceSource enum has correct values."""
        from backend.models.common import PriceSource

        assert PriceSource.MARKET.value == "market"
        assert PriceSource.MODEL.value == "model"
        assert PriceSource.CLIENT_OVERRIDE.value == "client_override"
        assert PriceSource.STALE.value == "stale"

    def test_position_create_model(self, sample_tenant_id, sample_book_id, sample_security_id):
        """Test PositionCreate model validation."""
        from backend.models.position import PositionCreate
        from backend.models.common import PositionDirection, PositionSource

        position = PositionCreate(
            tenant_id=sample_tenant_id,
            book_id=sample_book_id,
            security_id=sample_security_id,
            quantity=Decimal("1000"),
            direction=PositionDirection.LONG,
            source=PositionSource.API,
            as_of_timestamp=datetime.utcnow(),
        )

        assert position.quantity == Decimal("1000")
        assert position.direction == PositionDirection.LONG
        assert position.local_currency == "USD"  # Default

    def test_position_create_currency_uppercase(self, sample_tenant_id, sample_book_id, sample_security_id):
        """Test that currency codes are uppercased."""
        from backend.models.position import PositionCreate
        from backend.models.common import PositionDirection, PositionSource

        position = PositionCreate(
            tenant_id=sample_tenant_id,
            book_id=sample_book_id,
            security_id=sample_security_id,
            quantity=Decimal("1000"),
            direction=PositionDirection.LONG,
            source=PositionSource.API,
            as_of_timestamp=datetime.utcnow(),
            local_currency="gbp",  # lowercase
        )

        assert position.local_currency == "GBP"  # Should be uppercased
