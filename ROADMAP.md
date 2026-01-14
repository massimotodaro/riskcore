# RISKCORE Development Roadmap

> Living document tracking MVP development progress.
> **Last Updated:** 2026-01-14
> **Sync to Claude Desktop:** Copy this file + CLAUDE.md daily

---

## Quick Status

| Week | Phase | Status | Summary |
|------|-------|--------|---------|
| 1 | Foundation | ✅ COMPLETE | Database schema, mock data, OpenFIGI, validation pipeline |
| 2 | Data Ingestion | ✅ COMPLETE | Position/trade API, FIX adapter, CSV/Excel upload |
| 3 | Risk Engine | ✅ COMPLETE | VaR/CVaR (numpy/scipy), exposures, Greeks (Black-Scholes) |
| 4 | Aggregation | ✅ COMPLETE | Cross-PM netting, overlap detection, firm rollup |
| 5 | Dashboard | 🔄 IN PROGRESS | CIO Dashboard + Overlay Book, Trades page |
| 6 | AI Assistant | ⬜ NOT STARTED | Voice + NL queries, on-premises LLM, hybrid cloud option |
| 7 | Reports | ⬜ NOT STARTED | PDF/Excel generation, scheduling, email delivery |

**Current Focus:** Week 5 - Dashboard (Trades page, testing, polish)

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

## Week 4: Aggregation Engine ✅ COMPLETE

**Target:** THE CORE - Cross-PM aggregation, overlap detection, and correlation analysis
**Dates:** 2026-01-12
**Status:** All milestones complete and tested with mock data

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

- [x] Position aggregation across PMs
- [x] Net position calculation (long + short netting)
- [x] Cross-PM overlap detection algorithm
- [x] Firm-level position rollup
- [x] Hierarchy navigation (Firm → Fund → PM → Strategy → Book)
- [x] Overlap report generation
- [x] Aggregation API endpoints
- [x] **RiskPod mapping (5-pod model: Equity, Rates, Credit, FX, Other)**
- [x] **Returns tracking (book-level and PM-level daily returns)**
- [x] **PM-to-PM realized correlation (Pearson correlation from returns)**
- [x] **PM correlation matrix with high-correlation flagging**
- [x] **Implied correlation (from portfolio structure overlap)**
- [x] **Comprehensive correlation analysis endpoint for AI queries**

### Acceptance Criteria

- [x] Net positions correct: PM1 long 1000 AAPL + PM2 short 300 AAPL = firm net 700 AAPL
- [x] Overlaps detected: when 2+ PMs hold same security, flagged with details
- [x] Hierarchy drill-down works at all levels
- [x] Aggregation handles different position dates correctly
- [x] Currency conversion applied where needed
- [x] Aggregation completes in <1 second for 1,003 positions (mock data)
- [x] **PM correlations calculated from 21 days of return history**
- [x] **Correlation matrix shows all PM pairs with strength classification**
- [x] **High correlation pairs (|corr| >= 0.7) flagged as concerning**

### Verification Criteria (ALL PASSED)

```
VERIFY-4.1: Cross-PM Netting ✅
  [x] Unit test: PM1 long 1000 + PM2 short 300 = net 700
  [x] Mock data: 45.15% netting efficiency with real data
  [x] GreenPower: 9 PMs, 6 long (36,083) + 3 short (14,381) = net 21,702

VERIFY-4.2: Overlap Detection ✅
  [x] 198 overlaps detected across mock data
  [x] 162 netting opportunities (opposing positions)
  [x] Severity classification working (high/medium/low)
  [x] Concentration risk identification

VERIFY-4.3: Hierarchy Navigation ✅
  [x] Firm -> Fund -> PM -> Book structure working
  [x] PM-level and Fund-level summaries working
  [x] HierarchyNode dataclass with recursive structure

VERIFY-4.4: Performance ✅
  [x] 1,003 positions processed in <1 second
  [x] All 14 endpoints return 200 OK
  [x] No N+1 query issues (batch operations used)

VERIFY-4.5: Edge Cases ✅
  [x] Empty data handling (33 tests cover edge cases)
  [x] Zero quantity positions handled
  [x] Single position detection as non-overlap

VERIFY-4.6: RiskPod Mapping ✅
  [x] 5 pods implemented: Equity, Rates, Credit, FX, Other
  [x] Asset class → pod mapping working
  [x] Pod-specific risk metrics defined (DV01 for rates, Greeks for equity options, etc.)

VERIFY-4.7: Returns & Correlation ✅
  [x] Database tables created (book_daily_returns, pm_daily_returns, correlation_cache)
  [x] Mock data generated with 420 book returns (21 days × 20 books)
  [x] PM correlation endpoint tested: Matthew Davis vs Emily Davis = 0.455 (21d)
  [x] Full 10x10 correlation matrix endpoint working
  [x] Implied correlation calculated from pod weights (0.90 for similar portfolios)
  [x] Analysis endpoint returns realized + implied + AI recommendation
```

### Dependencies

- Week 2 position ingestion (need positions to aggregate)
- Week 1 security master (for security matching across systems)

### Files Created

| File | Purpose | Status |
|------|---------|--------|
| `backend/services/netting.py` | Cross-PM netting calculations | ✅ Complete |
| `backend/services/overlap.py` | Overlap detection algorithm | ✅ Complete |
| `backend/services/aggregation.py` | Main orchestrator, hierarchy navigation | ✅ Complete |
| `backend/api/aggregation.py` | 14 aggregation API endpoints | ✅ Complete |
| `backend/tests/test_aggregation.py` | 33 aggregation tests | ✅ Passing |
| `backend/services/riskpod.py` | RiskPod enum, asset class → pod mapping | ✅ Complete |
| `backend/services/correlation.py` | Pod-level correlations, firm VaR | ✅ Complete |
| `backend/services/returns.py` | Return tracking and aggregation | ✅ Complete |
| `backend/services/realized_correlation.py` | PM-to-PM Pearson correlation | ✅ Complete |
| `backend/api/correlation.py` | 10 correlation API endpoints | ✅ Complete |
| `backend/tests/test_correlation.py` | Correlation tests | ✅ Passing |
| `supabase/migrations/20260112100000_add_returns_correlation_tables.sql` | Returns/correlation schema | ✅ Applied |

---

## Week 5: Dashboard 🔄 IN PROGRESS

**Target:** Beautiful, responsive React dashboard with CIO/PM role-based views
**Status:** CIO Dashboard structure complete, needs testing and polish

### Milestones

- [x] React + Tailwind + Vite setup
- [ ] Authentication flow (Supabase Auth)
- [x] Dashboard layout (Riskboard)
- [x] RiskCards component library (AssetClassCard)
- [x] Firm-wide view page (CIO Dashboard)
- [ ] PM drill-down page
- [ ] Correlation matrix heatmap
- [ ] Real-time updates (Supabase subscriptions)
- [ ] Charts (Recharts or Tremor)
- [ ] Responsive design (desktop + tablet)
- [x] **CIO Dashboard with Overlay Book support**
- [x] **Portfolio comparison (side-by-side RiskPods)**
- [x] **Underlying trades drill-down page**
- [x] **Valuation transparency modal**

### CIO Dashboard Feature (NEW - Session 8)

**5-Row Layout:**
1. **Firm-Wide RiskPods** - Aggregate risk by asset class across all portfolios
2. **Overlay Portfolio** - CIO's hedge book to offset PM risk
3. **Portfolio A** - Selectable portfolio for comparison
4. **Portfolio B** - Second portfolio for comparison
5. **Correlation View** - Correlation between selected portfolios

**Components Created:**
- `AssetClassCard.tsx` - Color-coded risk card per asset class
- `RiskPodRow.tsx` - Horizontal row of asset class cards
- `PortfolioSelector.tsx` - Searchable portfolio dropdown
- `BookCorrelation.tsx` - Portfolio correlation visualization
- `ValuationModal.tsx` - Price source and model input details

**Pages Created:**
- `CIODashboard.tsx` - Full 5-row CIO view
- `UnderlyingTrades.tsx` - Trades table with drill-down

**Backend Additions:**
- `book_type` column on books ('trading' | 'overlay')
- `overlay_book_sources` table
- `model_valuation_inputs` table
- Risk-by-asset-class views and API endpoints

### Tomorrow's Agenda (2026-01-13)

| Priority | Task | Notes |
|----------|------|-------|
| 1 | Test CIO Dashboard with live data | Verify API calls work end-to-end |
| 2 | Style refinements | Polish colors, spacing, animations |
| 3 | Loading/error states | Improve UX for slow/failed requests |
| 4 | Test trades drill-down | Verify navigation and pagination |
| 5 | Test valuation modal | Verify model inputs display |
| 6 | Mobile responsiveness | Check tablet breakpoints |
| 7 | PM Dashboard | Simpler view for PM role |
| 8 | Chart visualizations | Add exposure charts if time |

### Acceptance Criteria

- [ ] Login/logout works with Supabase Auth
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time position updates reflected without refresh
- [ ] Charts render correctly with live data
- [ ] Responsive on desktop (1920px) and tablet (768px)
- [ ] RBAC enforced: PMs see only their books, CRO sees all
- [x] "Powered by RISKCORE" watermark visible (free tier)
- [x] **CIO Dashboard shows firm-wide, overlay, and selected portfolios**
- [x] **Portfolio selector allows comparison of any two books**
- [x] **Underlying trades accessible from each RiskPod**
- [ ] **Valuation modal shows price source and allows override (with auth)**

### Dependencies

- Week 4 aggregation API (for firm-wide/PM views) ✅
- Week 3 risk API (for risk metrics display) ✅

### Files Created (Session 8)

| File | Purpose | Status |
|------|---------|--------|
| `frontend/src/components/riskboard/AssetClassCard.tsx` | Asset class risk card | ✅ Done |
| `frontend/src/components/riskboard/RiskPodRow.tsx` | Row of asset class cards | ✅ Done |
| `frontend/src/components/riskboard/PortfolioSelector.tsx` | Portfolio dropdown | ✅ Done |
| `frontend/src/components/riskboard/BookCorrelation.tsx` | Correlation view | ✅ Done |
| `frontend/src/components/riskboard/ValuationModal.tsx` | Valuation details | ✅ Done |
| `frontend/src/pages/CIODashboard.tsx` | CIO Dashboard page | ✅ Done |
| `frontend/src/pages/UnderlyingTrades.tsx` | Trades drill-down | ✅ Done |
| `supabase/migrations/20260112110000_overlay_book_support.sql` | DB schema | ✅ Applied |

---

## Week 6: AI Assistant (Voice + NL Queries) ⬜ NOT STARTED

**Target:** AI-native platform with voice and natural language queries
**Philosophy:** This is what sets RISKCORE apart from legacy platforms

### Core Principle: ON-PREMISES FIRST

**CRITICAL:** Sensitive financial data NEVER leaves client network.
- All position/trade queries processed by on-premises LLM
- Optional cloud (Claude API) only for general queries with explicit client consent
- Voice processing runs locally (Whisper)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     RISKCORE AI LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐  │
│  │   Whisper   │────▶│  Query Router    │────▶│  Response   │  │
│  │  (Voice)    │     │                  │     │  Formatter  │  │
│  └─────────────┘     │  - Sanitization  │     └─────────────┘  │
│                      │  - Classification│                       │
│  ┌─────────────┐     │  - Routing logic │     ┌─────────────┐  │
│  │   Text UI   │────▶│                  │────▶│  Audit Log  │  │
│  │  (Chat)     │     └────────┬─────────┘     └─────────────┘  │
│  └─────────────┘              │                                 │
│                               ▼                                 │
│         ┌─────────────────────┴─────────────────────┐          │
│         │                                           │          │
│         ▼                                           ▼          │
│  ┌─────────────────┐                    ┌─────────────────┐   │
│  │  LOCAL LLM      │                    │  CLOUD LLM      │   │
│  │  (vLLM/Ollama)  │                    │  (Claude API)   │   │
│  │                 │                    │                 │   │
│  │  Qwen 72B or    │                    │  Claude Opus    │   │
│  │  QwQ 32B        │                    │  Zero Data      │   │
│  │                 │                    │  Retention      │   │
│  │  For: ALL       │                    │                 │   │
│  │  sensitive      │                    │  For: General   │   │
│  │  queries        │                    │  queries only   │   │
│  └─────────────────┘                    └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Milestones

**Voice Interface:**
- [ ] Whisper Large V3 Turbo deployment (local, 809M params, 6x faster)
- [ ] Voice activation ("Hey RISKCORE" or push-to-talk)
- [ ] Real-time transcription with visual feedback
- [ ] Financial vocabulary fine-tuning (CUSIP, VaR, delta, DV01, etc.)
- [ ] Vosk fallback for ultra-low latency command detection

**Natural Language Processing:**
- [ ] Query classification (risk, position, exposure, aggregation, general)
- [ ] Intent extraction with entity recognition
- [ ] Context-aware responses (remembers current portfolio selection)
- [ ] Multi-turn conversation support

**On-Premises LLM (Primary):**
- [ ] Ollama setup for development (easy, OpenAI-compatible API)
- [ ] vLLM deployment for production (PagedAttention, 2-4x throughput)
- [ ] Qwen2.5 72B or QwQ-32B model (best for financial reasoning)
- [ ] Mistral 7B fallback for simple queries (faster, less VRAM)
- [ ] RAG integration with local vector store (Chroma)

**Hybrid Cloud (Optional - Client Consent Required):**
- [ ] Claude API integration (Zero Data Retention endpoints)
- [ ] Query router: sensitive data → local, general → cloud
- [ ] Client configuration: enable/disable cloud
- [ ] Data anonymization for cloud queries

**Security & Compliance:**
- [ ] Query sanitization (block SQL injection, prompt injection)
- [ ] Audit logging for all AI queries (who, what, when, which model)
- [ ] OWASP LLM Top 10 mitigations implemented
- [ ] Role-based query restrictions (PM can only query own books)

**Chat Interface:**
- [ ] Chat sidebar in dashboard
- [ ] Voice input button with visual feedback
- [ ] Query suggestions based on current view
- [ ] Response with actionable links (e.g., "show me" → navigates to view)
- [ ] Chat history per session

### Example Queries

```
Voice: "Show me the RiskPods for portfolio 17 and portfolio 21"
→ Dashboard displays selected portfolios side by side

Voice: "What's our net tech exposure across all PMs?"
→ Returns: "Firm-wide net tech exposure is $45.2M long,
           driven primarily by PM Chen ($28M) and PM Davis ($12M)"

Voice: "Flag any PMs with correlation above 0.7"
→ Returns list of high-correlation pairs with recommendation

Voice: "Generate a risk summary for the macro fund"
→ Triggers report generation (Week 7 feature)
```

### Hardware Requirements

| Tier | GPU | VRAM | Models Supported |
|------|-----|------|------------------|
| **Entry** | RTX 4090 | 24GB | QwQ-32B (Q4), Mistral 7B |
| **Recommended** | A100 | 80GB | Qwen 72B, full precision |
| **Budget** | RTX 4060 | 8GB | Mistral 7B only |
| **CPU-only** | None | 64GB RAM | llama.cpp with Q4 models (slow) |

### Technology Stack

| Component | Development | Production |
|-----------|-------------|------------|
| **LLM Framework** | Ollama | vLLM |
| **LLM Model** | Mistral 7B | Qwen2.5 72B or QwQ-32B |
| **Voice-to-Text** | Whisper (faster-whisper) | Whisper Large V3 Turbo |
| **Vector Store** | Chroma (local) | Chroma (persistent) |
| **Cloud LLM** | Claude API (optional) | Claude with ZDR |

### Safety Implementation

```python
# Query sanitization (OWASP LLM01:2025)
BLOCKED_PATTERNS = [
    r'ignore\s+(previous|above)',      # Prompt injection
    r'forget\s+your\s+instructions',   # Jailbreak attempt
    r';\s*DROP',                        # SQL injection
    r'UNION\s+SELECT',                  # SQL injection
]

# Audit log schema
class AIQueryAuditLog:
    timestamp: datetime
    tenant_id: str
    user_id: str
    user_email: str  # Denormalized
    raw_query: str
    sanitized_query: str
    routed_to: str  # 'local_llm' | 'claude_api'
    model_used: str
    contains_positions: bool  # Always local if True
    response_tokens: int
    latency_ms: int
    flagged_for_review: bool
```

### Acceptance Criteria

- [ ] "Show me RiskPods for portfolio 17 and 21" works via voice and text
- [ ] Voice recognition accuracy >95% for financial terms
- [ ] Query response time <3 seconds (local LLM)
- [ ] All queries with position data use local LLM only
- [ ] Audit log captures every AI interaction
- [ ] Works fully offline (no internet required)
- [ ] Chat history persisted per user session

### Dependencies

- Week 5 dashboard (for chat interface integration)
- Week 4 aggregation (for position/overlap queries)
- Week 3 risk (for VaR/exposure queries)
- GPU hardware for production deployment

### Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `backend/services/ai_assistant.py` | Query router, LLM integration | ⬜ |
| `backend/services/voice_service.py` | Whisper integration | ⬜ |
| `backend/services/query_sanitizer.py` | Security, prompt injection prevention | ⬜ |
| `backend/services/llm_local.py` | Ollama/vLLM client | ⬜ |
| `backend/services/llm_cloud.py` | Claude API client (optional) | ⬜ |
| `backend/api/chat.py` | Chat API endpoints | ⬜ |
| `backend/api/voice.py` | Voice API endpoints | ⬜ |
| `frontend/src/components/ChatSidebar.tsx` | Chat UI component | ⬜ |
| `frontend/src/components/VoiceInput.tsx` | Voice button with feedback | ⬜ |
| `supabase/migrations/*_ai_audit_logs.sql` | Audit logging schema | ⬜ |

### Python Dependencies

```
# Add to requirements.txt
ollama>=0.1.0           # Local LLM (development)
vllm>=0.4.0             # Local LLM (production)
faster-whisper>=1.0.0   # Voice-to-text
chromadb>=0.4.0         # Vector store for RAG
anthropic>=0.25.0       # Claude API (optional cloud)
```

---

## Week 7: Reports & Scheduling ⬜ NOT STARTED

**Target:** Professional report generation with automated scheduling and delivery
**Philosophy:** Risk managers need printable, schedulable reports for compliance and stakeholders

### Core Features

1. **On-Demand Reports** - Generate PDF/Excel from any dashboard view
2. **Scheduled Reports** - Daily/weekly/monthly automated generation
3. **Email Delivery** - Send reports to configured recipients
4. **Multi-Format Export** - PDF (visual), Excel (data), CSV (raw)

### Report Types

| Report | Description | Formats |
|--------|-------------|---------|
| **Daily Risk Summary** | VaR, exposures, limit breaches | PDF, Excel |
| **RiskPod Report** | Single or multiple RiskPods snapshot | PDF |
| **RiskCard Detail** | Individual asset class deep dive | PDF |
| **Exposure Breakdown** | Sector/geography/asset class pie charts | PDF, Excel |
| **Correlation Matrix** | PM-to-PM correlation heatmap | PDF |
| **Overlap Report** | Cross-PM netting opportunities | PDF, Excel |
| **Limit Breach Report** | All breaches with timestamps | PDF, Excel |
| **Audit Trail** | AI queries, user actions, changes | Excel, CSV |

### Scheduling Options

| Schedule | Example | Use Case |
|----------|---------|----------|
| **Daily** | 6:00 AM EST | Morning risk briefing |
| **Weekly** | Friday 5:00 PM | Weekend review pack |
| **Monthly** | 1st of month, 8:00 AM | Compliance reporting |
| **On-Demand** | User triggered | Ad-hoc analysis |
| **Event-Triggered** | On limit breach | Real-time alerts |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISKCORE REPORTS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ Report       │   │ Template     │   │ Scheduler    │        │
│  │ Request API  │──▶│ Engine       │──▶│ (APScheduler)│        │
│  └──────────────┘   │ (Jinja2)     │   └──────┬───────┘        │
│         │           └──────────────┘          │                 │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ Data         │   │ PDF/Excel    │   │ Email        │        │
│  │ Aggregator   │   │ Generator    │   │ Service      │        │
│  │ (Risk APIs)  │   │ (WeasyPrint) │   │ (SMTP)       │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                            │                  │                 │
│                            ▼                  ▼                 │
│                     ┌──────────────────────────────┐           │
│                     │        Storage               │           │
│                     │  - Local filesystem          │           │
│                     │  - Audit trail in DB         │           │
│                     └──────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Milestones

**Report Generation:**
- [ ] WeasyPrint + Jinja2 template engine setup
- [ ] Base template with RISKCORE branding
- [ ] Daily Risk Summary report template
- [ ] RiskPod/RiskCard report templates
- [ ] Multi-tenant branding support (logo, colors)
- [ ] "Powered by RISKCORE" watermark (Free tier)

**Chart Integration:**
- [ ] Matplotlib charts embedded as base64/SVG
- [ ] Exposure pie charts
- [ ] VaR trend line charts
- [ ] Correlation heatmap

**Excel Reports:**
- [ ] XlsxWriter + Pandas integration
- [ ] Formatted headers, conditional formatting
- [ ] Multiple sheets per report
- [ ] Charts in Excel (native)

**Scheduling:**
- [ ] APScheduler with PostgreSQL job store
- [ ] Schedule management API (CRUD)
- [ ] User-configurable schedules
- [ ] Timezone support
- [ ] Job persistence across restarts

**Email Delivery:**
- [ ] SMTP integration (on-premises mail server)
- [ ] HTML email body with summary
- [ ] PDF/Excel attachments
- [ ] Delivery confirmation logging
- [ ] Bounce handling

**React UI:**
- [ ] Report configuration modal
- [ ] Schedule builder (cron-like UI)
- [ ] Recipient list management
- [ ] Report history view
- [ ] Download generated reports

### User Workflow

```
1. User opens Report modal from dashboard
2. Selects report type (Daily Summary, RiskPod, etc.)
3. Configures scope:
   - All portfolios / Selected portfolios
   - Date range
   - Include charts? Include raw data?
4. Chooses delivery:
   - Download now (PDF/Excel)
   - Schedule (Daily at 6 AM)
   - Email to: user@firm.com, cro@firm.com
5. System generates report and delivers
6. Audit log records: who, what, when, recipients
```

### Schedule Configuration Schema

```python
class ReportSchedule(BaseModel):
    id: str
    tenant_id: str
    created_by: str  # user_id

    # Report configuration
    report_type: str  # 'daily_summary', 'riskpod', 'exposure', etc.
    scope: dict  # {'book_ids': [...], 'fund_id': '...'}
    format: str  # 'pdf', 'excel', 'both'
    include_charts: bool = True

    # Schedule
    schedule_type: str  # 'daily', 'weekly', 'monthly', 'once'
    cron_expression: str  # '0 6 * * *' = daily at 6 AM
    timezone: str = 'America/New_York'

    # Delivery
    delivery_method: str  # 'email', 'download', 'both'
    recipients: list[str]  # email addresses

    # Status
    is_active: bool = True
    last_run: datetime | None
    next_run: datetime
    last_status: str  # 'success', 'failed', 'pending'
```

### Technology Stack

| Component | Library | Notes |
|-----------|---------|-------|
| **PDF Generation** | WeasyPrint + Jinja2 | HTML/CSS → PDF, flexbox support |
| **Excel Generation** | XlsxWriter + Pandas | Rich formatting, charts |
| **Scheduling** | APScheduler | PostgreSQL job store, no Redis needed |
| **Email** | smtplib (built-in) | On-premises SMTP compatible |
| **Charts** | Matplotlib | Embed as base64 in PDF |

### Acceptance Criteria

- [ ] Generate PDF report from dashboard in <5 seconds
- [ ] Schedule reports for daily/weekly/monthly delivery
- [ ] Email delivery works with on-premises SMTP
- [ ] Multi-tenant branding (logo, colors per tenant)
- [ ] Free tier shows "Powered by RISKCORE" watermark
- [ ] Report history accessible for 90 days
- [ ] Audit log tracks all report generation

### Dependencies

- Week 5 dashboard (report content comes from dashboard views)
- Week 4 aggregation (for firm-wide reports)
- Week 3 risk (for VaR/exposure data)

### Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `backend/services/report_generator.py` | WeasyPrint PDF generation | ⬜ |
| `backend/services/excel_service.py` | XlsxWriter Excel generation | ⬜ |
| `backend/services/scheduler.py` | APScheduler setup | ⬜ |
| `backend/services/email_service.py` | SMTP email delivery | ⬜ |
| `backend/api/reports.py` | Report API endpoints | ⬜ |
| `backend/templates/reports/base.html` | Base Jinja2 template | ⬜ |
| `backend/templates/reports/daily_summary.html` | Daily report template | ⬜ |
| `backend/templates/reports/riskpod.html` | RiskPod report template | ⬜ |
| `frontend/src/components/ReportModal.tsx` | Report configuration UI | ⬜ |
| `frontend/src/components/ScheduleBuilder.tsx` | Schedule configuration | ⬜ |
| `supabase/migrations/*_report_schedules.sql` | Schedules table | ⬜ |

### Python Dependencies

```
# Add to requirements.txt
weasyprint>=60.0        # HTML → PDF
Jinja2>=3.1.0           # Template engine
xlsxwriter>=3.1.0       # Excel generation
openpyxl>=3.1.0         # Excel reading
APScheduler>=3.10.0     # Job scheduling
# smtplib is built-in, no install needed
```

---

## Week 8: Production Readiness ⬜ NOT STARTED

**Target:** Documentation, testing, demo preparation
**This is the polish week before launch**

### Milestones

- [ ] API documentation (OpenAPI/Swagger at `/docs`)
- [ ] User documentation (USER_GUIDE.md)
- [ ] Installation guide (INSTALL.md)
- [ ] Error handling audit
- [ ] Performance testing
- [ ] Security audit
- [ ] Demo script preparation
- [ ] LinkedIn announcement post
- [ ] GitHub README polish

### Acceptance Criteria

- [ ] API docs auto-generated at `/docs`
- [ ] README has quick start guide
- [ ] Demo runs smoothly for 10 minutes
- [ ] All endpoints handle errors gracefully
- [ ] No security vulnerabilities (OWASP check)

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

*Last milestone completed: Week 5 - CIO Dashboard + Overlay Book feature structure (2026-01-12)*
