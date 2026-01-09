# RISKCORE

> Open-source multi-manager risk aggregation platform

## What Problem We Solve

Multi-manager hedge funds have PMs using different systems (Bloomberg, Enfusion, Eze, Excel). 
**No platform aggregates risk across all of them.** Central risk teams use spreadsheets and prayer.

RISKCORE gives firms a firm-wide view they've never had.

---

## Core Principle

**RISKCORE is a READ-ONLY overlay.**

We never write back to source systems. We only:
- Ingest position/trade data
- Price instruments
- Normalize and aggregate
- Calculate risk
- Analyse and report

This makes adoption easy — no one changes their workflow.

---

## Tech Stack

| Layer | Solution | Notes |
|-------|----------|-------|
| Database | **Supabase** | Postgres + real-time, project: `vukinjdeddwwlaumtfij` |
| Backend | **Python + FastAPI** | Standard, integrates with finance libs |
| Frontend | **React + Tailwind** | Beautiful, professional |
| Charts | **Recharts / Tremor** | Modern, React-native |
| AI | **Claude API** | Natural language risk queries |
| Hosting | **Vercel + Railway** | Free tier for MVP |
| Repo | **GitHub (public)** | Open-source visibility |

---

## What We BUILD (RISKCORE Unique Value)

These don't exist anywhere — this is our differentiation:

- [ ] Position ingestion & normalization API
- [ ] Security master (CUSIP/ISIN/SEDOL/Ticker mapping)
- [ ] Multi-PM aggregation engine
- [ ] Cross-PM netting & overlap detection
- [ ] Firm-wide risk rollup
- [ ] Natural language interface (Claude)
- [ ] Dashboard

---

## What We DON'T Build (Use Libraries)

**DO NOT REBUILD THESE — use existing open-source:**

| Need | Library | Stars | Notes |
|------|---------|-------|-------|
| Market Data | **OpenBB** | 31k+ | 100+ data providers |
| Derivatives Pricing | **FinancePy** | 2.6k+ | Bonds, swaps, options, CDS, Greeks |
| Risk Metrics | **Riskfolio-Lib** | 3k+ | VaR, CVaR, covariance, 24 risk measures |
| Performance Analytics | **QuantStats** | 4.5k+ | Tear sheets, reporting |

---

## Architecture Layers

```
1. DATA INGESTION
   - Client: File upload (CSV/Excel), REST API, Database read
   - Market: OpenBB (100+ providers)
   
2. PRICING LAYER (FinancePy)
   - Yield curves, swaps, CDS, options
   - Price hierarchy: Client Override → Our Feeds → Our Models → Stale + Warning
   
3. AGGREGATION ENGINE (RISKCORE Unique) ← THIS IS THE CORE
   - Multi-PM position consolidation
   - Security master mapping
   - Cross-PM netting & overlap detection
   - Hierarchy: Firm → Fund → PM → Strategy → Book
   - IBOR (Investment Book of Record)
   
4. RISK ENGINE (Riskfolio-Lib + Custom)
   - From Riskfolio: CVaR, EVaR, covariance, drawdowns
   - Custom: Firm-wide VaR, cross-PM correlation, stress testing, limits
   
5. AI LAYER (Claude)
   - Natural language queries
   - "What's our net tech exposure across all PMs?"
   
6. DASHBOARD (React + Tailwind)
   - Firm-wide view, PM drill-down
   - Real-time updates, alerts, chat interface
```

---

## Integration Priority

**Phase 1 (MVP):**
| System | Type | Priority | Reason |
|--------|------|----------|--------|
| Excel/CSV | File | HIGH | Universal, every fund has this |
| Enfusion | API | HIGH | Cloud-native, good API, 950+ HF clients |
| Eze Eclipse | API | HIGH | 200+ clients, modern API |

**Phase 2 (Post-MVP):**
| System | Type | Priority | Reason |
|--------|------|----------|--------|
| Bloomberg AIM/PORT | BLPAPI | MEDIUM | Complex API, enterprise sales cycle |
| Charles River | API | MEDIUM | OMS focus, less common at multi-managers |
| SimCorp | API | MEDIUM | Asset managers |

---

## MVP Timeline (6 Weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Database schema, mock data generator, GitHub repo public |
| 2 | Position & trade ingestion API, basic P&L calculation |
| 3 | Risk engine: VaR (Riskfolio-Lib), exposures, Greeks (FinancePy) |
| **4** | **AGGREGATION ENGINE: Cross-PM netting, firm-level view** |
| 5 | Dashboard: Beautiful, responsive, real-time |
| 6 | AI layer: Natural language queries, polish, docs |

---

## Current Phase

**Planning & Research** (before Week 1)

- [x] Competitor analysis (60 articles scraped)
- [x] GitHub research (found FinancePy, Riskfolio-Lib, OpenBB)
- [ ] Pre-build research (Reddit, PyPI, vendor APIs)
- [ ] Integration libraries research
- [ ] Database schema design
- [ ] Mock data generator

---

## Key Documentation

| Doc | Location | Contents |
|-----|----------|----------|
| Architecture | `/docs/ARCHITECTURE.md` | Full system design, layers, diagrams |
| MVP | `/docs/MVP.md` | Scope, timeline, success metrics |
| Tech Stack | `/docs/TECH_STACK.md` | What we use and why |
| Competitors | `/docs/COMPETITORS.md` | RiskVal, Imagine, Enfusion, Eze, etc. |
| GitHub Research | `/docs/GITHUB_RESEARCH.md` | Open-source findings |
| Pricing | `/docs/PRICING.md` | Pricing layer design, FinancePy integration |
| Integration | `/docs/INTEGRATION.md` | How we connect to client systems |
| Decisions | `/docs/DECISIONS.md` | Key decisions with rationale |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01-09 | Use FinancePy for pricing | Don't rebuild derivatives pricing, MIT license, active |
| 2025-01-09 | Use Riskfolio-Lib for VaR | 24 risk measures, active development |
| 2025-01-09 | Use OpenBB for market data | 100+ providers, well-maintained |
| 2025-01-09 | READ-ONLY overlay architecture | Easy adoption, no workflow disruption |
| 2025-01-09 | Excel/CSV first, then Enfusion/Eze | Universal format first, then popular platforms |
| 2025-01-09 | Supabase for database | Already set up, real-time, free tier |
| 2025-01-09 | Week 4 = Aggregation Engine | Core differentiator, must be solid |

---

## Supabase Connection

```
Project ID: vukinjdeddwwlaumtfij
URL: https://vukinjdeddwwlaumtfij.supabase.co
```

Tables created:
- `research_articles` (60 articles loaded)
- `jobs_raw`, `jobs`, `user_profile` (job hunt system)

Tables needed for RISKCORE:
- `positions`
- `trades`
- `securities`
- `portfolios`
- `price_history`
- `risk_metrics`

---

## Commands

```bash
# Start backend
cd backend && uvicorn main:app --reload

# Start frontend
cd frontend && npm run dev

# Run tests
pytest

# Generate mock data
python scripts/generate_mock_data.py
```

---

## Owner

**Massimo Todaro**
- 20+ years finance (Barclays Capital, Luperco Capital, fintech)
- CFA
- Building this as thought leadership + open-source contribution
- LinkedIn content strategy in parallel

---

## Context for Claude Code

When working on this project:

1. **Always check /docs first** before implementing anything
2. **Don't rebuild** what FinancePy, Riskfolio-Lib, or OpenBB already do
3. **The aggregation engine is the core** — everything else supports it
4. **READ-ONLY** — we never write to client systems
5. **Beautiful dashboard** — this will be demoed to prospects
6. **Ask if unsure** — check DECISIONS.md or ask for clarification
