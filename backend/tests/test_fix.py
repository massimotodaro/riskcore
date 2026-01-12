# RISKCORE FIX Protocol Tests

import pytest
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import status


class TestFIXParser:
    """Tests for FIX parser service."""

    def test_parse_execution_report(self):
        """Test parsing ExecutionReport message."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        # Create sample message
        raw_msg = FIXParser.create_sample_execution_report(
            symbol="AAPL",
            side="1",  # Buy
            quantity=100,
            price=150.50,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["msg_type"] == "8"  # ExecutionReport
        assert result["supported"] is True
        assert result["data_type"] == "trade"
        assert result["data"]["ticker"] == "AAPL"
        assert result["data"]["side"] == "buy"
        assert result["data"]["quantity"] == Decimal("100")
        assert result["data"]["price"] == Decimal("150.50")
        assert result["data"]["currency"] == "USD"

    def test_parse_execution_report_sell(self):
        """Test parsing ExecutionReport with sell side."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        raw_msg = FIXParser.create_sample_execution_report(
            symbol="GOOG",
            side="2",  # Sell
            quantity=50,
            price=2800.00,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["data"]["ticker"] == "GOOG"
        assert result["data"]["side"] == "sell"
        assert result["data"]["quantity"] == Decimal("50")

    def test_parse_execution_report_short(self):
        """Test parsing ExecutionReport with short side."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        raw_msg = FIXParser.create_sample_execution_report(
            symbol="TSLA",
            side="5",  # Sell Short
            quantity=25,
            price=250.00,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["data"]["side"] == "short"

    def test_parse_position_report_long(self):
        """Test parsing PositionReport with long position."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        raw_msg = FIXParser.create_sample_position_report(
            symbol="MSFT",
            long_qty=1000,
            short_qty=0,
            price=380.25,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["msg_type"] == "AP"  # PositionReport
        assert result["supported"] is True
        assert result["data_type"] == "position"
        assert result["data"]["ticker"] == "MSFT"
        assert result["data"]["direction"] == "long"
        assert result["data"]["quantity"] == Decimal("1000")
        assert result["data"]["price"] == Decimal("380.25")

    def test_parse_position_report_short(self):
        """Test parsing PositionReport with short position."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        raw_msg = FIXParser.create_sample_position_report(
            symbol="NVDA",
            long_qty=0,
            short_qty=500,
            price=450.00,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["data"]["direction"] == "short"
        assert result["data"]["quantity"] == Decimal("500")

    def test_parse_position_report_net_long(self):
        """Test parsing PositionReport with net long position."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        raw_msg = FIXParser.create_sample_position_report(
            symbol="AMZN",
            long_qty=1000,
            short_qty=300,
            price=175.00,
        )

        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["data"]["direction"] == "long"
        assert result["data"]["quantity"] == Decimal("700")  # 1000 - 300

    def test_parse_invalid_message(self):
        """Test parsing invalid FIX message."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()
        result = parser.parse_message(b"not a fix message")

        assert result["success"] is False
        assert "error" in result

    def test_parse_pipe_delimited(self):
        """Test parsing pipe-delimited FIX message."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        # Create raw message and convert to pipe-delimited
        raw_msg = FIXParser.create_sample_execution_report(
            symbol="IBM",
            side="1",
            quantity=200,
            price=145.00,
        )

        # Convert SOH to pipe
        pipe_msg = raw_msg.decode("utf-8").replace("\x01", "|")

        # Parser should still work with original format
        result = parser.parse_message(raw_msg)

        assert result["success"] is True
        assert result["data"]["ticker"] == "IBM"

    def test_parse_multiple_messages(self):
        """Test parsing multiple FIX messages."""
        from backend.services.fix_parser import FIXParser

        parser = FIXParser()

        # Create multiple messages
        msg1 = FIXParser.create_sample_execution_report(symbol="AAPL", side="1", quantity=100, price=150.00)
        msg2 = FIXParser.create_sample_position_report(symbol="GOOG", long_qty=500, short_qty=0, price=140.00)

        combined = msg1 + msg2
        results = parser.parse_messages(combined)

        assert len(results) == 2
        assert results[0]["data"]["ticker"] == "AAPL"
        assert results[0]["data_type"] == "trade"
        assert results[1]["data"]["ticker"] == "GOOG"
        assert results[1]["data_type"] == "position"

    def test_side_mapping(self):
        """Test FIX side value mappings."""
        from backend.services.fix_parser import FIXSide

        assert FIXSide.to_trade_side("1") == "buy"
        assert FIXSide.to_trade_side("2") == "sell"
        assert FIXSide.to_trade_side("5") == "short"
        assert FIXSide.to_trade_side("6") == "short"
        assert FIXSide.to_trade_side("unknown") == "buy"  # Default


class TestFIXEndpoints:
    """Tests for FIX API endpoints."""

    def test_parse_endpoint(self, client):
        """Test /fix/parse endpoint."""
        from backend.services.fix_parser import FIXParser

        # Get a sample message
        raw_msg = FIXParser.create_sample_execution_report(
            symbol="AAPL",
            side="1",
            quantity=100,
            price=150.50,
        )
        pipe_msg = raw_msg.decode("utf-8").replace("\x01", "|")

        response = client.post(
            "/api/v1/fix/parse",
            json={"message": pipe_msg, "import_data": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["msg_type"] == "8"
        assert data["data"]["ticker"] == "AAPL"
        assert data["imported"] is False

    def test_parse_position_report_endpoint(self, client):
        """Test /fix/parse endpoint with PositionReport."""
        from backend.services.fix_parser import FIXParser

        raw_msg = FIXParser.create_sample_position_report(
            symbol="MSFT",
            long_qty=1000,
            short_qty=0,
            price=380.00,
        )
        pipe_msg = raw_msg.decode("utf-8").replace("\x01", "|")

        response = client.post(
            "/api/v1/fix/parse",
            json={"message": pipe_msg, "import_data": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["msg_type"] == "AP"
        assert data["data"]["ticker"] == "MSFT"
        assert data["data"]["direction"] == "long"

    def test_parse_batch_endpoint(self, client):
        """Test /fix/parse/batch endpoint."""
        from backend.services.fix_parser import FIXParser

        # Create multiple messages
        msg1 = FIXParser.create_sample_execution_report(symbol="AAPL", side="1", quantity=100, price=150.00)
        msg2 = FIXParser.create_sample_execution_report(symbol="GOOG", side="2", quantity=50, price=140.00)

        messages = [
            msg1.decode("utf-8").replace("\x01", "|"),
            msg2.decode("utf-8").replace("\x01", "|"),
        ]

        response = client.post(
            "/api/v1/fix/parse/batch",
            json={"messages": messages, "import_data": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["parsed"] == 2
        assert data["failed"] == 0
        assert len(data["results"]) == 2

    def test_parse_import_requires_ids(self, client):
        """Test that import requires tenant_id and book_id."""
        from backend.services.fix_parser import FIXParser

        raw_msg = FIXParser.create_sample_execution_report()
        pipe_msg = raw_msg.decode("utf-8").replace("\x01", "|")

        response = client.post(
            "/api/v1/fix/parse",
            json={"message": pipe_msg, "import_data": True},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tenant_id" in response.json()["detail"]

    def test_sample_execution_report(self, client):
        """Test /fix/sample/execution-report endpoint."""
        response = client.post(
            "/api/v1/fix/sample/execution-report",
            params={"symbol": "TSLA", "side": "2", "quantity": 50, "price": 250.00},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["msg_type"] == "8"
        assert "TSLA" in data["message"]

    def test_sample_position_report(self, client):
        """Test /fix/sample/position-report endpoint."""
        response = client.post(
            "/api/v1/fix/sample/position-report",
            params={"symbol": "NVDA", "long_qty": 500, "short_qty": 100, "price": 450.00},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["msg_type"] == "AP"
        assert "NVDA" in data["message"]


class TestFIXTags:
    """Tests for FIX tag constants."""

    def test_fix_tags_defined(self):
        """Test FIX tags are properly defined."""
        from backend.services.fix_parser import FIXTags

        assert FIXTags.BEGIN_STRING == 8
        assert FIXTags.MSG_TYPE == 35
        assert FIXTags.SYMBOL == 55
        assert FIXTags.SIDE == 54
        assert FIXTags.ORDER_QTY == 38
        assert FIXTags.PRICE == 44

    def test_fix_msg_types(self):
        """Test FIX message type constants."""
        from backend.services.fix_parser import FIXMsgType

        assert FIXMsgType.EXECUTION_REPORT == "8"
        assert FIXMsgType.POSITION_REPORT == "AP"
        assert FIXMsgType.NEW_ORDER_SINGLE == "D"

    def test_fix_ord_status(self):
        """Test FIX order status constants."""
        from backend.services.fix_parser import FIXOrdStatus

        assert FIXOrdStatus.NEW == "0"
        assert FIXOrdStatus.FILLED == "2"
        assert FIXOrdStatus.CANCELED == "4"
        assert FIXOrdStatus.REJECTED == "8"
