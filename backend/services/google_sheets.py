# RISKCORE Google Sheets Service
# Fetch position/trade data from public Google Sheets
# On-premises processing - data fetched and stored locally only

import re
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Service for fetching data from public Google Sheets.

    Supports sheets that are shared as "Anyone with the link can view".
    Uses the Google Sheets API v4 export functionality for public sheets,
    which doesn't require authentication for read-only access.

    For private sheets, OAuth2 would be needed (Phase 2).
    """

    # Google Sheets export URL format
    EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export"

    # Alternative: Sheets API v4 (requires API key for higher rate limits)
    API_URL = "https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range}"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Sheets service.

        Args:
            api_key: Optional Google API key for higher rate limits.
                     Without API key, uses export URL (more limited).
        """
        self.api_key = api_key

    def extract_sheet_id(self, url_or_id: str) -> str:
        """
        Extract the sheet ID from a Google Sheets URL.

        Supports formats:
        - https://docs.google.com/spreadsheets/d/{id}/edit#gid=0
        - https://docs.google.com/spreadsheets/d/{id}/edit?usp=sharing
        - https://docs.google.com/spreadsheets/d/{id}
        - Just the ID itself

        Args:
            url_or_id: Google Sheets URL or direct ID

        Returns:
            The extracted sheet ID

        Raises:
            ValueError: If the URL format is not recognized
        """
        # Pattern to match sheet ID in URL
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',  # Standard URL format
            r'^([a-zA-Z0-9-_]{20,})$',  # Direct ID (typically 44 chars)
        ]

        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        raise ValueError(
            f"Could not extract sheet ID from: {url_or_id}. "
            "Please provide a valid Google Sheets URL or ID."
        )

    def extract_gid(self, url: str) -> Optional[int]:
        """
        Extract the sheet GID (tab identifier) from URL.

        Args:
            url: Google Sheets URL

        Returns:
            The GID as integer, or None if not specified
        """
        # Check for #gid= fragment
        if '#gid=' in url:
            match = re.search(r'#gid=(\d+)', url)
            if match:
                return int(match.group(1))

        # Check for ?gid= query param
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'gid' in params:
            return int(params['gid'][0])

        return None

    def fetch_sheet_data(
        self,
        url_or_id: str,
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch data from a public Google Sheet.

        Args:
            url_or_id: Google Sheets URL or ID
            sheet_name: Optional specific sheet/tab name

        Returns:
            Dict with:
            - success: bool
            - data: List of rows (each row is list of cell values)
            - columns: List of column headers (first row)
            - row_count: Number of data rows
            - error: Error message if failed
        """
        try:
            sheet_id = self.extract_sheet_id(url_or_id)
            gid = self.extract_gid(url_or_id) if '/' in url_or_id else None

            if self.api_key:
                return self._fetch_via_api(sheet_id, sheet_name)
            else:
                return self._fetch_via_export(sheet_id, gid, sheet_name)

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": [],
                "row_count": 0,
            }
        except Exception as e:
            logger.error(f"Error fetching Google Sheet: {e}")
            return {
                "success": False,
                "error": f"Failed to fetch sheet: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0,
            }

    def _fetch_via_export(
        self,
        sheet_id: str,
        gid: Optional[int] = None,
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch sheet data via CSV export (no API key needed).

        This works for public sheets without authentication.
        """
        import csv
        import io

        # Build export URL
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
        params = {"format": "csv"}

        if gid is not None:
            params["gid"] = gid
        elif sheet_name:
            # Can't specify sheet name directly with export, would need API
            pass

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Check if we got HTML (access denied) instead of CSV
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                return {
                    "success": False,
                    "error": "Sheet is not publicly accessible. Please set sharing to 'Anyone with the link can view'.",
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                }

            # Parse CSV
            text = response.text
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if not rows:
                return {
                    "success": False,
                    "error": "Sheet is empty",
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                }

            # First row is headers
            columns = rows[0]
            data_rows = rows[1:]

            # Convert to list of dicts
            data = []
            for row in data_rows:
                # Pad row to match column count
                padded_row = row + [''] * (len(columns) - len(row))
                row_dict = {col: val for col, val in zip(columns, padded_row)}
                data.append(row_dict)

            return {
                "success": True,
                "error": None,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "sheet_id": sheet_id,
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error = "Sheet not found. Please check the URL."
            elif e.response.status_code == 403:
                error = "Access denied. Please make sure the sheet is shared publicly."
            else:
                error = f"HTTP error: {e.response.status_code}"

            return {
                "success": False,
                "error": error,
                "data": [],
                "columns": [],
                "row_count": 0,
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out. Please try again.",
                "data": [],
                "columns": [],
                "row_count": 0,
            }

    def _fetch_via_api(
        self,
        sheet_id: str,
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch sheet data via Google Sheets API v4.

        Requires API key but provides more features and higher rate limits.
        """
        # Build range (default to all data in first sheet)
        range_str = f"'{sheet_name}'!A:ZZ" if sheet_name else "A:ZZ"

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_str}"
        params = {
            "key": self.api_key,
            "majorDimension": "ROWS",
            "valueRenderOption": "UNFORMATTED_VALUE",
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            rows = result.get("values", [])

            if not rows:
                return {
                    "success": False,
                    "error": "Sheet is empty",
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                }

            # First row is headers
            columns = [str(c) for c in rows[0]]
            data_rows = rows[1:]

            # Convert to list of dicts
            data = []
            for row in data_rows:
                # Pad row to match column count
                padded_row = list(row) + [''] * (len(columns) - len(row))
                row_dict = {col: str(val) if val is not None else '' for col, val in zip(columns, padded_row)}
                data.append(row_dict)

            return {
                "success": True,
                "error": None,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "sheet_id": sheet_id,
            }

        except requests.exceptions.HTTPError as e:
            error_body = e.response.json() if e.response.content else {}
            error_msg = error_body.get("error", {}).get("message", str(e))

            return {
                "success": False,
                "error": f"API error: {error_msg}",
                "data": [],
                "columns": [],
                "row_count": 0,
            }


def get_sheets_service(api_key: Optional[str] = None) -> GoogleSheetsService:
    """Factory function to create GoogleSheetsService."""
    return GoogleSheetsService(api_key=api_key)
