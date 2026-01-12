# RISKCORE Returns Tracking Service
# Captures and aggregates daily P&L for correlation analysis
# Week 4 Enhancement: Foundation for AI-native queries

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from .riskpod import get_riskpod, RiskPod

logger = logging.getLogger(__name__)


class ReturnWindow(str, Enum):
    """Standard windows for return calculations."""
    DAY_1 = "1d"
    DAY_5 = "5d"
    DAY_21 = "21d"      # ~1 month
    DAY_63 = "63d"      # ~3 months
    DAY_252 = "252d"    # ~1 year


@dataclass
class DailyReturn:
    """Daily return record for a book or PM."""
    entity_id: UUID
    entity_name: str
    return_date: date
    daily_pnl: Decimal
    daily_return_pct: Optional[Decimal]
    start_nav: Optional[Decimal]
    end_nav: Optional[Decimal]

    # Breakdown by pod
    pnl_by_pod: Dict[str, Decimal] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": str(self.entity_id),
            "entity_name": self.entity_name,
            "return_date": self.return_date.isoformat(),
            "daily_pnl": float(self.daily_pnl),
            "daily_return_pct": float(self.daily_return_pct) if self.daily_return_pct else None,
            "start_nav": float(self.start_nav) if self.start_nav else None,
            "end_nav": float(self.end_nav) if self.end_nav else None,
            "pnl_by_pod": {k: float(v) for k, v in self.pnl_by_pod.items()},
        }


@dataclass
class ReturnSeries:
    """Time series of returns for an entity."""
    entity_id: UUID
    entity_name: str
    entity_type: str  # 'book', 'pm', 'fund', 'pod'
    returns: List[DailyReturn]
    window: ReturnWindow

    @property
    def return_values(self) -> List[float]:
        """Get list of return percentages for correlation calculation."""
        return [
            float(r.daily_return_pct) if r.daily_return_pct else 0.0
            for r in self.returns
        ]

    @property
    def pnl_values(self) -> List[float]:
        """Get list of P&L values."""
        return [float(r.daily_pnl) for r in self.returns]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": str(self.entity_id),
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "window": self.window.value,
            "data_points": len(self.returns),
            "total_pnl": sum(self.pnl_values),
            "returns": [r.to_dict() for r in self.returns],
        }


class ReturnsService:
    """
    Service for tracking and retrieving daily returns.

    Captures daily P&L at book level, aggregates to PM and Pod levels,
    and provides time series for correlation calculations.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    # =========================================================================
    # CAPTURE RETURNS (End of Day Process)
    # =========================================================================

    def capture_book_daily_return(
        self,
        tenant_id: UUID,
        book_id: UUID,
        return_date: date,
        daily_pnl: Decimal,
        start_nav: Optional[Decimal] = None,
        end_nav: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """
        Capture daily return for a single book.

        This would typically be called by an EOD process.

        Args:
            tenant_id: Tenant ID
            book_id: Book ID
            return_date: Date of the return
            daily_pnl: P&L for the day
            start_nav: NAV at start of day
            end_nav: NAV at end of day

        Returns:
            Created record
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Calculate return percentage
        daily_return_pct = None
        if start_nav and start_nav != 0:
            daily_return_pct = (daily_pnl / start_nav) * 100

        # Get P&L breakdown by RiskPod from positions
        pnl_by_pod = self._calculate_pod_pnl_breakdown(tenant_id, book_id)

        cur.execute("""
            INSERT INTO book_daily_returns (
                tenant_id, book_id, return_date,
                daily_pnl, daily_return_pct,
                start_of_day_nav, end_of_day_nav,
                pnl_equity, pnl_rates, pnl_credit, pnl_fx, pnl_other
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (tenant_id, book_id, return_date)
            DO UPDATE SET
                daily_pnl = EXCLUDED.daily_pnl,
                daily_return_pct = EXCLUDED.daily_return_pct,
                start_of_day_nav = EXCLUDED.start_of_day_nav,
                end_of_day_nav = EXCLUDED.end_of_day_nav,
                pnl_equity = EXCLUDED.pnl_equity,
                pnl_rates = EXCLUDED.pnl_rates,
                pnl_credit = EXCLUDED.pnl_credit,
                pnl_fx = EXCLUDED.pnl_fx,
                pnl_other = EXCLUDED.pnl_other,
                updated_at = NOW()
            RETURNING *
        """, (
            str(tenant_id), str(book_id), return_date,
            daily_pnl, daily_return_pct,
            start_nav, end_nav,
            pnl_by_pod.get('equity', 0),
            pnl_by_pod.get('rates', 0),
            pnl_by_pod.get('credit', 0),
            pnl_by_pod.get('fx', 0),
            pnl_by_pod.get('other', 0),
        ))

        self.conn.commit()
        return dict(cur.fetchone())

    def _calculate_pod_pnl_breakdown(
        self,
        tenant_id: UUID,
        book_id: UUID,
    ) -> Dict[str, Decimal]:
        """Calculate P&L breakdown by RiskPod for a book."""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get positions with their asset class
        cur.execute("""
            SELECT
                s.asset_class,
                SUM(COALESCE(p.market_value, 0)) as total_value
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.tenant_id = %s AND p.book_id = %s
            GROUP BY s.asset_class
        """, (str(tenant_id), str(book_id)))

        breakdown = {pod.value: Decimal("0") for pod in RiskPod}

        for row in cur.fetchall():
            if row['asset_class']:
                pod = get_riskpod(row['asset_class'])
                # This is simplified - in reality would use actual P&L
                # For now, using market value as proxy
                breakdown[pod.value] += Decimal(str(row['total_value'] or 0))

        return breakdown

    def aggregate_pm_daily_returns(
        self,
        tenant_id: UUID,
        return_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate book returns to PM level for a specific date.

        Args:
            tenant_id: Tenant ID
            return_date: Date to aggregate

        Returns:
            List of PM return records created
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Aggregate from book returns
        cur.execute("""
            INSERT INTO pm_daily_returns (
                tenant_id, pm_id, return_date,
                daily_pnl, daily_return_pct,
                start_of_day_nav, end_of_day_nav,
                pnl_equity, pnl_rates, pnl_credit, pnl_fx, pnl_other,
                book_count
            )
            SELECT
                br.tenant_id,
                b.pm_id,
                br.return_date,
                SUM(br.daily_pnl) as daily_pnl,
                CASE
                    WHEN SUM(br.start_of_day_nav) > 0
                    THEN SUM(br.daily_pnl) / SUM(br.start_of_day_nav) * 100
                    ELSE NULL
                END as daily_return_pct,
                SUM(br.start_of_day_nav) as start_nav,
                SUM(br.end_of_day_nav) as end_nav,
                SUM(br.pnl_equity) as pnl_equity,
                SUM(br.pnl_rates) as pnl_rates,
                SUM(br.pnl_credit) as pnl_credit,
                SUM(br.pnl_fx) as pnl_fx,
                SUM(br.pnl_other) as pnl_other,
                COUNT(DISTINCT br.book_id) as book_count
            FROM book_daily_returns br
            JOIN books b ON br.book_id = b.id
            WHERE br.tenant_id = %s
              AND br.return_date = %s
              AND b.pm_id IS NOT NULL
            GROUP BY br.tenant_id, b.pm_id, br.return_date
            ON CONFLICT (tenant_id, pm_id, return_date)
            DO UPDATE SET
                daily_pnl = EXCLUDED.daily_pnl,
                daily_return_pct = EXCLUDED.daily_return_pct,
                start_of_day_nav = EXCLUDED.start_of_day_nav,
                end_of_day_nav = EXCLUDED.end_of_day_nav,
                pnl_equity = EXCLUDED.pnl_equity,
                pnl_rates = EXCLUDED.pnl_rates,
                pnl_credit = EXCLUDED.pnl_credit,
                pnl_fx = EXCLUDED.pnl_fx,
                pnl_other = EXCLUDED.pnl_other,
                book_count = EXCLUDED.book_count,
                updated_at = NOW()
            RETURNING *
        """, (str(tenant_id), return_date))

        self.conn.commit()
        return [dict(row) for row in cur.fetchall()]

    def aggregate_pod_daily_returns(
        self,
        tenant_id: UUID,
        return_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate returns to RiskPod level for a specific date.

        Args:
            tenant_id: Tenant ID
            return_date: Date to aggregate

        Returns:
            List of pod return records created
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Insert pod returns from book returns
        for pod in RiskPod:
            pod_col = f"pnl_{pod.value}"

            cur.execute(f"""
                INSERT INTO pod_daily_returns (
                    tenant_id, pod, return_date,
                    daily_pnl, daily_return_pct,
                    pm_count, book_count
                )
                SELECT
                    br.tenant_id,
                    %s as pod,
                    br.return_date,
                    SUM(br.{pod_col}) as daily_pnl,
                    NULL as daily_return_pct,  -- Would need exposure data
                    COUNT(DISTINCT b.pm_id) as pm_count,
                    COUNT(DISTINCT br.book_id) as book_count
                FROM book_daily_returns br
                JOIN books b ON br.book_id = b.id
                WHERE br.tenant_id = %s
                  AND br.return_date = %s
                GROUP BY br.tenant_id, br.return_date
                ON CONFLICT (tenant_id, pod, return_date)
                DO UPDATE SET
                    daily_pnl = EXCLUDED.daily_pnl,
                    pm_count = EXCLUDED.pm_count,
                    book_count = EXCLUDED.book_count
                RETURNING *
            """, (pod.value, str(tenant_id), return_date))

        self.conn.commit()

        # Return all pod returns for the date
        cur.execute("""
            SELECT * FROM pod_daily_returns
            WHERE tenant_id = %s AND return_date = %s
        """, (str(tenant_id), return_date))

        return [dict(row) for row in cur.fetchall()]

    # =========================================================================
    # RETRIEVE RETURNS
    # =========================================================================

    def get_book_returns(
        self,
        tenant_id: UUID,
        book_id: UUID,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> ReturnSeries:
        """
        Get return series for a book.

        Args:
            tenant_id: Tenant ID
            book_id: Book ID
            window: Time window
            end_date: End date (defaults to today)

        Returns:
            ReturnSeries for the book
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if end_date is None:
            end_date = date.today()

        days = int(window.value.replace('d', ''))
        start_date = end_date - timedelta(days=days)

        # Get book name
        cur.execute("""
            SELECT name FROM books WHERE id = %s
        """, (str(book_id),))
        book_row = cur.fetchone()
        book_name = book_row['name'] if book_row else 'Unknown'

        # Get returns
        cur.execute("""
            SELECT
                book_id, return_date, daily_pnl, daily_return_pct,
                start_of_day_nav, end_of_day_nav,
                pnl_equity, pnl_rates, pnl_credit, pnl_fx, pnl_other
            FROM book_daily_returns
            WHERE tenant_id = %s
              AND book_id = %s
              AND return_date BETWEEN %s AND %s
            ORDER BY return_date ASC
        """, (str(tenant_id), str(book_id), start_date, end_date))

        returns = []
        for row in cur.fetchall():
            returns.append(DailyReturn(
                entity_id=book_id,
                entity_name=book_name,
                return_date=row['return_date'],
                daily_pnl=Decimal(str(row['daily_pnl'])),
                daily_return_pct=Decimal(str(row['daily_return_pct'])) if row['daily_return_pct'] else None,
                start_nav=Decimal(str(row['start_of_day_nav'])) if row['start_of_day_nav'] else None,
                end_nav=Decimal(str(row['end_of_day_nav'])) if row['end_of_day_nav'] else None,
                pnl_by_pod={
                    'equity': Decimal(str(row['pnl_equity'] or 0)),
                    'rates': Decimal(str(row['pnl_rates'] or 0)),
                    'credit': Decimal(str(row['pnl_credit'] or 0)),
                    'fx': Decimal(str(row['pnl_fx'] or 0)),
                    'other': Decimal(str(row['pnl_other'] or 0)),
                }
            ))

        return ReturnSeries(
            entity_id=book_id,
            entity_name=book_name,
            entity_type='book',
            returns=returns,
            window=window,
        )

    def get_pm_returns(
        self,
        tenant_id: UUID,
        pm_id: UUID,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> ReturnSeries:
        """
        Get return series for a PM.

        Args:
            tenant_id: Tenant ID
            pm_id: PM user ID
            window: Time window
            end_date: End date (defaults to today)

        Returns:
            ReturnSeries for the PM
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if end_date is None:
            end_date = date.today()

        days = int(window.value.replace('d', ''))
        start_date = end_date - timedelta(days=days)

        # Get PM name
        cur.execute("""
            SELECT name FROM users WHERE id = %s
        """, (str(pm_id),))
        pm_row = cur.fetchone()
        pm_name = pm_row['name'] if pm_row else 'Unknown'

        # Get returns
        cur.execute("""
            SELECT
                pm_id, return_date, daily_pnl, daily_return_pct,
                start_of_day_nav, end_of_day_nav,
                pnl_equity, pnl_rates, pnl_credit, pnl_fx, pnl_other,
                book_count
            FROM pm_daily_returns
            WHERE tenant_id = %s
              AND pm_id = %s
              AND return_date BETWEEN %s AND %s
            ORDER BY return_date ASC
        """, (str(tenant_id), str(pm_id), start_date, end_date))

        returns = []
        for row in cur.fetchall():
            returns.append(DailyReturn(
                entity_id=pm_id,
                entity_name=pm_name,
                return_date=row['return_date'],
                daily_pnl=Decimal(str(row['daily_pnl'])),
                daily_return_pct=Decimal(str(row['daily_return_pct'])) if row['daily_return_pct'] else None,
                start_nav=Decimal(str(row['start_of_day_nav'])) if row['start_of_day_nav'] else None,
                end_nav=Decimal(str(row['end_of_day_nav'])) if row['end_of_day_nav'] else None,
                pnl_by_pod={
                    'equity': Decimal(str(row['pnl_equity'] or 0)),
                    'rates': Decimal(str(row['pnl_rates'] or 0)),
                    'credit': Decimal(str(row['pnl_credit'] or 0)),
                    'fx': Decimal(str(row['pnl_fx'] or 0)),
                    'other': Decimal(str(row['pnl_other'] or 0)),
                }
            ))

        return ReturnSeries(
            entity_id=pm_id,
            entity_name=pm_name,
            entity_type='pm',
            returns=returns,
            window=window,
        )

    def get_pod_returns(
        self,
        tenant_id: UUID,
        pod: RiskPod,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> ReturnSeries:
        """
        Get return series for a RiskPod.

        Args:
            tenant_id: Tenant ID
            pod: RiskPod
            window: Time window
            end_date: End date (defaults to today)

        Returns:
            ReturnSeries for the pod
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if end_date is None:
            end_date = date.today()

        days = int(window.value.replace('d', ''))
        start_date = end_date - timedelta(days=days)

        # Get returns
        cur.execute("""
            SELECT
                pod, return_date, daily_pnl, daily_return_pct,
                pm_count, book_count
            FROM pod_daily_returns
            WHERE tenant_id = %s
              AND pod = %s
              AND return_date BETWEEN %s AND %s
            ORDER BY return_date ASC
        """, (str(tenant_id), pod.value, start_date, end_date))

        # Use a placeholder UUID for pod
        pod_id = UUID('00000000-0000-0000-0000-000000000000')

        returns = []
        for row in cur.fetchall():
            returns.append(DailyReturn(
                entity_id=pod_id,
                entity_name=pod.value.upper(),
                return_date=row['return_date'],
                daily_pnl=Decimal(str(row['daily_pnl'])),
                daily_return_pct=Decimal(str(row['daily_return_pct'])) if row['daily_return_pct'] else None,
                start_nav=None,
                end_nav=None,
                pnl_by_pod={pod.value: Decimal(str(row['daily_pnl']))},
            ))

        return ReturnSeries(
            entity_id=pod_id,
            entity_name=pod.value.upper(),
            entity_type='pod',
            returns=returns,
            window=window,
        )

    def get_all_pm_returns(
        self,
        tenant_id: UUID,
        window: ReturnWindow = ReturnWindow.DAY_21,
        end_date: Optional[date] = None,
    ) -> List[ReturnSeries]:
        """
        Get return series for all PMs.

        Args:
            tenant_id: Tenant ID
            window: Time window
            end_date: End date

        Returns:
            List of ReturnSeries for each PM
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get all PMs with returns
        cur.execute("""
            SELECT DISTINCT pm_id FROM pm_daily_returns
            WHERE tenant_id = %s
        """, (str(tenant_id),))

        pm_ids = [UUID(row['pm_id']) for row in cur.fetchall()]

        return [
            self.get_pm_returns(tenant_id, pm_id, window, end_date)
            for pm_id in pm_ids
        ]

    # =========================================================================
    # SUMMARY METHODS
    # =========================================================================

    def get_pm_return_summary(
        self,
        tenant_id: UUID,
        pm_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get return summary for a PM across multiple windows.

        Args:
            tenant_id: Tenant ID
            pm_id: PM user ID

        Returns:
            Summary with returns for 1d, 5d, 21d, 63d windows
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get PM name
        cur.execute("SELECT name FROM users WHERE id = %s", (str(pm_id),))
        pm_row = cur.fetchone()
        pm_name = pm_row['name'] if pm_row else 'Unknown'

        # Get returns for each window
        summary = {
            "pm_id": str(pm_id),
            "pm_name": pm_name,
            "windows": {},
        }

        for window in [ReturnWindow.DAY_1, ReturnWindow.DAY_5,
                       ReturnWindow.DAY_21, ReturnWindow.DAY_63]:
            series = self.get_pm_returns(tenant_id, pm_id, window)
            total_pnl = sum(series.pnl_values)
            avg_return = (
                sum(series.return_values) / len(series.return_values)
                if series.return_values else 0
            )

            summary["windows"][window.value] = {
                "total_pnl": round(total_pnl, 2),
                "avg_daily_return_pct": round(avg_return, 4),
                "data_points": len(series.returns),
                "cumulative_return_pct": round(sum(series.return_values), 4),
            }

        return summary

    def get_firm_return_summary(
        self,
        tenant_id: UUID,
        return_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get firm-wide return summary for a date.

        Args:
            tenant_id: Tenant ID
            return_date: Date (defaults to most recent)

        Returns:
            Firm return summary
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        if return_date is None:
            cur.execute("""
                SELECT MAX(return_date) as max_date
                FROM pm_daily_returns WHERE tenant_id = %s
            """, (str(tenant_id),))
            row = cur.fetchone()
            return_date = row['max_date'] if row and row['max_date'] else date.today()

        # Aggregate all PM returns for the date
        cur.execute("""
            SELECT
                SUM(daily_pnl) as total_pnl,
                AVG(daily_return_pct) as avg_return,
                COUNT(DISTINCT pm_id) as pm_count,
                SUM(book_count) as book_count,
                SUM(pnl_equity) as pnl_equity,
                SUM(pnl_rates) as pnl_rates,
                SUM(pnl_credit) as pnl_credit,
                SUM(pnl_fx) as pnl_fx,
                SUM(pnl_other) as pnl_other
            FROM pm_daily_returns
            WHERE tenant_id = %s AND return_date = %s
        """, (str(tenant_id), return_date))

        result = cur.fetchone()

        # Get top/bottom performers
        cur.execute("""
            SELECT pm_id, daily_pnl, daily_return_pct
            FROM pm_daily_returns pr
            JOIN users u ON pr.pm_id = u.id
            WHERE pr.tenant_id = %s AND pr.return_date = %s
            ORDER BY daily_pnl DESC
            LIMIT 3
        """, (str(tenant_id), return_date))
        top_performers = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT pm_id, daily_pnl, daily_return_pct
            FROM pm_daily_returns pr
            JOIN users u ON pr.pm_id = u.id
            WHERE pr.tenant_id = %s AND pr.return_date = %s
            ORDER BY daily_pnl ASC
            LIMIT 3
        """, (str(tenant_id), return_date))
        bottom_performers = [dict(r) for r in cur.fetchall()]

        return {
            "tenant_id": str(tenant_id),
            "return_date": return_date.isoformat(),
            "firm_pnl": float(result['total_pnl'] or 0),
            "avg_pm_return_pct": float(result['avg_return'] or 0),
            "pm_count": result['pm_count'] or 0,
            "book_count": result['book_count'] or 0,
            "pnl_by_pod": {
                "equity": float(result['pnl_equity'] or 0),
                "rates": float(result['pnl_rates'] or 0),
                "credit": float(result['pnl_credit'] or 0),
                "fx": float(result['pnl_fx'] or 0),
                "other": float(result['pnl_other'] or 0),
            },
            "top_performers": top_performers,
            "bottom_performers": bottom_performers,
        }
