# RISKCORE State

> Living document tracking current development state.
> **Purpose:** Quick session context restoration, decision tracking, blocker visibility.

---

## Current Position

| Field | Value |
|-------|-------|
| **Week** | 3 - Risk Engine |
| **Status** | ✅ COMPLETE |
| **Next** | Week 4 - Aggregation Engine |
| **Tests** | 121 passing |
| **Last Commit** | 56b74e7 |

---

## Session Log

### 2026-01-12 Session 3 (Latest)

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
