# Risk Skill

> Riskfolio-Lib and FinancePy integration patterns for RISKCORE

---

## Libraries Overview

| Library | Purpose | Install |
|---------|---------|---------|
| **Riskfolio-Lib** | Portfolio risk metrics (VaR, CVaR, optimization) | `pip install riskfolio-lib` |
| **FinancePy** | Derivatives pricing, Greeks, curves | `pip install financepy` |
| **OpenBB** | Market data | `pip install openbb` |

**Note:** First FinancePy import takes 30-60 seconds (Numba compilation).

---

## Riskfolio-Lib: Risk Metrics

### Basic Portfolio Risk

```python
import riskfolio as rp
import pandas as pd
import numpy as np

def calculate_portfolio_risk(returns: pd.DataFrame, weights: pd.Series) -> dict:
    """
    Calculate risk metrics for a portfolio.
    
    Args:
        returns: DataFrame of asset returns (columns = assets, rows = dates)
        weights: Series of portfolio weights (index = assets)
    
    Returns:
        Dictionary of risk metrics
    """
    # Create portfolio object
    port = rp.Portfolio(returns=returns)
    
    # Calculate covariance (use ledoit-wolf for stability)
    port.assets_stats(method_mu='hist', method_cov='ledoit')
    
    # Portfolio return and volatility
    port_return = np.dot(weights, port.mu)
    port_vol = np.sqrt(np.dot(weights.T, np.dot(port.cov, weights)))
    
    # VaR and CVaR (using historical method)
    portfolio_returns = returns @ weights
    var_95 = np.percentile(portfolio_returns, 5)
    var_99 = np.percentile(portfolio_returns, 1)
    cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
    
    # Sharpe ratio (assuming 5% risk-free rate)
    rf = 0.05 / 252  # Daily risk-free rate
    sharpe = (port_return - rf) / port_vol * np.sqrt(252)
    
    # Max drawdown
    cumulative = (1 + portfolio_returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdowns = cumulative / rolling_max - 1
    max_drawdown = drawdowns.min()
    
    return {
        'expected_return': float(port_return * 252),  # Annualized
        'volatility': float(port_vol * np.sqrt(252)),  # Annualized
        'var_95': float(var_95),
        'var_99': float(var_99),
        'cvar_95': float(cvar_95),
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(max_drawdown)
    }
```

### Risk Contribution Analysis

```python
def risk_contribution(returns: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    """
    Calculate each asset's contribution to portfolio risk.
    
    Returns DataFrame with:
    - asset: Asset name
    - weight: Portfolio weight
    - marginal_risk: Marginal contribution to risk
    - risk_contribution: Absolute contribution
    - risk_contribution_pct: Percentage of total risk
    """
    port = rp.Portfolio(returns=returns)
    port.assets_stats(method_mu='hist', method_cov='ledoit')
    
    cov = port.cov.values
    w = weights.values.reshape(-1, 1)
    
    # Portfolio volatility
    port_var = w.T @ cov @ w
    port_vol = np.sqrt(port_var)[0, 0]
    
    # Marginal risk contribution
    marginal = (cov @ w) / port_vol
    
    # Risk contribution (weight * marginal)
    risk_contrib = w * marginal
    risk_contrib_pct = risk_contrib / port_vol
    
    return pd.DataFrame({
        'asset': weights.index,
        'weight': weights.values,
        'marginal_risk': marginal.flatten(),
        'risk_contribution': risk_contrib.flatten(),
        'risk_contribution_pct': risk_contrib_pct.flatten()
    })
```

### Correlation Matrix

```python
def calculate_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix from returns."""
    return returns.corr()

def calculate_rolling_correlation(
    returns: pd.DataFrame, 
    asset1: str, 
    asset2: str,
    window: int = 60
) -> pd.Series:
    """Calculate rolling correlation between two assets."""
    return returns[asset1].rolling(window).corr(returns[asset2])
```

---

## FinancePy: Derivatives Pricing

### Option Pricing (Black-Scholes)

```python
from financepy.utils.date import Date
from financepy.utils.global_types import OptionTypes
from financepy.products.equity.equity_vanilla_option import EquityVanillaOption
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes

def price_equity_option(
    spot_price: float,
    strike_price: float,
    expiry_date: str,  # YYYY-MM-DD
    option_type: str,  # 'call' or 'put'
    volatility: float,
    risk_free_rate: float = 0.05,
    dividend_yield: float = 0.0,
    valuation_date: str = None
) -> dict:
    """
    Price an equity option using Black-Scholes.
    
    Returns:
        Dictionary with price and Greeks
    """
    from datetime import datetime
    
    # Parse dates
    if valuation_date is None:
        val_dt = datetime.now()
    else:
        val_dt = datetime.strptime(valuation_date, "%Y-%m-%d")
    exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
    
    # FinancePy dates
    val_date = Date(val_dt.day, val_dt.month, val_dt.year)
    exp_date = Date(exp_dt.day, exp_dt.month, exp_dt.year)
    
    # Option type
    opt_type = OptionTypes.EUROPEAN_CALL if option_type.lower() == 'call' else OptionTypes.EUROPEAN_PUT
    
    # Create option
    option = EquityVanillaOption(exp_date, strike_price, opt_type)
    
    # Discount curve
    discount_curve = DiscountCurveFlat(val_date, risk_free_rate)
    
    # Model
    model = BlackScholes(volatility)
    
    # Price
    price = option.value(val_date, spot_price, discount_curve, dividend_yield, model)
    
    # Greeks
    delta = option.delta(val_date, spot_price, discount_curve, dividend_yield, model)
    gamma = option.gamma(val_date, spot_price, discount_curve, dividend_yield, model)
    vega = option.vega(val_date, spot_price, discount_curve, dividend_yield, model)
    theta = option.theta(val_date, spot_price, discount_curve, dividend_yield, model)
    rho = option.rho(val_date, spot_price, discount_curve, dividend_yield, model)
    
    return {
        'price': float(price),
        'delta': float(delta),
        'gamma': float(gamma),
        'vega': float(vega),
        'theta': float(theta),
        'rho': float(rho)
    }
```

### Bond Pricing and Duration

```python
from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.products.bonds.bond import Bond

def price_bond(
    issue_date: str,
    maturity_date: str,
    coupon_rate: float,
    settlement_date: str,
    yield_to_maturity: float,
    face_value: float = 100.0,
    frequency: int = 2  # Semi-annual
) -> dict:
    """
    Price a bond and calculate risk metrics.
    
    Returns:
        Dictionary with price, duration, DV01, convexity
    """
    from datetime import datetime
    
    # Parse dates
    issue_dt = datetime.strptime(issue_date, "%Y-%m-%d")
    mat_dt = datetime.strptime(maturity_date, "%Y-%m-%d")
    settle_dt = datetime.strptime(settlement_date, "%Y-%m-%d")
    
    # FinancePy dates
    issue = Date(issue_dt.day, issue_dt.month, issue_dt.year)
    maturity = Date(mat_dt.day, mat_dt.month, mat_dt.year)
    settlement = Date(settle_dt.day, settle_dt.month, settle_dt.year)
    
    # Frequency
    freq = FrequencyTypes.SEMI_ANNUAL if frequency == 2 else FrequencyTypes.ANNUAL
    
    # Create bond
    bond = Bond(issue, maturity, coupon_rate, freq, DayCountTypes.ACT_ACT_ICMA)
    
    # Prices
    clean_price = bond.clean_price_from_ytm(settlement, yield_to_maturity)
    dirty_price = bond.dirty_price_from_ytm(settlement, yield_to_maturity)
    accrued = bond.accrued_interest(settlement)
    
    # Risk metrics
    mac_duration = bond.macauley_duration(settlement, yield_to_maturity)
    mod_duration = bond.modified_duration(settlement, yield_to_maturity)
    convexity = bond.convexity_from_ytm(settlement, yield_to_maturity)
    
    # DV01 (dollar value of 1bp)
    dv01 = mod_duration * dirty_price / 10000
    
    return {
        'clean_price': float(clean_price),
        'dirty_price': float(dirty_price),
        'accrued_interest': float(accrued),
        'macauley_duration': float(mac_duration),
        'modified_duration': float(mod_duration),
        'convexity': float(convexity),
        'dv01': float(dv01)
    }
```

### Yield Curve Construction

```python
from financepy.utils.date import Date
from financepy.market.curves.discount_curve_zeros import DiscountCurveZeros
import numpy as np

def build_yield_curve(
    valuation_date: str,
    tenors: list,  # In years: [0.25, 0.5, 1, 2, 5, 10, 30]
    rates: list    # Zero rates: [0.05, 0.051, 0.052, ...]
) -> DiscountCurveZeros:
    """
    Build a yield curve from zero rates.
    """
    from datetime import datetime
    
    val_dt = datetime.strptime(valuation_date, "%Y-%m-%d")
    val_date = Date(val_dt.day, val_dt.month, val_dt.year)
    
    # Create maturity dates
    dates = [val_date.add_years(t) for t in tenors]
    
    # Build curve
    curve = DiscountCurveZeros(val_date, dates, rates)
    
    return curve

def get_discount_factor(curve, date: str) -> float:
    """Get discount factor for a given date."""
    from datetime import datetime
    dt = datetime.strptime(date, "%Y-%m-%d")
    d = Date(dt.day, dt.month, dt.year)
    return curve.df(d)
```

---

## Combined Risk Engine

```python
# services/risk_engine.py

from typing import Dict, List
import pandas as pd
import numpy as np
from services.market_data import MarketDataService

class RiskEngine:
    """
    Combined risk engine using Riskfolio-Lib and FinancePy.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
        self.market_data = MarketDataService()
    
    def analyze_portfolio(
        self,
        positions: List[Dict],
        lookback_days: int = 252
    ) -> Dict:
        """
        Full portfolio analysis.
        
        Args:
            positions: List of positions with symbol, quantity, market_value
            lookback_days: Days of history for risk calculations
        
        Returns:
            Complete risk analysis
        """
        # Separate by asset class
        equities = [p for p in positions if p['asset_class'] == 'equity']
        options = [p for p in positions if p['asset_class'] == 'option']
        bonds = [p for p in positions if p['asset_class'] == 'fixed_income']
        
        results = {
            'equity_risk': None,
            'options_greeks': None,
            'bond_risk': None,
            'total_risk': None
        }
        
        # Equity analysis
        if equities:
            symbols = [p['ticker'] for p in equities]
            weights = self._calculate_weights(equities)
            returns = self._get_returns(symbols, lookback_days)
            
            results['equity_risk'] = calculate_portfolio_risk(returns, weights)
            results['risk_contributions'] = risk_contribution(returns, weights)
        
        # Options analysis
        if options:
            total_greeks = {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0}
            for opt in options:
                greeks = price_equity_option(
                    spot_price=opt['spot_price'],
                    strike_price=opt['strike_price'],
                    expiry_date=opt['expiry_date'],
                    option_type=opt['option_type'],
                    volatility=opt['implied_vol']
                )
                quantity = opt['quantity']
                for greek in total_greeks:
                    total_greeks[greek] += greeks[greek] * quantity
            
            results['options_greeks'] = total_greeks
        
        # Bond analysis
        if bonds:
            total_dv01 = 0
            total_duration = 0
            total_value = 0
            
            for bond in bonds:
                metrics = price_bond(
                    issue_date=bond['issue_date'],
                    maturity_date=bond['maturity_date'],
                    coupon_rate=bond['coupon_rate'],
                    settlement_date=bond['settlement_date'],
                    yield_to_maturity=bond['ytm']
                )
                mv = bond['market_value']
                total_dv01 += metrics['dv01'] * mv / 100
                total_duration += metrics['modified_duration'] * mv
                total_value += mv
            
            results['bond_risk'] = {
                'total_dv01': total_dv01,
                'weighted_duration': total_duration / total_value if total_value else 0
            }
        
        return results
    
    def _calculate_weights(self, positions: List[Dict]) -> pd.Series:
        """Calculate portfolio weights from positions."""
        total_mv = sum(p['market_value'] for p in positions)
        weights = {p['ticker']: p['market_value'] / total_mv for p in positions}
        return pd.Series(weights)
    
    def _get_returns(self, symbols: List[str], days: int) -> pd.DataFrame:
        """Fetch historical returns for symbols."""
        prices = self.market_data.get_prices(symbols, days=days)
        returns = prices.pct_change().dropna()
        return returns
```

---

## Key Risk Measures Reference

| Measure | Description | Use |
|---------|-------------|-----|
| **VaR (95%)** | Max loss with 95% confidence | Daily risk limit |
| **VaR (99%)** | Max loss with 99% confidence | Stress scenario |
| **CVaR/ES** | Expected loss beyond VaR | Tail risk |
| **Volatility** | Standard deviation of returns | General risk |
| **Sharpe Ratio** | Return per unit of risk | Performance |
| **Max Drawdown** | Largest peak-to-trough loss | Worst case |
| **DV01** | $ change per 1bp yield move | Interest rate risk |
| **Duration** | Price sensitivity to rates | Bond risk |
| **Delta** | Option sensitivity to spot | Directional exposure |
| **Gamma** | Delta sensitivity to spot | Convexity |
| **Vega** | Sensitivity to volatility | Vol exposure |

---

## Don't

- ❌ Don't calculate VaR with < 100 observations
- ❌ Don't assume normal distribution for tail risk
- ❌ Don't use historical correlation in stress tests
- ❌ Don't forget to annualize properly (√252 for daily)
- ❌ Don't mix currencies without conversion
- ❌ Don't skip data validation before calculations

---

*Risk engine patterns for RISKCORE*
