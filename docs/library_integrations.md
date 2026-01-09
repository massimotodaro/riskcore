# RISKCORE Library Integrations

**Purpose:** Integration guide for OpenBB, FinancePy, and Riskfolio-Lib
**Target:** RISKCORE backend developers

---

## Overview

RISKCORE leverages three best-in-class open-source libraries:

| Library | Purpose | Version |
|---------|---------|---------|
| **OpenBB** | Market data ingestion | 4.x |
| **FinancePy** | Derivatives pricing & Greeks | 0.350+ |
| **Riskfolio-Lib** | Portfolio risk calculations | 7.x |

---

## 1. OpenBB Integration

### Installation

```bash
pip install openbb
```

### Purpose in RISKCORE

- Fetch real-time and historical prices
- Get fundamental data for securities
- Source market data from multiple providers
- Feed data into risk calculations

### Basic Usage

```python
from openbb import obb

# Get historical prices for a single stock
data = obb.equity.price.historical("AAPL")
df = data.to_dataframe()
print(df.head())
```

### RISKCORE Integration Example

```python
"""
riskcore/backend/services/market_data.py
OpenBB integration for RISKCORE market data service
"""

from openbb import obb
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd


class MarketDataService:
    """Service for fetching market data via OpenBB."""

    def __init__(self, provider: str = "yfinance"):
        """
        Initialize market data service.

        Args:
            provider: Data provider (yfinance, polygon, alpha_vantage, etc.)
        """
        self.provider = provider

    def get_prices(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical prices for multiple symbols.

        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, 5m, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        result = obb.equity.price.historical(
            symbol=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider=self.provider
        )

        return result.to_dataframe()

    def get_quote(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get real-time quotes for symbols.

        Args:
            symbols: List of ticker symbols

        Returns:
            DataFrame with current quotes
        """
        result = obb.equity.price.quote(
            symbol=symbols,
            provider=self.provider
        )
        return result.to_dataframe()

    def get_company_info(self, symbol: str) -> dict:
        """
        Get company fundamental information.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with company info
        """
        result = obb.equity.profile(symbol=symbol)
        return result.to_dict()

    def get_options_chain(self, symbol: str) -> pd.DataFrame:
        """
        Get options chain for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            DataFrame with options data
        """
        result = obb.derivatives.options.chains(
            symbol=symbol,
            provider=self.provider
        )
        return result.to_dataframe()


# Usage example
if __name__ == "__main__":
    service = MarketDataService()

    # Fetch prices for portfolio
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    prices = service.get_prices(symbols, start_date="2024-01-01")

    print("Historical Prices:")
    print(prices.tail())

    # Get current quotes
    quotes = service.get_quote(symbols)
    print("\nCurrent Quotes:")
    print(quotes)
```

### Multi-Asset Data Fetching

```python
"""
Fetch data across multiple asset classes
"""

from openbb import obb
import pandas as pd


class MultiAssetDataService:
    """Fetch data for equities, bonds, FX, and crypto."""

    def get_equity_data(self, symbols: List[str]) -> pd.DataFrame:
        """Fetch equity prices."""
        return obb.equity.price.historical(symbol=symbols).to_dataframe()

    def get_treasury_rates(self) -> pd.DataFrame:
        """Fetch US Treasury rates."""
        return obb.fixedincome.rate.treasury(provider="federal_reserve").to_dataframe()

    def get_fx_rates(self, pairs: List[str]) -> pd.DataFrame:
        """
        Fetch FX rates.

        Args:
            pairs: Currency pairs like ["EURUSD", "GBPUSD"]
        """
        return obb.currency.price.historical(symbol=pairs).to_dataframe()

    def get_crypto_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch cryptocurrency prices.

        Args:
            symbols: Crypto symbols like ["BTC", "ETH"]
        """
        # Format for crypto provider
        crypto_symbols = [f"{s}-USD" for s in symbols]
        return obb.crypto.price.historical(symbol=crypto_symbols).to_dataframe()

    def get_economic_indicators(self) -> dict:
        """Fetch key economic indicators."""
        indicators = {}

        # GDP
        indicators['gdp'] = obb.economy.gdp.nominal(
            provider="oecd"
        ).to_dataframe()

        # CPI / Inflation
        indicators['cpi'] = obb.economy.cpi(
            provider="fred"
        ).to_dataframe()

        # Unemployment
        indicators['unemployment'] = obb.economy.unemployment(
            provider="oecd"
        ).to_dataframe()

        return indicators


# Usage
if __name__ == "__main__":
    service = MultiAssetDataService()

    # Get treasury curve
    treasuries = service.get_treasury_rates()
    print("Treasury Rates:")
    print(treasuries.tail())
```

---

## 2. FinancePy Integration

### Installation

```bash
pip install financepy
```

**Note:** First import may take 30-60 seconds as Numba compiles the models.

### Purpose in RISKCORE

- Price fixed income instruments (bonds, swaps)
- Calculate derivatives Greeks (delta, gamma, vega, theta)
- Build yield curves
- Value equity options

### Basic Usage

```python
from financepy.utils.date import Date
from financepy.products.bonds import Bond
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes

# Create a bond
issue_date = Date(15, 1, 2020)
maturity_date = Date(15, 1, 2030)
coupon = 0.05  # 5%
freq = FrequencyTypes.SEMI_ANNUAL
accrual_type = DayCountTypes.ACT_ACT_ICMA

bond = Bond(issue_date, maturity_date, coupon, freq, accrual_type)

# Price the bond
settlement_date = Date(15, 1, 2025)
ytm = 0.045  # 4.5% yield
clean_price = bond.clean_price_from_ytm(settlement_date, ytm)
print(f"Clean Price: {clean_price:.4f}")
```

### RISKCORE Integration Example

```python
"""
riskcore/backend/services/derivatives_pricing.py
FinancePy integration for derivatives pricing
"""

from financepy.utils.date import Date
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes
from financepy.products.bonds import Bond, BondZeroCoupon
from financepy.products.equity import EquityVanillaOption
from financepy.models.black_scholes import BlackScholes
from financepy.market.curves import DiscountCurveFlat
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class BondPricingResult:
    """Result of bond pricing calculation."""
    clean_price: float
    dirty_price: float
    accrued_interest: float
    yield_to_maturity: float
    duration: float
    modified_duration: float
    convexity: float
    dv01: float


@dataclass
class OptionGreeks:
    """Greeks for an option position."""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    value: float


class DerivativesPricingService:
    """Service for pricing derivatives using FinancePy."""

    @staticmethod
    def _to_fp_date(dt: datetime) -> Date:
        """Convert Python datetime to FinancePy Date."""
        return Date(dt.day, dt.month, dt.year)

    def price_bond(
        self,
        issue_date: datetime,
        maturity_date: datetime,
        coupon_rate: float,
        settlement_date: datetime,
        yield_to_maturity: float,
        frequency: str = "semi_annual",
        face_value: float = 100.0
    ) -> BondPricingResult:
        """
        Price a fixed-rate bond.

        Args:
            issue_date: Bond issue date
            maturity_date: Bond maturity date
            coupon_rate: Annual coupon rate (e.g., 0.05 for 5%)
            settlement_date: Settlement date for pricing
            yield_to_maturity: YTM for pricing
            frequency: Coupon frequency (annual, semi_annual, quarterly)
            face_value: Face value of bond

        Returns:
            BondPricingResult with price and risk metrics
        """
        # Map frequency
        freq_map = {
            "annual": FrequencyTypes.ANNUAL,
            "semi_annual": FrequencyTypes.SEMI_ANNUAL,
            "quarterly": FrequencyTypes.QUARTERLY,
            "monthly": FrequencyTypes.MONTHLY
        }
        freq = freq_map.get(frequency, FrequencyTypes.SEMI_ANNUAL)

        # Create bond
        bond = Bond(
            issue_dt=self._to_fp_date(issue_date),
            maturity_dt=self._to_fp_date(maturity_date),
            coupon=coupon_rate,
            freq_type=freq,
            dc_type=DayCountTypes.ACT_ACT_ICMA,
            face_amount=face_value
        )

        settle = self._to_fp_date(settlement_date)

        # Calculate prices
        clean_price = bond.clean_price_from_ytm(settle, yield_to_maturity)
        dirty_price = bond.dirty_price_from_ytm(settle, yield_to_maturity)
        accrued = bond.accrued_interest(settle)

        # Calculate risk metrics
        duration = bond.dollar_duration(settle, yield_to_maturity)
        mod_duration = bond.modified_duration(settle, yield_to_maturity)
        convexity = bond.convexity_from_ytm(settle, yield_to_maturity)
        dv01 = bond.dollar_duration(settle, yield_to_maturity) / 100

        return BondPricingResult(
            clean_price=clean_price,
            dirty_price=dirty_price,
            accrued_interest=accrued,
            yield_to_maturity=yield_to_maturity,
            duration=duration,
            modified_duration=mod_duration,
            convexity=convexity,
            dv01=dv01
        )

    def price_equity_option(
        self,
        spot_price: float,
        strike_price: float,
        expiry_date: datetime,
        valuation_date: datetime,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        option_type: str = "call",
        is_european: bool = True
    ) -> OptionGreeks:
        """
        Price an equity option and calculate Greeks.

        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            expiry_date: Option expiration date
            valuation_date: Valuation date
            volatility: Implied volatility (e.g., 0.25 for 25%)
            risk_free_rate: Risk-free rate
            dividend_yield: Continuous dividend yield
            option_type: "call" or "put"
            is_european: True for European, False for American

        Returns:
            OptionGreeks with value and sensitivities
        """
        from financepy.utils.global_types import OptionTypes

        opt_type = OptionTypes.EUROPEAN_CALL if option_type.lower() == "call" else OptionTypes.EUROPEAN_PUT

        option = EquityVanillaOption(
            expiry_dt=self._to_fp_date(expiry_date),
            strike_price=strike_price,
            option_type=opt_type
        )

        val_date = self._to_fp_date(valuation_date)

        # Create discount curve
        discount_curve = DiscountCurveFlat(val_date, risk_free_rate)

        # Create model
        model = BlackScholes(volatility)

        # Calculate value
        value = option.value(
            val_date,
            spot_price,
            discount_curve,
            dividend_yield,
            model
        )

        # Calculate Greeks
        delta = option.delta(val_date, spot_price, discount_curve, dividend_yield, model)
        gamma = option.gamma(val_date, spot_price, discount_curve, dividend_yield, model)
        vega = option.vega(val_date, spot_price, discount_curve, dividend_yield, model)
        theta = option.theta(val_date, spot_price, discount_curve, dividend_yield, model)
        rho = option.rho(val_date, spot_price, discount_curve, dividend_yield, model)

        return OptionGreeks(
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
            rho=rho,
            value=value
        )

    def calculate_portfolio_greeks(
        self,
        positions: list[dict]
    ) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for a portfolio of options.

        Args:
            positions: List of position dicts with option params and quantity

        Returns:
            Aggregated Greeks for the portfolio
        """
        total_greeks = {
            "delta": 0.0,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
            "value": 0.0
        }

        for pos in positions:
            greeks = self.price_equity_option(
                spot_price=pos["spot_price"],
                strike_price=pos["strike_price"],
                expiry_date=pos["expiry_date"],
                valuation_date=pos["valuation_date"],
                volatility=pos["volatility"],
                risk_free_rate=pos["risk_free_rate"],
                dividend_yield=pos.get("dividend_yield", 0.0),
                option_type=pos["option_type"]
            )

            quantity = pos["quantity"]
            total_greeks["delta"] += greeks.delta * quantity
            total_greeks["gamma"] += greeks.gamma * quantity
            total_greeks["vega"] += greeks.vega * quantity
            total_greeks["theta"] += greeks.theta * quantity
            total_greeks["rho"] += greeks.rho * quantity
            total_greeks["value"] += greeks.value * quantity

        return total_greeks


# Usage example
if __name__ == "__main__":
    service = DerivativesPricingService()

    # Price a corporate bond
    bond_result = service.price_bond(
        issue_date=datetime(2020, 1, 15),
        maturity_date=datetime(2030, 1, 15),
        coupon_rate=0.05,
        settlement_date=datetime(2025, 1, 15),
        yield_to_maturity=0.045
    )

    print("Bond Pricing Result:")
    print(f"  Clean Price: {bond_result.clean_price:.4f}")
    print(f"  Dirty Price: {bond_result.dirty_price:.4f}")
    print(f"  Modified Duration: {bond_result.modified_duration:.4f}")
    print(f"  DV01: {bond_result.dv01:.4f}")

    # Price an equity option
    greeks = service.price_equity_option(
        spot_price=150.0,
        strike_price=155.0,
        expiry_date=datetime(2025, 6, 15),
        valuation_date=datetime(2025, 1, 15),
        volatility=0.25,
        risk_free_rate=0.05,
        option_type="call"
    )

    print("\nOption Greeks:")
    print(f"  Value: ${greeks.value:.2f}")
    print(f"  Delta: {greeks.delta:.4f}")
    print(f"  Gamma: {greeks.gamma:.4f}")
    print(f"  Vega: {greeks.vega:.4f}")
    print(f"  Theta: {greeks.theta:.4f}")
```

---

## 3. Riskfolio-Lib Integration

### Installation

```bash
pip install riskfolio-lib
```

### Purpose in RISKCORE

- Calculate portfolio VaR and CVaR
- Risk decomposition and attribution
- Portfolio optimization
- Stress testing

### Basic Usage

```python
import riskfolio as rp
import pandas as pd
import yfinance as yf

# Get returns data
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
data = yf.download(symbols, start="2022-01-01", end="2024-01-01")
returns = data["Adj Close"].pct_change().dropna()

# Create portfolio
port = rp.Portfolio(returns=returns)
port.assets_stats(method_mu="hist", method_cov="hist")

# Optimize for minimum CVaR
w = port.optimization(model="Classic", rm="CVaR", obj="MinRisk")
print(w)
```

### RISKCORE Integration Example

```python
"""
riskcore/backend/services/risk_analytics.py
Riskfolio-Lib integration for portfolio risk calculations
"""

import riskfolio as rp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskMeasure(Enum):
    """Supported risk measures."""
    STANDARD_DEVIATION = "MV"
    MEAN_ABSOLUTE_DEVIATION = "MAD"
    CVaR = "CVaR"  # Conditional Value at Risk
    EVaR = "EVaR"  # Entropic Value at Risk
    MAX_DRAWDOWN = "MDD"
    ULCER_INDEX = "UCI"
    VaR = "VaR"


@dataclass
class PortfolioRiskMetrics:
    """Portfolio risk analysis results."""
    expected_return: float
    volatility: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    beta: Optional[float] = None


@dataclass
class RiskContribution:
    """Risk contribution by asset."""
    asset: str
    weight: float
    marginal_risk: float
    risk_contribution: float
    risk_contribution_pct: float


class RiskAnalyticsService:
    """Service for portfolio risk analytics using Riskfolio-Lib."""

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize risk analytics service.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculations
        """
        self.risk_free_rate = risk_free_rate

    def calculate_returns(
        self,
        prices: pd.DataFrame,
        method: str = "simple"
    ) -> pd.DataFrame:
        """
        Calculate returns from price data.

        Args:
            prices: DataFrame with price history (columns = assets)
            method: "simple" or "log" returns

        Returns:
            DataFrame with returns
        """
        if method == "log":
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()

        return returns.dropna()

    def calculate_portfolio_risk(
        self,
        returns: pd.DataFrame,
        weights: pd.Series,
        confidence_levels: List[float] = [0.95, 0.99]
    ) -> PortfolioRiskMetrics:
        """
        Calculate comprehensive risk metrics for a portfolio.

        Args:
            returns: DataFrame with asset returns
            weights: Series with portfolio weights (should sum to 1)
            confidence_levels: Confidence levels for VaR/CVaR

        Returns:
            PortfolioRiskMetrics with all risk measures
        """
        # Ensure weights align with returns columns
        weights = weights.reindex(returns.columns).fillna(0)

        # Portfolio returns
        portfolio_returns = (returns * weights).sum(axis=1)

        # Basic statistics
        expected_return = portfolio_returns.mean() * 252  # Annualized
        volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized

        # VaR (Historical)
        var_95 = -np.percentile(portfolio_returns, 5) * np.sqrt(252)
        var_99 = -np.percentile(portfolio_returns, 1) * np.sqrt(252)

        # CVaR (Expected Shortfall)
        cvar_95 = -portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean() * np.sqrt(252)
        cvar_99 = -portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 1)].mean() * np.sqrt(252)

        # Sharpe Ratio
        excess_return = expected_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0

        # Maximum Drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = cumulative / rolling_max - 1
        max_drawdown = drawdowns.min()

        return PortfolioRiskMetrics(
            expected_return=expected_return,
            volatility=volatility,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown
        )

    def calculate_var_cvar_riskfolio(
        self,
        returns: pd.DataFrame,
        weights: pd.Series,
        alpha: float = 0.05
    ) -> Tuple[float, float]:
        """
        Calculate VaR and CVaR using Riskfolio-Lib.

        Args:
            returns: Asset returns DataFrame
            weights: Portfolio weights
            alpha: Significance level (default 5%)

        Returns:
            Tuple of (VaR, CVaR)
        """
        # Create portfolio object
        port = rp.Portfolio(returns=returns)

        # Calculate stats
        port.assets_stats(method_mu='hist', method_cov='hist')

        # Convert weights to required format
        w = weights.values.reshape(-1, 1)

        # Portfolio return
        port_return = (returns * weights).sum(axis=1)

        # VaR
        var = rp.RiskFunctions.VaR_Hist(port_return.values, alpha=alpha)

        # CVaR
        cvar = rp.RiskFunctions.CVaR_Hist(port_return.values, alpha=alpha)

        return var, cvar

    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        risk_measure: RiskMeasure = RiskMeasure.CVaR,
        objective: str = "Sharpe",
        constraints: Optional[Dict] = None
    ) -> pd.Series:
        """
        Optimize portfolio weights.

        Args:
            returns: Asset returns DataFrame
            risk_measure: Risk measure for optimization
            objective: "MinRisk", "MaxRet", "Sharpe", or "Utility"
            constraints: Optional constraints dict

        Returns:
            Optimal portfolio weights
        """
        # Create portfolio
        port = rp.Portfolio(returns=returns)

        # Calculate statistics
        port.assets_stats(method_mu='hist', method_cov='hist')

        # Apply constraints if provided
        if constraints:
            if "max_weight" in constraints:
                port.upperlng = constraints["max_weight"]
            if "min_weight" in constraints:
                port.lowerlng = constraints["min_weight"]

        # Optimize
        weights = port.optimization(
            model='Classic',
            rm=risk_measure.value,
            obj=objective,
            rf=self.risk_free_rate / 252,  # Daily risk-free rate
            hist=True
        )

        return pd.Series(weights.flatten(), index=returns.columns)

    def risk_contribution_analysis(
        self,
        returns: pd.DataFrame,
        weights: pd.Series
    ) -> List[RiskContribution]:
        """
        Calculate risk contribution by asset.

        Args:
            returns: Asset returns DataFrame
            weights: Portfolio weights

        Returns:
            List of RiskContribution for each asset
        """
        # Covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        # Portfolio variance
        w = weights.values
        port_var = np.dot(w.T, np.dot(cov_matrix.values, w))
        port_vol = np.sqrt(port_var)

        # Marginal contribution to risk
        marginal_risk = np.dot(cov_matrix.values, w) / port_vol

        # Component contribution to risk
        component_risk = w * marginal_risk

        results = []
        for i, asset in enumerate(returns.columns):
            results.append(RiskContribution(
                asset=asset,
                weight=weights[asset],
                marginal_risk=marginal_risk[i],
                risk_contribution=component_risk[i],
                risk_contribution_pct=component_risk[i] / port_vol
            ))

        return results

    def stress_test(
        self,
        returns: pd.DataFrame,
        weights: pd.Series,
        scenarios: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        Run stress test scenarios on portfolio.

        Args:
            returns: Asset returns DataFrame
            weights: Portfolio weights
            scenarios: Dict of scenario name -> {asset: shock}

        Returns:
            DataFrame with scenario impacts
        """
        results = []

        # Current portfolio value (normalized to 1)
        current_value = 1.0

        for scenario_name, shocks in scenarios.items():
            scenario_return = 0.0

            for asset, shock in shocks.items():
                if asset in weights.index:
                    scenario_return += weights[asset] * shock

            new_value = current_value * (1 + scenario_return)
            pnl = new_value - current_value
            pnl_pct = scenario_return * 100

            results.append({
                "scenario": scenario_name,
                "portfolio_return": scenario_return,
                "pnl_pct": pnl_pct,
                "new_value": new_value
            })

        return pd.DataFrame(results)


# Usage example
if __name__ == "__main__":
    # Sample data
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="D")

    # Simulated returns
    returns = pd.DataFrame({
        "AAPL": np.random.normal(0.001, 0.02, 252),
        "MSFT": np.random.normal(0.0008, 0.018, 252),
        "GOOGL": np.random.normal(0.0009, 0.022, 252),
        "AMZN": np.random.normal(0.0007, 0.025, 252),
    }, index=dates)

    # Portfolio weights
    weights = pd.Series({
        "AAPL": 0.30,
        "MSFT": 0.25,
        "GOOGL": 0.25,
        "AMZN": 0.20
    })

    # Initialize service
    service = RiskAnalyticsService(risk_free_rate=0.05)

    # Calculate risk metrics
    metrics = service.calculate_portfolio_risk(returns, weights)

    print("Portfolio Risk Metrics:")
    print(f"  Expected Return: {metrics.expected_return:.2%}")
    print(f"  Volatility: {metrics.volatility:.2%}")
    print(f"  VaR (95%): {metrics.var_95:.2%}")
    print(f"  CVaR (95%): {metrics.cvar_95:.2%}")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")

    # Optimize portfolio
    optimal_weights = service.optimize_portfolio(
        returns,
        risk_measure=RiskMeasure.CVaR,
        objective="Sharpe"
    )

    print("\nOptimal Weights (Min CVaR, Max Sharpe):")
    print(optimal_weights)

    # Risk contribution
    contributions = service.risk_contribution_analysis(returns, weights)

    print("\nRisk Contribution Analysis:")
    for rc in contributions:
        print(f"  {rc.asset}: {rc.risk_contribution_pct:.1%} of portfolio risk")

    # Stress test
    scenarios = {
        "Market Crash (-20%)": {"AAPL": -0.20, "MSFT": -0.18, "GOOGL": -0.22, "AMZN": -0.25},
        "Tech Selloff (-15%)": {"AAPL": -0.15, "MSFT": -0.12, "GOOGL": -0.18, "AMZN": -0.20},
        "Mild Correction (-5%)": {"AAPL": -0.05, "MSFT": -0.04, "GOOGL": -0.06, "AMZN": -0.07},
        "Rally (+10%)": {"AAPL": 0.10, "MSFT": 0.08, "GOOGL": 0.12, "AMZN": 0.15},
    }

    stress_results = service.stress_test(returns, weights, scenarios)

    print("\nStress Test Results:")
    print(stress_results.to_string(index=False))
```

---

## 4. Combined Integration: RISKCORE Risk Engine

```python
"""
riskcore/backend/services/risk_engine.py
Combined integration of all libraries for RISKCORE risk engine
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

# Import our service modules
from market_data import MarketDataService
from derivatives_pricing import DerivativesPricingService, OptionGreeks
from risk_analytics import RiskAnalyticsService, PortfolioRiskMetrics, RiskMeasure


class RiskCoreEngine:
    """
    Main risk engine combining OpenBB, FinancePy, and Riskfolio-Lib.

    This is the core service that RISKCORE uses to:
    1. Fetch market data (OpenBB)
    2. Price derivatives (FinancePy)
    3. Calculate risk metrics (Riskfolio-Lib)
    """

    def __init__(
        self,
        market_data_provider: str = "yfinance",
        risk_free_rate: float = 0.05
    ):
        """
        Initialize the risk engine.

        Args:
            market_data_provider: Provider for OpenBB
            risk_free_rate: Annual risk-free rate
        """
        self.market_data = MarketDataService(provider=market_data_provider)
        self.derivatives = DerivativesPricingService()
        self.risk = RiskAnalyticsService(risk_free_rate=risk_free_rate)
        self.risk_free_rate = risk_free_rate

    def analyze_portfolio(
        self,
        positions: List[Dict],
        lookback_days: int = 252
    ) -> Dict:
        """
        Full portfolio analysis.

        Args:
            positions: List of position dicts with symbol, quantity, asset_type
            lookback_days: Days of history for risk calculations

        Returns:
            Complete portfolio analysis
        """
        # Separate equity and derivative positions
        equity_positions = [p for p in positions if p.get("asset_type") == "equity"]
        option_positions = [p for p in positions if p.get("asset_type") == "option"]
        bond_positions = [p for p in positions if p.get("asset_type") == "bond"]

        results = {
            "timestamp": datetime.now().isoformat(),
            "positions_count": len(positions),
            "equity_analysis": None,
            "options_greeks": None,
            "bond_metrics": None,
            "portfolio_risk": None
        }

        # === EQUITY ANALYSIS ===
        if equity_positions:
            symbols = [p["symbol"] for p in equity_positions]
            quantities = {p["symbol"]: p["quantity"] for p in equity_positions}

            # Fetch prices via OpenBB
            prices = self.market_data.get_prices(
                symbols,
                start_date=(datetime.now() - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
            )

            # Get current quotes for market values
            quotes = self.market_data.get_quote(symbols)

            # Calculate market values and weights
            market_values = {}
            for symbol in symbols:
                if symbol in quotes.index:
                    price = quotes.loc[symbol, "last_price"]
                    market_values[symbol] = price * quantities[symbol]

            total_equity_value = sum(market_values.values())
            weights = pd.Series({s: mv / total_equity_value for s, mv in market_values.items()})

            # Calculate returns
            returns = self.risk.calculate_returns(prices["close"].unstack(level=0))

            # Risk metrics via Riskfolio-Lib
            risk_metrics = self.risk.calculate_portfolio_risk(returns, weights)

            # Risk contribution
            risk_contrib = self.risk.risk_contribution_analysis(returns, weights)

            results["equity_analysis"] = {
                "total_value": total_equity_value,
                "positions": market_values,
                "weights": weights.to_dict(),
                "risk_metrics": risk_metrics.__dict__,
                "risk_contributions": [rc.__dict__ for rc in risk_contrib]
            }

        # === OPTIONS ANALYSIS ===
        if option_positions:
            # Price each option via FinancePy
            portfolio_greeks = self.derivatives.calculate_portfolio_greeks([
                {
                    "spot_price": p["spot_price"],
                    "strike_price": p["strike_price"],
                    "expiry_date": p["expiry_date"],
                    "valuation_date": datetime.now(),
                    "volatility": p["implied_vol"],
                    "risk_free_rate": self.risk_free_rate,
                    "option_type": p["option_type"],
                    "quantity": p["quantity"]
                }
                for p in option_positions
            ])

            results["options_greeks"] = portfolio_greeks

        # === BOND ANALYSIS ===
        if bond_positions:
            bond_metrics = []
            total_dv01 = 0

            for bond in bond_positions:
                pricing = self.derivatives.price_bond(
                    issue_date=bond["issue_date"],
                    maturity_date=bond["maturity_date"],
                    coupon_rate=bond["coupon_rate"],
                    settlement_date=datetime.now(),
                    yield_to_maturity=bond["ytm"]
                )

                position_dv01 = pricing.dv01 * bond["quantity"] / 100
                total_dv01 += position_dv01

                bond_metrics.append({
                    "name": bond.get("name", "Bond"),
                    "clean_price": pricing.clean_price,
                    "modified_duration": pricing.modified_duration,
                    "dv01": position_dv01
                })

            results["bond_metrics"] = {
                "positions": bond_metrics,
                "total_dv01": total_dv01
            }

        # === AGGREGATE PORTFOLIO RISK ===
        # Combine all position values
        total_value = 0
        if results["equity_analysis"]:
            total_value += results["equity_analysis"]["total_value"]
        if results["options_greeks"]:
            total_value += results["options_greeks"]["value"]

        results["portfolio_risk"] = {
            "total_value": total_value,
            "total_delta": results["options_greeks"]["delta"] if results["options_greeks"] else 0,
            "total_dv01": results["bond_metrics"]["total_dv01"] if results["bond_metrics"] else 0
        }

        return results


# Usage example
if __name__ == "__main__":
    engine = RiskCoreEngine()

    # Sample portfolio
    positions = [
        {"symbol": "AAPL", "quantity": 100, "asset_type": "equity"},
        {"symbol": "MSFT", "quantity": 50, "asset_type": "equity"},
        {"symbol": "GOOGL", "quantity": 30, "asset_type": "equity"},
    ]

    # Run analysis
    analysis = engine.analyze_portfolio(positions)

    print("Portfolio Analysis:")
    print(f"  Total Equity Value: ${analysis['equity_analysis']['total_value']:,.2f}")
    print(f"  VaR (95%): {analysis['equity_analysis']['risk_metrics']['var_95']:.2%}")
    print(f"  Sharpe Ratio: {analysis['equity_analysis']['risk_metrics']['sharpe_ratio']:.2f}")
```

---

## 5. Requirements

Add to `backend/requirements.txt`:

```text
# Market Data
openbb>=4.0.0

# Derivatives Pricing
financepy>=0.350

# Risk Analytics
riskfolio-lib>=7.0.0

# Dependencies
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
cvxpy>=1.4.0
numba>=0.57.0
```

---

## 6. Architecture Diagram

```
                    RISKCORE Architecture

    ┌─────────────────────────────────────────────────────┐
    │                   RISKCORE API                       │
    │                  (FastAPI)                           │
    └─────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────┐
    │                 Risk Engine Service                  │
    │              (risk_engine.py)                        │
    └─────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌───────────┐      ┌───────────────┐    ┌──────────────┐
    │  OpenBB   │      │   FinancePy   │    │ Riskfolio-   │
    │           │      │               │    │    Lib       │
    │ - Prices  │      │ - Bond Price  │    │ - VaR/CVaR   │
    │ - Quotes  │      │ - Greeks      │    │ - Optimize   │
    │ - FX      │      │ - Curves      │    │ - Contrib    │
    │ - Crypto  │      │ - Swaps       │    │ - Stress     │
    └───────────┘      └───────────────┘    └──────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌─────────────────────────────────────────────────────┐
    │                  Supabase Database                   │
    │   (positions, portfolios, risk_metrics, etc.)       │
    └─────────────────────────────────────────────────────┘
```

---

## Sources

- [OpenBB Documentation](https://docs.openbb.co/)
- [OpenBB GitHub](https://github.com/OpenBB-finance/OpenBB)
- [FinancePy GitHub](https://github.com/domokane/FinancePy)
- [FinancePy PyPI](https://pypi.org/project/financepy/)
- [Riskfolio-Lib Documentation](https://riskfolio-lib.readthedocs.io/)
- [Riskfolio-Lib GitHub](https://github.com/dcajasn/Riskfolio-Lib)

---

*Integration guide for RISKCORE development team*
