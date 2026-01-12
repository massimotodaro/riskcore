# RISKCORE Trade API Tests

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import date, time, datetime, UTC
from decimal import Decimal

from fastapi.testclient import TestClient
from fastapi import status


class TestListTrades:
    """Tests for GET /trades/ endpoint."""

    def test_list_trades_empty(self, client):
        """Test listing trades returns valid structure."""
        response = client.get("/api/v1/trades/")

        # Should work even with no trades
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_trades_with_pagination(self, client):
        """Test pagination parameters are accepted."""
        response = client.get("/api/v1/trades/?page=1&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_trades_invalid_page_size(self, client):
        """Test invalid page size is rejected."""
        response = client.get("/api/v1/trades/?page_size=200")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_trades_with_book_filter(self, client):
        """Test filtering by book_id."""
        book_id = uuid4()
        response = client.get(f"/api/v1/trades/?book_id={book_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_list_trades_with_side_filter(self, client):
        """Test filtering by side."""
        response = client.get("/api/v1/trades/?side=buy")

        assert response.status_code == status.HTTP_200_OK

    def test_list_trades_with_date_filter(self, client):
        """Test filtering by trade date range."""
        response = client.get(
            "/api/v1/trades/?trade_date_from=2026-01-01&trade_date_to=2026-01-31"
        )

        assert response.status_code == status.HTTP_200_OK


class TestGetTrade:
    """Tests for GET /trades/{trade_id} endpoint."""

    def test_get_trade_not_found(self, client):
        """Test getting non-existent trade returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/trades/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_trade_invalid_uuid(self, client):
        """Test invalid UUID returns 422."""
        response = client.get("/api/v1/trades/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateTrade:
    """Tests for POST /trades/ endpoint."""

    def test_create_trade_missing_required_fields(self, client):
        """Test creating trade without required fields returns 422."""
        response = client.post(
            "/api/v1/trades/",
            json={"book_id": str(uuid4())},  # Missing most required fields
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trade_invalid_side(self, client, valid_trade_data):
        """Test invalid side value is rejected."""
        data = valid_trade_data.copy()
        data["side"] = "invalid_side"

        response = client.post("/api/v1/trades/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trade_invalid_source(self, client, valid_trade_data):
        """Test invalid source value is rejected."""
        data = valid_trade_data.copy()
        data["source"] = "invalid_source"

        response = client.post("/api/v1/trades/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trade_negative_quantity(self, client, valid_trade_data):
        """Test negative quantity is rejected."""
        data = valid_trade_data.copy()
        data["quantity"] = -100

        response = client.post("/api/v1/trades/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trade_negative_price(self, client, valid_trade_data):
        """Test negative price is rejected."""
        data = valid_trade_data.copy()
        data["price"] = -50.00

        response = client.post("/api/v1/trades/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trade_currency_validation(self, client, valid_trade_data):
        """Test currency code validation."""
        data = valid_trade_data.copy()
        data["currency"] = "USDD"  # Too long

        response = client.post("/api/v1/trades/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCancelTrade:
    """Tests for POST /trades/{trade_id}/cancel endpoint."""

    def test_cancel_trade_not_found(self, client):
        """Test cancelling non-existent trade returns 404."""
        fake_id = uuid4()
        response = client.post(f"/api/v1/trades/{fake_id}/cancel")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteTrade:
    """Tests for DELETE /trades/{trade_id} endpoint."""

    def test_delete_trade_not_found(self, client):
        """Test deleting non-existent trade returns 404."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/trades/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_trade_invalid_uuid(self, client):
        """Test invalid UUID returns 422."""
        response = client.delete("/api/v1/trades/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBookTrades:
    """Tests for GET /trades/book/{book_id} endpoint."""

    def test_get_book_trades(self, client):
        """Test getting trades for a book."""
        book_id = uuid4()
        response = client.get(f"/api/v1/trades/book/{book_id}")

        # Should return empty list, not error
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_book_trades_with_date(self, client):
        """Test getting trades for a book filtered by date."""
        book_id = uuid4()
        response = client.get(
            f"/api/v1/trades/book/{book_id}?trade_date=2026-01-15"
        )

        assert response.status_code == status.HTTP_200_OK


class TestBulkCreateTrades:
    """Tests for POST /trades/bulk endpoint."""

    def test_bulk_create_empty_list(self, client):
        """Test bulk create with empty list."""
        response = client.post("/api/v1/trades/bulk", json=[])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["created"] == 0
        assert data["failed"] == 0

    def test_bulk_create_invalid_trades(self, client, valid_trade_data):
        """Test bulk create with invalid trades."""
        invalid_trade = valid_trade_data.copy()
        invalid_trade["quantity"] = -100  # Invalid

        response = client.post("/api/v1/trades/bulk", json=[invalid_trade])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTradeModels:
    """Tests for trade model validation."""

    def test_trade_side_enum(self):
        """Test TradeSide enum values."""
        from backend.models.common import TradeSide

        assert TradeSide.BUY.value == "buy"
        assert TradeSide.SELL.value == "sell"
        assert TradeSide.SHORT.value == "short"
        assert TradeSide.COVER.value == "cover"

    def test_trade_create_model(self):
        """Test TradeCreate model validation."""
        from backend.models.trade import TradeCreate
        from backend.models.common import TradeSide, PositionSource

        trade = TradeCreate(
            tenant_id=uuid4(),
            book_id=uuid4(),
            security_id=uuid4(),
            side=TradeSide.BUY,
            quantity=Decimal("100"),
            price=Decimal("150.50"),
            currency="usd",
            trade_date=date.today(),
            source=PositionSource.API,
        )

        assert trade.currency == "USD"  # Uppercased
        assert trade.quantity == Decimal("100")

    def test_trade_create_currency_uppercase(self):
        """Test currency is automatically uppercased."""
        from backend.models.trade import TradeCreate
        from backend.models.common import TradeSide, PositionSource

        trade = TradeCreate(
            tenant_id=uuid4(),
            book_id=uuid4(),
            security_id=uuid4(),
            side=TradeSide.SELL,
            quantity=Decimal("50"),
            price=Decimal("200.00"),
            currency="eur",
            trade_date=date.today(),
            source=PositionSource.FILE_UPLOAD,
        )

        assert trade.currency == "EUR"

    def test_trade_response_model(self):
        """Test TradeResponse model."""
        from backend.models.trade import TradeResponse
        from backend.models.common import TradeSide, PositionSource

        response = TradeResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            book_id=uuid4(),
            security_id=uuid4(),
            side=TradeSide.BUY,
            quantity=Decimal("100"),
            price=Decimal("150.50"),
            currency="USD",
            trade_date=date.today(),
            source=PositionSource.API,
            created_at=datetime.now(UTC),
        )

        assert response.is_cancelled is False

    def test_trade_list_model(self):
        """Test TradeList model."""
        from backend.models.trade import TradeList, TradeResponse
        from backend.models.common import TradeSide, PositionSource

        trade_list = TradeList(
            items=[
                TradeResponse(
                    id=uuid4(),
                    tenant_id=uuid4(),
                    book_id=uuid4(),
                    security_id=uuid4(),
                    side=TradeSide.BUY,
                    quantity=Decimal("100"),
                    price=Decimal("150.50"),
                    currency="USD",
                    trade_date=date.today(),
                    source=PositionSource.API,
                    created_at=datetime.now(UTC),
                )
            ],
            total=1,
            page=1,
            page_size=50,
            total_pages=1,
        )

        assert len(trade_list.items) == 1
        assert trade_list.total == 1
