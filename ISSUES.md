# RISKCORE Issues & Deferred Items

> Track technical debt, enhancements, and deferred work.
> **Purpose:** Don't lose good ideas. Review before each week starts.

---

## Priority Levels

| Level | Meaning |
|-------|---------|
| P0 | Blocking - must fix before next milestone |
| P1 | High - should address this week |
| P2 | Medium - address when convenient |
| P3 | Low - nice to have, future consideration |

---

## Open Issues

### P2 - Medium Priority

#### ISSUE-001: Add retry logic to OpenFIGI client
**Created:** 2026-01-11
**Component:** `backend/services/openfigi.py`
**Description:** OpenFIGI API occasionally returns 429 (rate limit). Current client waits but doesn't retry failed requests.
**Impact:** Some security lookups may silently fail.
**Suggested Fix:** Add exponential backoff retry for 429 and 5xx errors.

#### ISSUE-002: Position validation doesn't check book ownership
**Created:** 2026-01-12
**Component:** `backend/api/positions.py`
**Description:** Position creation accepts any book_id without verifying it belongs to the tenant.
**Impact:** Data integrity issue in multi-tenant environment.
**Suggested Fix:** Call `validate_book_exists()` in create endpoint, return 404 if not found.

#### ISSUE-003: Upload preview doesn't persist
**Created:** 2026-01-12
**Component:** `backend/api/upload.py`
**Description:** Preview endpoint shows what will be imported but doesn't cache the result. User must re-upload to import.
**Impact:** Inefficient for large files.
**Suggested Fix:** Cache parsed data in Redis/memory with TTL, return token for import.

### P3 - Low Priority

#### ISSUE-004: FIX parser doesn't support all message types
**Created:** 2026-01-12
**Component:** `backend/services/fix_parser.py`
**Description:** Only ExecutionReport (35=8) and PositionReport (35=AP) are supported.
**Impact:** Other FIX messages return "unsupported" error.
**Suggested Fix:** Add support for NewOrderSingle, OrderCancelRequest, etc. as needed.

#### ISSUE-007: riskfolio-lib not installed (Windows build issues)
**Created:** 2026-01-12
**Component:** `backend/requirements.txt`
**Description:** riskfolio-lib fails to install on Windows due to cvxpy/osqp wheel build failures.
**Impact:** Portfolio optimization features not available. VaR/CVaR implemented directly with numpy/scipy as workaround.
**Suggested Fix:** Use Docker/Linux for development, or wait for pre-built Windows wheels.

#### ISSUE-005: Trade bulk create doesn't use transactions
**Created:** 2026-01-12
**Component:** `backend/services/trade_service.py`
**Description:** Bulk trade creation commits each trade individually. Partial failures leave inconsistent state.
**Impact:** Risk of partial imports on error.
**Suggested Fix:** Wrap bulk operations in transaction, rollback on any failure.

#### ISSUE-006: No pagination for book trades endpoint
**Created:** 2026-01-12
**Component:** `backend/api/trades.py`
**Description:** `GET /trades/book/{book_id}` returns all trades without pagination.
**Impact:** Performance issue for books with many trades.
**Suggested Fix:** Add page/page_size params like list endpoint.

---

## Closed Issues

*None yet - issues will be moved here when resolved.*

---

## Enhancement Ideas (Future)

These are good ideas that don't fit current MVP scope:

| ID | Idea | Week/Phase |
|----|------|------------|
| ENH-001 | Real-time WebSocket updates for position changes | Week 5 |
| ENH-002 | Bloomberg BLPAPI integration | Phase 2 |
| ENH-003 | Enfusion REST API adapter | Phase 2 |
| ENH-004 | Position reconciliation with external systems | Phase 2 |
| ENH-005 | Automated data quality scoring | Phase 2 |
| ENH-006 | Historical position replay | Phase 3 |

---

## Review Schedule

- **Before each week:** Review P1/P2 issues, decide what to address
- **End of MVP:** Review all issues, prioritize for Phase 2
- **After major features:** Add any new issues discovered

---

*Last updated: 2026-01-12*
