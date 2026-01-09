# RISKCORE Decision Log

> All key decisions with rationale. Add new decisions at the top.

---

## 2025-01-09 (Afternoon)

### DECISION: Build Correlation Framework as Phase 2-3 differentiator

**Context:** CIO/CRO at multi-manager funds need to see correlation between books/PMs. No platform does this well. 2008 showed correlations spike to 1 in crisis.

**Decision:** Build comprehensive correlation framework:
- Phase 2: Realized + Implied correlation matrices
- Phase 3: Stress testing + Hedge overlay suggestions

**Components:**
1. Risk factor taxonomy (standard factors per asset class)
2. Factor exposure decomposition per book
3. Realized correlation (historical P&L-based)
4. Implied correlation (factor-based, forward-looking)
5. Stress testing (correlation → 0.9 scenario)
6. Hedge overlay suggestions (AI-powered trade recommendations)

**Rationale:**
- Unique differentiator — no competitor has this
- Solves real CIO/CRO pain point
- Builds on existing Riskfolio-Lib capabilities
- Natural extension of aggregation engine

**Status:** ✅ Added to roadmap

---

### DECISION: Use simplefix for FIX protocol parsing

**Context:** Need to ingest trade/position data from client systems. Vendor APIs require client relationships.

**Decision:** Use `simplefix` library for MVP FIX parsing.

**Rationale:**
- MIT license
- Pure Python, no dependencies
- Simple API
- Upgrade path to `quickfix` for enterprise

**Status:** ✅ Confirmed

---

### DECISION: Use pyopenfigi for identifier mapping

**Context:** Need to map CUSIP/ISIN/SEDOL/Ticker to canonical identifier.

**Decision:** Use `pyopenfigi` library with OpenFIGI API.

**Rationale:**
- Free API (no subscription)
- Bloomberg-backed standard
- MIT license
- Maps all major identifier types

**Status:** ✅ Confirmed

---

### DECISION: Prioritize data validation pipeline

**Context:** Pre-build research found data quality is #1 cause of risk system failures.

**Decision:** Build data validation pipeline in Week 1, before other features.

**Rationale:**
- Garbage in, garbage out
- Reddit/HN consensus: data quality is critical
- Better to validate early than debug later

**Status:** ✅ Confirmed

---

### DECISION: FIX + CSV for MVP (not vendor APIs)

**Context:** Enfusion, Eze, Bloomberg APIs all require client relationships. No public documentation.

**Decision:** Focus on FIX protocol and CSV/Excel import for MVP. Vendor APIs in Phase 2+ when we have client relationships.

**Rationale:**
- FIX is open standard
- CSV is universal
- Can't build vendor connectors without API access
- Client relationship comes after we have working product

**Status:** ✅ Confirmed

---

## 2025-01-09 (Morning)

### DECISION: Create knowledge base for Claude Code

**Context:** Knowledge scattered across Notion, chat, and local files. CC doesn't automatically know what we've decided.

**Decision:** Use CLAUDE.md + /docs structure:
- CLAUDE.md at repo root = summary CC reads first
- /docs folder = detailed documentation
- Markdown files = version controlled, CC can read directly

**Alternatives Considered:**
- Supabase tables (queryable but extra step)
- Notion API (single source but requires MCP)
- Single CLAUDE.md only (gets too long)

**Status:** ✅ Implemented

---

### DECISION: Research before building

**Context:** Almost started building without checking what exists. GitHub research revealed FinancePy, Riskfolio-Lib, OpenBB.

**Decision:** Always research before building:
- GitHub for open-source solutions
- Reddit for practitioner insights
- PyPI for existing packages
- Vendor docs for integration patterns
- Academic papers for methodologies

**Lesson Learned:** Would have rebuilt huge amount of work if we hadn't checked.

**Status:** ✅ Research process established

---

### DECISION: Use FinancePy for derivatives pricing

**Context:** Pricing derivatives requires complex models (yield curves, vol surfaces, Greeks).

**Decision:** Use FinancePy library instead of building our own.

**Rationale:**
- 2,600+ GitHub stars
- MIT License (commercial OK)
- Written by EDHEC professor (academically rigorous)
- Covers FI, equity, FX, credit derivatives
- Active development
- 60+ Jupyter notebooks for learning

**What we DON'T build:** Yield curve bootstrap, Black-Scholes, swap valuation, CDS pricing.

**Status:** ✅ Confirmed

---

### DECISION: Use Riskfolio-Lib for risk metrics

**Context:** Need VaR, CVaR, covariance matrices, risk measures.

**Decision:** Use Riskfolio-Lib instead of building our own.

**Rationale:**
- 3,000+ GitHub stars
- BSD-3 License
- 24 convex risk measures
- CVaR, EVaR, RLVaR
- Active development (v7.0.1)
- Comprehensive documentation

**What we DON'T build:** VaR algorithms, covariance estimation, drawdown measures.

**Status:** ✅ Confirmed

---

### DECISION: Use OpenBB for market data

**Context:** Need prices for equities, FX, bonds, options.

**Decision:** Use OpenBB instead of building data connectors.

**Rationale:**
- 31,000+ GitHub stars
- Connects to 100+ data providers
- REST API and Python SDK
- Active development
- MCP servers available for AI agents

**What we DON'T build:** Individual data provider integrations.

**Status:** ✅ Confirmed

---

### DECISION: READ-ONLY architecture

**Context:** Clients won't change their trading systems. We need to integrate without disruption.

**Decision:** RISKCORE is a READ-ONLY overlay. We never write to source systems.

**Benefits:**
- Easy adoption (no workflow changes)
- No risk of corrupting client data
- Faster integration
- Lower client IT burden

**Status:** ✅ Core principle

---

### DECISION: Integration priority order

**Context:** Need to decide which systems to support first.

**Decision:**
1. **MVP (HIGH):** Excel/CSV, FIX protocol
2. **Phase 2 (MEDIUM):** Bloomberg AIM/PORT, Enfusion, Eze (with client relationships)
3. **Phase 3:** Real-time WebSocket, database connectors

**Rationale:**
- Excel/CSV = universal, every fund has this
- FIX = open standard, no vendor relationship needed
- Vendor APIs = require client relationship first

**Status:** ✅ Updated based on research

---

### DECISION: Supabase for database

**Context:** Need a database for positions, securities, risk metrics.

**Decision:** Use Supabase (managed Postgres).

**Rationale:**
- Already set up (project: vukinjdeddwwlaumtfij)
- Real-time subscriptions (good for dashboard)
- Free tier sufficient for MVP
- Easy authentication
- Good DX

**Status:** ✅ Already configured

---

### DECISION: Week 4 = Aggregation Engine

**Context:** Need to prioritize the 6-week timeline.

**Decision:** Week 4 is dedicated to the aggregation engine — our core differentiator.

**What Week 4 delivers:**
- Cross-PM position consolidation
- Security master mapping
- Overlap detection
- Firm-level rollup

**This is what no one else has.**

**Status:** ✅ Confirmed in MVP

---

### DECISION: Open source core, paid enterprise

**Context:** Need a business model that builds trust and generates revenue.

**Decision:**
- Core platform = open source (MIT License)
- Enterprise features = paid

**Enterprise features (future):**
- SSO/SAML authentication
- Multi-tenant isolation
- SLA guarantees
- Premium support
- Advanced compliance reports
- Correlation framework (Phase 2-3)
- Hedge overlay suggestions

**Status:** ✅ Strategic direction

---

## Template for New Decisions

```markdown
### DECISION: [Title]

**Context:** [Why this decision was needed]

**Decision:** [What we decided]

**Rationale:** [Why this option]

**Alternatives Considered:**
- [Option A] - [Why rejected]
- [Option B] - [Why rejected]

**Status:** ✅ Confirmed / 🔄 Pending / ❌ Reversed
```
