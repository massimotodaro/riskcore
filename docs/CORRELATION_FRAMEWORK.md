# RISKCORE Correlation Framework

> Last Updated: 2025-01-09
> Status: Roadmap (Phase 2-3)
> Author: Massimo Todaro

---

## Executive Summary

The Correlation Framework is a **key differentiator** for RISKCORE. No platform provides:
- Cross-book correlation matrices (realized + implied)
- Factor-based risk decomposition across asset classes
- Stress testing with correlation spikes (2008 scenario)
- AI-powered hedge overlay suggestions

This document defines the architecture for these features.

---

## The Problem

Multi-manager funds have multiple books (PMs/desks) trading different strategies. The CIO/CRO needs to answer:

1. **"How correlated are my books?"** — If PM_Alpha and PM_Beta are 0.9 correlated, we have concentration risk
2. **"What happens when correlations spike?"** — 2008 showed correlations → 1 in stress
3. **"How do I hedge the aggregate?"** — What trades reduce firm-wide risk?

**No platform answers these questions well.**

---

## Two Types of Correlation

### 1. Realized Correlation (Historical)

| Attribute | Description |
|-----------|-------------|
| **Definition** | Correlation of historical P&L changes between books |
| **Calculation** | Pearson correlation on daily P&L time series |
| **Lookback** | Configurable (30, 60, 90, 252 days) |
| **Difficulty** | Easy — standard time series math |
| **Limitation** | Backward-looking, may not predict future |

```python
# Realized correlation calculation
import pandas as pd

def realized_correlation(pnl_book_a: pd.Series, pnl_book_b: pd.Series, window: int = 60) -> float:
    """Calculate rolling realized correlation between two books."""
    return pnl_book_a.rolling(window).corr(pnl_book_b).iloc[-1]
```

### 2. Implied Correlation (Forward-Looking)

| Attribute | Description |
|-----------|-------------|
| **Definition** | Expected correlation based on current positions and factor exposures |
| **Calculation** | Decompose positions → factor exposures → factor correlation matrix |
| **Difficulty** | Hard — requires factor model |
| **Advantage** | Forward-looking, captures current risk |

```
Book A Positions → Factor Exposures A → ┐
                                        ├→ Implied Correlation
Book B Positions → Factor Exposures B → ┘
```

---

## Risk Factor Taxonomy

### Standard Risk Factors by Asset Class

| Asset Class | Risk Factor | Unit | Description |
|-------------|-------------|------|-------------|
| **Equities** | Beta | $ per 1% market move | Market sensitivity |
| | Sector Delta | $ per 1% sector move | Sector exposure |
| | Country Delta | $ per 1% country move | Geographic exposure |
| | Size Factor | Loading | Small vs Large cap |
| | Value Factor | Loading | Value vs Growth |
| | Momentum Factor | Loading | Winners vs Losers |
| **Fixed Income** | DV01 (Duration) | $ per 1bp yield change | Interest rate sensitivity |
| | KR01 (Key Rate) | $ per 1bp at tenor | Curve sensitivity (2Y, 5Y, 10Y, 30Y) |
| | CS01 (Credit) | $ per 1bp spread change | Credit spread sensitivity |
| | Convexity | $ per 1bp² | Second-order rate sensitivity |
| **FX** | FX Delta | $ per 1% currency move | Currency exposure per pair |
| **Options** | Delta | $ per 1% underlying | Directional exposure |
| | Gamma | Δ Delta per 1% underlying | Convexity |
| | Vega | $ per 1% vol move | Volatility sensitivity |
| | Theta | $ per day | Time decay |
| | Rho | $ per 1% rate change | Interest rate sensitivity |
| **Credit (CDS)** | CS01 | $ per 1bp spread | Spread sensitivity |
| | JTD | $ | Jump-to-default exposure |
| **Commodities** | Commodity Delta | $ per 1% price move | Price sensitivity per commodity |

### Factor Hierarchy

```
Level 1: Asset Class (Equity, FI, FX, Credit, Commodities)
    │
    └── Level 2: Sub-factors
            │
            ├── Equity: Beta, Sectors (11 GICS), Countries, Styles
            ├── FI: Curve tenors (3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
            ├── FX: Currency pairs (G10, EM)
            ├── Credit: Rating buckets (AAA, AA, A, BBB, HY), Sectors
            └── Options: Greeks by underlying
```

---

## Factor Exposure Calculation

### For Each Position

```python
def calculate_factor_exposures(position: Position) -> Dict[str, float]:
    """
    Decompose a position into risk factor exposures.
    
    Returns dict of {factor_name: exposure_value}
    """
    exposures = {}
    
    if position.asset_class == "equity":
        exposures["equity_beta"] = position.market_value * position.beta
        exposures[f"sector_{position.sector}"] = position.market_value
        exposures[f"country_{position.country}"] = position.market_value
        
    elif position.asset_class == "fixed_income":
        exposures["dv01_total"] = position.dv01
        for tenor, kr01 in position.key_rate_durations.items():
            exposures[f"kr01_{tenor}"] = kr01
        exposures["cs01"] = position.credit_spread_sensitivity
        
    elif position.asset_class == "fx":
        exposures[f"fx_{position.currency_pair}"] = position.notional
        
    elif position.asset_class == "option":
        exposures["delta"] = position.delta * position.notional
        exposures["gamma"] = position.gamma * position.notional
        exposures["vega"] = position.vega * position.notional
        exposures["theta"] = position.theta * position.notional
        
    elif position.asset_class == "cds":
        exposures["cs01"] = position.cs01
        exposures["jtd"] = position.jump_to_default
    
    return exposures
```

### Aggregate to Book Level

```python
def aggregate_book_exposures(book: List[Position]) -> Dict[str, float]:
    """Aggregate all position exposures to book level."""
    book_exposures = defaultdict(float)
    
    for position in book:
        position_exposures = calculate_factor_exposures(position)
        for factor, exposure in position_exposures.items():
            book_exposures[factor] += exposure
    
    return dict(book_exposures)
```

---

## Implied Correlation Calculation

### Step 1: Build Factor Covariance Matrix

Use historical factor returns to build covariance matrix:

```python
def build_factor_covariance_matrix(factor_returns: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """
    Build factor covariance matrix from historical returns.
    
    Args:
        factor_returns: DataFrame with columns = factors, rows = dates
        window: Lookback period in days
        
    Returns:
        Covariance matrix (factors x factors)
    """
    return factor_returns.tail(window).cov()
```

### Step 2: Calculate Book Variance

```python
def calculate_book_variance(exposures: np.array, cov_matrix: np.array) -> float:
    """
    Calculate book variance using factor exposures and covariance matrix.
    
    Variance = E' * Σ * E
    where E = exposure vector, Σ = covariance matrix
    """
    return exposures @ cov_matrix @ exposures.T
```

### Step 3: Calculate Implied Correlation

```python
def implied_correlation(
    exposures_a: np.array,
    exposures_b: np.array,
    cov_matrix: np.array
) -> float:
    """
    Calculate implied correlation between two books.
    
    Correlation = Cov(A,B) / (σ_A * σ_B)
    where Cov(A,B) = E_A' * Σ * E_B
    """
    cov_ab = exposures_a @ cov_matrix @ exposures_b.T
    var_a = exposures_a @ cov_matrix @ exposures_a.T
    var_b = exposures_b @ cov_matrix @ exposures_b.T
    
    return cov_ab / (np.sqrt(var_a) * np.sqrt(var_b))
```

---

## Correlation Matrix Display

### Dashboard View

```
CROSS-BOOK CORRELATION MATRIX
─────────────────────────────────────────────────────────────────
                 PM_Alpha   PM_Beta   PM_Gamma   PM_Delta   FIRM
─────────────────────────────────────────────────────────────────
PM_Alpha           1.00      0.45      -0.12       0.67     0.78
PM_Beta            0.45      1.00       0.23       0.34     0.65
PM_Gamma          -0.12      0.23       1.00      -0.45     0.12
PM_Delta           0.67      0.34      -0.45       1.00     0.71
─────────────────────────────────────────────────────────────────

Toggle: [Realized ◉] [Implied ○]    Lookback: [60 days ▼]
```

### Color Coding

| Correlation | Color | Meaning |
|-------------|-------|---------|
| > 0.7 | 🔴 Red | High concentration risk |
| 0.3 to 0.7 | 🟡 Yellow | Moderate correlation |
| -0.3 to 0.3 | 🟢 Green | Low correlation (diversified) |
| < -0.3 | 🔵 Blue | Negative correlation (hedged) |

---

## Stress Testing: Correlation Spike Scenario

### The 2008 Problem

In normal markets: correlations are moderate (0.3-0.5)
In crisis: correlations spike to 0.9+ ("correlation breakdown")

**Result:** Diversification benefits disappear when you need them most.

### Stress Correlation Matrix

```python
def stress_correlation_matrix(
    normal_corr_matrix: np.array,
    stress_level: float = 0.9
) -> np.array:
    """
    Create stressed correlation matrix.
    
    Args:
        normal_corr_matrix: Normal correlation matrix
        stress_level: Target correlation in stress (e.g., 0.9)
        
    Returns:
        Stressed correlation matrix
    """
    n = normal_corr_matrix.shape[0]
    stressed = np.full((n, n), stress_level)
    np.fill_diagonal(stressed, 1.0)
    return stressed
```

### Dashboard: Stress Test View

```
STRESS TEST: CORRELATION SPIKE
─────────────────────────────────────────────────────────────────
Scenario: All correlations → 0.9 (2008-style crisis)

                    NORMAL         STRESSED        CHANGE
─────────────────────────────────────────────────────────────────
Firm VaR (95%)      $12.3M         $28.7M         +133%
Firm VaR (99%)      $18.1M         $41.2M         +128%
Max Drawdown        -8.2%          -19.4%         +137%
─────────────────────────────────────────────────────────────────

⚠️ WARNING: Diversification benefit reduced by $16.4M under stress
```

---

## Hedge Overlay Suggestions

### The Goal

Given firm-wide factor exposures, suggest trades to reduce risk.

### Algorithm

```python
def suggest_hedge_trades(
    firm_exposures: Dict[str, float],
    target_reduction: Dict[str, float],
    available_instruments: List[Instrument]
) -> List[SuggestedTrade]:
    """
    Suggest trades to reduce specific factor exposures.
    
    Args:
        firm_exposures: Current firm-wide factor exposures
        target_reduction: Desired reduction per factor
        available_instruments: Liquid instruments for hedging
        
    Returns:
        List of suggested trades with impact analysis
    """
    suggestions = []
    
    for factor, current_exposure in firm_exposures.items():
        if factor in target_reduction:
            target = target_reduction[factor]
            needed_hedge = current_exposure - target
            
            # Find best instrument to hedge this factor
            best_instrument = find_best_hedge(factor, needed_hedge, available_instruments)
            
            if best_instrument:
                trade = SuggestedTrade(
                    instrument=best_instrument,
                    quantity=calculate_hedge_quantity(best_instrument, needed_hedge),
                    factor_impact=calculate_factor_impact(best_instrument),
                    estimated_cost=estimate_transaction_cost(best_instrument)
                )
                suggestions.append(trade)
    
    return suggestions
```

### Dashboard: Hedge Suggestions

```
HEDGE OVERLAY SUGGESTIONS
─────────────────────────────────────────────────────────────────
Current Risk: Firm is LONG $5.2M DV01 at 3Y tenor

SUGGESTED TRADE #1:
  Action:     SELL $520M 3-Year Treasury Note
  Impact:     DV01 -$1.0M (from $5.2M to $4.2M)
  Side Effects:
    - Convexity: +$12K
    - Carry: -$45K/month
  Est. Cost:  $15K (spread + market impact)
  
  [EXECUTE] [MODIFY] [DISMISS]

─────────────────────────────────────────────────────────────────
Current Risk: Firm is SHORT $3.1M Vega (SPX options)

SUGGESTED TRADE #2:
  Action:     BUY 450 SPX 3-month ATM straddles
  Impact:     Vega +$1.0M (from -$3.1M to -$2.1M)
  Side Effects:
    - Delta: +$50K (minor)
    - Theta: -$8K/day
  Est. Cost:  $22K (spread + market impact)
  
  [EXECUTE] [MODIFY] [DISMISS]
```

---

## Implementation Roadmap

### Phase 2: Correlation Framework (Post-MVP)

| Week | Deliverable |
|------|-------------|
| 1 | Risk factor taxonomy implementation |
| 2 | Factor exposure calculation per position |
| 3 | Book-level aggregation |
| 4 | Realized correlation matrix |
| 5 | Factor covariance matrix builder |
| 6 | Implied correlation calculation |
| 7 | Dashboard: correlation matrix view |
| 8 | Testing and refinement |

### Phase 3: Stress Testing & Hedging (Future)

| Week | Deliverable |
|------|-------------|
| 1-2 | Stress correlation scenarios (2008, 2020 COVID) |
| 3-4 | Stress test dashboard view |
| 5-6 | Hedge instrument library |
| 7-8 | Hedge suggestion algorithm |
| 9-10 | Hedge overlay dashboard |
| 11-12 | AI-powered hedge recommendations (Claude) |

---

## Technical Requirements

### Data Requirements

| Data | Source | Frequency |
|------|--------|-----------|
| Position data | Client systems | Daily/Real-time |
| Factor returns | OpenBB / vendor | Daily |
| Factor covariance | Calculated | Daily refresh |
| P&L history | Client systems | Daily |
| Instrument reference | Security master | Static |

### Libraries

| Library | Purpose |
|---------|---------|
| **Riskfolio-Lib** | Covariance estimation, risk metrics |
| **NumPy/Pandas** | Matrix operations |
| **SciPy** | Statistical calculations |
| **OpenBB** | Factor return data |

### Database Tables

```sql
-- Factor exposures per book
CREATE TABLE factor_exposures (
    id UUID PRIMARY KEY,
    book_id UUID REFERENCES books(id),
    factor_name VARCHAR(50),
    exposure_value DECIMAL(18, 4),
    as_of_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Correlation matrix snapshots
CREATE TABLE correlation_matrices (
    id UUID PRIMARY KEY,
    matrix_type VARCHAR(20),  -- 'realized' or 'implied'
    lookback_days INT,
    matrix_data JSONB,  -- {book_a: {book_b: correlation}}
    as_of_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Hedge suggestions
CREATE TABLE hedge_suggestions (
    id UUID PRIMARY KEY,
    factor_name VARCHAR(50),
    current_exposure DECIMAL(18, 4),
    suggested_instrument VARCHAR(100),
    suggested_quantity DECIMAL(18, 4),
    expected_impact JSONB,
    estimated_cost DECIMAL(18, 4),
    status VARCHAR(20),  -- 'pending', 'executed', 'dismissed'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Research Needed

### Factor Model Sources

| Source | Description | Cost |
|--------|-------------|------|
| Barra (MSCI) | Industry standard factor model | $$$$$ |
| Axioma (Qontigo) | Alternative factor model | $$$$ |
| Bloomberg | PORT factor model | $$$ (with Terminal) |
| **Open Source** | Build from Fama-French + extensions | Free |

### GitHub Resources to Investigate

- Fama-French factor data (publicly available)
- `empyrical` - risk metrics library
- `alphalens` - factor analysis
- `pyfinance` - financial calculations

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Correlation matrix refresh | < 5 seconds |
| Factor decomposition per position | < 100ms |
| Stress test calculation | < 10 seconds |
| Hedge suggestion generation | < 5 seconds |
| User adoption | CIO/CRO uses daily |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Start with realized correlation | Easier to implement, immediate value |
| Build factor taxonomy from standards | Don't reinvent, use Barra/Fama-French conventions |
| Store factor exposures in DB | Enable historical analysis |
| Stress test with 0.9 correlation | Industry standard crisis assumption |
| Suggest hedges, don't auto-execute | Human in the loop for trading decisions |

---

## References

- Barra Risk Model Handbook
- Fama-French Factor Data: [mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- "The Misbehavior of Markets" - Benoit Mandelbrot (correlation in crisis)
- "Against the Gods" - Peter Bernstein (risk management history)
- 2008 Financial Crisis: Correlation breakdown case study

---

*Correlation Framework design for RISKCORE Phase 2-3*
