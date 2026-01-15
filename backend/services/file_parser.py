# RISKCORE File Parser Service
# CSV/Excel parsing with column auto-detection
# On-premises - files processed locally, never sent to cloud

import io
import csv
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


# Column mapping patterns for auto-detection
COLUMN_PATTERNS = {
    # Position fields
    "ticker": [r"^ticker$", r"^symbol$", r"^stock$", r"^security$", r"^sec$"],
    "cusip": [r"^cusip$", r"^cusip.?id$"],
    "isin": [r"^isin$", r"^isin.?code$"],
    "sedol": [r"^sedol$", r"^sedol.?code$"],
    "quantity": [r"^qty$", r"^quantity$", r"^shares$", r"^units$", r"^position$", r"^size$"],
    "price": [r"^price$", r"^px$", r"^last.?price$", r"^market.?price$", r"^close$"],
    "direction": [r"^direction$", r"^side$", r"^long.?short$", r"^l.?s$", r"^pos.?type$"],
    "cost_basis": [r"^cost.?basis$", r"^cost$", r"^avg.?cost$", r"^average.?cost$"],
    "market_value": [r"^market.?value$", r"^mv$", r"^value$", r"^notional$"],
    "currency": [r"^currency$", r"^ccy$", r"^curr$"],
    "book": [r"^book$", r"^portfolio$", r"^account$", r"^fund$", r"^strategy$"],
    "as_of_date": [r"^as.?of.?date$", r"^date$", r"^position.?date$", r"^trade.?date$", r"^value.?date$"],

    # Instrument type (for normalization)
    "instrument_type": [
        r"^instrument.?type$", r"^product.?type$", r"^security.?type$",
        r"^type$", r"^product$", r"^asset.?type$", r"^asset.?class$",
        r"^inst.?type$", r"^sec.?type$", r"^instr.?type$",
    ],

    # Trade-specific fields
    "trade_date": [r"^trade.?date$", r"^exec.?date$", r"^execution.?date$"],
    "settlement_date": [r"^settle.?date$", r"^settlement.?date$", r"^settl.?date$"],
    "trade_time": [r"^trade.?time$", r"^exec.?time$", r"^time$"],
    "broker": [r"^broker$", r"^executing.?broker$", r"^exec.?broker$"],
    "counterparty": [r"^counterparty$", r"^cpty$", r"^counter.?party$"],
    "commission": [r"^commission$", r"^comm$", r"^commissions$"],
    "fees": [r"^fees$", r"^fee$", r"^other.?fees$"],
    "trade_id": [r"^trade.?id$", r"^exec.?id$", r"^execution.?id$", r"^order.?id$"],
}

# Direction value mappings
DIRECTION_MAPPINGS = {
    # Long
    "long": "long", "l": "long", "buy": "long", "b": "long", "1": "long", "+": "long",
    # Short
    "short": "short", "s": "short", "sell": "short", "ss": "short", "-1": "short", "-": "short",
    # Flat
    "flat": "flat", "f": "flat", "0": "flat", "none": "flat",
}

# Trade side mappings
SIDE_MAPPINGS = {
    "buy": "buy", "b": "buy", "bought": "buy", "long": "buy",
    "sell": "sell", "s": "sell", "sold": "sell",
    "short": "short", "ss": "short", "short sell": "short",
    "cover": "cover", "c": "cover", "buy to cover": "cover", "bc": "cover",
}


class FileParser:
    """
    Parser for CSV and Excel files with column auto-detection.

    All processing happens locally - files never leave the on-premises server.
    """

    def __init__(self):
        self.supported_extensions = [".csv", ".xlsx", ".xls"]

    def parse_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str = "positions",
    ) -> Dict[str, Any]:
        """
        Parse a file and return structured data with column mapping.

        Args:
            file_content: Raw file bytes
            filename: Original filename (for extension detection)
            file_type: 'positions' or 'trades'

        Returns:
            Dict with:
            - data: List of parsed rows
            - columns: List of column names from file
            - mapping: Auto-detected column mapping
            - preview: First 10 rows for user confirmation
            - row_count: Total number of data rows
            - errors: Any parsing errors
        """
        extension = self._get_extension(filename)

        if extension not in self.supported_extensions:
            return {
                "success": False,
                "error": f"Unsupported file type: {extension}. Supported: {', '.join(self.supported_extensions)}",
                "data": [],
                "columns": [],
                "mapping": {},
                "preview": [],
                "row_count": 0,
            }

        try:
            # Parse based on extension
            if extension == ".csv":
                df = self._parse_csv(file_content)
            else:
                df = self._parse_excel(file_content)

            if df.empty:
                return {
                    "success": False,
                    "error": "File is empty or contains no data rows",
                    "data": [],
                    "columns": [],
                    "mapping": {},
                    "preview": [],
                    "row_count": 0,
                }

            # Clean column names
            df.columns = [self._clean_column_name(col) for col in df.columns]
            columns = list(df.columns)

            # Auto-detect column mapping
            mapping = self._auto_detect_columns(columns, file_type)

            # Convert to list of dicts
            data = df.to_dict(orient="records")

            # Create preview (first 10 rows)
            preview = data[:10]

            return {
                "success": True,
                "error": None,
                "data": data,
                "columns": columns,
                "mapping": mapping,
                "preview": preview,
                "row_count": len(data),
                "unmapped_columns": [c for c in columns if c not in mapping.values()],
            }

        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
            return {
                "success": False,
                "error": f"Failed to parse file: {str(e)}",
                "data": [],
                "columns": [],
                "mapping": {},
                "preview": [],
                "row_count": 0,
            }

    def _parse_csv(self, content: bytes) -> pd.DataFrame:
        """Parse CSV content."""
        # Try different encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Could not decode file with any supported encoding")

        # Detect delimiter
        sample = text[:4096]
        delimiter = self._detect_delimiter(sample)

        return pd.read_csv(
            io.StringIO(text),
            delimiter=delimiter,
            dtype=str,  # Read all as strings initially
            na_values=["", "NA", "N/A", "NULL", "null", "None", "none"],
        )

    def _parse_excel(self, content: bytes) -> pd.DataFrame:
        """Parse Excel content."""
        return pd.read_excel(
            io.BytesIO(content),
            dtype=str,
            na_values=["", "NA", "N/A", "NULL", "null", "None", "none"],
        )

    def _detect_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter from sample."""
        delimiters = [",", "\t", ";", "|"]
        counts = {d: sample.count(d) for d in delimiters}
        return max(counts, key=counts.get)

    def _clean_column_name(self, name: str) -> str:
        """Clean and normalize column name."""
        if not isinstance(name, str):
            name = str(name)
        # Remove leading/trailing whitespace
        name = name.strip()
        # Replace multiple spaces with single underscore
        name = re.sub(r"\s+", "_", name)
        # Convert to lowercase
        name = name.lower()
        return name

    def _auto_detect_columns(
        self,
        columns: List[str],
        file_type: str,
    ) -> Dict[str, str]:
        """
        Auto-detect column mapping based on patterns.

        Returns dict of {target_field: source_column}
        """
        mapping = {}
        used_columns = set()

        for target_field, patterns in COLUMN_PATTERNS.items():
            for col in columns:
                if col in used_columns:
                    continue

                col_lower = col.lower().replace("_", " ").replace("-", " ")

                for pattern in patterns:
                    if re.match(pattern, col_lower, re.IGNORECASE):
                        mapping[target_field] = col
                        used_columns.add(col)
                        break

                if target_field in mapping:
                    break

        return mapping

    def _get_extension(self, filename: str) -> str:
        """Get lowercase file extension."""
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", 1)[-1].lower()

    def transform_rows(
        self,
        data: List[Dict[str, Any]],
        mapping: Dict[str, str],
        file_type: str,
        tenant_id: str,
        book_id: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Transform parsed rows using column mapping.

        Args:
            data: Parsed rows from file
            mapping: Column mapping {target_field: source_column}
            file_type: 'positions' or 'trades'
            tenant_id: Tenant UUID
            book_id: Target book UUID

        Returns:
            Tuple of (valid_rows, error_rows)
        """
        valid_rows = []
        error_rows = []

        for i, row in enumerate(data):
            try:
                transformed = self._transform_row(row, mapping, file_type, tenant_id, book_id)
                if transformed:
                    valid_rows.append(transformed)
            except Exception as e:
                error_rows.append({
                    "row_number": i + 1,
                    "error": str(e),
                    "data": row,
                })

        return valid_rows, error_rows

    def _transform_row(
        self,
        row: Dict[str, Any],
        mapping: Dict[str, str],
        file_type: str,
        tenant_id: str,
        book_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Transform a single row."""
        result = {
            "tenant_id": tenant_id,
            "book_id": book_id,
            "source": "file_upload",
        }

        # Extract mapped fields
        for target_field, source_col in mapping.items():
            if source_col in row and row[source_col] is not None:
                value = row[source_col]
                if pd.isna(value):
                    continue
                result[target_field] = self._convert_value(target_field, str(value).strip())

        # Validate required fields
        if file_type == "positions":
            # Need at least one identifier
            has_identifier = any(
                result.get(f) for f in ["ticker", "cusip", "isin", "sedol", "security_id"]
            )
            if not has_identifier:
                raise ValueError("No security identifier found (ticker, cusip, isin, or sedol)")

            # Need quantity
            if "quantity" not in result:
                raise ValueError("Quantity is required")

            # Default direction
            if "direction" not in result:
                qty = result.get("quantity", 0)
                result["direction"] = "short" if qty < 0 else "long"

            # Default as_of_timestamp
            if "as_of_date" not in result:
                result["as_of_timestamp"] = datetime.utcnow().isoformat()
            else:
                result["as_of_timestamp"] = result.pop("as_of_date")

        elif file_type == "trades":
            # Need identifier
            has_identifier = any(
                result.get(f) for f in ["ticker", "cusip", "isin", "sedol", "security_id"]
            )
            if not has_identifier:
                raise ValueError("No security identifier found")

            # Need quantity, price, side
            for field in ["quantity", "price"]:
                if field not in result:
                    raise ValueError(f"{field} is required")

            # Map direction to side for trades
            if "direction" in result and "side" not in result:
                result["side"] = self._map_to_side(result.pop("direction"))
            elif "side" not in result:
                raise ValueError("Trade side is required (buy/sell/short/cover)")

            # Need trade_date
            if "trade_date" not in result:
                result["trade_date"] = date.today().isoformat()

            # Default currency
            if "currency" not in result:
                result["currency"] = "USD"

        return result

    def _convert_value(self, field: str, value: str) -> Any:
        """Convert string value to appropriate type."""
        if not value:
            return None

        # Numeric fields
        if field in ["quantity", "price", "cost_basis", "market_value", "commission", "fees"]:
            # Remove currency symbols and commas
            cleaned = re.sub(r"[$€£¥,]", "", value)
            # Handle parentheses as negative
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1]
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                raise ValueError(f"Invalid number for {field}: {value}")

        # Direction
        if field == "direction":
            return self._map_direction(value)

        # Side (for trades)
        if field == "side":
            return self._map_to_side(value)

        # Date fields
        if field in ["as_of_date", "trade_date", "settlement_date"]:
            return self._parse_date(value)

        # Time fields
        if field == "trade_time":
            return self._parse_time(value)

        # Currency (uppercase)
        if field == "currency":
            return value.upper()[:3]

        # Default: return as-is
        return value

    def _map_direction(self, value: str) -> str:
        """Map direction value to standard."""
        normalized = value.lower().strip()
        if normalized in DIRECTION_MAPPINGS:
            return DIRECTION_MAPPINGS[normalized]
        raise ValueError(f"Unknown direction: {value}")

    def _map_to_side(self, value: str) -> str:
        """Map trade side value to standard."""
        normalized = value.lower().strip()
        if normalized in SIDE_MAPPINGS:
            return SIDE_MAPPINGS[normalized]
        raise ValueError(f"Unknown trade side: {value}")

    def _parse_date(self, value: str) -> str:
        """Parse date string to ISO format."""
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
            "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y",
            "%Y%m%d", "%d %b %Y", "%d %B %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {value}")

    def _parse_time(self, value: str) -> str:
        """Parse time string to ISO format."""
        formats = [
            "%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.time().isoformat()
            except ValueError:
                continue

        return value  # Return as-is if can't parse
