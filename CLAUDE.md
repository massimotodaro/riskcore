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
| Repo | **GitHub (public)** | github.com/massimotodaro/riskcore |

---

## What We BUILD (RISKCORE Unique Value)

These don't exist anywhere — this is our differentiation:

- [x] Data validation pipeline
- [ ] Position ingestion & normalization API
- [x] Security master (CUSIP/ISIN/SEDOL/Ticker + FIGI mapping)
- [ ] Multi-PM aggregation engine
- [ ] Cross-PM netting & overlap detection
- [ ] Firm-wide risk rollup
- [ ] Natural language interface (Claude)
- [ ] Riskboard Dashboard

---

## What We DON'T Build (Use Libraries)

**DO NOT REBUILD THESE — use existing open-source:**

| Need | Library | Stars | Notes |
|------|---------|-------|-------|
| Market Data | **OpenBB** | 31k+ | 100+ data providers |
| Derivatives Pricing | **FinancePy** | 2.6k+ | Bonds, swaps, options, CDS, Greeks |
| Risk Metrics | **Riskfolio-Lib** | 3k+ | VaR, CVaR, covariance, 24 risk measures |
| Performance Analytics | **QuantStats** | 4.5k+ | Tear sheets, reporting |
| FIX Protocol | **simplefix** | 250+ | Lightweight FIX parsing |
| Identifier Mapping | **pyopenfigi** | 23+ | Free OpenFIGI API |

---

## Architecture Layers

```
1. DATA INGESTION
   - Client: File upload (CSV/Excel), REST API, FIX protocol
   - Market: OpenBB (100+ providers)
   
2. PRICING LAYER (FinancePy)
   - Yield curves, swaps, CDS, options
   - Price hierarchy: Client Override → Our Feeds → Our Models → Stale + Warning
   
3. AGGREGATION ENGINE (RISKCORE Unique) ← THIS IS THE CORE
   - Multi-PM position consolidation
   - Security master mapping (pyopenfigi)
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
   - Riskboard with RiskCards
   - Firm-wide view, PM drill-down
   - Correlation matrix heatmap
   - Real-time updates, alerts, chat interface
```

---

## Business Model

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Core platform, 1 user, CSV upload, basic risk, "Powered by RISKCORE" watermark |
| **Pro** | $500-2K/mo | Multi-user (10), API access (100 req/min), priority support |
| **Enterprise** | $5-25K/mo | Unlimited users, SSO/SAML, 2FA required, API (1000 req/min), SLA, custom integrations |

---

## Integration Priority

**Phase 1 (MVP):**
| System | Type | Priority | Reason |
|--------|------|----------|--------|
| CSV/Excel | File | HIGH | Universal, every fund has this |
| FIX Protocol | simplefix | HIGH | Open standard, no vendor relationship needed |
| JSON API | REST | HIGH | Modern integration |

**Phase 2 (With Client Relationships):**
| System | Type | Priority | Reason |
|--------|------|----------|--------|
| Bloomberg AIM/PORT | BLPAPI | MEDIUM | Requires Terminal access |
| Enfusion | REST API | MEDIUM | Requires partnership |
| Eze Eclipse | REST API | MEDIUM | Requires SS&C relationship |

---

## MVP Timeline (6 Weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Database schema, data validation pipeline, mock data generator, pyopenfigi integration |
| 2 | Position & trade ingestion API, FIX adapter (simplefix), CSV/Excel upload |
| 3 | Risk engine: VaR (Riskfolio-Lib), exposures, Greeks (FinancePy) |
| **4** | **AGGREGATION ENGINE: Cross-PM netting, firm-level view, overlap detection** |
| 5 | Dashboard: Riskboard, RiskCards, correlation matrix, responsive |
| 6 | AI layer: Natural language queries, documentation, polish |

---

## Current Phase

**Week 1 COMPLETE**

- [x] Competitor analysis (60 articles)
- [x] GitHub research (FinancePy, Riskfolio-Lib, OpenBB)
- [x] Pre-build research (Reddit, PyPI, vendor APIs, academic papers)
- [x] Integration libraries research (simplefix, pyopenfigi, blp, quickfix)
- [x] Library integrations guide (code examples)
- [x] UI/Auth architecture design
- [x] Security architecture design
- [x] GDPR & data residency research
- [x] Database schema design (34 tables, RLS, validation pipeline)
- [x] Mock data generator (realistic multi-PM hedge fund data)
- [x] OpenFIGI integration (custom client, security master service)
- [x] Data validation pipeline (configurable rules, multi-table validation)

---

## Current Implementation State

**Last Updated:** 2026-01-11

### Backend Services

| Service | File | Status | Notes |
|---------|------|--------|-------|
| OpenFIGI Client | `backend/services/openfigi.py` | ✅ Complete | Custom API v3 client, rate-limited |
| Security Master | `backend/services/security_master.py` | ✅ Complete | FIGI resolution + DB integration |
| Validation | `backend/services/validation.py` | ✅ Complete | 11 rules, 5 rule types |
| Position Ingestion | `backend/api/positions.py` | ⬜ Week 2 | FastAPI endpoints |
| Trade Ingestion | `backend/api/trades.py` | ⬜ Week 2 | FastAPI endpoints |
| FIX Parser | `backend/services/fix_parser.py` | ⬜ Week 2 | simplefix integration |
| Risk Engine | `backend/services/risk_engine.py` | ⬜ Week 3 | Riskfolio-Lib |
| Aggregation | `backend/services/aggregation.py` | ⬜ Week 4 | Cross-PM netting |

### Database Migrations

| Migration | Purpose | Status |
|-----------|---------|--------|
| `20260109*_initial` | 32 core tables with RLS | ✅ Applied |
| `20260111160000_schema_improvements` | +2 tables, indexes, triggers | ✅ Applied |
| `20260111180000_add_composite_figi` | FIGI enum values | ✅ Applied |

### Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/generate_mock_data.py` | Test data (~$1.2B AUM, 10 PMs) | ✅ Working |
| `scripts/test_validation.py` | Validation pipeline tests | ✅ Passing |

### Frontend

| Component | Status | Notes |
|-----------|--------|-------|
| React App | ⬜ Week 5 | Vite + Tailwind |
| Dashboard | ⬜ Week 5 | Riskboard layout |
| Chat Interface | ⬜ Week 6 | Claude integration |

---

## Knowledge Sync (CC ↔ CD)

**For Claude Desktop sync, copy these 2 files:**
- `CLAUDE.md` - Architecture, decisions, current state
- `ROADMAP.md` - Detailed milestones, progress tracking

See `ROADMAP.md` for detailed week-by-week progress.

---

## Key Documentation

### Core Architecture
| Doc | Location | Contents |
|-----|----------|----------|
| Architecture | `/docs/ARCHITECTURE.md` | System design, layers, data flow |
| MVP | `/docs/MVP.md` | Scope, timeline, success metrics |
| Tech Stack | `/docs/TECH_STACK.md` | What we use and why |
| Vision | `/docs/VISION.md` | Problem statement, why open source |
| Decisions | `/docs/DECISIONS.md` | Key decisions with rationale |

### Product & Business
| Doc | Location | Contents |
|-----|----------|----------|
| Business Model | `/docs/BUSINESS_MODEL.md` | Pricing, monetization, go-to-market |
| Correlation Framework | `/docs/CORRELATION_FRAMEWORK.md` | Phase 2-3: realized/implied correlation |

### UI & Security
| Doc | Location | Contents |
|-----|----------|----------|
| **UI/Auth Architecture** | `/docs/UI_AUTH_ARCHITECTURE.md` | Riskboard, RiskCards, RBAC, multi-tenant |
| **Security** | `/docs/SECURITY.md` | Auth, encryption, GDPR, audit logging, export controls |

### Research
| Doc | Location | Contents |
|-----|----------|----------|
| Competitor Analysis | `/docs/competitor_analysis.md` | RiskVal, Imagine, Enfusion, Eze, etc. |
| GitHub Research | `/docs/github_research.md` | Open-source landscape |
| Market Research | `/docs/market_research_analysis.md` | 60 articles, pain points, gaps |
| Pre-Build Research | `/docs/pre_build_research.md` | Reddit, PyPI, vendor APIs, academic papers |

### Integration
| Doc | Location | Contents |
|-----|----------|----------|
| Integration Libraries | `/docs/integration_libraries.md` | GitHub libraries for FIX, Bloomberg, identifiers |
| Library Integrations | `/docs/library_integrations.md` | OpenBB, FinancePy, Riskfolio-Lib code examples |

---

## RBAC Roles

| Role | Scope | Key Permissions |
|------|-------|-----------------|
| **SuperAdmin** | Platform | All permissions, manage tenants |
| **Admin** | Tenant | User management, configuration |
| **CIO** | Tenant | View all, approve limits, export |
| **CRO** | Tenant | View all, set limits, RiskOff |
| **PM** | Own Books | View own positions, acknowledge alerts |
| **Analyst** | Assigned | View assigned books only |

---

## Database Tables

### Legacy (Job Hunt System - keeping for now)
- `research_articles`, `jobs_raw`, `jobs`, `user_profile`, `cv_profile`, `scrape_sources`

### RISKCORE Core
| Table | Purpose |
|-------|---------|
| `tenants` | Multi-tenant isolation |
| `users` | User accounts with roles |
| `funds` | Organizational grouping of books |
| `books` | Trading books (PM portfolios) - has `pm_id` |
| `book_user_access` | Granular access control for PM/Analyst |
| `securities` | Global security master (NOT tenant-scoped) |
| `security_identifiers` | FIGI/ISIN/CUSIP/SEDOL/ticker mapping |
| `security_prices` | Historical prices |
| `positions` | Current positions (includes convexity) |
| `position_history` | Historical snapshots |
| `position_changes` | Event log of position changes |
| `trades` | Trade history |
| `risk_metrics` | Pre-calculated risk metrics |
| `risk_metric_history` | Historical risk metrics |
| `limits` | Risk limits per book/fund/tenant |
| `limit_breaches` | Breach history with workflow |
| `correlation_matrices` | Cross-book correlations |
| `factor_exposures` | Factor exposures per book |
| `model_overrides` | User overrides for model inputs |
| `validation_rules` | Data validation rule definitions |
| `validation_results` | Validation errors and warnings |
| `uploads` | File upload tracking |
| `upload_records` | Individual records from uploads |
| `notifications` | User notifications |
| `saved_views` | User-saved book combinations |
| `api_keys` | API key management |
| `audit_logs` | Security audit trail (includes `user_email`) |
| `pending_invitations` | User invitations |

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-11 | Mock data generator with 3 scales | Realistic multi-PM hedge fund data, fake but believable tickers |
| 2026-01-11 | Schema improvements: convexity, pm_id, validation tables | Complete fixed income support, PM tracking, data quality pipeline |
| 2026-01-11 | audit_logs.user_email denormalized | Permanent audit trail preserved after user deletion |
| 2026-01-11 | snapshot_type converted to enum | Type safety and consistency |
| 2026-01-10 | Free tier: "Powered by RISKCORE" watermark | Subtle branding, removed in Pro |
| 2026-01-10 | Audit logging: sensitive actions only | Viewing platform, not trading - expand later if needed |
| 2026-01-10 | 2FA: Enterprise only | Balance security vs friction |
| 2026-01-10 | SSO/SAML: Phase 2-3 | Nice-to-have, not MVP |
| 2026-01-10 | Data retention: 5 years fixed | Regulatory standard, not configurable |
| 2026-01-10 | US infrastructure for MVP | GDPR allows with SCCs, EU option in Enterprise |
| 2026-01-10 | Export controls by role | PMs own book only, CRO/CIO firm-wide |
| 2026-01-10 | Riskboard dashboard design | RiskCards, book selector, correlation heatmap |
| 2026-01-10 | Multi-tenant from day 1 | tenant_id + RLS on all tables |
| 2026-01-09 | Use simplefix for FIX parsing | Lightweight, MIT, upgrade to quickfix later |
| 2026-01-09 | Use pyopenfigi for identifiers | Free OpenFIGI API, Bloomberg-backed |
| 2026-01-09 | Data validation pipeline Week 1 | Data quality = #1 failure cause |
| 2026-01-09 | READ-ONLY architecture | Easy adoption, no workflow disruption |

---

## Supabase Connection

```
Project ID: vukinjdeddwwlaumtfij
URL: https://vukinjdeddwwlaumtfij.supabase.co
```

---

## Commands

```bash
# Start backend
cd backend && uvicorn main:app --reload

# Start frontend
cd frontend && npm run dev

# Run tests
pytest

# Generate mock data (medium scale: 10 PMs, 200 securities, ~1000 positions)
python scripts/generate_mock_data.py --clean --scale medium

# Other mock data options
python scripts/generate_mock_data.py --scale small   # 5 PMs, 50 securities
python scripts/generate_mock_data.py --scale large   # 20 PMs, 500 securities
python scripts/generate_mock_data.py --clean-only    # Just clean, don't generate
```

---

## Owner

**Massimo Todaro**
- 20+ years finance (Barclays Capital, Luperco Capital, fintech)
- CFA
- Building this as thought leadership + open-source contribution
- LinkedIn content strategy in parallel


## Local Development Environment

**Status:** Configured and working (2026-01-11)

### Setup Complete
- ✅ Supabase CLI installed (v2.67.1)
- ✅ Project linked to `vukinjdeddwwlaumtfij`
- ✅ Schema pulled to `supabase/migrations/`
- ✅ Local environment tested (32 tables)

### Project Folder
```
C:\Users\massi\Desktop\RISKCORE
```

### Start Local Environment
```powershell
cd C:\Users\massi\Desktop\RISKCORE
supabase start
```

### Local URLs
| Service | URL |
|---------|-----|
| Studio | http://127.0.0.1:54323 |
| API | http://127.0.0.1:54321 |
| Database | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` |

### Key Commands
```powershell
supabase start      # Start local environment
supabase stop       # Stop local environment
supabase db reset   # Wipe and reapply migrations
supabase db pull    # Download production schema
supabase db push    # Deploy to production
```

### Schema Source of Truth
Migrations are in `supabase/migrations/`. **Query these files** instead of guessing column names.

### For Claude/CC
- If user says "query local" → use `127.0.0.1:54322`
- If user says "check schema" → read `supabase/migrations/*.sql`
- If writing tests → use local database URL
- Schema changes → test locally first with `supabase db reset`

---


## Context for Claude Code

When working on this project:

1. **Always check /docs first** before implementing anything
2. **Don't rebuild** what FinancePy, Riskfolio-Lib, or OpenBB already do
3. **The aggregation engine is the core** — everything else supports it
4. **READ-ONLY** — we never write to client systems
5. **Multi-tenant from day 1** — tenant_id + RLS on every table
6. **Security matters** — see SECURITY.md for auth, audit, export controls
7. **Beautiful dashboard** — this will be demoed to prospects
8. **Ask if unsure** — check DECISIONS.md or ask for clarification

---

## Subagent Strategy

Use these subagent types strategically based on task complexity:

### When to Use Each Subagent

| Subagent | Use For | Example |
|----------|---------|---------|
| **Explore** | Finding files, understanding patterns across 3+ files | "Where is validation handled?" |
| **Plan** | Architecture decisions, algorithm design | Week 4 aggregation features |
| **Bash** | Git operations, running commands | Tests, builds, deployments |
| **general-purpose** | Complex multi-step research | Library integration research |

### Week 4 Aggregation (CRITICAL - Use Plan Agent)

Before implementing Week 4 aggregation features, **always use Plan agent first**:

```
Week 4 Tasks Requiring Plan Agent:
├── Cross-PM netting algorithm
│   → Plan: Design netting logic, handle currency, same-day trades
├── Overlap detection
│   → Plan: Define overlap threshold, reporting format, alert triggers
├── Firm-level rollup
│   → Plan: Hierarchy traversal, aggregation levels, caching strategy
└── Position consolidation
    → Plan: Security matching logic, handling stale prices, reconciliation
```

**Why Plan agent for Week 4:**
- Aggregation is RISKCORE's core differentiator
- Mistakes here affect all downstream features
- Algorithm design needs careful thought before coding
- Cross-PM netting has edge cases (splits, corporate actions, FX)

### Direct Implementation (No Subagent Needed)

- Simple CRUD endpoints
- Standard FastAPI patterns
- Unit tests for existing code
- Bug fixes with clear scope

---

## Hooks Configured

Python syntax validation runs automatically after Edit/Write on `.py` files.

Location: `.claude/hooks/validate-python.ps1`
