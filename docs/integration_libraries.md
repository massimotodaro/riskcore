# RISKCORE Integration Libraries

**Generated:** 2026-01-09
**Purpose:** GitHub libraries for RISKCORE integrations

---

## Summary

| Category | Recommended | Alternative | Notes |
|----------|-------------|-------------|-------|
| Bloomberg API | blp | pdblp, xbbg-blpapi | Requires Terminal |
| FIX Protocol | simplefix | quickfix | simplefix for MVP |
| Portfolio Analytics | quantstats | pyfolio-reloaded | quantstats is active |
| Optimization | PyPortfolioOpt | Riskfolio-Lib | Both excellent |
| Identifier Mapping | pyopenfigi | Std_Security_Code | OpenFIGI is free API |
| Security Master | securitiesdb (reference) | - | Build custom |

---

## 1. Bloomberg API Libraries

### blp (Recommended)

| Attribute | Details |
|-----------|---------|
| **Repository** | [matthewgilbert/blp](https://github.com/matthewgilbert/blp) |
| **Stars/Forks** | 141 / 36 |
| **Problem Solved** | Pythonic pandas wrapper for Bloomberg Open API |
| **Status** | **Active** - Successor to pdblp |
| **License** | Apache-2.0 |
| **Integration Effort** | **Medium** - Requires Bloomberg Terminal/Server |

**Usage:**
```python
from blp import blp

bquery = blp.BlpQuery().start()
df = bquery.bdh(['AAPL US Equity'], ['PX_LAST'], '2024-01-01', '2024-12-31')
```

### pdblp (Legacy)

| Attribute | Details |
|-----------|---------|
| **Repository** | [matthewgilbert/pdblp](https://github.com/matthewgilbert/pdblp) |
| **Stars/Forks** | 252 / 72 |
| **Problem Solved** | Original pandas Bloomberg wrapper |
| **Status** | **Superseded** by blp |
| **License** | MIT |
| **Integration Effort** | Medium |

### xbbg-blpapi

| Attribute | Details |
|-----------|---------|
| **Repository** | [anchorblock/xbbg-blpapi](https://github.com/anchorblock/xbbg-blpapi) |
| **Stars/Forks** | 0 / 0 (new) |
| **Problem Solved** | Intuitive API with subscription support |
| **Status** | Active (Dec 2023) |
| **License** | Apache-2.0 |
| **Integration Effort** | **Low-Medium** |

---

## 2. FIX Protocol Libraries

### simplefix (Recommended for MVP)

| Attribute | Details |
|-----------|---------|
| **Repository** | [da4089/simplefix](https://github.com/da4089/simplefix) |
| **Stars/Forks** | 252 / 65 |
| **Problem Solved** | Lightweight FIX message creation/parsing |
| **Status** | Maintained (Sep 2023) |
| **License** | MIT |
| **Integration Effort** | **Low** |

**Why for MVP:**
- Pure Python, no dependencies
- Simple API for message parsing
- No complex session management
- Easy to upgrade to quickfix later

**Usage:**
```python
import simplefix

# Parse FIX message
parser = simplefix.FixParser()
parser.append_buffer(raw_fix_data)
msg = parser.get_message()

# Get execution details
exec_type = msg.get(simplefix.TAG_EXECTYPE)
order_qty = msg.get(simplefix.TAG_ORDERQTY)
```

### QuickFIX (Enterprise)

| Attribute | Details |
|-----------|---------|
| **Repository** | [quickfix/quickfix](https://github.com/quickfix/quickfix) |
| **Stars/Forks** | 1,900 / 823 |
| **Problem Solved** | Full FIX protocol engine (FIX 4.0-5.0) |
| **Status** | **Active** (Jan 2025) |
| **License** | QuickFIX License (BSD-like) |
| **Integration Effort** | **High** |

**When to use:**
- Need full session management
- Bi-directional FIX communication
- Production trading connectivity

---

## 3. Portfolio Analytics Libraries

### quantstats (Recommended)

| Attribute | Details |
|-----------|---------|
| **Repository** | [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) |
| **Stars/Forks** | 6,600 / 1,100 |
| **Problem Solved** | Portfolio profiling, risk metrics, tear sheets |
| **Status** | **Active** (Sep 2025) |
| **License** | Apache-2.0 |
| **Integration Effort** | **Low** |

**Features:**
- Sharpe, Sortino, Calmar ratios
- VaR, CVaR calculations
- Drawdown analysis
- HTML report generation
- Benchmark comparison

**Usage:**
```python
import quantstats as qs

# Generate full report
qs.reports.html(returns, benchmark, output='report.html')

# Individual metrics
sharpe = qs.stats.sharpe(returns)
var = qs.stats.var(returns)
```

### pyfolio-reloaded

| Attribute | Details |
|-----------|---------|
| **Repository** | [stefan-jansen/pyfolio-reloaded](https://github.com/stefan-jansen/pyfolio-reloaded) |
| **Stars/Forks** | Fork of quantopian/pyfolio |
| **Problem Solved** | Updated pyfolio with modern dependencies |
| **Status** | More maintained than original |
| **License** | Apache-2.0 |
| **Integration Effort** | **Low** |

### PyPortfolioOpt

| Attribute | Details |
|-----------|---------|
| **Repository** | [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) |
| **Stars/Forks** | 5,400 / 1,100 |
| **Problem Solved** | Portfolio optimization (MVO, Black-Litterman, HRP) |
| **Status** | Maintained |
| **License** | MIT |
| **Integration Effort** | **Low** |

---

## 4. Security Identifier Mapping

### pyopenfigi (Recommended)

| Attribute | Details |
|-----------|---------|
| **Repository** | [tlouarn/pyopenfigi](https://github.com/tlouarn/pyopenfigi) |
| **Stars/Forks** | 23 / 2 |
| **Problem Solved** | Python wrapper for OpenFIGI API v3 |
| **Status** | Maintained (Apr 2023) |
| **License** | MIT |
| **Integration Effort** | **Low** |

**Why OpenFIGI:**
- Free API (no subscription)
- Maps CUSIP, ISIN, SEDOL, ticker to FIGI
- Bloomberg-backed identifier standard
- Rate limit: 25 requests/min (free), higher with API key

**Usage:**
```python
from pyopenfigi import OpenFigi

figi = OpenFigi()

# Map ticker to FIGI
result = figi.map([
    {'idType': 'TICKER', 'idValue': 'AAPL', 'exchCode': 'US'}
])
```

### Std_Security_Code

| Attribute | Details |
|-----------|---------|
| **Repository** | [Wenzhi-Ding/Std_Security_Code](https://github.com/Wenzhi-Ding/Std_Security_Code) |
| **Stars/Forks** | 61 / 8 |
| **Problem Solved** | Pre-built link tables: ISIN, CUSIP, CIK, GVKEY, tickers |
| **Status** | Maintained (Jun 2022) |
| **License** | GPL-3.0 |
| **Integration Effort** | **Low** - Parquet files ready to use |

**Note:** GPL-3.0 license has copyleft implications.

### cik-cusip-mapping

| Attribute | Details |
|-----------|---------|
| **Repository** | [leoliu0/cik-cusip-mapping](https://github.com/leoliu0/cik-cusip-mapping) |
| **Stars/Forks** | 174 / 49 |
| **Problem Solved** | CIK to CUSIP mapping from SEC 13D/13G filings |
| **Status** | **Archived** (Apr 2025) |
| **License** | Not specified |
| **Integration Effort** | **Medium** |

### OpenFIGI Official Examples

| Attribute | Details |
|-----------|---------|
| **Repository** | [OpenFIGI/api-examples](https://github.com/OpenFIGI/api-examples) |
| **Stars/Forks** | - |
| **Problem Solved** | Official API examples in multiple languages |
| **Status** | Official Bloomberg/OpenFIGI |
| **License** | - |
| **Integration Effort** | **Low** |

---

## 5. Security Master Database

### securitiesdb (Reference Architecture)

| Attribute | Details |
|-----------|---------|
| **Repository** | [davidkellis/securitiesdb](https://github.com/davidkellis/securitiesdb) |
| **Stars/Forks** | 57 / 18 |
| **Problem Solved** | Complete securities master: EOD prices, splits, dividends, fundamentals |
| **Status** | **Abandoned** (Jan 2016) |
| **License** | MIT |
| **Integration Effort** | **High** - Reference only |

**Use as reference for:**
- Database schema design
- Data model for securities
- Corporate actions handling
- Multi-source data integration

**Schema includes:**
- Securities (equities, indices, options)
- EOD price data
- Splits and dividends
- Company fundamentals
- Economic indicators

### Security-Master

| Attribute | Details |
|-----------|---------|
| **Repository** | [carstenf/Security-Master](https://github.com/carstenf/Security-Master) |
| **Stars/Forks** | 12 / 3 |
| **Problem Solved** | Securities database with Quandl/Yahoo import |
| **Status** | Older (Feb 2020) |
| **License** | Not specified |
| **Integration Effort** | **Medium** - Zipline-specific |

---

## 6. Financial Data ETL

### ETL-SEC-EDGAR-10-K-Filings

| Attribute | Details |
|-----------|---------|
| **Repository** | [pChitral/ETL-SEC-EDGAR-10-k-Filings](https://github.com/pChitral/ETL-SEC-EDGAR-10-k-Filings) |
| **Stars/Forks** | 15 / 1 |
| **Problem Solved** | Extract MDA sections from 10-K filings |
| **Status** | Maintained (Feb 2024) |
| **License** | Not specified |
| **Integration Effort** | **Medium** |

---

## 7. Risk Analytics (Already in library_integrations.md)

### Riskfolio-Lib

| Attribute | Details |
|-----------|---------|
| **Repository** | [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) |
| **Stars/Forks** | 3,000+ / 600+ |
| **Problem Solved** | 24 convex risk measures, portfolio optimization |
| **Status** | **Very Active** (v7.x) |
| **License** | BSD-3 |
| **Integration Effort** | **Low** |

---

## Integration Priority Matrix

### High Priority (MVP)

| Library | Reason | Effort |
|---------|--------|--------|
| **simplefix** | FIX parsing for trade data | Low |
| **pyopenfigi** | Identifier mapping (free API) | Low |
| **quantstats** | Portfolio analytics | Low |
| **Riskfolio-Lib** | Risk calculations | Low |

### Medium Priority (Phase 2)

| Library | Reason | Effort |
|---------|--------|--------|
| **PyPortfolioOpt** | Advanced optimization | Low |
| **Std_Security_Code** | Pre-built mappings | Low |
| **blp** | Bloomberg integration | Medium |

### Low Priority (Phase 3)

| Library | Reason | Effort |
|---------|--------|--------|
| **quickfix** | Full FIX connectivity | High |
| **securitiesdb** | Reference architecture | High |

---

## License Compatibility

| Library | License | Commercial Use | Copyleft |
|---------|---------|----------------|----------|
| simplefix | MIT | Yes | No |
| pyopenfigi | MIT | Yes | No |
| quantstats | Apache-2.0 | Yes | No |
| Riskfolio-Lib | BSD-3 | Yes | No |
| PyPortfolioOpt | MIT | Yes | No |
| blp | Apache-2.0 | Yes | No |
| quickfix | QuickFIX (BSD-like) | Yes | No |
| Std_Security_Code | **GPL-3.0** | Yes | **Yes** |

**Note:** Std_Security_Code's GPL-3.0 license requires derivative works to also be GPL. Consider using OpenFIGI API directly instead.

---

## Installation Commands

```bash
# Core integrations (MVP)
pip install simplefix
pip install pyopenfigi  # or use requests directly with OpenFIGI API
pip install quantstats
pip install riskfolio-lib

# Additional (Phase 2)
pip install pyportfolioopt

# Bloomberg (requires Terminal)
pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
pip install blp

# FIX (enterprise)
pip install quickfix
```

---

## Enfusion/Eze Eclipse Note

**No unofficial connectors found.** Searches for "enfusion api" returned results for the Enfusion game engine (ARMA Reforger), not Enfusion Systems portfolio management.

For Enfusion and SS&C Eze integration:
- Requires client relationship
- API documentation is private
- Consider FIX protocol as alternative
- CSV export/import as fallback

---

## Sources

- [matthewgilbert/blp](https://github.com/matthewgilbert/blp)
- [matthewgilbert/pdblp](https://github.com/matthewgilbert/pdblp)
- [da4089/simplefix](https://github.com/da4089/simplefix)
- [quickfix/quickfix](https://github.com/quickfix/quickfix)
- [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats)
- [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt)
- [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib)
- [tlouarn/pyopenfigi](https://github.com/tlouarn/pyopenfigi)
- [Wenzhi-Ding/Std_Security_Code](https://github.com/Wenzhi-Ding/Std_Security_Code)
- [OpenFIGI/api-examples](https://github.com/OpenFIGI/api-examples)
- [davidkellis/securitiesdb](https://github.com/davidkellis/securitiesdb)

---

*Integration library research for RISKCORE development*
