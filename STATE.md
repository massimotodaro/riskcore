# RISKCORE State

> Living document tracking current development state.
> **Purpose:** Quick session context restoration, decision tracking, blocker visibility.

---

## Current Position

| Field | Value |
|-------|-------|
| **Week** | 5 - Dashboard (Riskboard Polish) |
| **Status** | ✅ HTML Mockup Complete with Calculate, Accessibility, Price Override |
| **Next** | Tomorrow: Review User Manual, Test all card calculations |
| **Tests** | 154+ passing (backend), frontend builds successfully |
| **Branch** | develop |

---

## Session Log

### 2026-01-13 Session 11 (Latest)

**Focus:** Riskboard HTML Mockup Polish & New Features

**Features Implemented Today:**

1. **Calculate/Refresh System:**
   - Added "Calculate" button to each Pod header (green in color mode, white in accessibility mode)
   - Added "Last calculated" timestamp per Pod
   - Added "Refresh All Pods" button at top summary strip
   - Visual stale indicator when portfolio selection changes (orange pulse animation)
   - Pod header layout: Portfolio selector → Selected → Calculate → Gross → Net → Positions → Timestamp

2. **Accessibility/Color Blind Mode:**
   - Added toggle switch in top header (multicolored circle ↔ white circle)
   - Rainbow gradient `conic-gradient` for color mode indicator
   - When toggled, all card colors become white/monochrome
   - Affects: card titles, trade buttons, table headers, row labels, progress bars
   - Persisted to localStorage for user preference

3. **Manual Price Override System (CRITICAL FEATURE):**
   - Trades button opens modal showing all underlying positions
   - Price inputs are editable - user can manually override prices for illiquid securities
   - Modified prices highlighted with orange border
   - Warning icon (⚠) appears on card header when overrides exist (orange pulse animation)
   - Clicking warning icon opens Overrides modal showing all manual changes
   - Each override can be: edited (change value) or reset (return to system price)
   - Implemented for all 12 cards (6 asset classes × 2 pods)

**Files Modified:**
- `designs/Riskboard.html` - Added all features above

**Tomorrow's Agenda:**
1. Review user manual and understand all Riskboard features
2. Test each RiskCard and understand how numbers are calculated
3. Walk through: Equity, Rates, Credit, FX, Commodities, Other cards
4. Verify all metrics (Delta, DV01, CS01, Greeks, VAR, CVAR)
5. Test Calculate/Refresh system behavior
6. Test accessibility mode toggle
7. Test manual price override workflow end-to-end

---

### 2026-01-13 Session 10

**Focus:** Complete Riskboard Dashboard with Unified UI

**Key Design Decisions (User Confirmed):**
1. **NO P&L Display** - Focus on Risk Metrics and Correlation only (can't accurately track P&L between file imports)
2. **Unified UI** - Same dashboard for all roles (CIO, PM, Analyst), permissions control data access
3. **Multi-Select Portfolio Aggregation** - Each RiskPod can aggregate multiple books
4. **5 Asset Class RiskCards** - Equity, Rates, Credit, FX, Other
5. **Pricing Hierarchy** - Client Override → Market Feed (OpenBB) → Model-Derived (FinancePy) → Stale

**Backend Completed:**
- Fixed `source` vs `price_source` column name issue in `pricing_service.py` and `riskpod.py`
- Created `market_data_service.py` - Market indices snapshot service with demo data
- Created `market.py` API - `/market/snapshot`, `/market/quote/{symbol}`, `/market/symbols`
- All pricing and market APIs tested and working

**Frontend Completed:**
- Created `MarketSnapshot.tsx` - Live market indices with sparklines (SPX, VIX, US10Y, EURUSD)
- Created `TopBar.tsx` - Risk summary bar with NAV, Gross, Net, Long/Short, Positions, Delta, DV01, CS01, Reprice button
- Created `CorrelationPanel.tsx` - Position overlap, sector concentration, single-name concentration
- Created `Riskboard.tsx` - Main unified dashboard page with dynamic RiskPods
- Updated `api.ts` with new API types and methods (riskboardApi, pricingApi, marketApi)
- Updated `App.tsx` with new routes (default to /riskboard)
- Fixed tenant ID to match mock data (`b95fbd3b-e6f0-41f8-9c0c-5337e469cf50`)

**API Endpoints Added:**
- `GET /market/snapshot` - Market indices for dashboard
- `GET /market/quote/{symbol}` - Single market quote
- `GET /market/symbols` - Available market symbols

**Files Created:**
- `backend/services/market_data_service.py`
- `backend/api/market.py`
- `frontend/src/components/riskboard/MarketSnapshot.tsx`
- `frontend/src/components/riskboard/TopBar.tsx`
- `frontend/src/components/riskboard/CorrelationPanel.tsx`
- `frontend/src/pages/Riskboard.tsx`

**Files Modified:**
- `backend/services/pricing_service.py` - Fixed `source` column name
- `backend/services/riskpod.py` - Fixed `source` column name
- `backend/api/__init__.py` - Added market router
- `frontend/src/services/api.ts` - Added new API types and methods
- `frontend/src/App.tsx` - Added Riskboard route

**Riskboard Features:**
- Dynamic RiskPods - Add/remove portfolio aggregations
- Multi-select portfolio dropdown - Select any combination of books
- Market snapshot bar with live indices and sparklines
- Risk summary bar with key metrics and Reprice All button
- Position overlap analysis with netting opportunities
- Sector concentration with >40% warning
- Single-name concentration with >10% warning
- Drill-down to positions by asset class

**Test Results:**
- Risk Summary: NAV $585.8M, Gross $1.49B, Net $585.8M, 1,075 positions
- 5 asset class categories working: equity, fixed_income, other, option, future
- Market snapshot: SPX, VIX, US10Y, EURUSD with change percentages
- All pricing status, valuation, and market APIs tested and passing

**Week 5 Quality Gate: PASSED**
- [x] All dashboard components created
- [x] Backend APIs working with correct data
- [x] Frontend builds and routes correctly
- [x] Multi-select portfolio aggregation working
- [x] Market snapshot with sparklines
- [x] Correlation panel with overlap/concentration
- [x] Pricing status and Reprice All button
- [x] Documentation updated

---

### 2026-01-13 Session 9

**Focus:** Comprehensive Compliance Architecture (SOC 2, GDPR, Privacy)

**Strategic Decisions:**
- SOC 2 certification deferred to post-revenue ($500K+ ARR)
- Build following all SOC 2 principles from day 1
- Emphasize self-hosted architecture as security/privacy advantage

**Completed:**
- Created comprehensive compliance architecture (`docs/COMPLIANCE_ARCHITECTURE.md`)
  - Full SOC 2 Trust Services Criteria implementation
  - GDPR analysis for self-hosted software
  - Global privacy regulations overview
  - Financial services regulations (SEC, MiFID II, AIFMD)
  - Security features by tier (Free/Pro/Enterprise)
  - Compliance roadmap (Foundation → Documentation → Validation → Certification)
- Updated SOC 2 compliance plan with post-revenue certification strategy
- Updated BUSINESS_MODEL.md with detailed security features matrix
- Created Word documents for Notion storage:
  - `docs/SOC2_Findings_and_Recommendations.docx`
  - `docs/GDPR_Privacy_Findings_and_Recommendations.docx`
- Created RiskPods and Metrics documentation (`docs/RISKPODS_AND_METRICS.docx`)

**Key Findings:**
1. **SOC 2 requires external audit** - Cannot self-certify, costs $55K-90K/year
2. **Self-hosted = reduced compliance burden** - We don't store/access client data
3. **GDPR: We're NOT a data processor** for client positions (they control their own data)
4. **DPA only needed** when we actually access client data (support sessions)

**Files Created:**
- `docs/COMPLIANCE_ARCHITECTURE.md` - Master compliance document
- `docs/SOC2_COMPLIANCE_PLAN.md` - SOC 2 roadmap (updated)
- `docs/SOC2_Findings_and_Recommendations.docx` - For Notion
- `docs/GDPR_Privacy_Findings_and_Recommendations.docx` - For Notion
- `docs/RISKPODS_AND_METRICS.docx` - RiskPods reference
- `scripts/create_compliance_docs.py` - Document generator

**Files Modified:**
- `docs/BUSINESS_MODEL.md` - Added security features by tier
- `docs/SECURITY.md` - Added SOC 2 plan reference
- `CLAUDE.md` - Added documentation index entries

**Next (UI Work when ready):**
1. Test CIO Dashboard with live backend data
2. Style refinements and polish
3. Add loading/error states where missing
4. Test trades drill-down flow
5. Test valuation modal with mock data
6. Mobile responsiveness check
7. Add PM Dashboard view
8. Consider adding more chart visualizations

---

### 2026-01-12 Session 8

**Focus:** CIO Dashboard + Overlay Book Feature Implementation

**Completed:**
- Created database migration for overlay book support (`20260112110000_overlay_book_support.sql`)
  - Added `book_type` column to books table ('trading' | 'overlay')
  - Created `overlay_book_sources` table linking overlay to source books
  - Created `model_valuation_inputs` table for valuation transparency
  - Created views: `v_risk_by_asset_class`, `v_firm_risk_by_asset_class`, `v_overlay_risk_by_asset_class`
- Updated mock data generator with overlay book (CIO Overlay Portfolio)
- Extended `riskpod_service.py` with new methods for CIO Dashboard
- Added 5 new API endpoints to `aggregation.py`:
  - `GET /risk/by-asset-class` - Firm-wide risk by asset class
  - `GET /risk/by-asset-class/{book_id}` - Single book risk
  - `GET /risk/overlay` - Overlay book risk
  - `GET /books` - List all books
  - `GET /books/overlay` - Get overlay books with source links
- Added new TypeScript types (AssetClassRisk, Book, OverlayBook, TradeDetail, ValuationDetail, etc.)
- Updated frontend API service with new API functions
- Created 5 new React components:
  - `AssetClassCard.tsx` - Asset class-specific risk card with color coding
  - `RiskPodRow.tsx` - Horizontal row of asset class cards
  - `PortfolioSelector.tsx` - Searchable portfolio dropdown
  - `BookCorrelation.tsx` - Portfolio correlation visualization
  - `ValuationModal.tsx` - Price source and model input override modal
- Created 2 new pages:
  - `CIODashboard.tsx` - 5-row layout (firm-wide, overlay, portfolio A, portfolio B, correlation)
  - `UnderlyingTrades.tsx` - Trades drill-down with pagination
- Updated routing (App.tsx) and navigation (Sidebar.tsx)
- Fixed TypeScript compilation errors
- Frontend builds successfully

**Tomorrow's Agenda (UI Work):**
1. Test CIO Dashboard with live backend data
2. Style refinements and polish
3. Add loading/error states where missing
4. Test trades drill-down flow
5. Test valuation modal with mock data
6. Mobile responsiveness check
7. Add PM Dashboard view (simpler version for PM role)
8. Consider adding more chart visualizations

**Files Created:**
- `supabase/migrations/20260112110000_overlay_book_support.sql`
- `frontend/src/components/riskboard/AssetClassCard.tsx`
- `frontend/src/components/riskboard/RiskPodRow.tsx`
- `frontend/src/components/riskboard/PortfolioSelector.tsx`
- `frontend/src/components/riskboard/BookCorrelation.tsx`
- `frontend/src/components/riskboard/ValuationModal.tsx`
- `frontend/src/pages/CIODashboard.tsx`
- `frontend/src/pages/UnderlyingTrades.tsx`

**Files Modified:**
- `backend/services/riskpod.py` - Extended with CIO Dashboard methods
- `backend/api/aggregation.py` - Added 5 new endpoints
- `backend/config.py` - Added CORS origin
- `scripts/generate_mock_data.py` - Added overlay book generation
- `frontend/src/types/index.ts` - Added new TypeScript types
- `frontend/src/services/api.ts` - Added new API functions
- `frontend/src/App.tsx` - Added routes
- `frontend/src/components/layout/Sidebar.tsx` - Added CIO View nav item

---

### 2026-01-12 Session 7

**Completed:**
- Applied returns/correlation database migration (manually via psycopg2)
- Created 5 new tables: book_daily_returns, pm_daily_returns, correlation_cache, pod_daily_returns, benchmark_returns
- Regenerated mock data with 420 book returns (21 days × 20 books)
- Battle tested all 10 correlation API endpoints

**Migration Notes:**
- Partial migration existed from previous session (correlation_type already created)
- Manually applied remaining types: correlation_entity_type, correlation_window
- Renamed `window` column to `time_window` (reserved word in PostgreSQL)
- Created calculate_correlation() helper function

**Correlation API Test Results:**
- `/correlation/pm/{pm1}/correlation/{pm2}` - Success! Matthew Davis & Emily Davis = 0.455
- `/correlation/pm/matrix` - Full 10x10 PM correlation matrix working
- `/correlation/pm/high-correlations` - No high correlations found (good diversification)
- `/correlation/pm/{pm1}/correlation/{pm2}/analysis` - Comprehensive analysis working

**Example Analysis (Matthew Davis vs Emily Davis):**
- Pod weights: ~67% equity, ~26% rates, ~7% other (both similar)
- Realized correlation: 0.455 (21d), 0.14 (63d), 0.05 (5d)
- Implied correlation: 0.8985 (high - similar portfolio structure)
- AI recommendation: "Portfolio overlap is high but realized correlation moderate. Watch for increase."

**Week 4 Enhanced Quality Gate: PASSED**
- [x] All aggregation milestones checked
- [x] RiskPod mapping implemented (5 pods)
- [x] Returns tracking with mock data (420 records)
- [x] PM correlation endpoints working
- [x] Correlation matrix endpoint working
- [x] Documentation updated (ROADMAP + STATE)

---

### 2026-01-12 Session 6

**Completed:**
- Battle tested aggregation with real mock data (1,003 positions, 10 PMs)
- Fixed mock data generator duplicate key issues
- Merged feature/week4-aggregation to develop
- Pushed to remote

**Mock Data Test Results:**
- $1.3B gross exposure across 10 PMs
- 45.15% netting efficiency ($588M reduction)
- 198 overlaps detected (162 netting opportunities)
- Verified detailed security netting (GreenPower: 9 PMs, 6 long/3 short)
- All aggregation endpoints working correctly with real data

**Week 4 Quality Gate: PASSED**
- [x] All milestones checked
- [x] All verification criteria passed
- [x] All 154 tests passing
- [x] Battle testing complete (empty data + mock data)
- [x] Documentation updated
- [x] Pushed to remote

---

### 2026-01-12 Session 5

**Completed:**
- Created NettingService (cross-PM net position calculations)
- Created OverlapDetectionService (overlap detection, severity classification)
- Created AggregationService (main orchestrator, hierarchy navigation)
- Created aggregation API endpoints (14 new endpoints)
- Created test_aggregation.py (33 tests)
- All 154 tests passing
- Battle tested all API endpoints (all returning 200 OK)

**Files Created:**
- `backend/services/netting.py` - Cross-PM netting, NetPosition model
- `backend/services/overlap.py` - Overlap detection, severity, concentration
- `backend/services/aggregation.py` - Main orchestrator, hierarchy
- `backend/api/aggregation.py` - 14 API endpoints
- `backend/tests/test_aggregation.py` - 33 tests

**Key Features Implemented:**
- Net position calculation: PM1 long 1000 + PM2 short 300 = net 700
- Netting efficiency calculation (gross to net reduction %)
- Overlap detection (same-direction = concentration, opposing = netting opportunity)
- Severity classification (high/medium/low)
- Firm hierarchy navigation (Firm → Fund → PM → Book)
- PM contribution to netting analysis

**API Endpoints Added:**
- `/aggregation/firm/summary` - Firm-level summary with netting/overlaps
- `/aggregation/firm/hierarchy` - Full hierarchy tree
- `/aggregation/firm/positions` - Netted or raw positions
- `/aggregation/netting/summary` - Netting efficiency summary
- `/aggregation/netting/positions` - All net positions
- `/aggregation/netting/security/{id}` - Per-security detail
- `/aggregation/netting/pm/{id}` - PM netting contribution
- `/aggregation/overlaps` - All overlaps with filters
- `/aggregation/overlaps/summary` - Overlap statistics
- `/aggregation/overlaps/concentration-risks` - Same-direction risks
- `/aggregation/overlaps/netting-opportunities` - Opposing overlaps
- `/aggregation/overlaps/pm/{id}` - PM overlap exposure
- `/aggregation/pm/{id}/summary` - PM-level summary
- `/aggregation/fund/{id}/summary` - Fund-level summary

---

### 2026-01-12 Session 4

**Completed:**
- Analyzed SpecKit/ralph-wiggum plugin from Anthropic
- Adopted lightweight persona review workflow (without full plugin)
- Created NEW_PROJECT_SETUP.md with complete workflow guide
- Added pre-commit persona review checklist to CLAUDE.md
- Added feature branch workflow for Week 4
- Added quality gates and battle testing protocol
- Created .claude/review-checklist.md template (local only)

**Key Decisions:**
- Adopted rotating persona review (Code Reviewer, QA, Architect, Docs)
- Feature branches for complex features (Week 4 Aggregation)
- Quality gates before marking weeks complete
- Did NOT adopt: full SpecKit plugin, 1000s of tasks, spec-first workflow

**Rationale:** SpecKit solves problems we don't have. Our ROADMAP + STATE workflow is simpler and working well. Added the review perspectives to catch more issues.

---

### 2026-01-12 Session 3

**Completed:**
- Battle-tested all 8 risk API endpoints
- Fixed schema issues (s.ticker → s.name, expiration_date → expiry_date)
- Fixed test imports for proper package structure
- All 121 tests passing
- Updated ROADMAP.md with Week 3 complete
- Week 3 verification criteria all passed

**Verified:**
- VaR calculations with known normal distribution values
- Greeks: ATM call delta = 0.5695 (~0.5 expected)
- Put-call parity: Call delta - Put delta = 1.0
- All API endpoints return 200 OK

**Key Fixes:**
- Test imports changed from `backend.` to correct module path
- Database schema: `s.ticker` doesn't exist, use `s.name` instead
- Database schema: `expiration_date` → `expiry_date` for options
- Added `total_gross_exposure` to empty concentration response

---

### 2026-01-12 Session 2

**Completed:**
- Risk engine with VaR/CVaR calculations (historical, parametric, Monte Carlo)
- Exposure service (sector, geography, asset class, currency breakdowns)
- Greeks service (delta, gamma, vega, theta, rho) using Black-Scholes
- Risk API endpoints (12 new endpoints)
- Risk tests (31 tests)

**Tests Added:**
- `test_risk.py` - 31 tests (VaR, CVaR, Greeks, exposures, API)

**Key Decisions:**
- Implemented VaR/CVaR directly with numpy/scipy (riskfolio-lib has Windows build issues with cvxpy)
- Pure Python Black-Scholes for Greeks (FinancePy as optional enhancement)
- Three VaR methods: historical, parametric, Monte Carlo
- VaR scaling with sqrt(time) for different horizons

**Blockers:** riskfolio-lib install fails on Windows (cvxpy/osqp wheel build issues) - not blocking, implemented directly

---

### 2026-01-12 Session 1

**Completed:**
- Upload API (CSV/Excel with column auto-detection)
- FIX protocol parser (ExecutionReport, PositionReport)
- Trade API tests (26 tests)
- Book-level P&L aggregation endpoint
- All Week 2 milestones
- Process improvement files (STATE.md, ISSUES.md, verification criteria)

**Tests Added:**
- `test_upload.py` - 20 tests
- `test_fix.py` - 19 tests
- `test_trades.py` - 26 tests

**Key Decisions:**
- Used simplefix for FIX parsing (lightweight, MIT license)
- P&L formula: `unrealized_pnl = market_value - cost_basis`
- Book P&L includes long/short exposure breakdown

**Blockers:** None

---

## Architecture Decisions (Recent)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-12 | psycopg2 for database | On-premises architecture - hedge funds won't accept cloud storage |
| 2026-01-12 | simplefix over quickfix | Lightweight for MVP, can upgrade later if needed |
| 2026-01-12 | Column auto-detection for uploads | Better UX - don't require exact column names |

---

## Week 3 Preparation

### Risk Engine Dependencies
- [x] Position data (Week 2)
- [x] Security master (Week 1)
- [x] Mock data generator (Week 1)
- [ ] Market data integration (OpenBB) - needed for VaR

### Files to Create
| File | Purpose |
|------|---------|
| `backend/services/risk_engine.py` | Core risk calculations (VaR, CVaR) |
| `backend/services/exposures.py` | Sector/geography/asset class breakdowns |
| `backend/services/greeks.py` | Options Greeks using FinancePy |
| `backend/api/risk.py` | Risk API endpoints |
| `backend/tests/test_risk.py` | Risk calculation tests |

### Libraries to Use
- **Riskfolio-Lib** - VaR, CVaR, covariance (already researched)
- **FinancePy** - Greeks for options positions
- **OpenBB** - Market data for historical returns

---

## Verification Checklist (Week 4)

### Aggregation
- [x] Cross-PM netting calculates correctly (long 1000 + short 300 = net 700)
- [x] Netting efficiency percentage calculated (45.15% with mock data)
- [x] Overlap detection works (same-direction, opposing, mixed)
- [x] Severity classification works (high/medium/low based on PM count)
- [x] Firm hierarchy navigation works (Firm → Fund → PM → Book)
- [x] All 14 aggregation API endpoints return 200 OK
- [x] Battle tested with mock data (1,003 positions, 10 PMs)
- [x] 154 tests passing (121 + 33 aggregation)

### RiskPods & Correlation (Week 4 Enhancement)
- [x] RiskPod mapping: 5 pods (Equity, Rates, Credit, FX, Other)
- [x] Asset class → pod mapping working
- [x] Returns tables created (book_daily_returns, pm_daily_returns)
- [x] Mock data includes 420 book returns (21 days × 20 books)
- [x] PM-to-PM correlation calculation working (Pearson)
- [x] Correlation matrix endpoint returns 10x10 matrix
- [x] High correlation flagging works (threshold 0.7)
- [x] Implied correlation from pod weights working
- [x] Analysis endpoint returns comprehensive report
- [x] All 10 correlation API endpoints return 200 OK

## Verification Checklist (Week 3)

- [x] VaR/CVaR calculations correct (tested with known distributions)
- [x] Greeks calculations correct (ATM delta ~0.5, put-call parity)
- [x] All 8 risk API endpoints return 200 OK
- [x] Exposure breakdowns work (sector, geography, asset class, currency)
- [x] Concentration metrics work (top 10, single name, HHI)
- [x] Book Greeks work (returns valid response for empty book)
- [x] 121 tests passing (90 Week 2 + 31 Week 3)

## Verification Checklist (Week 2)

- [x] `POST /api/v1/positions` accepts valid data, rejects invalid
- [x] `POST /api/v1/trades` accepts valid data with validation
- [x] `POST /api/v1/upload` handles CSV/Excel, auto-detects columns
- [x] FIX messages (ExecutionReport, PositionReport) parse correctly
- [x] P&L = (quantity x price) - cost_basis calculated correctly
- [x] Book-level P&L aggregation working
- [x] All endpoints have tests (90 total)
- [x] All tests passing

---

## Known Issues / Tech Debt

See `ISSUES.md` for deferred items.

---

## Workflow Procedures

### Pre-Commit Persona Review

**Apply before EVERY commit:**

```
[0] CODE REVIEWER
    [ ] Security issues (injection, XSS, secrets)
    [ ] Error handling complete
    [ ] Edge cases covered

[1] QA ENGINEER
    [ ] Tests exist for new code
    [ ] Tests pass
    [ ] Edge case tests included

[2] ARCHITECT
    [ ] Follows existing patterns
    [ ] Files in correct locations
    [ ] No circular imports

[3] DOCUMENTATION
    [ ] ROADMAP.md updated
    [ ] STATE.md updated
    [ ] New issues in ISSUES.md
```

### Feature Branch (Week 4+)

For complex features like Week 4 Aggregation:

```bash
git checkout -b feature/week4-aggregation
# ... develop with persona review on each commit ...
git checkout develop && git merge feature/week4-aggregation
```

### Quality Gate (Before Week Completion)

```
[ ] All milestones checked
[ ] All verification criteria passed
[ ] All tests passing
[ ] Battle testing complete
[ ] Documentation updated
[ ] Pushed to remote
```

---

## Quick Commands

```bash
# Run all tests (from RISKCORE directory!)
cd C:\Users\massi\Desktop\RISKCORE
python -m pytest backend/tests -v

# Run specific test file
python -m pytest backend/tests/test_risk.py -v

# Start FastAPI server
cd backend && uvicorn backend.main:app --reload

# Generate mock data
python scripts/generate_mock_data.py --clean --scale medium

# Battle test API endpoints
python -c "from backend.main import app; from fastapi.testclient import TestClient; client = TestClient(app); print(client.get('/api/v1/health').json())"
```

---

*Last updated: 2026-01-13 (Session 9 - Compliance Architecture: SOC 2 + GDPR + Privacy)*
