# RISKCORE State

> Living document tracking current development state.
> **Purpose:** Quick session context restoration, decision tracking, blocker visibility.

---

## Current Position

| Field | Value |
|-------|-------|
| **Week** | 4 - Aggregation Engine |
| **Status** | 🔄 IN PROGRESS |
| **Next** | Battle test with mock data, merge to develop |
| **Tests** | 154 passing (121 + 33 aggregation) |
| **Branch** | feature/week4-aggregation |

---

## Session Log

### 2026-01-12 Session 5 (Latest)

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

*Last updated: 2026-01-12*
