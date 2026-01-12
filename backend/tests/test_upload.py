# RISKCORE Upload API Tests

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
import io

from fastapi.testclient import TestClient
from fastapi import status


class TestFileParser:
    """Tests for FileParser service."""

    def test_parse_csv_simple(self):
        """Test parsing a simple CSV file."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        csv_content = b"ticker,quantity,price\nAAPL,100,150.50\nGOOG,50,2800.00"

        result = parser.parse_file(csv_content, "test.csv", "positions")

        assert result["success"] is True
        assert result["row_count"] == 2
        assert "ticker" in result["columns"]
        assert "quantity" in result["columns"]
        assert "price" in result["columns"]

    def test_parse_csv_auto_detect_columns(self):
        """Test column auto-detection for various naming conventions."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        # Use various column naming conventions
        csv_content = b"Symbol,Qty,Px,Side\nAAPL,100,150.50,Long\nGOOG,50,2800.00,Short"

        result = parser.parse_file(csv_content, "test.csv", "positions")

        assert result["success"] is True
        # Should auto-detect these mappings
        assert result["mapping"].get("ticker") == "symbol"
        assert result["mapping"].get("quantity") == "qty"
        assert result["mapping"].get("price") == "px"
        assert result["mapping"].get("direction") == "side"

    def test_parse_csv_with_different_delimiters(self):
        """Test parsing CSV with semicolon delimiter."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        csv_content = b"ticker;quantity;price\nAAPL;100;150.50\nGOOG;50;2800.00"

        result = parser.parse_file(csv_content, "test.csv", "positions")

        assert result["success"] is True
        assert result["row_count"] == 2

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        result = parser.parse_file(b"", "test.csv", "positions")

        assert result["success"] is False
        # Error may say "empty" or "no columns to parse"
        assert "empty" in result["error"].lower() or "no columns" in result["error"].lower()

    def test_parse_unsupported_format(self):
        """Test parsing unsupported file format."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        result = parser.parse_file(b"some content", "test.txt", "positions")

        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    def test_transform_position_rows(self):
        """Test transforming parsed rows to position format."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        data = [
            {"ticker": "AAPL", "qty": "100", "price": "150.50", "side": "Long"},
            {"ticker": "GOOG", "qty": "50", "price": "2800.00", "side": "Short"},
        ]
        mapping = {
            "ticker": "ticker",
            "quantity": "qty",
            "price": "price",
            "direction": "side",
        }

        valid, errors = parser.transform_rows(
            data, mapping, "positions",
            str(uuid4()), str(uuid4())
        )

        assert len(valid) == 2
        assert len(errors) == 0
        assert valid[0]["ticker"] == "AAPL"
        assert valid[0]["quantity"] == Decimal("100")
        assert valid[0]["direction"] == "long"

    def test_transform_with_missing_identifier(self):
        """Test that rows without security identifier are rejected."""
        from backend.services.file_parser import FileParser

        parser = FileParser()
        data = [
            {"qty": "100", "price": "150.50"},  # No ticker/cusip/isin/sedol
        ]
        mapping = {
            "quantity": "qty",
            "price": "price",
        }

        valid, errors = parser.transform_rows(
            data, mapping, "positions",
            str(uuid4()), str(uuid4())
        )

        assert len(valid) == 0
        assert len(errors) == 1
        assert "identifier" in errors[0]["error"].lower()

    def test_direction_mapping(self):
        """Test various direction value mappings."""
        from backend.services.file_parser import FileParser

        parser = FileParser()

        # Test long mappings
        assert parser._map_direction("Long") == "long"
        assert parser._map_direction("L") == "long"
        assert parser._map_direction("BUY") == "long"

        # Test short mappings
        assert parser._map_direction("Short") == "short"
        assert parser._map_direction("S") == "short"
        assert parser._map_direction("SELL") == "short"

    def test_parse_date_formats(self):
        """Test various date format parsing."""
        from backend.services.file_parser import FileParser

        parser = FileParser()

        assert parser._parse_date("2026-01-15") == "2026-01-15"
        assert parser._parse_date("01/15/2026") == "2026-01-15"
        assert parser._parse_date("15/01/2026") == "2026-01-15"
        assert parser._parse_date("20260115") == "2026-01-15"


class TestUploadPreview:
    """Tests for upload preview endpoint."""

    def test_preview_csv_positions(self, client):
        """Test preview endpoint with CSV file."""
        csv_content = b"ticker,quantity,price,direction\nAAPL,100,150.50,long\nGOOG,50,2800.00,short"

        response = client.post(
            "/api/v1/upload/preview",
            files={"file": ("positions.csv", io.BytesIO(csv_content), "text/csv")},
            data={"file_type": "positions"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["row_count"] == 2
        assert len(data["preview"]) == 2
        assert "ticker" in data["mapping"]

    def test_preview_invalid_file_type(self, client):
        """Test preview with invalid file type."""
        csv_content = b"ticker,quantity,price\nAAPL,100,150.50"

        response = client.post(
            "/api/v1/upload/preview",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"file_type": "invalid"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_preview_empty_file(self, client):
        """Test preview with empty file."""
        response = client.post(
            "/api/v1/upload/preview",
            files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
            data={"file_type": "positions"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUploadImport:
    """Tests for upload import endpoint."""

    def test_import_missing_required_fields(self, client):
        """Test import with missing required fields."""
        csv_content = b"ticker,quantity,price\nAAPL,100,150.50"

        response = client.post(
            "/api/v1/upload/import",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={
                # Missing tenant_id, book_id
                "file_type": "positions",
                "mapping": '{"ticker": "ticker", "quantity": "quantity"}',
                "uploaded_by": str(uuid4()),
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_import_invalid_mapping_json(self, client):
        """Test import with invalid mapping JSON."""
        csv_content = b"ticker,quantity,price\nAAPL,100,150.50"

        response = client.post(
            "/api/v1/upload/import",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={
                "tenant_id": str(uuid4()),
                "book_id": str(uuid4()),
                "file_type": "positions",
                "mapping": "not valid json",
                "uploaded_by": str(uuid4()),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()


class TestUploadList:
    """Tests for upload list endpoint."""

    def test_list_uploads_empty(self, client):
        """Test listing uploads returns valid structure."""
        response = client.get("/api/v1/upload/")

        # Should work even with no uploads
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_uploads_with_pagination(self, client):
        """Test pagination parameters are accepted."""
        response = client.get("/api/v1/upload/?page=1&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestUploadModels:
    """Tests for upload model validation."""

    def test_upload_file_type_enum(self):
        """Test UploadFileType enum values."""
        from backend.models.upload import UploadFileType

        assert UploadFileType.POSITIONS_CSV.value == "positions_csv"
        assert UploadFileType.POSITIONS_XLSX.value == "positions_xlsx"
        assert UploadFileType.TRADES_CSV.value == "trades_csv"
        assert UploadFileType.TRADES_XLSX.value == "trades_xlsx"
        assert UploadFileType.FIX_MESSAGE.value == "fix_message"

    def test_upload_status_enum(self):
        """Test UploadStatus enum values."""
        from backend.models.upload import UploadStatus

        assert UploadStatus.PENDING.value == "pending"
        assert UploadStatus.PROCESSING.value == "processing"
        assert UploadStatus.COMPLETED.value == "completed"
        assert UploadStatus.FAILED.value == "failed"
        assert UploadStatus.CANCELLED.value == "cancelled"

    def test_file_preview_response(self):
        """Test FilePreviewResponse model."""
        from backend.models.upload import FilePreviewResponse

        response = FilePreviewResponse(
            success=True,
            filename="test.csv",
            file_type="positions",
            columns=["ticker", "quantity"],
            mapping={"ticker": "ticker"},
            preview=[{"ticker": "AAPL", "quantity": "100"}],
            row_count=1,
        )

        assert response.success is True
        assert response.filename == "test.csv"
        assert response.row_count == 1

    def test_import_response(self):
        """Test ImportResponse model."""
        from backend.models.upload import ImportResponse

        response = ImportResponse(
            success=True,
            upload_id=uuid4(),
            records_total=10,
            records_processed=8,
            records_failed=2,
            message="Imported 8 positions, 2 failed",
        )

        assert response.success is True
        assert response.records_total == 10
        assert response.records_processed == 8
