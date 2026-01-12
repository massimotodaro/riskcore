# RISKCORE Options Greeks Calculation
# Using FinancePy for Black-Scholes Greeks

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
import logging
import math

import numpy as np
from scipy.stats import norm
import psycopg2
from psycopg2.extras import RealDictCursor

# FinancePy imports
try:
    from financepy.utils.date import Date as FinDate
    from financepy.products.equity.equity_vanilla_option import EquityVanillaOption
    from financepy.utils.global_types import OptionTypes
    from financepy.models.black_scholes import BlackScholes
    FINANCEPY_AVAILABLE = True
except ImportError:
    FINANCEPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class OptionType(str, Enum):
    """Option types."""
    CALL = "call"
    PUT = "put"


class GreeksService:
    """
    Service for calculating options Greeks.

    Provides:
    - Delta: Rate of change of option price w.r.t. underlying price
    - Gamma: Rate of change of delta w.r.t. underlying price
    - Vega: Sensitivity to volatility
    - Theta: Time decay
    - Rho: Sensitivity to interest rates

    Uses FinancePy for Black-Scholes calculations when available,
    falls back to pure Python implementation otherwise.

    All data stays on-premises.
    """

    def __init__(self, conn: psycopg2.extensions.connection):
        """
        Initialize with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    # =========================================================================
    # Black-Scholes Greeks (Pure Python fallback)
    # =========================================================================

    def _d1(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> float:
        """Calculate d1 in Black-Scholes formula."""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    def _d2(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> float:
        """Calculate d2 in Black-Scholes formula."""
        if T <= 0 or sigma <= 0:
            return 0.0
        return self._d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

    def calculate_delta(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: OptionType,
    ) -> float:
        """
        Calculate option delta.

        Delta measures the rate of change of option price with respect to
        changes in the underlying asset's price.

        Args:
            spot_price: Current price of underlying
            strike_price: Strike price of option
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free interest rate (annual)
            volatility: Implied volatility (annual)
            option_type: Call or put

        Returns:
            Delta value (-1 to 1)
        """
        if time_to_expiry <= 0:
            # At expiry
            if option_type == OptionType.CALL:
                return 1.0 if spot_price > strike_price else 0.0
            else:
                return -1.0 if spot_price < strike_price else 0.0

        d1 = self._d1(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)

        if option_type == OptionType.CALL:
            return float(norm.cdf(d1))
        else:
            return float(norm.cdf(d1) - 1)

    def calculate_gamma(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
    ) -> float:
        """
        Calculate option gamma.

        Gamma measures the rate of change in delta with respect to
        changes in the underlying price.

        Returns:
            Gamma value (always positive)
        """
        if time_to_expiry <= 0 or volatility <= 0:
            return 0.0

        d1 = self._d1(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)
        return float(norm.pdf(d1) / (spot_price * volatility * math.sqrt(time_to_expiry)))

    def calculate_vega(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
    ) -> float:
        """
        Calculate option vega.

        Vega measures sensitivity of option price to changes in volatility.
        Returned as change per 1% change in volatility.

        Returns:
            Vega value (always positive)
        """
        if time_to_expiry <= 0:
            return 0.0

        d1 = self._d1(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)
        # Vega per 1% vol change
        return float(spot_price * math.sqrt(time_to_expiry) * norm.pdf(d1) / 100)

    def calculate_theta(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: OptionType,
    ) -> float:
        """
        Calculate option theta.

        Theta measures the rate of decline in option value due to time passage.
        Returned as daily decay (negative for long positions).

        Returns:
            Theta value (typically negative)
        """
        if time_to_expiry <= 0:
            return 0.0

        d1 = self._d1(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)
        d2 = self._d2(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)

        # First term (time decay of underlying volatility component)
        term1 = -(spot_price * volatility * norm.pdf(d1)) / (2 * math.sqrt(time_to_expiry))

        if option_type == OptionType.CALL:
            term2 = -risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        else:
            term2 = risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)

        # Return daily theta (divide annual by 365)
        return float((term1 + term2) / 365)

    def calculate_rho(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: OptionType,
    ) -> float:
        """
        Calculate option rho.

        Rho measures sensitivity of option price to changes in interest rate.
        Returned as change per 1% change in rate.

        Returns:
            Rho value
        """
        if time_to_expiry <= 0:
            return 0.0

        d2 = self._d2(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility)

        if option_type == OptionType.CALL:
            return float(strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100)
        else:
            return float(-strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100)

    def calculate_all_greeks(
        self,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: OptionType,
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option.

        Args:
            spot_price: Current price of underlying
            strike_price: Strike price
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free rate (annual, e.g., 0.05 for 5%)
            volatility: Implied volatility (annual, e.g., 0.20 for 20%)
            option_type: Call or put

        Returns:
            Dict with all Greeks
        """
        return {
            "delta": self.calculate_delta(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type),
            "gamma": self.calculate_gamma(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility),
            "vega": self.calculate_vega(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility),
            "theta": self.calculate_theta(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type),
            "rho": self.calculate_rho(spot_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type),
            "spot_price": spot_price,
            "strike_price": strike_price,
            "time_to_expiry": time_to_expiry,
            "volatility": volatility,
            "option_type": option_type.value,
        }

    # =========================================================================
    # Position-Level Greeks
    # =========================================================================

    def calculate_position_greeks(
        self,
        position_id: UUID,
        spot_price: Optional[float] = None,
        volatility: float = 0.20,
        risk_free_rate: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Calculate Greeks for an options position.

        Args:
            position_id: Position ID
            spot_price: Current spot price (if None, uses security price)
            volatility: Implied volatility (default 20%)
            risk_free_rate: Risk-free rate (default 5%)

        Returns:
            Dict with position Greeks
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get position and security details
        cur.execute("""
            SELECT
                p.id,
                p.quantity,
                p.market_value,
                p.direction,
                s.id as security_id,
                s.ticker,
                s.name,
                s.asset_class,
                s.option_type,
                s.strike_price,
                s.expiration_date,
                s.underlying_security_id
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.id = %s
        """, (str(position_id),))

        position = cur.fetchone()

        if not position:
            return {"error": f"Position {position_id} not found"}

        # Check if it's an option
        if position["asset_class"] != "option":
            return {
                "position_id": str(position_id),
                "error": "Position is not an option",
                "asset_class": position["asset_class"],
            }

        # Get underlying price if not provided
        if spot_price is None and position["underlying_security_id"]:
            cur.execute("""
                SELECT close_price
                FROM security_prices
                WHERE security_id = %s
                ORDER BY price_date DESC
                LIMIT 1
            """, (str(position["underlying_security_id"]),))
            price_row = cur.fetchone()
            if price_row:
                spot_price = float(price_row["close_price"])

        if spot_price is None:
            return {
                "position_id": str(position_id),
                "error": "Could not determine underlying price",
            }

        # Calculate time to expiry
        if position["expiration_date"]:
            today = date.today()
            expiry = position["expiration_date"]
            if isinstance(expiry, datetime):
                expiry = expiry.date()
            days_to_expiry = (expiry - today).days
            time_to_expiry = max(0, days_to_expiry) / 365.0
        else:
            return {
                "position_id": str(position_id),
                "error": "No expiration date for option",
            }

        # Determine option type
        opt_type_str = position["option_type"]
        if opt_type_str and opt_type_str.lower() in ["call", "c"]:
            opt_type = OptionType.CALL
        else:
            opt_type = OptionType.PUT

        strike = float(position["strike_price"]) if position["strike_price"] else spot_price
        quantity = float(position["quantity"])

        # Calculate Greeks
        greeks = self.calculate_all_greeks(
            spot_price=spot_price,
            strike_price=strike,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            volatility=volatility,
            option_type=opt_type,
        )

        # Scale by position size (options typically represent 100 shares)
        contract_multiplier = 100
        position_size = quantity * contract_multiplier

        return {
            "position_id": str(position_id),
            "ticker": position["ticker"],
            "quantity": quantity,
            "direction": position["direction"],
            "option_type": opt_type.value,
            "strike_price": strike,
            "spot_price": spot_price,
            "days_to_expiry": int(time_to_expiry * 365),
            "volatility": volatility,
            # Per-contract Greeks
            "delta": greeks["delta"],
            "gamma": greeks["gamma"],
            "vega": greeks["vega"],
            "theta": greeks["theta"],
            "rho": greeks["rho"],
            # Position-level Greeks (scaled by quantity)
            "position_delta": greeks["delta"] * position_size,
            "position_gamma": greeks["gamma"] * position_size,
            "position_vega": greeks["vega"] * position_size,
            "position_theta": greeks["theta"] * position_size,
            "position_rho": greeks["rho"] * position_size,
        }

    # =========================================================================
    # Book-Level Greeks
    # =========================================================================

    def calculate_book_greeks(
        self,
        book_id: UUID,
        tenant_id: UUID,
        volatility: float = 0.20,
        risk_free_rate: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate Greeks for all options in a book.

        Args:
            book_id: Book ID
            tenant_id: Tenant ID
            volatility: Default implied volatility
            risk_free_rate: Risk-free rate

        Returns:
            Dict with book-level Greeks
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get all option positions
        cur.execute("""
            SELECT
                p.id as position_id,
                p.quantity,
                p.direction,
                s.asset_class,
                s.option_type,
                s.strike_price,
                s.expiration_date,
                s.underlying_security_id,
                s.ticker
            FROM positions p
            JOIN securities s ON p.security_id = s.id
            WHERE p.book_id = %s AND p.tenant_id = %s
              AND s.asset_class = 'option'
        """, (str(book_id), str(tenant_id)))

        options = cur.fetchall()

        if not options:
            return {
                "book_id": str(book_id),
                "option_count": 0,
                "net_delta": 0.0,
                "net_gamma": 0.0,
                "net_vega": 0.0,
                "net_theta": 0.0,
                "net_rho": 0.0,
                "note": "No options positions found",
            }

        # Calculate Greeks for each position
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        total_rho = 0.0
        position_details = []

        for opt in options:
            result = self.calculate_position_greeks(
                position_id=opt["position_id"],
                volatility=volatility,
                risk_free_rate=risk_free_rate,
            )

            if "error" not in result:
                # Adjust sign for direction
                direction_mult = 1 if opt["direction"] == "long" else -1

                total_delta += result["position_delta"] * direction_mult
                total_gamma += result["position_gamma"] * direction_mult
                total_vega += result["position_vega"] * direction_mult
                total_theta += result["position_theta"] * direction_mult
                total_rho += result["position_rho"] * direction_mult

                position_details.append({
                    "ticker": opt["ticker"],
                    "delta": result["position_delta"] * direction_mult,
                    "gamma": result["position_gamma"] * direction_mult,
                })

        return {
            "book_id": str(book_id),
            "option_count": len(options),
            "net_delta": round(total_delta, 2),
            "net_gamma": round(total_gamma, 4),
            "net_vega": round(total_vega, 2),
            "net_theta": round(total_theta, 2),
            "net_rho": round(total_rho, 2),
            "positions": position_details[:10],  # Top 10 by contribution
        }
