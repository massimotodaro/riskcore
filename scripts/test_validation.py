#!/usr/bin/env python3
"""
Test script for RISKCORE Data Validation Pipeline

Tests the validation service against the local Supabase database.
"""

import os
import sys
import uuid
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.validation import (
    DataValidator,
    Severity,
    create_validator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_connection():
    """Get database connection from environment or use local defaults."""
    return psycopg2.connect(
        host=os.getenv("SUPABASE_DB_HOST", "127.0.0.1"),
        port=os.getenv("SUPABASE_DB_PORT", "54322"),
        database=os.getenv("SUPABASE_DB_NAME", "postgres"),
        user=os.getenv("SUPABASE_DB_USER", "postgres"),
        password=os.getenv("SUPABASE_DB_PASSWORD", "postgres"),
    )


def get_test_tenant(conn) -> uuid.UUID:
    """Get or create a test tenant for validation testing."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Try to find existing tenant
        cur.execute("SELECT id FROM tenants LIMIT 1")
        row = cur.fetchone()
        if row:
            return uuid.UUID(str(row["id"]))

        # Create test tenant
        tenant_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO tenants (id, name, status)
            VALUES (%s, 'Test Tenant', 'active')
            RETURNING id
        """, (str(tenant_id),))
        conn.commit()
        return tenant_id


def test_validation_rules_loaded(validator: DataValidator):
    """Test that validation rules are loaded from the database."""
    logger.info("Testing rule loading...")

    position_rules = validator.get_rules_for_table("positions")
    trade_rules = validator.get_rules_for_table("trades")
    security_rules = validator.get_rules_for_table("securities")
    price_rules = validator.get_rules_for_table("security_prices")

    logger.info(f"  Positions rules: {len(position_rules)}")
    logger.info(f"  Trades rules: {len(trade_rules)}")
    logger.info(f"  Securities rules: {len(security_rules)}")
    logger.info(f"  Prices rules: {len(price_rules)}")

    for rule in position_rules:
        logger.info(f"    - {rule.name}: {rule.rule_type.value} on {rule.target_column}")

    assert len(position_rules) > 0, "Should have position rules"
    assert len(trade_rules) > 0, "Should have trade rules"
    logger.info("  ✓ Rules loaded successfully")


def test_position_validation(validator: DataValidator):
    """Test position validation with various scenarios."""
    logger.info("Testing position validation...")

    # Valid position
    valid_positions = [
        {
            "book_id": str(uuid.uuid4()),
            "security_id": str(uuid.uuid4()),
            "quantity": 1000,
        }
    ]

    # Invalid positions
    invalid_positions = [
        # Missing quantity
        {
            "book_id": str(uuid.uuid4()),
            "security_id": str(uuid.uuid4()),
            "quantity": None,
        },
        # Missing book_id
        {
            "book_id": None,
            "security_id": str(uuid.uuid4()),
            "quantity": 500,
        },
        # Invalid quantity (not numeric)
        {
            "book_id": str(uuid.uuid4()),
            "security_id": str(uuid.uuid4()),
            "quantity": "invalid",
        },
    ]

    # Test valid positions
    summary = validator.validate_positions(valid_positions)
    logger.info(f"  Valid positions: {summary.records_validated} validated, {summary.error_count} errors")
    # Note: referential check will fail since UUIDs don't exist in DB, but schema checks pass
    schema_errors = [r for r in summary.results if r.error_code != "INVALID_REFERENCE"]
    assert len(schema_errors) == 0, f"Valid position should have no schema errors: {schema_errors}"
    logger.info("  ✓ Valid position passed schema checks")

    # Test invalid positions
    summary = validator.validate_positions(invalid_positions)
    logger.info(f"  Invalid positions: {summary.records_validated} validated, {summary.error_count} errors")
    assert summary.error_count >= 3, "Invalid positions should have errors"
    logger.info("  ✓ Invalid positions detected correctly")

    # Show the errors
    for result in summary.results:
        logger.info(f"    {result.severity.value}: {result.error_code} - {result.error_message}")


def test_trade_validation(validator: DataValidator):
    """Test trade validation."""
    logger.info("Testing trade validation...")

    trades = [
        # Valid trade
        {
            "security_id": str(uuid.uuid4()),
            "quantity": 100,
            "price": 150.50,
            "trade_date": "2026-01-10",
        },
        # Zero quantity (invalid - must be positive)
        {
            "security_id": str(uuid.uuid4()),
            "quantity": 0,
            "price": 150.50,
            "trade_date": "2026-01-10",
        },
        # Negative price (invalid)
        {
            "security_id": str(uuid.uuid4()),
            "quantity": 100,
            "price": -5,
            "trade_date": "2026-01-10",
        },
        # Future date (warning)
        {
            "security_id": str(uuid.uuid4()),
            "quantity": 100,
            "price": 150.50,
            "trade_date": "2027-12-31",
        },
    ]

    summary = validator.validate_trades(trades)
    logger.info(f"  Trades: {summary.records_validated} validated")
    logger.info(f"  Errors: {summary.error_count}, Warnings: {summary.warning_count}")

    for result in summary.results:
        logger.info(f"    {result.severity.value}: {result.error_code} - {result.error_message}")

    # Should have errors for quantity and price
    assert summary.error_count >= 2, "Should detect quantity and price errors"
    # Should have warning for future date
    assert summary.warning_count >= 1, "Should warn about future trade date"
    logger.info("  ✓ Trade validation working correctly")


def test_security_validation(validator: DataValidator):
    """Test security validation."""
    logger.info("Testing security validation...")

    securities = [
        # Valid security
        {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "currency": "USD",
        },
        # Missing name
        {
            "name": "",
            "ticker": "TEST",
            "currency": "USD",
        },
        # Invalid currency format
        {
            "name": "Test Company",
            "ticker": "TEST",
            "currency": "INVALID",
        },
    ]

    summary = validator.validate_securities(securities)
    logger.info(f"  Securities: {summary.records_validated} validated")
    logger.info(f"  Errors: {summary.error_count}")

    for result in summary.results:
        logger.info(f"    {result.severity.value}: {result.error_code} - {result.error_message}")

    assert summary.error_count >= 2, "Should detect name and currency errors"
    logger.info("  ✓ Security validation working correctly")


def test_price_validation(validator: DataValidator):
    """Test price validation."""
    logger.info("Testing price validation...")

    prices = [
        # Valid price
        {
            "security_id": str(uuid.uuid4()),
            "price": 150.50,
            "price_date": "2026-01-10",
        },
        # Negative price
        {
            "security_id": str(uuid.uuid4()),
            "price": -10,
            "price_date": "2026-01-10",
        },
        # Missing date
        {
            "security_id": str(uuid.uuid4()),
            "price": 100,
            "price_date": None,
        },
    ]

    summary = validator.validate_prices(prices)
    logger.info(f"  Prices: {summary.records_validated} validated")
    logger.info(f"  Errors: {summary.error_count}")

    for result in summary.results:
        logger.info(f"    {result.severity.value}: {result.error_code} - {result.error_message}")

    assert summary.error_count >= 2, "Should detect price and date errors"
    logger.info("  ✓ Price validation working correctly")


def test_validation_summary(validator: DataValidator):
    """Test validation summary functionality."""
    logger.info("Testing validation summary...")

    # Mix of valid and invalid
    positions = [
        {"book_id": str(uuid.uuid4()), "security_id": str(uuid.uuid4()), "quantity": 100},
        {"book_id": str(uuid.uuid4()), "security_id": str(uuid.uuid4()), "quantity": None},
        {"book_id": None, "security_id": str(uuid.uuid4()), "quantity": 200},
        {"book_id": str(uuid.uuid4()), "security_id": str(uuid.uuid4()), "quantity": 300},
    ]

    summary = validator.validate_positions(positions)

    logger.info(f"  Summary:")
    logger.info(f"    Records validated: {summary.records_validated}")
    logger.info(f"    Records failed: {summary.records_failed}")
    logger.info(f"    Is valid: {summary.is_valid()}")
    logger.info(f"    Total errors: {summary.error_count}")
    logger.info(f"    Total warnings: {summary.warning_count}")

    # Convert to dict for API response
    summary_dict = summary.to_dict()
    assert "is_valid" in summary_dict
    assert "results" in summary_dict
    logger.info("  ✓ Summary working correctly")


def main():
    """Run all validation tests."""
    logger.info("=" * 60)
    logger.info("RISKCORE Data Validation Pipeline Tests")
    logger.info("=" * 60)

    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_connection()
        logger.info("  ✓ Connected")

        # Get test tenant
        tenant_id = get_test_tenant(conn)
        logger.info(f"  Using tenant: {tenant_id}")

        # Create validator
        logger.info("Creating validator...")
        validator = create_validator(conn, tenant_id)
        logger.info("  ✓ Validator created")

        # Run tests
        print()
        test_validation_rules_loaded(validator)
        print()
        test_position_validation(validator)
        print()
        test_trade_validation(validator)
        print()
        test_security_validation(validator)
        print()
        test_price_validation(validator)
        print()
        test_validation_summary(validator)

        print()
        logger.info("=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
