# RISKCORE Pre-Build Research

**Generated:** 2026-01-09
**Purpose:** Comprehensive analysis of existing solutions before development

---

## Executive Summary

### Key Findings

| Category | Finding | Impact on RISKCORE |
|----------|---------|-------------------|
| **IBOR Gap** | No open-source IBOR package exists on PyPI | **Major opportunity** - build this as core differentiator |
| **Security Master Gap** | No complete security master solution exists | Build custom with OpenFIGI integration |
| **Reconciliation Gap** | No portfolio reconciliation packages | Build custom engine |
| **Correlation Crisis** | Multi-manager correlations surge in crises | Implement regime-aware correlation modeling |
| **Data Quality** | #1 cause of risk system failures | Prioritize data validation pipeline |
| **Legacy Pain** | 45% of funds stuck on inflexible systems | Cloud-native architecture is key differentiator |
| **Vendor Lock-in** | All major vendor APIs require client relationship | FIX protocol + CSV import critical for MVP |

### Architecture Implications

1. **Build Custom:** IBOR, Security Master, Reconciliation Engine
2. **Integrate:** Riskfolio-Lib, PyPortfolioOpt, simplefix, pyopenfigi
3. **Prioritize:** Data quality pipeline, regime-aware risk metrics, FIX protocol support
4. **Defer:** Direct vendor API integration (requires client relationships)

---

## 1. Reddit & Community Insights

### Pain Points from r/quant, r/algotrading, r/fintech

| Pain Point | Frequency | Source |
|------------|-----------|--------|
| **Data Quality Issues** | High | "The biggest reason for failure in risk monitoring is data quality" |
| **Correlation Instability** | High | Correlations surge during crises, undermining diversification |
| **Legacy System Lock-in** | High | 45% of funds stymied by inflexible systems |
| **API Outages** | Medium | ~$200/month for services with unreliable uptime |
| **Manual Data Bridging** | High | "Humans bridge gap between messy PDFs and clean systems manually" |
| **Regulatory Fatigue** | Medium | "Tired of CCAR, BASEL, and regulatory reporting" |

### Solutions That Worked

| Solution | Context |
|----------|---------|
| **Percentage Risk Rule** | Limiting 1-2% of capital per position |
| **Dynamic Correlation Modeling** | Regime-dependent updates during stress |
| **Kill-switch Rules** | Real-time monitoring to cut exposure fast |
| **Tiered Allocation** | 40-50% major, 30-40% established, 10-20% speculative |
| **Multi-broker Aggregation** | Tools monitoring positions across sources |

### Solutions That Failed

| Solution | Why It Failed |
|----------|---------------|
| Static diversification | Correlations converge during crises |
| PMS tools expecting clean data | Real world has messy PDFs and emails |
| Default reporting features | Too rigid, lack customization |
| Building on poor data quality | Garbage in, garbage out |

### Relevant Discussions

- [Breaking Alpha - Correlation Risk Management](https://breakingalpha.io/insights/correlation-risk-management-multiple-algorithms)
- [Hedge Fund Journal - Managing Complexity](https://thehedgefundjournal.com/managing-complexity-with-technology/)
- [Broadridge - HF Technology Challenges](https://www.broadridge.com/_assets/pdf/broadridge-hedge-funds-face-growing-risk-technology-and-data-challenges.pdf)

---

## 2. Useful PyPI Packages

### Recommended for Integration

| Package | Purpose | Stars | License | Use Case |
|---------|---------|-------|---------|----------|
| **Riskfolio-Lib** | Portfolio optimization | 3k+ | BSD-3 | VaR, CVaR, 24 risk measures |
| **PyPortfolioOpt** | Mean-variance optimization | 4.5k+ | MIT | Black-Litterman, HRP |
| **skfolio** | ML-compatible optimization | New | BSD | scikit-learn integration |
| **quantstats** | Portfolio analytics | 4.5k+ | Apache-2.0 | Performance reporting |
| **simplefix** | FIX message parsing | 250+ | MIT | Lightweight FIX support |
| **quickfix** | Full FIX protocol | 1.9k+ | BSD-like | Enterprise FIX connectivity |
| **financedatabase** | Security reference data | - | - | 300k+ symbols bootstrap |
| **pyopenfigi** | Identifier mapping | - | MIT | CUSIP/ISIN/FIGI mapping |

### Critical Gaps Identified

| Gap | Current State | RISKCORE Opportunity |
|-----|---------------|---------------------|
| **IBOR** | No packages exist | Core feature |
| **Security Master** | No complete solution | Build with OpenFIGI |
| **Reconciliation** | No packages exist | Build custom engine |
| **Multi-portfolio aggregation** | Not addressed | Core differentiator |

### Package Details

**Riskfolio-Lib** - [pypi.org/project/Riskfolio-Lib](https://pypi.org/project/Riskfolio-Lib/)
- 24 convex risk measures
- Kelly Criterion, Risk Parity, HRP
- CVaR, EVaR, drawdown measures
- Active development (v7.x)

**simplefix** - [pypi.org/project/simplefix](https://pypi.org/project/simplefix/)
- Pure Python, no dependencies
- Simple FIX message creation/parsing
- MIT license
- Good for MVP, upgrade to quickfix later

---

## 3. Vendor API Notes

### Summary

| Vendor | Public Docs | Auth | Formats | Client Required |
|--------|-------------|------|---------|-----------------|
| **Enfusion** | No | Proprietary | REST, WebSocket | Yes |
| **SS&C Eze** | No | Proprietary | REST, xAPI, FIX | Yes |
| **Bloomberg BLPAPI** | Yes | App Key/Cert | BLPAPI, HTTP | Yes (Terminal/B-PIPE) |
| **Charles River** | No | Proprietary | REST, FIX | Yes |
| **FIX Protocol** | Yes | Logon Message | Tag=Value | No (Open Standard) |

### Bloomberg BLPAPI (Most Accessible)

**Documentation:** [bloomberg.github.io/blpapi-docs/python](https://bloomberg.github.io/blpapi-docs/python/3.25.3/)

**Key Services:**
- `//blp/refdata` - Reference data
- `//blp/mktdata` - Market data
- Historical data requests
- Real-time subscriptions

**Python Installation:**
```bash
pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
```

**Wrapper Libraries:**
- `blp` - Pythonic interface
- `pdblp` - pandas integration

### FIX Protocol 4.4 (Open Standard)

**Specification:** [fixtrading.org/standards/fix-4-4](https://www.fixtrading.org/standards/fix-4-4/)

**Key Message Types for RISKCORE:**

| MsgType | Tag 35 | Description |
|---------|--------|-------------|
| Execution Report | 8 | Order fills, status |
| Trade Capture Report | AE | Executed trades |
| Position Report | AP | Position information |
| Allocation Instruction | J | Post-trade allocation |

**RISKCORE Implication:** Build FIX adapter for trade/position ingestion as MVP integration path.

### Enfusion Notes

- Cloud-native SaaS (PMS, OEMS, accounting, compliance)
- REST API + WebSocket (real-time)
- Google Cloud BigQuery for historical data
- Supports: equities, options, futures, FI, FX, swaps, OTC
- 80% of clients use complete front-to-back package
- **API access requires client relationship**

---

## 4. Academic References

### Top 10 Papers for RISKCORE

| Paper | Year | Key Methodology | Applicability |
|-------|------|-----------------|---------------|
| [Cross-Asset Risk Management with LLMs](https://arxiv.org/abs/2504.04292) | 2025 | Real-time AI monitoring | Very High |
| [Risk Aggregation and Diversification](https://belkcollege.charlotte.edu/wp-content/uploads/sites/953/2023/12/Risk-Aggregation-and-Diversification.pdf) | 2015 | VaR/TVaR theory | Very High |
| [Asset and Factor Risk Budgeting](https://arxiv.org/html/2312.11132) | 2024 | Dual risk budgeting | High |
| [Risk factor aggregation](https://arxiv.org/abs/2310.04511) | 2023 | PCA + autoencoders | High |
| [Portfolio Rebalancing Strategies](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=297639) | 2001 | CVaR comparison | Very High |
| [Systemic Risk and Hedge Funds](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=689381) | 2005 | Regime-switching | High |
| [Multi-Asset Risk Prediction with CNNs](https://arxiv.org/abs/2412.03618) | 2024 | Deep learning | High |
| [Multi-asset return risk measures](https://arxiv.org/abs/2411.08763) | 2024 | MARRM framework | High |
| [Hedge Fund Systemic Risk Signals](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1799852) | 2010 | Early warning system | High |
| [Risk Management for Hedge Funds](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=283308) | 2001 | Nonlinear risk | High |

### Key Methodological Insights

1. **Simple summation inadequate** - Correlation-based and copula methods required
2. **Factor-based decomposition** - Enables asset + factor level attribution
3. **Dependence uncertainty** - Must account for tail risk scenarios
4. **Regime-switching models** - Essential for market state detection
5. **LLMs for monitoring** - Emerging approach for real-time text/news analysis

### Gap in Literature

**No papers specifically address multi-PM aggregation from an IBOR perspective.** Academic focus is on single-portfolio optimization and market-level systemic risk, not operational aggregation across portfolio managers.

---

## 5. Community Discussions (HN/SO)

### Hacker News Insights

**Portfolio Aggregation:**
- Broker/bank integration is "make or break" feature
- Users rely heavily on CSV exports and data processing
- Key features: exact rebalancing amounts, add-only mode for taxes, portfolio health scoring

**Security Master Database:**
- Core entities: Exchanges, Vendors, Instruments, Prices
- Map identifiers to consistent standards (ISIN, FIGI, CUSIP, SEDOL)
- Support multiple vendors per ticker for error correction
- Store splits, dividends, corporate actions alongside prices

**Hedge Fund Technology:**
- Only 4-5 trading firms have great tech reputation
- Technology is table stakes, not differentiator
- Balance ML with traditional approaches
- Build for scalability from start

### Recommended Resources

| Resource | URL | Topic |
|----------|-----|-------|
| QuantStart Security Master | [quantstart.com](https://www.quantstart.com/articles/Securities-Master-Databases-for-Algorithmic-Trading/) | Database design |
| securitiesdb | [github.com/davidkellis/securitiesdb](https://github.com/davidkellis/securitiesdb) | PostgreSQL implementation |
| Databento Normalization | [databento.com](https://databento.com/microstructure/normalization) | Data normalization |
| Wealthfolio Discussion | [HN](https://news.ycombinator.com/item?id=41465735) | Portfolio tracking |

### Key Takeaways

1. **Data Quality is Paramount** - Multiple sources, error correction, audit trails
2. **Integration Complexity** - Connecting to multiple data sources is consistently hard
3. **Normalization Non-Negotiable** - Standardize symbols, timezones, formats before analysis
4. **Technology Necessary but Not Sufficient** - Strategy and data quality matter more
5. **Scale Considerations** - What works small often breaks at institutional scale
6. **Open Source Viable** - PostgreSQL + Python can match enterprise functionality

---

## 6. Recommendations for RISKCORE

### MVP Architecture Changes

| Original Plan | Research Finding | Recommended Change |
|---------------|------------------|-------------------|
| Generic data ingestion | FIX protocol is open standard | Prioritize FIX adapter |
| Assume clean data | Data quality is #1 failure cause | Add validation pipeline |
| Static correlation | Correlations surge in crises | Implement regime detection |
| Vendor API integrations | All require client relationships | CSV + FIX for MVP |

### Build vs. Buy Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Risk calculations | **Integrate** Riskfolio-Lib | Mature, 24 risk measures |
| Portfolio optimization | **Integrate** PyPortfolioOpt | Well-tested, MIT license |
| FIX parsing | **Integrate** simplefix | Lightweight, pure Python |
| Identifier mapping | **Integrate** pyopenfigi | Free OpenFIGI API |
| IBOR engine | **Build** | No solution exists |
| Security master | **Build** | No complete solution |
| Reconciliation | **Build** | No solution exists |
| Cross-PM netting | **Build** | No solution exists |

### Priority Stack

**Phase 1 (MVP):**
1. Data ingestion (CSV, FIX)
2. Security master (PostgreSQL + OpenFIGI)
3. Position aggregation engine
4. Basic risk metrics (Riskfolio-Lib)

**Phase 2 (Differentiation):**
5. Reconciliation engine
6. Cross-PM netting detection
7. Regime-aware correlation
8. Natural language queries (Claude)

**Phase 3 (Scale):**
9. Real-time streaming (WebSocket)
10. Regulatory reporting templates
11. Vendor API adapters (as client relationships form)

### Risk Factors to Monitor

| Risk | Mitigation |
|------|------------|
| Data quality failures | Build validation pipeline first |
| Correlation underestimation | Implement stress testing day 1 |
| Feature creep | Stick to IBOR/aggregation core |
| Vendor competition | Focus on open-source, multi-source value prop |

---

## Sources

### Reddit/Community
- [Breaking Alpha - Correlation Risk](https://breakingalpha.io/insights/correlation-risk-management-multiple-algorithms)
- [Hedge Fund Journal](https://thehedgefundjournal.com/managing-complexity-with-technology/)
- [Broadridge Research](https://www.broadridge.com/_assets/pdf/broadridge-hedge-funds-face-growing-risk-technology-and-data-challenges.pdf)
- [LuxAlgo - Risk Strategies](https://www.luxalgo.com/blog/risk-management-strategies-for-algo-trading/)

### PyPI
- [Riskfolio-Lib](https://pypi.org/project/Riskfolio-Lib/)
- [PyPortfolioOpt](https://pypi.org/project/pyportfolioopt/)
- [simplefix](https://pypi.org/project/simplefix/)
- [quickfix](https://pypi.org/project/quickfix/)
- [pyopenfigi](https://pypi.org/project/pyopenfigi/)

### Vendor APIs
- [Bloomberg BLPAPI](https://bloomberg.github.io/blpapi-docs/python/3.25.3/)
- [FIX Protocol 4.4](https://www.fixtrading.org/standards/fix-4-4/)
- [Enfusion](https://www.enfusion.com/connectivity-data-and-apis/)

### Academic
- [arXiv - Cross-Asset Risk with LLMs](https://arxiv.org/abs/2504.04292)
- [SSRN - Hedge Fund Risk](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=283308)
- [Risk Aggregation Theory](https://belkcollege.charlotte.edu/wp-content/uploads/sites/953/2023/12/Risk-Aggregation-and-Diversification.pdf)

### HN/SO
- [QuantStart - Security Master](https://www.quantstart.com/articles/Securities-Master-Databases-for-Algorithmic-Trading/)
- [securitiesdb GitHub](https://github.com/davidkellis/securitiesdb)
- [Databento Normalization](https://databento.com/microstructure/normalization)

---

*Research compiled for RISKCORE pre-build planning*
