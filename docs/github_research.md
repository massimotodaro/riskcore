# Open-Source GitHub Research for RISKCORE

**Generated:** 2025-01-08
**Focus:** Portfolio risk management, VaR, IBOR, and hedge fund analytics

---

## Executive Summary

Analysis of open-source projects on GitHub reveals a rich ecosystem of portfolio analytics and optimization tools, but **no comprehensive multi-manager risk aggregation solution exists**. Most projects focus on:

- Portfolio optimization (weights, efficient frontier)
- Performance analytics (returns, Sharpe, drawdowns)
- VaR calculation (single portfolio)
- Derivatives pricing

**Key Gap:** No open-source project addresses the multi-PM risk aggregation problem that RISKCORE targets.

---

## Top Projects by Category

### 1. Portfolio Analytics & Performance

| Project | Stars | Forks | Language | Last Active | License |
|---------|-------|-------|----------|-------------|---------|
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | 31k+ | 3k+ | Python | Active | AGPL-3.0 |
| [pyfolio](https://github.com/quantopian/pyfolio) | 5.5k+ | 1.9k+ | Python | Archived | Apache 2.0 |
| [QuantStats](https://github.com/ranaroussi/quantstats) | 4.5k+ | 800+ | Python | Active | Apache 2.0 |
| [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) | 4.5k+ | 1k+ | Python | Active | MIT |
| [Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | 3k+ | 600+ | Python | Active | BSD-3 |

---

## Detailed Project Analysis

### OpenBB (OpenBB-finance/OpenBB)

**URL:** https://github.com/OpenBB-finance/OpenBB
**Stars:** 31,000+ | **Forks:** 3,000+
**Language:** Python | **License:** AGPL-3.0
**Status:** Very Active (daily commits)

#### Overview
OpenBB is a financial data platform for analysts, quants, and AI agents. It's the most comprehensive open-source financial data infrastructure available.

#### Key Features
- Connects to 100+ data providers
- Covers equities, options, crypto, forex, macro, fixed income
- REST API via FastAPI
- Python SDK for quants
- MCP servers for AI agents
- Excel integration

#### Tech Stack
- Python 3.9-3.13
- FastAPI + Uvicorn
- Modular extension system
- 220+ contributors

#### What It Solves
- Data aggregation from multiple sources
- Unified API for financial data
- Research and analysis workflows

#### What's Missing (RISKCORE Opportunity)
- No position management
- No portfolio aggregation
- No risk calculations (VaR, Greeks)
- No multi-manager views
- Data-focused, not risk-focused

---

### pyfolio (quantopian/pyfolio)

**URL:** https://github.com/quantopian/pyfolio
**Stars:** 5,500+ | **Forks:** 1,900+
**Language:** Python | **License:** Apache 2.0
**Status:** Archived (Quantopian shut down 2020)

#### Overview
Portfolio and risk analytics library developed by Quantopian. Creates comprehensive "tear sheets" for portfolio analysis.

#### Key Features
- Performance tear sheets with multiple plots
- Risk metrics (Sharpe, Sortino, drawdowns)
- Factor analysis and attribution
- Rolling volatility analysis
- Intraday strategy support
- Integration with Zipline backtester

#### Tech Stack
- Python, NumPy, Pandas
- Matplotlib for visualization
- empyrical for metrics

#### What It Solves
- Backtest analysis
- Strategy performance evaluation
- Risk/return profiling

#### What's Missing (RISKCORE Opportunity)
- No real-time capability
- No multi-portfolio aggregation
- No position-level data
- No VaR calculations
- Archived/unmaintained

---

### QuantStats (ranaroussi/quantstats)

**URL:** https://github.com/ranaroussi/quantstats
**Stars:** 4,500+ | **Forks:** 800+
**Language:** Python | **License:** Apache 2.0
**Status:** Active

#### Overview
Portfolio profiling library providing in-depth analytics and risk metrics for quants and portfolio managers.

#### Key Features
- CVaR (Conditional Value at Risk)
- Monthly returns heatmaps
- Performance metrics
- HTML report generation
- Benchmark comparison

#### Tech Stack
- Python, Pandas, NumPy
- Matplotlib, Seaborn

#### What It Solves
- Portfolio performance reporting
- Risk metric calculations
- Visual analytics

#### What's Missing (RISKCORE Opportunity)
- Returns-focused, not position-focused
- No multi-portfolio support
- No real-time updates
- Limited risk measures

---

### PyPortfolioOpt (robertmartin8/PyPortfolioOpt)

**URL:** https://github.com/robertmartin8/PyPortfolioOpt
**Stars:** 4,500+ | **Forks:** 1,000+
**Language:** Python | **License:** MIT
**Status:** Active

#### Overview
Comprehensive portfolio optimization library implementing classical and modern methods.

#### Key Features
- Mean-variance optimization (Markowitz)
- Black-Litterman allocation
- Hierarchical Risk Parity (HRP)
- Covariance shrinkage
- Long/short portfolios
- Market-neutral portfolios
- L2 regularization

#### Tech Stack
- Python, NumPy, Pandas
- SciPy for optimization
- cvxpy for convex optimization

#### What It Solves
- Portfolio weight optimization
- Risk-adjusted allocation
- Efficient frontier construction

#### What's Missing (RISKCORE Opportunity)
- Optimization only, no monitoring
- No real-time position tracking
- No multi-manager support
- No VaR or Greeks

---

### Riskfolio-Lib (dcajasn/Riskfolio-Lib)

**URL:** https://github.com/dcajasn/Riskfolio-Lib
**Stars:** 3,000+ | **Forks:** 600+
**Language:** Python | **License:** BSD-3
**Status:** Very Active (version 7.0.1)

#### Overview
Comprehensive quantitative portfolio optimization library from Peru. Most feature-rich optimization library available.

#### Key Features
- 24 convex risk measures
- Mean-Risk optimization
- Kelly Criterion (log utility)
- Risk Parity
- HRP and HERC clustering
- Black-Litterman (multiple variants)
- CVaR, EVaR, RLVaR
- Drawdown-based measures (CDaR, EDaR)
- Tracking error constraints
- Turnover constraints

#### Tech Stack
- Python 3.9+
- CVXPY for optimization
- Pandas integration
- Optional: MOSEK, GUROBI solvers

#### What It Solves
- Advanced portfolio optimization
- Risk budgeting
- Factor-based allocation

#### What's Missing (RISKCORE Opportunity)
- Optimization-focused, not monitoring
- No position tracking
- No multi-portfolio aggregation
- No real-time capability

---

### FinancePy (domokane/FinancePy)

**URL:** https://github.com/domokane/FinancePy
**Stars:** 2,600+ | **Forks:** 400+
**Language:** Python | **License:** MIT
**Status:** Active

#### Overview
Derivatives pricing and risk management library by EDHEC professor. C++-like performance via Numba.

#### Key Features
- Fixed income (bonds, swaps, swaptions)
- Equity derivatives (options, variance swaps)
- FX derivatives
- Credit derivatives (CDS, CDO)
- Interest rate models
- 60+ Jupyter notebooks

#### Tech Stack
- Python, NumPy, Numba
- SciPy

#### What It Solves
- Derivatives pricing
- Greeks calculation
- Curve construction
- Model calibration

#### What's Missing (RISKCORE Opportunity)
- Single instrument focus
- No portfolio aggregation
- No position management
- No multi-manager support

---

## VaR Calculation Projects

### ibaris/VaR

**URL:** https://github.com/ibaris/VaR
**Stars:** 100+ | **Language:** Python
**Status:** Maintained

#### Features
- Historical VaR
- Parametric VaR
- Monte Carlo VaR
- Parametric GARCH
- Expected Shortfall (CVaR)
- PELVE (Probability Equivalent Level)
- Backtesting routines

#### What's Missing
- Single portfolio only
- No real-time capability
- Limited aggregation

### VaRCalculator (prudhvi-reddy-m)

**URL:** https://github.com/prudhvi-reddy-m/VaRCalculator
**Stars:** 50+ | **Language:** Python

#### Features
- Historical, Parametric, Monte Carlo methods
- Clean class-based API
- Educational focus

---

## AI-Powered Hedge Fund Projects

### AutoHedge (The-Swarm-Corporation)

**URL:** https://github.com/The-Swarm-Corporation/AutoHedge
**Stars:** 500+ | **Language:** Python
**Status:** Active

#### Features
- Multi-agent AI architecture
- Director, Quant, Risk, Execution agents
- Automated market analysis
- Trade execution

### ai-hedge-fund (virattt)

**URL:** https://github.com/virattt/ai-hedge-fund
**Stars:** 3,000+ | **Language:** Python
**Status:** Active

#### Features
- AI agents modeled after famous investors
- Risk manager agent
- Portfolio manager for decisions
- Educational/proof of concept

### Ghostfolio

**URL:** https://github.com/ghostfolio/ghostfolio
**Stars:** 4,000+ | **Language:** TypeScript
**Status:** Very Active

#### Features
- Open source wealth management
- Stocks, ETFs, crypto tracking
- Performance analytics
- Self-hosted

#### What's Missing
- Personal finance focus
- No institutional features
- No multi-manager support

---

## IBOR (Investment Book of Record)

### Key Finding
**No open-source IBOR implementation exists.**

All IBOR solutions are commercial:
- SimCorp Dimension
- BlackRock Aladdin
- Bloomberg AIM
- Advent Geneva
- SS&C

This represents a significant opportunity for RISKCORE.

---

## Curated Resource Lists

### awesome-quant

**URL:** https://github.com/wilsonfreitas/awesome-quant
**Stars:** 17,000+

Comprehensive list of quant finance libraries including:
- Trading platforms
- Backtesting frameworks
- Risk analysis tools
- Data providers
- Machine learning for finance

---

## Gap Analysis for RISKCORE

### What Exists (Solved Problems)

| Capability | Best Solution | Maturity |
|------------|---------------|----------|
| Portfolio optimization | Riskfolio-Lib | Excellent |
| Performance analytics | pyfolio/QuantStats | Good |
| VaR calculation | ibaris/VaR | Basic |
| Derivatives pricing | FinancePy | Excellent |
| Financial data | OpenBB | Excellent |
| Wealth tracking | Ghostfolio | Good |

### What's Missing (RISKCORE Opportunities)

| Gap | Current State | RISKCORE Solution |
|-----|---------------|-------------------|
| **Multi-manager aggregation** | Nothing exists | Core feature |
| **Real-time position tracking** | Spreadsheets | Position API |
| **Cross-PM netting** | Manual | Automated detection |
| **Firm-wide VaR** | Not available | Correlation-aware VaR |
| **IBOR** | Commercial only | Open-source IBOR |
| **Source-agnostic ingestion** | Each tool has own format | Universal adapters |
| **Natural language queries** | None | Claude integration |

### Technical Gaps in Existing Projects

1. **No Multi-Portfolio Architecture**
   - All projects assume single portfolio
   - No hierarchy (fund → PM → strategy)
   - No aggregation across portfolios

2. **No Real-Time Position Management**
   - Most work with historical returns
   - No live position tracking
   - No intraday updates

3. **No Cross-Asset Aggregation**
   - Projects specialize (FI, equity, derivatives)
   - No unified multi-asset view
   - No netting across asset classes

4. **No Identifier Reconciliation**
   - No CUSIP/ISIN/SEDOL mapping
   - No security master concept
   - Manual identifier handling

5. **Limited Risk Aggregation**
   - VaR at portfolio level only
   - No correlation handling across PMs
   - No firm-wide stress testing

---

## Recommendations for RISKCORE

### Leverage Existing Libraries

| Library | Use For | Integration |
|---------|---------|-------------|
| Riskfolio-Lib | Portfolio optimization | Optional module |
| FinancePy | Derivatives pricing | Greeks calculation |
| OpenBB | Market data | Data ingestion |
| QuantStats | Performance reporting | Report generation |

### Build What's Missing

1. **Position Aggregation Engine**
   - Multi-source ingestion
   - Identifier reconciliation
   - Hierarchy management

2. **Risk Aggregation Layer**
   - Correlation-aware VaR
   - Cross-PM netting
   - Firm-wide stress tests

3. **Real-Time Infrastructure**
   - WebSocket updates
   - Supabase real-time
   - Event-driven architecture

4. **Natural Language Interface**
   - Claude API integration
   - Query understanding
   - Risk insights generation

### Differentiation Strategy

| Feature | Existing Projects | RISKCORE |
|---------|-------------------|----------|
| Target user | Single PM / Quant | CRO / Risk team |
| Portfolio scope | One portfolio | Firm-wide |
| Data sources | One system | Any source |
| Updates | Batch / Historical | Real-time |
| Queries | Code / API | Natural language |
| Cost | Free (limited) | Free + Enterprise |

---

## Sources

- [GitHub Topics: Portfolio Management](https://github.com/topics/portfolio-management)
- [GitHub Topics: Risk Management](https://github.com/topics/risk-management)
- [GitHub Topics: Value at Risk](https://github.com/topics/value-at-risk)
- [GitHub Topics: Quantitative Finance](https://github.com/topics/quantitative-finance)
- [awesome-quant](https://github.com/wilsonfreitas/awesome-quant)

---

*Research compiled for RISKCORE competitive analysis*
