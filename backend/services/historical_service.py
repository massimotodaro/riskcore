# RISKCORE Historical Service
# Query position_history for point-in-time snapshots
# Supports time travel for the Trades page

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class HistoricalService:
    """
    Service for historical position queries.

    Enables point-in-time views of positions for:
    - Historical risk analysis
    - Audit and compliance
    - Regression testing
    - Time travel in the Trades page
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """Initialize with database connection."""
        self.conn = conn

    def get_available_snapshots(
        self,
        tenant_id: UUID,
        days_back: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get available EOD snapshots for time selector.

        Args:
            tenant_id: Tenant ID
            days_back: How many days back to look

        Returns:
            List of available snapshot dates with counts
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                DATE_TRUNC('day', snapshot_timestamp) as snapshot_date,
                snapshot_type,
                COUNT(*) as position_count,
                MAX(snapshot_timestamp) as latest_timestamp
            FROM position_history
            WHERE tenant_id = %s
              AND snapshot_timestamp >= NOW() - INTERVAL '%s days'
              AND snapshot_type = 'eod'
            GROUP BY DATE_TRUNC('day', snapshot_timestamp), snapshot_type
            ORDER BY snapshot_date DESC
        """, (str(tenant_id), days_back))

        results = cur.fetchall()

        return [
            {
                'snapshot_date': r['snapshot_date'].date().isoformat(),
                'snapshot_type': r['snapshot_type'],
                'position_count': r['position_count'],
                'timestamp': r['latest_timestamp'].isoformat() if r['latest_timestamp'] else None,
            }
            for r in results
        ]

    def get_positions_at_time(
        self,
        book_ids: List[UUID],
        as_of: datetime,
        asset_class: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get positions at a specific point in time from position_history.

        Uses the most recent snapshot before or at the requested timestamp.

        Args:
            book_ids: List of book IDs to query
            as_of: Point-in-time timestamp
            asset_class: Optional asset class filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated list of historical positions
        """
        if not book_ids:
            return {'positions': [], 'total': 0, 'page': page, 'page_size': page_size}

        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        book_id_strs = [str(bid) for bid in book_ids]
        offset = (page - 1) * page_size

        # Build asset class filter
        asset_filter = ""
        params_count = [book_id_strs, as_of]
        params_positions = [book_id_strs, as_of]

        if asset_class:
            asset_filter = "AND s.asset_class = %s"
            params_count.append(asset_class)
            params_positions.append(asset_class)

        # Get total count using a subquery to get latest snapshot per position
        cur.execute(f"""
            WITH latest_snapshots AS (
                SELECT DISTINCT ON (ph.book_id, ph.security_id)
                    ph.id,
                    ph.book_id,
                    ph.security_id,
                    ph.snapshot_timestamp
                FROM position_history ph
                WHERE ph.book_id = ANY(%s::uuid[])
                  AND ph.snapshot_timestamp <= %s
                ORDER BY ph.book_id, ph.security_id, ph.snapshot_timestamp DESC
            )
            SELECT COUNT(*)
            FROM latest_snapshots ls
            JOIN position_history ph ON ls.id = ph.id
            JOIN securities s ON ph.security_id = s.id
            WHERE ph.quantity != 0
              {asset_filter}
        """, params_count)

        total = cur.fetchone()['count']

        # Get positions with the latest snapshot for each security/book
        params_positions.extend([page_size, offset])

        cur.execute(f"""
            WITH latest_snapshots AS (
                SELECT DISTINCT ON (ph.book_id, ph.security_id)
                    ph.id
                FROM position_history ph
                WHERE ph.book_id = ANY(%s::uuid[])
                  AND ph.snapshot_timestamp <= %s
                ORDER BY ph.book_id, ph.security_id, ph.snapshot_timestamp DESC
            )
            SELECT
                ph.id as history_id,
                ph.position_id,
                ph.book_id,
                b.name as book_name,
                b.pm_id,
                u.name as pm_name,
                ph.security_id,
                COALESCE(si.identifier_value, s.figi) as ticker,
                s.name as security_name,
                s.asset_class,
                s.sector,
                ph.direction,
                ph.quantity,
                ph.market_value,
                ph.cost_basis,
                ph.unrealized_pnl,
                ph.price,
                ph.price_source,
                ph.delta,
                ph.gamma,
                ph.vega,
                ph.theta,
                ph.rho,
                ph.dv01,
                ph.cs01,
                ph.convexity,
                ph.snapshot_timestamp,
                ph.snapshot_type
            FROM latest_snapshots ls
            JOIN position_history ph ON ls.id = ph.id
            JOIN securities s ON ph.security_id = s.id
            JOIN books b ON ph.book_id = b.id
            LEFT JOIN users u ON b.pm_id = u.id
            LEFT JOIN security_identifiers si ON ph.security_id = si.security_id
                AND si.identifier_type = 'ticker'
            WHERE ph.quantity != 0
              {asset_filter}
            ORDER BY ABS(ph.market_value) DESC
            LIMIT %s OFFSET %s
        """, params_positions)

        results = cur.fetchall()

        positions = [
            {
                'position_id': str(r['position_id']) if r['position_id'] else None,
                'history_id': str(r['history_id']),
                'book_id': str(r['book_id']),
                'book_name': r['book_name'],
                'pm_id': str(r['pm_id']) if r['pm_id'] else None,
                'pm_name': r['pm_name'],
                'security_id': str(r['security_id']),
                'ticker': r['ticker'],
                'security_name': r['security_name'],
                'asset_class': r['asset_class'],
                'sector': r['sector'],
                'direction': r['direction'],
                'quantity': float(r['quantity'] or 0),
                'market_value': float(r['market_value'] or 0),
                'cost_basis': float(r['cost_basis'] or 0),
                'unrealized_pnl': float(r['unrealized_pnl'] or 0),
                'price': float(r['price'] or 0),
                'price_source': r['price_source'],
                'delta': float(r['delta'] or 0),
                'gamma': float(r['gamma'] or 0),
                'vega': float(r['vega'] or 0),
                'theta': float(r['theta'] or 0),
                'rho': float(r['rho'] or 0),
                'dv01': float(r['dv01'] or 0),
                'cs01': float(r['cs01'] or 0),
                'convexity': float(r['convexity'] or 0),
                'snapshot_timestamp': r['snapshot_timestamp'].isoformat() if r['snapshot_timestamp'] else None,
                'snapshot_type': r['snapshot_type'],
            }
            for r in results
        ]

        return {
            'positions': positions,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
            'as_of': as_of.isoformat(),
        }

    def get_positions_current(
        self,
        book_ids: List[UUID],
        asset_class: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get current (latest) positions from positions table.

        This is for "Latest" time selection - uses current positions,
        not position_history.

        Args:
            book_ids: List of book IDs to query
            asset_class: Optional asset class filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated list of current positions
        """
        if not book_ids:
            return {'positions': [], 'total': 0, 'page': page, 'page_size': page_size}

        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        book_id_strs = [str(bid) for bid in book_ids]
        offset = (page - 1) * page_size

        # Build asset class filter
        asset_filter = ""
        params_count = [book_id_strs]
        params_positions = [book_id_strs]

        if asset_class:
            asset_filter = "AND s.asset_class = %s"
            params_count.append(asset_class)
            params_positions.append(asset_class)

        # Get total count
        cur.execute(f"""
            SELECT COUNT(*)
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = ANY(%s::uuid[])
              AND p.quantity != 0
              {asset_filter}
        """, params_count)

        total = cur.fetchone()['count']

        # Get positions
        params_positions.extend([page_size, offset])

        cur.execute(f"""
            SELECT
                p.id as position_id,
                p.book_id,
                b.name as book_name,
                b.pm_id,
                u.name as pm_name,
                p.security_id,
                COALESCE(si.identifier_value, s.figi) as ticker,
                s.name as security_name,
                s.asset_class,
                s.sector,
                p.direction,
                p.quantity,
                p.market_value,
                p.cost_basis,
                p.unrealized_pnl,
                p.price,
                COALESCE(p.price_source::text, 'unknown') as price_source,
                p.price_as_of,
                p.delta,
                p.gamma,
                p.vega,
                p.theta,
                p.rho,
                p.dv01,
                p.cs01,
                p.convexity,
                p.updated_at
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            JOIN books b ON p.book_id = b.id
            LEFT JOIN users u ON b.pm_id = u.id
            LEFT JOIN security_identifiers si ON p.security_id = si.security_id
                AND si.identifier_type = 'ticker'
            WHERE p.book_id = ANY(%s::uuid[])
              AND p.quantity != 0
              {asset_filter}
            ORDER BY ABS(p.market_value) DESC
            LIMIT %s OFFSET %s
        """, params_positions)

        results = cur.fetchall()

        positions = [
            {
                'position_id': str(r['position_id']),
                'book_id': str(r['book_id']),
                'book_name': r['book_name'],
                'pm_id': str(r['pm_id']) if r['pm_id'] else None,
                'pm_name': r['pm_name'],
                'security_id': str(r['security_id']),
                'ticker': r['ticker'],
                'security_name': r['security_name'],
                'asset_class': r['asset_class'],
                'sector': r['sector'],
                'direction': r['direction'],
                'quantity': float(r['quantity'] or 0),
                'market_value': float(r['market_value'] or 0),
                'cost_basis': float(r['cost_basis'] or 0),
                'unrealized_pnl': float(r['unrealized_pnl'] or 0),
                'price': float(r['price'] or 0),
                'price_source': r['price_source'],
                'price_as_of': r['price_as_of'].isoformat() if r['price_as_of'] else None,
                'delta': float(r['delta'] or 0),
                'gamma': float(r['gamma'] or 0),
                'vega': float(r['vega'] or 0),
                'theta': float(r['theta'] or 0),
                'rho': float(r['rho'] or 0),
                'dv01': float(r['dv01'] or 0),
                'cs01': float(r['cs01'] or 0),
                'convexity': float(r['convexity'] or 0),
                'updated_at': r['updated_at'].isoformat() if r['updated_at'] else None,
            }
            for r in results
        ]

        return {
            'positions': positions,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
            'as_of': 'latest',
        }

    def get_trades_for_position(
        self,
        book_id: UUID,
        security_id: UUID,
        include_cancelled: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all open trades that make up a position.

        For equities: Shows all trades that sum to net position
        For OTC (CDS, swaps): Shows each open contract with counterparty

        Args:
            book_id: Book ID
            security_id: Security ID
            include_cancelled: Whether to include cancelled trades

        Returns:
            List of trades for this position
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        cancelled_filter = "" if include_cancelled else "AND t.is_cancelled = false"

        cur.execute(f"""
            SELECT
                t.id as trade_id,
                t.trade_id_external,
                t.side,
                t.quantity,
                t.price,
                t.notional,
                t.currency,
                t.trade_date,
                t.trade_time,
                t.settlement_date,
                t.counterparty,
                t.broker,
                t.commission,
                t.fees,
                t.source,
                t.is_cancelled,
                t.cancelled_at,
                t.created_at
            FROM trades t
            WHERE t.book_id = %s
              AND t.security_id = %s
              {cancelled_filter}
            ORDER BY t.trade_date DESC, t.trade_time DESC NULLS LAST
        """, (str(book_id), str(security_id)))

        results = cur.fetchall()

        return [
            {
                'trade_id': str(r['trade_id']),
                'trade_id_external': r['trade_id_external'],
                'side': r['side'],
                'quantity': float(r['quantity'] or 0),
                'price': float(r['price'] or 0),
                'notional': float(r['notional'] or 0),
                'currency': r['currency'],
                'trade_date': r['trade_date'].isoformat() if r['trade_date'] else None,
                'trade_time': r['trade_time'].isoformat() if r['trade_time'] else None,
                'settlement_date': r['settlement_date'].isoformat() if r['settlement_date'] else None,
                'counterparty': r['counterparty'],
                'broker': r['broker'],
                'commission': float(r['commission'] or 0),
                'fees': float(r['fees'] or 0),
                'source': r['source'],
                'is_cancelled': r['is_cancelled'],
                'cancelled_at': r['cancelled_at'].isoformat() if r['cancelled_at'] else None,
                'created_at': r['created_at'].isoformat() if r['created_at'] else None,
            }
            for r in results
        ]

    def get_positions_grouped_by_riskpod(
        self,
        book_ids: List[UUID],
        as_of: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get positions grouped by RiskPod (asset class category).

        Returns a dict with keys: equity, rates, credit, fx, other
        Each containing paginated position lists.

        Args:
            book_ids: List of book IDs
            as_of: Optional point-in-time (None = latest)

        Returns:
            Dict mapping RiskPod to position data
        """
        # Define asset class to RiskPod mapping
        riskpod_mapping = {
            'equity': ['equity', 'option', 'future', 'fund'],
            'rates': ['fixed_income', 'swap'],
            'credit': ['cds'],
            'fx': ['fx'],
            'other': ['commodity', 'crypto', 'other'],
        }

        result = {}

        for pod_name, asset_classes in riskpod_mapping.items():
            # Get positions for each asset class in this pod
            all_positions = []
            total_count = 0

            for asset_class in asset_classes:
                if as_of:
                    data = self.get_positions_at_time(
                        book_ids=book_ids,
                        as_of=as_of,
                        asset_class=asset_class,
                        page=1,
                        page_size=1000,  # Get all for aggregation
                    )
                else:
                    data = self.get_positions_current(
                        book_ids=book_ids,
                        asset_class=asset_class,
                        page=1,
                        page_size=1000,
                    )

                all_positions.extend(data['positions'])
                total_count += data['total']

            # Sort by market value
            all_positions.sort(key=lambda x: abs(x['market_value']), reverse=True)

            # Calculate pod summary
            gross_exposure = sum(abs(p['market_value']) for p in all_positions)
            net_exposure = sum(
                p['market_value'] if p['direction'] == 'long' else -p['market_value']
                for p in all_positions
            )
            total_delta = sum(p.get('delta', 0) for p in all_positions)
            total_dv01 = sum(p.get('dv01', 0) for p in all_positions)
            total_cs01 = sum(p.get('cs01', 0) for p in all_positions)

            result[pod_name] = {
                'pod': pod_name,
                'position_count': total_count,
                'gross_exposure': gross_exposure,
                'net_exposure': net_exposure,
                'total_delta': total_delta,
                'total_dv01': total_dv01,
                'total_cs01': total_cs01,
                'positions': all_positions[:100],  # Limit to top 100 per pod
                'as_of': as_of.isoformat() if as_of else 'latest',
            }

        return result

    def get_time_presets(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """
        Get time selector presets with actual available dates.

        Returns presets like "Yesterday EOD", "Last Week" with
        the actual snapshot timestamps.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of preset options with timestamps
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get most recent snapshots for each day
        cur.execute("""
            SELECT DISTINCT ON (DATE_TRUNC('day', snapshot_timestamp))
                DATE_TRUNC('day', snapshot_timestamp) as snapshot_day,
                MAX(snapshot_timestamp) as latest_snapshot
            FROM position_history
            WHERE tenant_id = %s
              AND snapshot_type = 'eod'
              AND snapshot_timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('day', snapshot_timestamp)
            ORDER BY DATE_TRUNC('day', snapshot_timestamp) DESC
            LIMIT 30
        """, (str(tenant_id),))

        snapshots = cur.fetchall()

        if not snapshots:
            return [{'type': 'latest', 'label': 'Latest', 'timestamp': None}]

        presets = [{'type': 'latest', 'label': 'Latest', 'timestamp': None}]

        today = datetime.now().date()

        for snap in snapshots:
            snap_date = snap['snapshot_day'].date()
            delta = (today - snap_date).days

            if delta == 1:
                presets.append({
                    'type': 'yesterday',
                    'label': 'Yesterday EOD',
                    'timestamp': snap['latest_snapshot'].isoformat(),
                    'date': snap_date.isoformat(),
                })
            elif delta == 7:
                presets.append({
                    'type': 'lastWeek',
                    'label': 'Last Week EOD',
                    'timestamp': snap['latest_snapshot'].isoformat(),
                    'date': snap_date.isoformat(),
                })
            elif delta == 30:
                presets.append({
                    'type': 'lastMonth',
                    'label': 'Last Month EOD',
                    'timestamp': snap['latest_snapshot'].isoformat(),
                    'date': snap_date.isoformat(),
                })

        return presets
