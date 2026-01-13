# RISKCORE Market Data Service
# Provides market indices for dashboard snapshot
# Uses OpenBB for live data when available, fallback to static for demo

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
import random

logger = logging.getLogger(__name__)


# Static market data for demo/fallback when OpenBB unavailable
STATIC_MARKET_DATA = {
    'SPX': {
        'symbol': 'SPX',
        'name': 'S&P 500',
        'base_value': 5234.18,
        'category': 'equity',
    },
    'VIX': {
        'symbol': 'VIX',
        'name': 'VIX',
        'base_value': 14.52,
        'category': 'volatility',
    },
    'US10Y': {
        'symbol': 'US10Y',
        'name': '10Y UST',
        'base_value': 4.25,
        'category': 'rates',
        'format': 'percent',
    },
    'EURUSD': {
        'symbol': 'EURUSD',
        'name': 'EUR/USD',
        'base_value': 1.0842,
        'category': 'fx',
        'format': 'fx',
    },
    'DXY': {
        'symbol': 'DXY',
        'name': 'Dollar Index',
        'base_value': 104.35,
        'category': 'fx',
    },
    'GOLD': {
        'symbol': 'GOLD',
        'name': 'Gold',
        'base_value': 2045.30,
        'category': 'commodity',
    },
}


class MarketDataService:
    """
    Service for fetching market data for the dashboard.

    In production, this would use OpenBB to fetch live data.
    For demo purposes, generates realistic mock data.
    """

    def __init__(self, use_live: bool = False):
        """
        Initialize market data service.

        Args:
            use_live: Whether to attempt live OpenBB data fetch
        """
        self.use_live = use_live
        self._cache: Dict[str, Dict] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=60)  # 1 minute cache

    def get_market_snapshot(
        self,
        symbols: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get market snapshot for dashboard.

        Args:
            symbols: List of symbols to fetch (default: SPX, VIX, US10Y, EURUSD)

        Returns:
            List of market index data with change percentages and sparklines
        """
        if symbols is None:
            symbols = ['SPX', 'VIX', 'US10Y', 'EURUSD']

        # Check cache
        if self._is_cache_valid():
            return [self._cache[s] for s in symbols if s in self._cache]

        # Try live data first if enabled
        if self.use_live:
            try:
                result = self._fetch_live_data(symbols)
                if result:
                    self._update_cache(result)
                    return result
            except Exception as e:
                logger.warning(f"Live data fetch failed, using static: {e}")

        # Fall back to static data with simulated movements
        result = self._generate_demo_data(symbols)
        self._update_cache(result)
        return result

    def get_single_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get quote for a single symbol.

        Args:
            symbol: Market symbol (e.g., 'SPX', 'VIX')

        Returns:
            Quote data or None if not found
        """
        snapshot = self.get_market_snapshot([symbol])
        return snapshot[0] if snapshot else None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_time:
            return False
        return datetime.now(timezone.utc) - self._cache_time < self._cache_ttl

    def _update_cache(self, data: List[Dict]) -> None:
        """Update cache with new data."""
        self._cache = {d['symbol']: d for d in data}
        self._cache_time = datetime.now(timezone.utc)

    def _fetch_live_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch live data from OpenBB.

        Note: This is a placeholder. In production, would integrate with:
        - OpenBB SDK for equities and indices
        - FRED API for rates
        - Various FX providers

        Returns:
            List of market data dicts
        """
        # Placeholder - would use openbb SDK
        # from openbb import obb
        # obb.equity.price.quote(symbol="SPY")
        raise NotImplementedError("Live data fetch requires OpenBB configuration")

    def _generate_demo_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Generate realistic demo data for symbols.

        Creates plausible current values with change percentages
        and sparkline data.
        """
        result = []

        for symbol in symbols:
            if symbol not in STATIC_MARKET_DATA:
                continue

            config = STATIC_MARKET_DATA[symbol]
            base = config['base_value']

            # Generate realistic change percentage based on category
            if config['category'] == 'volatility':
                # VIX is more volatile
                change_pct = random.uniform(-5.0, 5.0)
            elif config['category'] == 'rates':
                # Rates move in basis points
                change_pct = random.uniform(-0.5, 0.5)
            elif config['category'] == 'fx':
                # FX moves less
                change_pct = random.uniform(-0.3, 0.3)
            else:
                # Equities
                change_pct = random.uniform(-1.5, 1.5)

            # Calculate current value
            current_value = base * (1 + change_pct / 100)

            # Generate sparkline (20 data points)
            sparkline = self._generate_sparkline(base, change_pct, 20)

            # Determine direction
            if change_pct > 0.05:
                direction = 'up'
            elif change_pct < -0.05:
                direction = 'down'
            else:
                direction = 'flat'

            # Format value based on type
            if config.get('format') == 'percent':
                formatted_value = f"{current_value:.2f}%"
            elif config.get('format') == 'fx':
                formatted_value = f"{current_value:.4f}"
            else:
                formatted_value = f"{current_value:,.2f}"

            result.append({
                'symbol': symbol,
                'name': config['name'],
                'value': round(current_value, 4),
                'formatted_value': formatted_value,
                'change_pct': round(change_pct, 2),
                'change_direction': direction,
                'sparkline': sparkline,
                'category': config['category'],
                'as_of': datetime.now(timezone.utc).isoformat(),
            })

        return result

    def _generate_sparkline(
        self,
        base_value: float,
        final_change_pct: float,
        points: int,
    ) -> List[float]:
        """
        Generate realistic sparkline data.

        Creates a path from the base value to the final value
        with some random walk variance.
        """
        sparkline = []

        # Target value
        target = base_value * (1 + final_change_pct / 100)

        # Generate path with random walk
        current = base_value
        step = (target - base_value) / points

        for i in range(points):
            # Add some noise
            noise = random.uniform(-0.3, 0.3) * abs(step) if step != 0 else random.uniform(-0.001, 0.001) * base_value
            current = current + step + noise
            sparkline.append(round(current, 4))

        # Ensure last point matches target (close enough)
        sparkline[-1] = round(target, 4)

        return sparkline

    def get_available_symbols(self) -> List[str]:
        """Get list of available market symbols."""
        return list(STATIC_MARKET_DATA.keys())

    def get_symbol_categories(self) -> Dict[str, List[str]]:
        """Get symbols grouped by category."""
        categories: Dict[str, List[str]] = {}
        for symbol, config in STATIC_MARKET_DATA.items():
            cat = config['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(symbol)
        return categories
