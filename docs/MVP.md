# RISKCORE MVP

> Last Updated: 2025-01-09

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
| Performance analytics | **QuantStats** | Tear sheets, reporting |

**DO NOT REBUILD THESE.**

---

## What We DO Build (RISKCORE Unique)

These don't exist anywhere — this is our value:

- [ ] Position ingestion & normalization
- [ ] Security master / identifier mapping (CUSIP/ISIN/SEDOL/Ticker)
- [ ] Multi-PM aggregation engine
- [ ] Cross-PM netting & overlap detection
- [ ] Firm-wide risk rollup
- [ ] Natural language interface (Claude)
- [ ] Dashboard

---

## 6-Week Timeline

| Week | Deliverable | Details |
|------|-------------|---------|
| **1** | Foundation | Database schema, mock data generator, GitHub repo public |
| **2** | Ingestion | Position & trade ingestion API, basic P&L calculation |
| **3** | Risk | Risk engine using Riskfolio-Lib, exposures, Greeks via FinancePy |
| **4** | **Aggregation** | **Cross-PM netting, firm-level view, overlap detection** ← CORE |
| **5** | Dashboard | Beautiful, responsive, real-time (React + Tailwind) |
| **6** | AI + Polish | Natural language queries (Claude), documentation |

---

## Integration Phases

### Phase 1 (MVP): File Drop + FIX + REST API

| System | Type | Priority | Reason |
|--------|------|----------|--------|
| Excel/CSV | File | HIGH | Universal, every fund has this |
| **FIX Protocol** | simplefix | HIGH | Open standard, vendor APIs require client relationship |
| JSON | File | HIGH | API-friendly format |

**Key Research Finding:** Vendor APIs (Enfusion, Eze, Bloomberg) all require client relationships. FIX protocol is open standard.

Deliverables:
- Accept CSV/Excel/JSON uploads (any format)
- Auto-detect columns, map to RISKCORE schema
- **FIX adapter using simplefix** for trade/position ingestion
- **Data validation pipeline** (research shows data quality is #1 failure cause)
- **pyopenfigi integration** for identifier mapping (CUSIP/ISIN/SEDOL/Ticker to FIGI)

### Phase 2: Database Connectors

- Read replicas from common databases (Postgres, SQL Server, Oracle)
- Scheduled sync (every 5 min, hourly, EOD)

### Phase 3: Real-time

- FIX protocol listener
- Webhooks for instant updates

---

## Success Metrics

MVP is successful when:

- [ ] Upload positions from 3 different file formats (CSV, Excel, JSON)
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
- [ ] Build mock data generator (realistic positions, multiple PMs)
- [ ] **Data validation pipeline** (schema validation, required fields, data types)
- [ ] **pyopenfigi integration** for security master identifier mapping
- [ ] Set up GitHub repo structure
- [ ] Write README
- [ ] Create project board (GitHub Projects or Notion)
- [ ] First commit

---

## Week 2 Checklist

- [ ] Position ingestion API (POST /positions)
- [ ] File upload endpoint (CSV, Excel, JSON)
- [ ] **FIX adapter using simplefix** (parse FIX messages for trades/positions)
- [ ] Column auto-detection
- [ ] Data validation (using Week 1 pipeline)
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
- [ ] Identifier mapping logic (CUSIP ↔ ISIN ↔ SEDOL ↔ Ticker)
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
| **Vendor APIs require client relationship** | Can't build direct connectors | **FIX protocol + CSV for MVP** (confirmed by research) |
| **Data quality issues** | Risk system failures (#1 cause) | **Data validation pipeline in Week 1** |
| FinancePy doesn't cover all instruments | Pricing gaps | Use client override for edge cases |
| Riskfolio-Lib learning curve | Delays Week 3 | Study library in Week 1-2 |
| Dashboard takes longer than expected | Week 5 overruns | Use component library (shadcn/ui) |
| AI queries too slow | Poor UX | Cache common queries, optimize prompts |
| Correlation instability in crises | VaR underestimation | Implement regime-aware modeling (Phase 2) |
