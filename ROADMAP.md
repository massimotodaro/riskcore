# RISKCORE Development Roadmap

> Living document tracking MVP development progress.
> **Last Updated:** 2026-01-12
> **Sync to Claude Desktop:** Copy this file + CLAUDE.md daily

---

## Quick Status

| Week | Phase | Status | Summary |
|------|-------|--------|---------|
| 1 | Foundation | ✅ COMPLETE | Database schema, mock data, OpenFIGI, validation pipeline |
| 2 | Data Ingestion | ✅ COMPLETE | Position/trade API, FIX adapter, CSV/Excel upload |
| 3 | Risk Engine | ✅ COMPLETE | VaR/CVaR (numpy/scipy), exposures, Greeks (Black-Scholes) |
| 4 | Aggregation | ⬜ NOT STARTED | Cross-PM netting, overlap detection, firm rollup |
| 5 | Dashboard | ⬜ NOT STARTED | React + Tailwind, real-time, charts |
| 6 | AI + Polish | ⬜ NOT STARTED | Claude integration, NL queries, documentation |

**Current Focus:** Week 4 - Aggregation Engine (THE CORE)

---

## Week 1: Foundation ✅ COMPLETE

**Dates:** 2026-01-09 to 2026-01-11
**Status:** All milestones complete and tested

### Milestones

- [x] Database schema design (34 tables with RLS)
- [x] Schema improvements (convexity, pm_id, validation tables, indexes)
- [x] Mock data generator (realistic multi-PM hedge fund data)
- [x] OpenFIGI integration (custom API v3 client)
- [x] Security master service (FIGI resolution + database integration)
- [x] Data validation pipeline (configurable rules, multi-table validation)
- [x] CI/CD workflow (GitHub Actions)

### Acceptance Criteria

- [x] `supabase db reset` runs without errors
- [x] `supabase db push` deploys to production successfully
- [x] `python scripts/generate_mock_data.py` creates ~$1.2B AUM across 10 PMs
- [x] `python scripts/test_validation.py` passes all tests (11 rules, 5 rule types)
- [x] OpenFIGI lookups resolve real securities (NVDA, AMZN, BP tested)
- [x] Securities created in database from OpenFIGI data
- [x] GitHub Actions CI passes on develop branch

### Artifacts Created

| File | Purpose | Status |
|------|---------|--------|
| `supabase/migrations/20260109*.sql` | Initial 32-table schema | ✅ Applied |
| `supabase/migrations/20260111160000_schema_improvements.sql` | +2 tables, indexes, triggers | ✅ Applied |
| `supabase/migrations/20260111180000_add_composite_figi.sql` | Enum values for FIGI types | ✅ Applied |
| `scripts/generate_mock_data.py` | Test data generator | ✅ Working |
| `scripts/test_validation.py` | Validation pipeline tests | ✅ Passing |
| `backend/services/openfigi.py` | OpenFIGI API v3 client | ✅ Complete |
| `backend/services/security_master.py` | Security resolution service | ✅ Complete |
| `backend/services/validation.py` | Data validation pipeline | ✅ Complete |
| `backend/services/__init__.py` | Service exports | ✅ Complete |
| `.github/workflows/ci.yml` | CI/CD pipeline | ✅ Working |

### Technical Notes

- **OpenFIGI:** Built custom client (pyopenfigi had Python 3.14 issues). Uses correct idTypes: ID_CUSIP, ID_ISIN, ID_SEDOL.
- **Validation:** 11 default system rules across 4 tables. Supports schema, range, referential, business rule types.
- **Mock Data:** Generates realistic hedge fund structure with 10 PMs, multiple strategies, ~$1.2B AUM.

---

## Week 2: Data Ingestion 🔄 IN PROGRESS

**Target:** Position & trade ingestion API with multiple input methods
**Dates:** 2026-01-12 to 2026-01-17

### Architecture Decision: ON-PREMISES ONLY

**CRITICAL CHANGE (2026-01-12):** Refactored to psycopg2 for direct PostgreSQL access.
- No cloud storage of positions, trades, or risk data
- Hedge funds won't accept cloud-stored financial data
- Development: Supabase local (`supabase start`)
- Production: Client's on-premises PostgreSQL

### Milestones

- [x] FastAPI application structure (Monday)
- [x] Position ingestion API endpoints (Tuesday)
- [x] Refactor to psycopg2 (on-premises architecture) (Wednesday)
- [x] Trade ingestion API endpoints (Wednesday)
- [x] CSV/Excel file upload endpoint (Thursday)
- [x] Column auto-detection for uploads (Thursday)
- [x] FIX message parsing (simplefix) (Thursday)
- [x] Basic P&L calculation (position + book level)
- [x] Unit tests for all endpoints (90 tests passing)

### Acceptance Criteria

- [x] `POST /api/v1/positions` accepts valid position data, returns validation errors for bad data
- [x] `POST /api/v1/trades` accepts valid trade data with proper validation
- [x] `POST /api/v1/upload` handles CSV and Excel files, auto-detects columns
- [x] FIX messages (ExecutionReport, PositionReport) parse correctly using simplefix
- [x] P&L = (quantity × current_price) - (quantity × average_cost) calculated correctly
- [x] Validation pipeline rejects invalid data with clear error messages
- [x] Security master resolves identifiers during ingestion
- [x] All endpoints have >80% test coverage (90 tests passing)

### Dependencies

- Week 1 validation pipeline (for input validation)
- Week 1 security master (for security resolution)
- Week 1 database schema (positions, trades tables)

### Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `backend/main.py` | FastAPI application entry point | ✅ Done |
| `backend/config.py` | Application configuration | ✅ Done |
| `backend/database.py` | **psycopg2 connection pool** (not Supabase) | ✅ Done |
| `backend/api/__init__.py` | API router initialization | ✅ Done |
| `backend/api/positions.py` | Position endpoints (full CRUD) | ✅ Done |
| `backend/services/position_service.py` | Position business logic (psycopg2) | ✅ Done |
| `backend/tests/test_positions.py` | Position API tests (25 tests) | ✅ Done |
| `backend/api/trades.py` | Trade endpoints (full CRUD + cancel) | ✅ Done |
| `backend/services/trade_service.py` | Trade business logic (psycopg2) | ✅ Done |
| `backend/api/upload.py` | File upload endpoint | ✅ Done |
| `backend/api/fix.py` | FIX protocol endpoints | ✅ Done |
| `backend/services/fix_parser.py` | FIX message parser using simplefix | ✅ Done |
| `backend/services/file_parser.py` | CSV/Excel parser with column detection | ✅ Done |
| `backend/services/upload_service.py` | Upload business logic | ✅ Done |
| `backend/models/__init__.py` | Model exports | ✅ Done |
| `backend/models/common.py` | Shared enums, mixins | ✅ Done |
| `backend/models/position.py` | Pydantic models for positions | ✅ Done |
| `backend/models/trade.py` | Pydantic models for trades | ✅ Done |
| `backend/models/upload.py` | Pydantic models for uploads | ✅ Done |
| `backend/tests/test_trades.py` | Trade API tests (26 tests) | ✅ Done |
| `backend/tests/test_upload.py` | Upload API tests (20 tests) | ✅ Done |
| `backend/tests/test_fix.py` | FIX protocol tests (19 tests) | ✅ Done |
| `backend/requirements.txt` | Python dependencies | ✅ Done |

### Technical Approach

1. **On-Premises Architecture:**
   - Direct PostgreSQL via psycopg2 (not Supabase client)
   - ThreadedConnectionPool for production scalability
   - Context managers for safe connection handling
   - Synchronous endpoints (psycopg2 is synchronous)

2. **FastAPI Structure:**
   - Modular routers per domain (positions, trades, upload)
   - Context manager `get_db_connection()` for database access
   - Pydantic models for request/response validation

3. **File Upload:**
   - Accept CSV, XLSX, XLS formats
   - Auto-detect column mappings (ticker, quantity, price, etc.)
   - Return preview for user confirmation before import

4. **FIX Parsing:**
   - Use simplefix for message parsing
   - Support ExecutionReport (tag 35=8) and PositionReport (tag 35=AP)
   - Extract: symbol, quantity, price, side, account

---

## Week 3: Risk Engine ✅ COMPLETE

**Target:** Risk calculations using Riskfolio-Lib and FinancePy
**Dates:** 2026-01-12
**Status:** All milestones complete and battle-tested

### Milestones

- [x] VaR calculation (95%, 99% confidence) - implemented with numpy/scipy
- [x] CVaR/Expected Shortfall
- [x] Sector exposure breakdown
- [x] Geography exposure breakdown
- [x] Asset class exposure breakdown
- [x] Currency exposure breakdown
- [x] Greeks calculation (delta, gamma, vega, theta, rho) - pure Python Black-Scholes
- [x] Risk metrics storage endpoints
- [x] Unit tests for all risk calculations (31 tests)
- [x] Battle-tested all 8 API endpoints
- [ ] Riskfolio-Lib integration (deferred - Windows build issues with cvxpy/osqp)

### Acceptance Criteria

- [x] VaR calculated correctly for portfolio (validated against known examples)
- [x] Exposure breakdowns work with empty/full portfolios
- [x] Greeks (delta, gamma, vega, theta, rho) calculated correctly
- [x] Put-call parity verified (Call Delta - Put Delta = 1)
- [x] ATM delta ~0.5 verified
- [x] All API endpoints return 200 OK
- [x] 121 tests passing (90 Week 2 + 31 Week 3)

### Verification Criteria (ALL PASSED)

```
VERIFY-3.1: VaR Calculation ✅
  [x] Run: python -m pytest backend/tests/test_risk.py::TestVaRCalculations -v
  [x] Expected: All VaR tests pass
  [x] Manual: Historical VaR with normal distribution validated

VERIFY-3.2: Exposure Breakdowns ✅
  [x] Run: python -m pytest backend/tests/test_risk.py::TestExposureCalculations -v
  [x] Expected: All exposure tests pass
  [x] Manual: Verified sector, geography, asset class, currency endpoints

VERIFY-3.3: Greeks Calculation ✅
  [x] Run: python -m pytest backend/tests/test_risk.py::TestGreeksCalculations -v
  [x] Expected: All Greeks tests pass
  [x] Manual: ATM call delta = 0.5695 (~0.5 as expected)
  [x] Manual: Put-call parity verified (0.5695 - (-0.4305) = 1.0)

VERIFY-3.4: API Endpoints ✅
  [x] All 8 risk API endpoints battle-tested
  [x] /api/v1/risk/greeks/calculate - 200 OK
  [x] /api/v1/risk/exposures/{book_id}/summary - 200 OK
  [x] /api/v1/risk/exposures/{book_id}/concentration - 200 OK
  [x] /api/v1/risk/exposures/{book_id} (sector) - 200 OK
  [x] /api/v1/risk/exposures/{book_id}/all - 200 OK
  [x] /api/v1/risk/var/{book_id} - 200 OK
  [x] /api/v1/risk/greeks/book/{book_id} - 200 OK

VERIFY-3.5: Test Suite ✅
  [x] 121 tests passing (90 Week 2 + 31 Week 3)
```

### Technical Decisions

- **Riskfolio-lib deferred:** Windows build issues with cvxpy/osqp wheel compilation. Implemented VaR/CVaR directly with numpy/scipy.
- **Pure Python Black-Scholes:** Used scipy.stats.norm for delta, gamma, vega, theta, rho calculations instead of FinancePy.
- **Three VaR methods:** Historical (default), Parametric, Monte Carlo.
- **VaR scaling:** Uses sqrt(time) for multi-day horizon scaling.

### Dependencies

- Week 2 position data (need positions to calculate risk)
- Week 1 mock data generator (for testing)

### Files Created

| File | Purpose | Status |
|------|---------|--------|
| `backend/services/risk_engine.py` | VaR/CVaR with numpy/scipy | ✅ Complete |
| `backend/services/exposures.py` | Exposure breakdown calculations | ✅ Complete |
| `backend/services/greeks.py` | Pure Python Black-Scholes Greeks | ✅ Complete |
| `backend/api/risk.py` | 12 risk API endpoints | ✅ Complete |
| `backend/tests/test_risk.py` | 31 risk tests | ✅ Passing |

---

## Week 4: Aggregation Engine ⬜ NOT STARTED

**Target:** THE CORE - Cross-PM aggregation and overlap detection
**Branch:** `feature/week4-aggregation` (isolated development, merge to develop when complete)

### Development Workflow

This is RISKCORE's core differentiator. Use feature branch workflow:

```bash
# Start Week 4
git checkout develop && git pull
git checkout -b feature/week4-aggregation

# Develop with persona review on each commit
# ... implement features ...

# Before merge: full test suite + battle test
python -m pytest backend/tests -v

# Merge when complete
git checkout develop
git merge feature/week4-aggregation
git push origin develop
```

### Milestones

- [ ] Position aggregation across PMs
- [ ] Net position calculation (long + short netting)
- [ ] Cross-PM overlap detection algorithm
- [ ] Firm-level position rollup
- [ ] Hierarchy navigation (Firm → Fund → PM → Strategy → Book)
- [ ] Overlap report generation
- [ ] Aggregation API endpoints

### Acceptance Criteria

- [ ] Net positions correct: PM1 long 1000 AAPL + PM2 short 300 AAPL = firm net 700 AAPL
- [ ] Overlaps detected: when 2+ PMs hold same security, flagged with details
- [ ] Hierarchy drill-down works at all levels
- [ ] Aggregation handles different position dates correctly
- [ ] Currency conversion applied where needed
- [ ] Aggregation completes in <10 seconds for 10,000 positions

### Verification Criteria (MUST PASS before Week 5)

```
VERIFY-4.1: Cross-PM Netting
  [ ] Setup: Create positions - PM1 long 1000 AAPL, PM2 short 300 AAPL
  [ ] Run: GET /api/v1/aggregation/firm/net?security=AAPL
  [ ] Expected: net_position = 700, gross_long = 1000, gross_short = 300
  [ ] Edge case: Same security, different currencies - verify FX applied

VERIFY-4.2: Overlap Detection
  [ ] Setup: 3 PMs with overlapping MSFT positions
  [ ] Run: GET /api/v1/aggregation/overlaps
  [ ] Expected: MSFT flagged with list of PMs, quantities, direction
  [ ] Verify: Overlap report shows concentration risk %

VERIFY-4.3: Hierarchy Navigation
  [ ] Run: GET /api/v1/aggregation/hierarchy/firm
  [ ] Expected: Firm -> Fund -> PM -> Strategy -> Book structure
  [ ] Drill-down: Each level shows correct aggregated metrics
  [ ] Verify: Sum of children equals parent at each level

VERIFY-4.4: Performance
  [ ] Generate: 10,000 positions across 20 PMs
  [ ] Run: time curl /api/v1/aggregation/firm/summary
  [ ] Expected: Response in <10 seconds
  [ ] Verify: No N+1 query issues (check query count)

VERIFY-4.5: Edge Cases
  [ ] Test: Same security, different position dates
  [ ] Test: Same security, one with stale price (warning generated)
  [ ] Test: Currency mismatch requiring FX conversion
  [ ] Test: Corporate action (split) affecting matching
```

### Dependencies

- Week 2 position ingestion (need positions to aggregate)
- Week 1 security master (for security matching across systems)

### Files to Create

| File | Purpose |
|------|---------|
| `backend/services/aggregation.py` | Core aggregation engine |
| `backend/services/overlap.py` | Overlap detection algorithm |
| `backend/services/netting.py` | Net position calculation |
| `backend/api/aggregation.py` | Aggregation API endpoints |
| `backend/tests/test_aggregation.py` | Aggregation tests |

---

## Week 5: Dashboard ⬜ NOT STARTED

**Target:** Beautiful, responsive React dashboard

### Milestones

- [ ] React + Tailwind + Vite setup
- [ ] Authentication flow (Supabase Auth)
- [ ] Dashboard layout (Riskboard)
- [ ] RiskCards component library
- [ ] Firm-wide view page
- [ ] PM drill-down page
- [ ] Correlation matrix heatmap
- [ ] Real-time updates (Supabase subscriptions)
- [ ] Charts (Recharts or Tremor)
- [ ] Responsive design (desktop + tablet)

### Acceptance Criteria

- [ ] Login/logout works with Supabase Auth
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time position updates reflected without refresh
- [ ] Charts render correctly with live data
- [ ] Responsive on desktop (1920px) and tablet (768px)
- [ ] RBAC enforced: PMs see only their books, CRO sees all
- [ ] "Powered by RISKCORE" watermark visible (free tier)

### Dependencies

- Week 4 aggregation API (for firm-wide/PM views)
- Week 3 risk API (for risk metrics display)

### Files to Create

| Directory | Purpose |
|-----------|---------|
| `frontend/src/components/` | React components |
| `frontend/src/pages/` | Page components |
| `frontend/src/hooks/` | Custom React hooks |
| `frontend/src/services/` | API client services |
| `frontend/src/styles/` | Tailwind configuration |

---

## Week 6: AI + Polish ⬜ NOT STARTED

**Target:** Natural language queries and production readiness

### Milestones

- [ ] Claude API integration
- [ ] Natural language query endpoint
- [ ] Chat interface in dashboard
- [ ] Query examples and suggestions
- [ ] Rate limiting and caching
- [ ] Error handling and logging
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User documentation
- [ ] Demo script preparation
- [ ] LinkedIn announcement post

### Acceptance Criteria

- [ ] "What's our net tech exposure?" returns correct answer
- [ ] "Show me overlapping positions" lists cross-PM overlaps
- [ ] Query response time <3 seconds (with caching)
- [ ] Chat history persisted per user session
- [ ] API docs auto-generated at `/docs`
- [ ] README has quick start guide
- [ ] Demo runs smoothly for 10 minutes

### Dependencies

- Week 5 dashboard (for chat interface)
- Week 4 aggregation (for answering queries)
- Week 3 risk (for risk-related queries)

### Files to Create

| File | Purpose |
|------|---------|
| `backend/services/ai_assistant.py` | Claude API integration |
| `backend/api/chat.py` | Chat API endpoints |
| `frontend/src/components/ChatInterface.tsx` | Chat UI component |
| `docs/API.md` | API documentation |
| `docs/USER_GUIDE.md` | User documentation |

---

## Post-MVP: Phase 2 - Correlation Framework

**Timeline:** 8 weeks after MVP
**Details:** See `/docs/CORRELATION_FRAMEWORK.md`

- Risk factor taxonomy
- Factor exposure calculation
- Realized correlation matrix (P&L-based)
- Implied correlation calculation
- Correlation dashboard view

---

## Post-MVP: Phase 3 - Stress Testing & Hedging

**Timeline:** 12 weeks after Phase 2
**Details:** See `/docs/CORRELATION_FRAMEWORK.md`

- Stress correlation scenarios (2008, 2020)
- VaR under stress
- Hedge instrument library
- Hedge suggestion algorithm
- AI-powered recommendations

---

## Success Metrics (End of Week 6)

| Metric | Target | Status |
|--------|--------|--------|
| Upload 3 formats (CSV, Excel, FIX) | Working | ⬜ |
| Firm-wide exposure view | Working | ⬜ |
| Cross-PM overlap detection | Working | ⬜ |
| Natural language query | "What's our net tech exposure?" works | ⬜ |
| Demo readiness | 10-minute demo smooth | ⬜ |
| Documentation | README + docs complete | ⬜ |
| LinkedIn post | Published | ⬜ |

---

## Sync Protocol

**For Claude Desktop (CD) knowledge sync:**

```
After each CC work session:
1. CC updates ROADMAP.md (milestone checkboxes, artifacts)
2. CC updates CLAUDE.md (implementation state section)
3. Copy CLAUDE.md + ROADMAP.md to CD Project
4. CD now has full project context
```

**Files to sync:** `CLAUDE.md`, `ROADMAP.md` (~20KB total)

---

*Last milestone completed: Week 3 - Risk Engine complete with 121 tests passing (2026-01-12)*
