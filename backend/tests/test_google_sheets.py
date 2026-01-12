# RISKCORE Google Sheets Service Tests

import pytest
from unittest.mock import patch, MagicMock

from backend.services.google_sheets import GoogleSheetsService, get_sheets_service


class TestGoogleSheetsService:
    """Tests for GoogleSheetsService."""

    def test_extract_sheet_id_standard_url(self):
        """Test extracting sheet ID from standard Google Sheets URL."""
        service = GoogleSheetsService()

        # Standard edit URL
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        assert service.extract_sheet_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_extract_sheet_id_with_gid(self):
        """Test extracting sheet ID from URL with gid parameter."""
        service = GoogleSheetsService()

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123456"
        assert service.extract_sheet_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_extract_sheet_id_sharing_url(self):
        """Test extracting sheet ID from sharing URL."""
        service = GoogleSheetsService()

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        assert service.extract_sheet_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_extract_sheet_id_direct_id(self):
        """Test passing sheet ID directly."""
        service = GoogleSheetsService()

        sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        assert service.extract_sheet_id(sheet_id) == sheet_id

    def test_extract_sheet_id_invalid_url(self):
        """Test error on invalid URL."""
        service = GoogleSheetsService()

        with pytest.raises(ValueError) as excinfo:
            service.extract_sheet_id("https://example.com/not-a-sheet")

        assert "Could not extract sheet ID" in str(excinfo.value)

    def test_extract_gid_from_fragment(self):
        """Test extracting GID from URL fragment."""
        service = GoogleSheetsService()

        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=456"
        assert service.extract_gid(url) == 456

    def test_extract_gid_from_query_param(self):
        """Test extracting GID from query parameter."""
        service = GoogleSheetsService()

        url = "https://docs.google.com/spreadsheets/d/abc123/edit?gid=789"
        assert service.extract_gid(url) == 789

    def test_extract_gid_none_when_missing(self):
        """Test None returned when no GID in URL."""
        service = GoogleSheetsService()

        url = "https://docs.google.com/spreadsheets/d/abc123/edit"
        assert service.extract_gid(url) is None

    @patch('backend.services.google_sheets.requests.get')
    def test_fetch_sheet_data_success(self, mock_get):
        """Test successful sheet data fetch."""
        # Mock CSV response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/csv'}
        mock_response.text = "ticker,quantity,price\nAAPL,100,150.00\nGOOG,50,2800.00"
        mock_get.return_value = mock_response

        service = GoogleSheetsService()
        result = service.fetch_sheet_data("https://docs.google.com/spreadsheets/d/test123/edit")

        assert result["success"] is True
        assert result["columns"] == ["ticker", "quantity", "price"]
        assert result["row_count"] == 2
        assert len(result["data"]) == 2
        assert result["data"][0]["ticker"] == "AAPL"
        assert result["data"][0]["quantity"] == "100"
        assert result["data"][1]["ticker"] == "GOOG"

    @patch('backend.services.google_sheets.requests.get')
    def test_fetch_sheet_data_not_public(self, mock_get):
        """Test error when sheet is not publicly accessible."""
        # Mock HTML response (access denied page)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = "<html>Sign in required</html>"
        mock_get.return_value = mock_response

        service = GoogleSheetsService()
        result = service.fetch_sheet_data("https://docs.google.com/spreadsheets/d/private123/edit")

        assert result["success"] is False
        assert "not publicly accessible" in result["error"]

    @patch('backend.services.google_sheets.requests.get')
    def test_fetch_sheet_data_empty_sheet(self, mock_get):
        """Test error when sheet is empty."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/csv'}
        mock_response.text = ""
        mock_get.return_value = mock_response

        service = GoogleSheetsService()
        result = service.fetch_sheet_data("https://docs.google.com/spreadsheets/d/empty123/edit")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    @patch('backend.services.google_sheets.requests.get')
    def test_fetch_sheet_data_404(self, mock_get):
        """Test error when sheet not found."""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        service = GoogleSheetsService()
        result = service.fetch_sheet_data("https://docs.google.com/spreadsheets/d/notfound/edit")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch('backend.services.google_sheets.requests.get')
    def test_fetch_sheet_data_timeout(self, mock_get):
        """Test error on request timeout."""
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout()

        service = GoogleSheetsService()
        result = service.fetch_sheet_data("https://docs.google.com/spreadsheets/d/slow/edit")

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    def test_get_sheets_service_factory(self):
        """Test factory function creates service."""
        service = get_sheets_service()
        assert isinstance(service, GoogleSheetsService)
        assert service.api_key is None

    def test_get_sheets_service_with_api_key(self):
        """Test factory function with API key."""
        service = get_sheets_service(api_key="test-api-key")
        assert isinstance(service, GoogleSheetsService)
        assert service.api_key == "test-api-key"


class TestGoogleSheetsAPI:
    """Tests for Google Sheets API endpoints."""

    def test_preview_endpoint_exists(self):
        """Test that preview endpoint is registered."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        # Just check the endpoint exists (OPTIONS request)
        response = client.options("/api/v1/upload/google-sheets/preview")
        assert response.status_code in [200, 405]  # 405 = method not allowed but route exists

    def test_import_endpoint_exists(self):
        """Test that import endpoint is registered."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.options("/api/v1/upload/google-sheets/import")
        assert response.status_code in [200, 405]

    def test_validate_endpoint_exists(self):
        """Test that validate endpoint is registered."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.options("/api/v1/upload/google-sheets/validate")
        assert response.status_code in [200, 405]

    @patch('backend.api.upload.GoogleSheetsService')
    def test_preview_invalid_file_type(self, mock_service_class):
        """Test preview rejects invalid file type."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/upload/google-sheets/preview",
            json={
                "url": "https://docs.google.com/spreadsheets/d/test/edit",
                "file_type": "invalid"
            }
        )

        assert response.status_code == 400
        assert "positions" in response.json()["detail"] or "trades" in response.json()["detail"]

    @patch('backend.api.upload.GoogleSheetsService')
    def test_preview_returns_column_mapping(self, mock_service_class):
        """Test preview returns auto-detected column mapping."""
        from fastapi.testclient import TestClient
        from backend.main import app

        # Mock the service
        mock_service = MagicMock()
        mock_service.fetch_sheet_data.return_value = {
            "success": True,
            "error": None,
            "data": [
                {"Symbol": "AAPL", "Qty": "100", "Price": "150.00"},
                {"Symbol": "GOOG", "Qty": "50", "Price": "2800.00"},
            ],
            "columns": ["Symbol", "Qty", "Price"],
            "row_count": 2,
            "sheet_id": "test123",
        }
        mock_service_class.return_value = mock_service

        client = TestClient(app)
        response = client.post(
            "/api/v1/upload/google-sheets/preview",
            json={
                "url": "https://docs.google.com/spreadsheets/d/test123/edit",
                "file_type": "positions"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ticker" in data["mapping"]  # Symbol -> ticker
        assert "quantity" in data["mapping"]  # Qty -> quantity
        assert "price" in data["mapping"]  # Price -> price

    @patch('backend.api.upload.GoogleSheetsService')
    def test_validate_valid_url(self, mock_service_class):
        """Test validate endpoint with valid URL."""
        from fastapi.testclient import TestClient
        from backend.main import app

        mock_service = MagicMock()
        mock_service.extract_sheet_id.return_value = "test123"
        mock_service.fetch_sheet_data.return_value = {
            "success": True,
            "row_count": 10,
            "columns": ["A", "B", "C"],
        }
        mock_service_class.return_value = mock_service

        client = TestClient(app)
        response = client.get(
            "/api/v1/upload/google-sheets/validate",
            params={"url": "https://docs.google.com/spreadsheets/d/test123/edit"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid_url"] is True
        assert data["accessible"] is True
        assert data["sheet_id"] == "test123"
