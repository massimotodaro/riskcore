# RISKCORE MVP

> Last Updated: 2025-01-09
> Status: Ready to start Week 1

---

## MVP Focus: The Core Problem

**No platform directly addresses multi-manager risk aggregation.**

MVP solves this with three priorities:

1. **Position Aggregation API** — the core problem
2. **Unified Security Master** — normalize data across systems
3. **Basic Exposure Views** — sector, geography, asset class

---

## What We DON'T Build (Use Libraries)

These are solved problems — use existing open-source:

| Need | Library | Why |
|------|---------|-----|
| Derivatives pricing | **FinancePy** | Bonds, swaps, CDS, options, Greeks |
| Risk metrics | **Riskfolio-Lib** | VaR, CVaR, 24 risk measures |
| Market data | **OpenBB** | 100+ data providers |
| FIX parsing | **simplefix** | Lightweight, MIT license |
| Identifier mapping | **pyopenfigi** | Free OpenFIGI API |
| Performance analytics | **quantstats** | Tear sheets, reporting |

**DO NOT REBUILD THESE.**

---

## What We DO Build (RISKCORE Unique)

These don't exist anywhere — this is our value:

- [ ] Data validation pipeline
- [ ] Position ingestion & normalization
- [ ] Security master / identifier mapping (CUSIP/ISIN/SEDOL/Ticker + FIGI)
- [ ] Multi-PM aggregation engine
- [ ] Cross-PM netting & overlap detection
- [ ] Firm-wide risk rollup
- [ ] Natural language interface (Claude)
- [ ] Dashboard

---

## 6-Week Timeline

| Week | Deliverable | Details |
|------|-------------|---------|
| **1** | Foundation | Database schema, **data validation pipeline**, mock data generator, GitHub repo, pyopenfigi integration |
| **2** | Ingestion | Position & trade ingestion API, **FIX adapter (simplefix)**, CSV/Excel upload, basic P&L calculation |
| **3** | Risk | Risk engine using Riskfolio-Lib, exposures, Greeks via FinancePy |
| **4** | **Aggregation** | **Cross-PM netting, firm-level view, overlap detection** ← CORE |
| **5** | Dashboard | Beautiful, responsive, real-time (React + Tailwind) |
| **6** | AI + Polish | Natural language queries (Claude), documentation |

---

## Integration Phases

### Phase 1 (MVP): File Drop + FIX + REST API

| Method | Priority | Notes |
|--------|----------|-------|
| CSV/Excel | HIGH | Universal, every fund has this |
| FIX Protocol | HIGH | Open standard, use simplefix |
| JSON API | HIGH | REST endpoints |

**Note:** Vendor APIs (Enfusion, Eze, Bloomberg) require client relationships. Focus on open standards for MVP.

### Phase 2: Vendor Connectors (With Client Relationships)

| System | Priority | Notes |
|--------|----------|-------|
| Bloomberg AIM/PORT | MEDIUM | Requires BLPAPI access |
| Enfusion | MEDIUM | Requires partnership |
| Eze Eclipse | MEDIUM | Requires SS&C relationship |

### Phase 3: Real-time + Advanced

| Feature | Notes |
|---------|-------|
| WebSocket streaming | Real-time position updates |
| Database connectors | Read replicas (Postgres, SQL Server) |
| Webhook receivers | Push from source systems |

---

## Post-MVP Roadmap

### Phase 2: Correlation Framework (8 weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Risk factor taxonomy implementation |
| 2 | Factor exposure calculation per position |
| 3 | Book-level aggregation |
| 4 | Realized correlation matrix (P&L-based) |
| 5 | Factor covariance matrix builder |
| 6 | Implied correlation calculation |
| 7 | Dashboard: correlation matrix view |
| 8 | Testing and refinement |

**Deliverables:**
- Cross-book correlation matrix (realized + implied)
- Risk factor decomposition per book
- Factor exposure heatmap
- Correlation trend analysis

### Phase 3: Stress Testing & Hedging (12 weeks)

| Week | Deliverable |
|------|-------------|
| 1-2 | Stress correlation scenarios (2008, 2020 COVID) |
| 3-4 | Stress test dashboard view |
| 5-6 | Hedge instrument library |
| 7-8 | Hedge suggestion algorithm |
| 9-10 | Hedge overlay dashboard |
| 11-12 | AI-powered hedge recommendations (Claude) |

**Deliverables:**
- "Correlation → 1" stress test
- VaR under stress scenarios
- Hedge trade suggestions
- Overlay portfolio construction

---

## Success Metrics

MVP is successful when:

- [ ] Upload positions from 3 different formats (CSV, Excel, FIX)
- [ ] See aggregated firm-wide exposure in dashboard
- [ ] Identify cross-PM overlaps automatically
- [ ] Ask "What's our net tech exposure?" and get an answer
- [ ] Demo-able to a prospect in 10 minutes
- [ ] GitHub repo has README, docs, working code
- [ ] At least one LinkedIn post published about the journey

---

## The Pitch

> "Keep your trading systems. Keep your PMs' workflows. RISKCORE sits on top and gives you the firm-wide view you've never had. Connect in minutes with file upload, or days with API integration. No migration, no disruption."

---

## Week 1 Checklist

- [ ] Finalize database schema
- [ ] Create Supabase tables
- [ ] Build data validation pipeline (data quality = #1 priority)
- [ ] Integrate pyopenfigi for identifier mapping
- [ ] Build mock data generator (realistic positions, multiple PMs)
- [ ] Set up GitHub repo structure
- [ ] Write README
- [ ] Create project board (GitHub Projects or Notion)
- [ ] First commit

---

## Week 2 Checklist

- [ ] Position ingestion API (POST /positions)
- [ ] FIX adapter using simplefix
- [ ] File upload endpoint (CSV, Excel)
- [ ] Column auto-detection
- [ ] Basic validation
- [ ] P&L calculation (position × price - cost)
- [ ] Unit tests

---

## Week 3 Checklist

- [ ] Integrate Riskfolio-Lib
- [ ] VaR calculation (95%, 99%)
- [ ] Exposure breakdowns (sector, geography, asset class)
- [ ] Integrate FinancePy for Greeks (if needed)
- [ ] Store risk metrics in database

---

## Week 4 Checklist (CORE)

- [ ] Security master table
- [ ] Identifier mapping logic (CUSIP ↔ ISIN ↔ SEDOL ↔ Ticker ↔ FIGI)
- [ ] Position aggregation across PMs
- [ ] Net position calculation
- [ ] Overlap detection algorithm
- [ ] Firm-level rollup

---

## Week 5 Checklist

- [ ] React + Tailwind setup
- [ ] Dashboard layout
- [ ] Firm-wide view component
- [ ] PM drill-down component
- [ ] Real-time updates (Supabase subscription)
- [ ] Charts (Recharts/Tremor)

---

## Week 6 Checklist

- [ ] Claude API integration
- [ ] Natural language query endpoint
- [ ] Chat interface in dashboard
- [ ] Documentation
- [ ] Demo script
- [ ] LinkedIn post: "RISKCORE is live"

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vendor APIs not accessible | Can't build connectors | Focus on FIX + CSV (open standards) |
| Data quality issues | Garbage in, garbage out | Build validation pipeline first |
| FinancePy doesn't cover all instruments | Pricing gaps | Use client override for edge cases |
| Riskfolio-Lib learning curve | Delays Week 3 | Study library in Week 1-2 |
| Dashboard takes longer than expected | Week 5 overruns | Use component library (shadcn/ui) |
| AI queries too slow | Poor UX | Cache common queries, optimize prompts |
| Correlation calculation complexity | Phase 2 delays | Start with realized correlation only |

---

## Documentation

| Doc | Location | Contents |
|-----|----------|----------|
| Architecture | `/docs/ARCHITECTURE.md` | System design, layers |
| Tech Stack | `/docs/TECH_STACK.md` | What we use and why |
| Decisions | `/docs/DECISIONS.md` | Key decisions with rationale |
| Correlation Framework | `/docs/CORRELATION_FRAMEWORK.md` | Phase 2-3 correlation features |
| Pre-Build Research | `/docs/pre_build_research.md` | Reddit, PyPI, vendor API findings |
| Integration Libraries | `/docs/integration_libraries.md` | GitHub libraries for integration |
| Library Integrations | `/docs/library_integrations.md` | Code examples for OpenBB, FinancePy, Riskfolio-Lib |

---

*MVP scope for RISKCORE development*
