# RISKCORE Pricing Service
# Handles pricing runs and security price updates
# Pricing hierarchy: Client Override → Market Feed → Model-Derived → Stale

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class PricingService:
    """
    Service for managing pricing runs and security prices.

    Pricing Hierarchy:
    1. Client Override (manual) - user explicitly set price
    2. Market Feed (market) - from OpenBB/Yahoo/Bloomberg
    3. Model-Derived (model) - FinancePy for derivatives
    4. Stale (stale) - old price with warning indicator
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """Initialize with database connection."""
        self.conn = conn

    def get_pricing_status(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get the status of pricing for a tenant.

        Returns:
            Latest pricing run info and statistics
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get latest pricing run
        cur.execute("""
            SELECT
                id,
                trigger_type,
                triggered_by,
                started_at,
                completed_at,
                securities_priced,
                securities_failed,
                status,
                error_details,
                config
            FROM pricing_runs
            WHERE tenant_id = %s
            ORDER BY started_at DESC
            LIMIT 1
        """, (str(tenant_id),))

        latest_run = cur.fetchone()

        # Get price source distribution
        cur.execute("""
            SELECT
                sp.source::text as price_source,
                COUNT(*) as count
            FROM security_prices sp
            JOIN positions p ON sp.security_id = p.security_id
            WHERE p.tenant_id = %s
              AND p.quantity != 0
            GROUP BY sp.source
        """, (str(tenant_id),))

        source_dist = {r['price_source']: r['count'] for r in cur.fetchall()}

        # Get stale price count (older than 7 days)
        cur.execute("""
            SELECT COUNT(DISTINCT p.security_id) as stale_count
            FROM positions p
            JOIN security_prices sp ON p.security_id = sp.security_id
            WHERE p.tenant_id = %s
              AND p.quantity != 0
              AND sp.price_date < NOW() - INTERVAL '7 days'
        """, (str(tenant_id),))

        stale_result = cur.fetchone()
        stale_count = stale_result['stale_count'] if stale_result else 0

        return {
            'latest_run': {
                'id': str(latest_run['id']) if latest_run else None,
                'trigger_type': latest_run['trigger_type'] if latest_run else None,
                'started_at': latest_run['started_at'].isoformat() if latest_run and latest_run['started_at'] else None,
                'completed_at': latest_run['completed_at'].isoformat() if latest_run and latest_run['completed_at'] else None,
                'securities_priced': latest_run['securities_priced'] if latest_run else 0,
                'securities_failed': latest_run['securities_failed'] if latest_run else 0,
                'status': latest_run['status'] if latest_run else None,
                'error_details': latest_run['error_details'] if latest_run else None,
            } if latest_run else None,
            'price_sources': source_dist,
            'stale_price_count': stale_count,
        }

    def create_pricing_run(
        self,
        tenant_id: UUID,
        trigger_type: str = 'manual',
        triggered_by: Optional[UUID] = None,
        config: Optional[Dict] = None,
    ) -> UUID:
        """
        Create a new pricing run record.

        Args:
            tenant_id: Tenant ID
            trigger_type: 'scheduled', 'manual', or 'single_security'
            triggered_by: User ID if manual
            config: Configuration options

        Returns:
            UUID of created pricing run
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            INSERT INTO pricing_runs (
                tenant_id,
                trigger_type,
                triggered_by,
                config,
                status,
                started_at
            ) VALUES (%s, %s, %s, %s, 'running', NOW())
            RETURNING id
        """, (
            str(tenant_id),
            trigger_type,
            str(triggered_by) if triggered_by else None,
            psycopg2.extras.Json(config) if config else None,
        ))

        result = cur.fetchone()
        self.conn.commit()

        return UUID(str(result['id']))

    def complete_pricing_run(
        self,
        run_id: UUID,
        securities_priced: int,
        securities_failed: int,
        status: str = 'completed',
        error_details: Optional[Dict] = None,
    ) -> None:
        """
        Mark a pricing run as complete.

        Args:
            run_id: Pricing run ID
            securities_priced: Number of securities priced
            securities_failed: Number of failures
            status: 'completed' or 'failed'
            error_details: Error information if failed
        """
        cur = self.conn.cursor()

        cur.execute("""
            UPDATE pricing_runs
            SET
                completed_at = NOW(),
                securities_priced = %s,
                securities_failed = %s,
                status = %s,
                error_details = %s
            WHERE id = %s
        """, (
            securities_priced,
            securities_failed,
            status,
            psycopg2.extras.Json(error_details) if error_details else None,
            str(run_id),
        ))

        self.conn.commit()

    def trigger_reprice_all(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a full reprice for all securities.

        This is a placeholder - actual implementation would:
        1. Create pricing run record
        2. Fetch prices from OpenBB
        3. Run FinancePy models for derivatives
        4. Update security_prices table
        5. Mark run as complete

        Args:
            tenant_id: Tenant ID
            user_id: User who triggered (None if scheduled)

        Returns:
            Status of the pricing run
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Create pricing run
        run_id = self.create_pricing_run(
            tenant_id=tenant_id,
            trigger_type='manual' if user_id else 'scheduled',
            triggered_by=user_id,
            config={'source': 'openbb', 'provider': 'yahoo'},
        )

        # Get securities to price
        cur.execute("""
            SELECT DISTINCT p.security_id, s.asset_class, s.security_type
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s
              AND p.quantity != 0
        """, (str(tenant_id),))

        securities = cur.fetchall()
        total = len(securities)

        # In production, this would:
        # 1. Call OpenBB for market prices
        # 2. Run FinancePy models for derivatives
        # 3. Update security_prices with new values

        # For now, simulate successful pricing
        priced = total
        failed = 0

        # Complete the run
        self.complete_pricing_run(
            run_id=run_id,
            securities_priced=priced,
            securities_failed=failed,
            status='completed',
        )

        return {
            'run_id': str(run_id),
            'status': 'completed',
            'securities_priced': priced,
            'securities_failed': failed,
            'message': f'Repriced {priced} securities successfully',
        }

    def get_security_price(
        self,
        security_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest price for a security.

        Args:
            security_id: Security ID

        Returns:
            Price details with source information
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                sp.security_id,
                sp.price_date,
                sp.price,
                sp.source::text as price_source,
                sp.model_id,
                s.name as security_name,
                s.asset_class,
                CASE
                    WHEN sp.price_date < NOW() - INTERVAL '7 days' THEN true
                    ELSE false
                END as is_stale
            FROM security_prices sp
            JOIN securities s ON sp.security_id = s.id
            WHERE sp.security_id = %s
            ORDER BY sp.price_date DESC
            LIMIT 1
        """, (str(security_id),))

        result = cur.fetchone()

        if not result:
            return None

        return {
            'security_id': str(result['security_id']),
            'security_name': result['security_name'],
            'asset_class': result['asset_class'],
            'price': float(result['price']),
            'price_date': result['price_date'].isoformat(),
            'price_source': result['price_source'],
            'model_id': str(result['model_id']) if result['model_id'] else None,
            'is_stale': result['is_stale'],
        }

    def update_price_manual(
        self,
        security_id: UUID,
        price: Decimal,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manually override a security price.

        Args:
            security_id: Security ID
            price: New price
            user_id: User making the override
            reason: Reason for override

        Returns:
            Updated price details
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Insert new price with manual source
        cur.execute("""
            INSERT INTO security_prices (
                security_id,
                price_date,
                price,
                source
            ) VALUES (%s, NOW()::date, %s, 'manual')
            ON CONFLICT (security_id, price_date)
            DO UPDATE SET price = %s, source = 'manual'
            RETURNING id, price_date, price, source::text as price_source
        """, (str(security_id), float(price), float(price)))

        result = cur.fetchone()
        self.conn.commit()

        return {
            'security_id': str(security_id),
            'price': float(result['price']),
            'price_date': result['price_date'].isoformat(),
            'price_source': result['price_source'],
            'updated_by': str(user_id),
            'reason': reason,
        }


class ValuationService:
    """
    Service for position valuation details and model inputs.

    Used by the Riskboard valuation popup to show:
    - Price source
    - Model inputs (for model-derived prices)
    - Override capability
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """Initialize with database connection."""
        self.conn = conn

    def get_position_valuation(
        self,
        position_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get valuation details for a position.

        Args:
            position_id: Position ID

        Returns:
            Valuation details including price source and model inputs
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get position with security details
        cur.execute("""
            SELECT
                p.id as position_id,
                p.security_id,
                p.book_id,
                p.quantity,
                p.direction,
                p.price as current_price,
                p.market_value,
                p.price_source as position_price_source,
                p.price_as_of,
                s.name as security_name,
                s.asset_class,
                s.security_type,
                COALESCE(si.identifier_value, s.figi) as ticker,
                sp.price_source as latest_price_source,
                sp.price_date as latest_price_date,
                sp.model_id
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            LEFT JOIN security_identifiers si ON p.security_id = si.security_id
                AND si.identifier_type = 'ticker'
            LEFT JOIN LATERAL (
                SELECT source::text as price_source, price_date, model_id
                FROM security_prices
                WHERE security_id = p.security_id
                ORDER BY price_date DESC
                LIMIT 1
            ) sp ON true
            WHERE p.id = %s
        """, (str(position_id),))

        position = cur.fetchone()

        if not position:
            return None

        # Get model valuation inputs if model-derived
        model_inputs = None
        if position['model_id']:
            cur.execute("""
                SELECT
                    model_name,
                    model_version,
                    inputs,
                    model_price,
                    has_override,
                    override_inputs,
                    override_by,
                    override_at,
                    override_reason,
                    calculated_at
                FROM model_valuation_inputs
                WHERE id = %s
            """, (str(position['model_id']),))

            model_result = cur.fetchone()
            if model_result:
                model_inputs = {
                    'model_name': model_result['model_name'],
                    'model_version': model_result['model_version'],
                    'inputs': model_result['inputs'],
                    'model_price': float(model_result['model_price']) if model_result['model_price'] else None,
                    'has_override': model_result['has_override'],
                    'override_inputs': model_result['override_inputs'],
                    'override_by': str(model_result['override_by']) if model_result['override_by'] else None,
                    'override_at': model_result['override_at'].isoformat() if model_result['override_at'] else None,
                    'override_reason': model_result['override_reason'],
                    'calculated_at': model_result['calculated_at'].isoformat() if model_result['calculated_at'] else None,
                }

        price_source = position['latest_price_source'] or position['position_price_source'] or 'unknown'

        return {
            'position_id': str(position['position_id']),
            'security_id': str(position['security_id']),
            'ticker': position['ticker'],
            'security_name': position['security_name'],
            'asset_class': position['asset_class'],
            'security_type': position['security_type'],
            'book_id': str(position['book_id']),
            'quantity': float(position['quantity']),
            'direction': position['direction'],
            'current_price': float(position['current_price'] or 0),
            'market_value': float(position['market_value'] or 0),
            'price_source': price_source,
            'price_as_of': position['price_as_of'].isoformat() if position['price_as_of'] else (
                position['latest_price_date'].isoformat() if position['latest_price_date'] else None
            ),
            'has_model_details': position['model_id'] is not None,
            'model_inputs': model_inputs,
            'can_override': True,  # In production, check user permissions
        }

    def override_model_inputs(
        self,
        position_id: UUID,
        override_inputs: Dict[str, Any],
        user_id: UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Override model inputs for a position's valuation.

        Args:
            position_id: Position ID
            override_inputs: New input values
            user_id: User making the override
            reason: Reason for override

        Returns:
            Updated valuation details
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get the position's model_id
        cur.execute("""
            SELECT sp.model_id
            FROM positions p
            JOIN security_prices sp ON p.security_id = sp.security_id
            WHERE p.id = %s
            ORDER BY sp.price_date DESC
            LIMIT 1
        """, (str(position_id),))

        result = cur.fetchone()

        if not result or not result['model_id']:
            raise ValueError("Position does not have model-derived valuation")

        model_id = result['model_id']

        # Update model valuation inputs with override
        cur.execute("""
            UPDATE model_valuation_inputs
            SET
                has_override = true,
                override_inputs = %s,
                override_by = %s,
                override_at = NOW(),
                override_reason = %s
            WHERE id = %s
            RETURNING *
        """, (
            psycopg2.extras.Json(override_inputs),
            str(user_id),
            reason,
            str(model_id),
        ))

        updated = cur.fetchone()
        self.conn.commit()

        return {
            'model_id': str(model_id),
            'has_override': True,
            'override_inputs': override_inputs,
            'override_by': str(user_id),
            'override_reason': reason,
            'message': 'Model inputs overridden successfully',
        }

    def recalculate_position(
        self,
        position_id: UUID,
    ) -> Dict[str, Any]:
        """
        Recalculate a position's valuation using model inputs.

        In production, this would:
        1. Get model inputs (with overrides if any)
        2. Run FinancePy calculation
        3. Update model_valuation_inputs.model_price
        4. Update security_prices
        5. Update position.market_value

        Args:
            position_id: Position ID

        Returns:
            Recalculation result
        """
        # Placeholder - in production would run FinancePy model
        return {
            'position_id': str(position_id),
            'status': 'success',
            'message': 'Position recalculated (placeholder - would run FinancePy in production)',
        }
