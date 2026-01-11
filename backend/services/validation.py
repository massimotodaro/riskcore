"""
RISKCORE Data Validation Pipeline

Validates incoming data (positions, trades, securities, prices) against
configurable rules stored in the validation_rules table.

Rule types:
- schema: Required fields, data types, patterns
- range: Min/max numeric bounds
- referential: Foreign key existence checks
- business: Custom business logic (trade dates, etc.)
- custom: SQL-based custom validations
"""

import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor, Json


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleType(Enum):
    SCHEMA = "schema"
    RANGE = "range"
    REFERENTIAL = "referential"
    BUSINESS = "business"
    CUSTOM = "custom"


class ValidationResult:
    """A single validation result (error, warning, or info)."""

    def __init__(
        self,
        severity: Severity,
        error_code: str,
        error_message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        expected_value: Optional[str] = None,
        record_identifier: Optional[Dict] = None,
        rule_id: Optional[uuid.UUID] = None,
    ):
        self.severity = severity
        self.error_code = error_code
        self.error_message = error_message
        self.field_name = field_name
        self.field_value = str(field_value) if field_value is not None else None
        self.expected_value = expected_value
        self.record_identifier = record_identifier
        self.rule_id = rule_id

    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "expected_value": self.expected_value,
            "record_identifier": self.record_identifier,
            "rule_id": str(self.rule_id) if self.rule_id else None,
        }

    def __repr__(self):
        return f"ValidationResult({self.severity.value}: {self.error_code} - {self.error_message})"


class ValidationSummary:
    """Summary of validation results for a batch of records."""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.records_validated = 0
        self.records_failed = 0

    def add_result(self, result: ValidationResult):
        self.results.append(result)
        if result.severity == Severity.ERROR:
            self.error_count += 1
        elif result.severity == Severity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    def is_valid(self) -> bool:
        """Returns True if no errors (warnings/info are OK)."""
        return self.error_count == 0

    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid(),
            "records_validated": self.records_validated,
            "records_failed": self.records_failed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "results": [r.to_dict() for r in self.results],
        }


class ValidationRule:
    """A validation rule loaded from the database."""

    def __init__(self, row: Dict):
        self.id = row["id"]
        self.tenant_id = row.get("tenant_id")
        self.name = row["name"]
        self.description = row.get("description")
        self.rule_type = RuleType(row["rule_type"])
        self.target_table = row["target_table"]
        self.target_column = row.get("target_column")
        self.rule_config = row["rule_config"]
        self.severity = Severity(row["severity"])
        self.is_active = row.get("is_active", True)

    def __repr__(self):
        return f"ValidationRule({self.name}, {self.rule_type.value}, {self.target_table}.{self.target_column})"


class DataValidator:
    """
    Main validation service. Loads rules from database and validates data.

    Usage:
        validator = DataValidator(conn, tenant_id)
        summary = validator.validate_positions(positions_data)
        if not summary.is_valid():
            # Handle errors
            for result in summary.results:
                print(result)
    """

    def __init__(self, conn, tenant_id: uuid.UUID):
        """
        Initialize validator with database connection and tenant context.

        Args:
            conn: psycopg2 connection
            tenant_id: Current tenant UUID for RLS and tenant-specific rules
        """
        self.conn = conn
        self.tenant_id = tenant_id
        self._rules_cache: Dict[str, List[ValidationRule]] = {}
        self._load_rules()

    def _load_rules(self):
        """Load all active validation rules for this tenant."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Load system rules (tenant_id IS NULL) and tenant-specific rules
            cur.execute("""
                SELECT *
                FROM validation_rules
                WHERE is_active = TRUE
                  AND (tenant_id IS NULL OR tenant_id = %s)
                ORDER BY target_table, name
            """, (str(self.tenant_id),))

            rows = cur.fetchall()

            # Group rules by target table
            for row in rows:
                rule = ValidationRule(row)
                table = rule.target_table
                if table not in self._rules_cache:
                    self._rules_cache[table] = []
                self._rules_cache[table].append(rule)

    def get_rules_for_table(self, table: str) -> List[ValidationRule]:
        """Get all active rules for a specific table."""
        return self._rules_cache.get(table, [])

    def _validate_schema_rule(
        self,
        rule: ValidationRule,
        value: Any,
        record_id: Dict
    ) -> Optional[ValidationResult]:
        """Validate schema rules (required, type, pattern, length)."""
        config = rule.rule_config
        column = rule.target_column

        # Required check
        if config.get("required", False):
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return ValidationResult(
                    severity=rule.severity,
                    error_code="REQUIRED_FIELD",
                    error_message=f"{column} is required",
                    field_name=column,
                    field_value=value,
                    expected_value="non-empty value",
                    record_identifier=record_id,
                    rule_id=rule.id,
                )

        # Skip other checks if value is None and not required
        if value is None:
            return None

        # Type check
        expected_type = config.get("type")
        if expected_type:
            if expected_type == "numeric":
                try:
                    if not isinstance(value, (int, float, Decimal)):
                        Decimal(str(value))
                except (InvalidOperation, ValueError):
                    return ValidationResult(
                        severity=rule.severity,
                        error_code="INVALID_TYPE",
                        error_message=f"{column} must be a number",
                        field_name=column,
                        field_value=value,
                        expected_value="numeric value",
                        record_identifier=record_id,
                        rule_id=rule.id,
                    )
            elif expected_type == "date":
                if not isinstance(value, (date, datetime)):
                    try:
                        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    except ValueError:
                        return ValidationResult(
                            severity=rule.severity,
                            error_code="INVALID_TYPE",
                            error_message=f"{column} must be a valid date",
                            field_name=column,
                            field_value=value,
                            expected_value="date (YYYY-MM-DD)",
                            record_identifier=record_id,
                            rule_id=rule.id,
                        )
            elif expected_type == "uuid":
                try:
                    uuid.UUID(str(value))
                except ValueError:
                    return ValidationResult(
                        severity=rule.severity,
                        error_code="INVALID_TYPE",
                        error_message=f"{column} must be a valid UUID",
                        field_name=column,
                        field_value=value,
                        expected_value="UUID format",
                        record_identifier=record_id,
                        rule_id=rule.id,
                    )

        # Pattern (regex) check
        pattern = config.get("pattern")
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                return ValidationResult(
                    severity=rule.severity,
                    error_code="PATTERN_MISMATCH",
                    error_message=f"{column} does not match required format",
                    field_name=column,
                    field_value=value,
                    expected_value=f"pattern: {pattern}",
                    record_identifier=record_id,
                    rule_id=rule.id,
                )

        # Length checks
        min_length = config.get("minLength")
        max_length = config.get("maxLength")
        if isinstance(value, str):
            if min_length and len(value) < min_length:
                return ValidationResult(
                    severity=rule.severity,
                    error_code="TOO_SHORT",
                    error_message=f"{column} must be at least {min_length} characters",
                    field_name=column,
                    field_value=value,
                    expected_value=f">= {min_length} chars",
                    record_identifier=record_id,
                    rule_id=rule.id,
                )
            if max_length and len(value) > max_length:
                return ValidationResult(
                    severity=rule.severity,
                    error_code="TOO_LONG",
                    error_message=f"{column} must be at most {max_length} characters",
                    field_name=column,
                    field_value=value,
                    expected_value=f"<= {max_length} chars",
                    record_identifier=record_id,
                    rule_id=rule.id,
                )

        return None

    def _validate_range_rule(
        self,
        rule: ValidationRule,
        value: Any,
        record_id: Dict
    ) -> Optional[ValidationResult]:
        """Validate range rules (min/max numeric bounds)."""
        if value is None:
            return None

        config = rule.rule_config
        column = rule.target_column

        try:
            num_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return ValidationResult(
                severity=rule.severity,
                error_code="INVALID_TYPE",
                error_message=f"{column} must be numeric for range check",
                field_name=column,
                field_value=value,
                expected_value="numeric value",
                record_identifier=record_id,
                rule_id=rule.id,
            )

        min_val = config.get("min")
        max_val = config.get("max")

        if min_val is not None and num_value < Decimal(str(min_val)):
            return ValidationResult(
                severity=rule.severity,
                error_code="BELOW_MINIMUM",
                error_message=f"{column} must be >= {min_val}",
                field_name=column,
                field_value=value,
                expected_value=f">= {min_val}",
                record_identifier=record_id,
                rule_id=rule.id,
            )

        if max_val is not None and num_value > Decimal(str(max_val)):
            return ValidationResult(
                severity=rule.severity,
                error_code="ABOVE_MAXIMUM",
                error_message=f"{column} must be <= {max_val}",
                field_name=column,
                field_value=value,
                expected_value=f"<= {max_val}",
                record_identifier=record_id,
                rule_id=rule.id,
            )

        return None

    def _validate_referential_rule(
        self,
        rule: ValidationRule,
        value: Any,
        record_id: Dict
    ) -> Optional[ValidationResult]:
        """Validate referential rules (foreign key existence)."""
        if value is None:
            return None

        config = rule.rule_config
        column = rule.target_column
        ref_table = config.get("table")
        ref_column = config.get("column", "id")

        if not ref_table:
            return None

        with self.conn.cursor() as cur:
            # Check if the referenced table has a tenant_id column
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                      AND column_name = 'tenant_id'
                )
            """, (ref_table,))
            has_tenant_id = cur.fetchone()[0]

            # Check if referenced record exists
            if has_tenant_id:
                cur.execute(f"""
                    SELECT EXISTS(
                        SELECT 1 FROM {ref_table}
                        WHERE {ref_column} = %s
                        AND (tenant_id IS NULL OR tenant_id = %s)
                    )
                """, (str(value), str(self.tenant_id)))
            else:
                cur.execute(f"""
                    SELECT EXISTS(
                        SELECT 1 FROM {ref_table}
                        WHERE {ref_column} = %s
                    )
                """, (str(value),))

            exists = cur.fetchone()[0]

            if not exists:
                return ValidationResult(
                    severity=rule.severity,
                    error_code="INVALID_REFERENCE",
                    error_message=f"{column} references non-existent {ref_table}.{ref_column}",
                    field_name=column,
                    field_value=value,
                    expected_value=f"valid {ref_table} {ref_column}",
                    record_identifier=record_id,
                    rule_id=rule.id,
                )

        return None

    def _validate_business_rule(
        self,
        rule: ValidationRule,
        value: Any,
        record_id: Dict,
        record: Dict
    ) -> Optional[ValidationResult]:
        """Validate business rules (custom logic)."""
        if value is None:
            return None

        config = rule.rule_config
        column = rule.target_column

        # "max": "today" - date cannot be in future
        if config.get("max") == "today":
            try:
                if isinstance(value, str):
                    check_date = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
                elif isinstance(value, datetime):
                    check_date = value.date()
                elif isinstance(value, date):
                    check_date = value
                else:
                    check_date = None

                if check_date and check_date > date.today():
                    return ValidationResult(
                        severity=rule.severity,
                        error_code="FUTURE_DATE",
                        error_message=f"{column} cannot be in the future",
                        field_name=column,
                        field_value=value,
                        expected_value=f"<= {date.today()}",
                        record_identifier=record_id,
                        rule_id=rule.id,
                    )
            except (ValueError, AttributeError):
                pass

        return None

    def _validate_record(
        self,
        table: str,
        record: Dict,
        record_identifier: Dict
    ) -> List[ValidationResult]:
        """Validate a single record against all rules for its table."""
        results = []
        rules = self.get_rules_for_table(table)

        for rule in rules:
            column = rule.target_column
            value = record.get(column) if column else None
            result = None

            if rule.rule_type == RuleType.SCHEMA:
                result = self._validate_schema_rule(rule, value, record_identifier)
            elif rule.rule_type == RuleType.RANGE:
                result = self._validate_range_rule(rule, value, record_identifier)
            elif rule.rule_type == RuleType.REFERENTIAL:
                result = self._validate_referential_rule(rule, value, record_identifier)
            elif rule.rule_type == RuleType.BUSINESS:
                result = self._validate_business_rule(rule, value, record_identifier, record)

            if result:
                results.append(result)

        return results

    def validate_positions(
        self,
        positions: List[Dict],
        source_type: str = "upload",
        source_reference: Optional[str] = None
    ) -> ValidationSummary:
        """
        Validate a list of position records.

        Args:
            positions: List of position dictionaries
            source_type: 'upload', 'api', 'fix', 'manual'
            source_reference: Optional reference (filename, API request ID, etc.)

        Returns:
            ValidationSummary with all results
        """
        summary = ValidationSummary()
        summary.records_validated = len(positions)
        failed_records = set()

        for i, position in enumerate(positions):
            record_id = {
                "row": i + 1,
                "security": position.get("security_id") or position.get("ticker"),
                "book": position.get("book_id") or position.get("book_name"),
            }

            results = self._validate_record("positions", position, record_id)
            for result in results:
                summary.add_result(result)
                if result.severity == Severity.ERROR:
                    failed_records.add(i)

        summary.records_failed = len(failed_records)
        return summary

    def validate_trades(
        self,
        trades: List[Dict],
        source_type: str = "upload",
        source_reference: Optional[str] = None
    ) -> ValidationSummary:
        """Validate a list of trade records."""
        summary = ValidationSummary()
        summary.records_validated = len(trades)
        failed_records = set()

        for i, trade in enumerate(trades):
            record_id = {
                "row": i + 1,
                "trade_id": trade.get("id") or trade.get("external_id"),
                "security": trade.get("security_id") or trade.get("ticker"),
            }

            results = self._validate_record("trades", trade, record_id)
            for result in results:
                summary.add_result(result)
                if result.severity == Severity.ERROR:
                    failed_records.add(i)

        summary.records_failed = len(failed_records)
        return summary

    def validate_securities(
        self,
        securities: List[Dict],
        source_type: str = "upload",
        source_reference: Optional[str] = None
    ) -> ValidationSummary:
        """Validate a list of security records."""
        summary = ValidationSummary()
        summary.records_validated = len(securities)
        failed_records = set()

        for i, security in enumerate(securities):
            record_id = {
                "row": i + 1,
                "name": security.get("name"),
                "ticker": security.get("ticker"),
            }

            results = self._validate_record("securities", security, record_id)
            for result in results:
                summary.add_result(result)
                if result.severity == Severity.ERROR:
                    failed_records.add(i)

        summary.records_failed = len(failed_records)
        return summary

    def validate_prices(
        self,
        prices: List[Dict],
        source_type: str = "upload",
        source_reference: Optional[str] = None
    ) -> ValidationSummary:
        """Validate a list of price records."""
        summary = ValidationSummary()
        summary.records_validated = len(prices)
        failed_records = set()

        for i, price in enumerate(prices):
            record_id = {
                "row": i + 1,
                "security": price.get("security_id") or price.get("ticker"),
                "date": str(price.get("price_date")),
            }

            results = self._validate_record("security_prices", price, record_id)
            for result in results:
                summary.add_result(result)
                if result.severity == Severity.ERROR:
                    failed_records.add(i)

        summary.records_failed = len(failed_records)
        return summary

    def save_results(
        self,
        summary: ValidationSummary,
        upload_id: Optional[uuid.UUID] = None,
        source_type: str = "upload",
        source_reference: Optional[str] = None
    ) -> int:
        """
        Save validation results to the database.

        Returns:
            Number of results saved
        """
        if not summary.results:
            return 0

        with self.conn.cursor() as cur:
            for result in summary.results:
                cur.execute("""
                    INSERT INTO validation_results (
                        tenant_id, rule_id, upload_id, source_type, source_reference,
                        record_identifier, severity, error_code, error_message,
                        field_name, field_value, expected_value
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    str(self.tenant_id),
                    str(result.rule_id) if result.rule_id else None,
                    str(upload_id) if upload_id else None,
                    source_type,
                    source_reference,
                    Json(result.record_identifier),
                    result.severity.value,
                    result.error_code,
                    result.error_message,
                    result.field_name,
                    result.field_value,
                    result.expected_value,
                ))

            self.conn.commit()

        return len(summary.results)

    def get_unresolved_errors(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """Get unresolved validation errors for this tenant."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT vr.*, r.name as rule_name
                FROM validation_results vr
                LEFT JOIN validation_rules r ON vr.rule_id = r.id
                WHERE vr.tenant_id = %s
                  AND vr.is_resolved = FALSE
                  AND vr.severity = 'error'
                ORDER BY vr.created_at DESC
                LIMIT %s
            """, (str(self.tenant_id), limit))

            return cur.fetchall()

    def resolve_error(
        self,
        result_id: uuid.UUID,
        user_id: uuid.UUID,
        notes: Optional[str] = None
    ):
        """Mark a validation error as resolved."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE validation_results
                SET is_resolved = TRUE,
                    resolved_by = %s,
                    resolved_at = NOW(),
                    resolution_notes = %s
                WHERE id = %s AND tenant_id = %s
            """, (str(user_id), notes, str(result_id), str(self.tenant_id)))

            self.conn.commit()


def create_validator(conn, tenant_id: uuid.UUID) -> DataValidator:
    """Factory function to create a validator instance."""
    return DataValidator(conn, tenant_id)
