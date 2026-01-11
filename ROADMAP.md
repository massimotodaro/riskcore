# RISKCORE Development Roadmap

> Living document tracking MVP development progress.
> **Last Updated:** 2026-01-11
> **Sync to Claude Desktop:** Copy this file + CLAUDE.md daily

---

## Quick Status

| Week | Phase | Status | Summary |
|------|-------|--------|---------|
| 1 | Foundation | ✅ COMPLETE | Database schema, mock data, OpenFIGI, validation pipeline |
| 2 | Data Ingestion | ⬜ NOT STARTED | Position/trade API, FIX adapter, CSV/Excel upload |
| 3 | Risk Engine | ⬜ NOT STARTED | Riskfolio-Lib integration, VaR, exposures, Greeks |
| 4 | Aggregation | ⬜ NOT STARTED | Cross-PM netting, overlap detection, firm rollup |
| 5 | Dashboard | ⬜ NOT STARTED | React + Tailwind, real-time, charts |
| 6 | AI + Polish | ⬜ NOT STARTED | Claude integration, NL queries, documentation |

**Current Focus:** Week 2 - Data Ingestion API

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

## Week 2: Data Ingestion ⬜ NOT STARTED

**Target:** Position & trade ingestion API with multiple input methods

### Milestones

- [ ] FastAPI application structure
- [ ] Position ingestion API endpoints
- [ ] Trade ingestion API endpoints
- [ ] CSV/Excel file upload endpoint
- [ ] Column auto-detection for uploads
- [ ] FIX message parsing (simplefix)
- [ ] Basic P&L calculation
- [ ] Unit tests for all endpoints

### Acceptance Criteria

- [ ] `POST /api/v1/positions` accepts valid position data, returns validation errors for bad data
- [ ] `POST /api/v1/trades` accepts valid trade data with proper validation
- [ ] `POST /api/v1/upload` handles CSV and Excel files, auto-detects columns
- [ ] FIX messages (ExecutionReport, PositionReport) parse correctly using simplefix
- [ ] P&L = (quantity × current_price) - (quantity × average_cost) calculated correctly
- [ ] Validation pipeline rejects invalid data with clear error messages
- [ ] Security master resolves identifiers during ingestion
- [ ] All endpoints have >80% test coverage

### Dependencies

- Week 1 validation pipeline (for input validation)
- Week 1 security master (for security resolution)
- Week 1 database schema (positions, trades tables)

### Files to Create

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI application entry point |
| `backend/api/__init__.py` | API router initialization |
| `backend/api/positions.py` | Position endpoints |
| `backend/api/trades.py` | Trade endpoints |
| `backend/api/upload.py` | File upload endpoint |
| `backend/services/fix_parser.py` | FIX message parser using simplefix |
| `backend/services/file_parser.py` | CSV/Excel parser with column detection |
| `backend/models/position.py` | Pydantic models for positions |
| `backend/models/trade.py` | Pydantic models for trades |
| `backend/tests/test_positions.py` | Position API tests |
| `backend/tests/test_trades.py` | Trade API tests |
| `backend/tests/test_upload.py` | Upload API tests |
| `requirements.txt` | Python dependencies |

### Technical Approach

1. **FastAPI Structure:**
   - Modular routers per domain (positions, trades, upload)
   - Dependency injection for database connections
   - Pydantic models for request/response validation

2. **File Upload:**
   - Accept CSV, XLSX, XLS formats
   - Auto-detect column mappings (ticker, quantity, price, etc.)
   - Return preview for user confirmation before import

3. **FIX Parsing:**
   - Use simplefix for message parsing
   - Support ExecutionReport (tag 35=8) and PositionReport (tag 35=AP)
   - Extract: symbol, quantity, price, side, account

---

## Week 3: Risk Engine ⬜ NOT STARTED

**Target:** Risk calculations using Riskfolio-Lib and FinancePy

### Milestones

- [ ] Riskfolio-Lib integration
- [ ] VaR calculation (95%, 99% confidence)
- [ ] CVaR/Expected Shortfall
- [ ] Sector exposure breakdown
- [ ] Geography exposure breakdown
- [ ] Asset class exposure breakdown
- [ ] FinancePy integration for Greeks (options)
- [ ] Risk metrics stored in database

### Acceptance Criteria

- [ ] VaR calculated correctly for portfolio (validated against known examples)
- [ ] Exposure breakdowns sum to 100% within tolerance
- [ ] Greeks (delta, gamma, vega, theta) calculated for options positions
- [ ] Risk metrics persisted to `risk_metrics` table
- [ ] Historical risk metrics queryable by date range
- [ ] Calculations complete in <5 seconds for typical portfolio

### Dependencies

- Week 2 position data (need positions to calculate risk)
- Week 1 mock data generator (for testing)

### Files to Create

| File | Purpose |
|------|---------|
| `backend/services/risk_engine.py` | Core risk calculations |
| `backend/services/exposures.py` | Exposure breakdown calculations |
| `backend/services/greeks.py` | Options Greeks using FinancePy |
| `backend/api/risk.py` | Risk API endpoints |
| `backend/tests/test_risk.py` | Risk calculation tests |

---

## Week 4: Aggregation Engine ⬜ NOT STARTED

**Target:** THE CORE - Cross-PM aggregation and overlap detection

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

*Last milestone completed: Week 1 - Foundation (2026-01-11)*
