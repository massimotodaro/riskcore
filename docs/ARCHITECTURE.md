# RISKCORE Architecture

> Last Updated: 2025-01-09

## Core Principle

**RISKCORE is a READ-ONLY overlay.**

We never write back to source systems. We only:
- Ingest position/trade data
- Price instruments (via FinancePy or client override)
- Normalize and aggregate
- Calculate risk
- Analyse and report

**This makes adoption easy — no one has to change their workflow.**

---

## System Position

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXISTING SYSTEMS (Don't touch)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PM 1: Bloomberg AIM    PM 2: Charles River    PM 3: Excel      │
│  PM 4: Eze Eclipse      PM 5: Enfusion         PM 6: In-house   │
│                                                                 │
│         │                    │                      │           │
│         ▼                    ▼                      ▼           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      RISKCORE                            │   │
│  │         (sits on top, reads everything, writes nothing)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### Layer 1: Data Ingestion

| Source | Method |
|--------|--------|
| Client Systems | File upload (CSV/Excel), REST API pull, Database read replica |
| Market Data | OpenBB (100+ providers), Free: Yahoo/FRED/ECB, Paid: Polygon/Bloomberg |

**Integration Methods (Priority Order):**

| # | Method | Complexity | Real-time? |
|---|--------|------------|------------|
| 1 | File Drop (CSV/Excel) | Easy | No (batch) |
| 2 | REST API Pull | Medium | Near real-time |
| 3 | Database Read Replica | Medium | Real-time |
| 4 | FIX Protocol | Hard | Real-time |
| 5 | Webhook/Push | Medium | Real-time |

---

### Layer 2: Pricing Layer (FinancePy)

**DO NOT BUILD PRICING MODELS — use FinancePy.**

Capabilities from FinancePy:
- Yield curve bootstrap
- Swap valuation
- CDS pricing
- Black-Scholes/76
- Binomial trees
- Vol surface interpolation
- Greeks calculation
- Model calibration

**Price Source Hierarchy:**

```
1. Client Override (they provide price → we use it)
      ↓ if missing
2. RISKCORE Data Feeds (OpenBB)
      ↓ if missing
3. RISKCORE Models (FinancePy)
      ↓ if missing
4. Stale Price + Warning Flag
```

**Critical Design Decisions:**

1. **Transparency is Non-Negotiable** — every price shows: source, timestamp, assumptions, confidence
2. **Client Override Always Wins** — if they say bond = 98, we use 98
3. **Stale Price Handling** — T+0: Green, T+1: Yellow, T+2+: Red
4. **Model Assumptions are Auditable** — every change logged

---

### Layer 3: Aggregation Engine (RISKCORE Unique)

**⚠️ THIS IS THE CORE — what no other platform does.**

Features:
- Multi-PM position consolidation
- Security master (CUSIP/ISIN/SEDOL/Ticker mapping)
- Cross-PM netting & overlap detection
- Hierarchy: Firm → Fund → PM → Strategy → Book
- IBOR (Investment Book of Record)

**No open-source IBOR exists.** All are commercial (SimCorp, Aladdin, Bloomberg AIM).
This is a major opportunity.

---

### Layer 4: Risk Engine (Riskfolio-Lib + Custom)

| From Riskfolio-Lib | Custom (RISKCORE) |
|--------------------|-------------------|
| CVaR, EVaR, RLVaR | Firm-wide VaR |
| Covariance matrices | Cross-PM correlation |
| Drawdown measures | Stress testing |
| Risk parity | Scenario analysis |
| | Limit monitoring & Alerts |

**DO NOT BUILD VaR FROM SCRATCH — use Riskfolio-Lib.**

---

### Layer 5: AI Layer (Claude Integration)

Natural language queries — operators talk to the app:

- "What's our net exposure to tech across all PMs?"
- "Show me positions where PM1 and PM3 have opposite views"
- "Run a stress test: rates +100bps, credit spreads +50bps"
- "Which PM has the highest concentration risk?"

---

### Layer 6: Dashboard (React + Tailwind)

Features:
- Firm-wide view with PM drill-down
- Real-time updates via Supabase subscriptions
- Alerts & breach notifications
- Report generation (PDF)
- Chat interface for AI queries

---

## Target Systems to Support

**Phase 1 (MVP):**

| System | Type | API? | Priority |
|--------|------|------|----------|
| Excel/CSV | File | N/A | HIGH |
| Enfusion | PMS/OMS | Yes | HIGH |
| Eze Eclipse | PMS/OMS | Yes | HIGH |

**Phase 2:**

| System | Type | API? | Priority |
|--------|------|------|----------|
| Bloomberg AIM/PORT | PMS | BLPAPI | MEDIUM |
| Charles River | OMS | Yes | MEDIUM |
| SimCorp | PMS | Yes | MEDIUM |
| Internal Systems | Custom | Database | MEDIUM |

---

## Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PM 1       │     │   PM 2       │     │   PM 3       │
│  Bloomberg   │     │   Enfusion   │     │   Excel      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                   INGESTION LAYER                       │
│  • Parse different formats                              │
│  • Validate data                                        │
│  • Queue for processing                                 │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  SECURITY MASTER                        │
│  • Map identifiers (CUSIP/ISIN/SEDOL/Ticker)           │
│  • Resolve to canonical security ID                     │
│  • Enrich with reference data                          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   PRICING ENGINE                        │
│  • Get prices (OpenBB → FinancePy → Stale)             │
│  • Apply client overrides                              │
│  • Flag stale/missing                                  │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 AGGREGATION ENGINE                      │
│  • Consolidate positions by security                   │
│  • Apply hierarchy (Firm → Fund → PM → Strategy)       │
│  • Detect cross-PM overlaps                            │
│  • Calculate net positions                             │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    RISK ENGINE                          │
│  • Calculate exposures (sector, geography, asset)      │
│  • Calculate VaR (Riskfolio-Lib)                       │
│  • Run stress tests                                    │
│  • Check limits                                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     DASHBOARD                           │
│  • Real-time display                                   │
│  • Alerts                                              │
│  • Reports                                             │
│  • AI chat                                             │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema (High Level)

```
portfolios
├── id
├── name
├── pm_name
├── fund_id
└── created_at

securities
├── id
├── cusip
├── isin
├── sedol
├── ticker
├── name
├── asset_class
├── sector
├── country
└── currency

positions
├── id
├── portfolio_id (FK)
├── security_id (FK)
├── quantity
├── market_value
├── cost_basis
├── as_of_date
└── source_system

prices
├── id
├── security_id (FK)
├── price
├── source (feed/model/override)
├── as_of_date
└── is_stale

risk_metrics
├── id
├── portfolio_id (FK)
├── metric_type (var_95, var_99, cvar, etc.)
├── value
├── as_of_date
└── parameters (JSON)
```

---

## Security Considerations

1. **No credentials in code** — use environment variables
2. **Client data isolation** — multi-tenant design
3. **Audit logging** — all data access logged
4. **Encryption at rest** — Supabase handles this
5. **API authentication** — JWT tokens
