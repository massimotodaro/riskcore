# RISKCORE Decision Log

> All key decisions with rationale. Add new decisions at the top.

---

## 2026-01-09

### DECISION: Use simplefix for FIX protocol parsing

**Context:** Need to ingest trade/position data from systems that support FIX protocol.

**Decision:** Use simplefix library for MVP FIX message parsing.

**Rationale:**
- 250+ GitHub stars
- MIT License (commercial OK)
- Pure Python, no dependencies
- Simple API for message creation/parsing
- Easy upgrade path to quickfix for enterprise features

**What we DON'T build:** FIX message parsing, validation, session management (for MVP).

**Status:** Confirmed

---

### DECISION: Use pyopenfigi for identifier mapping

**Context:** Need to map security identifiers (CUSIP, ISIN, SEDOL, Ticker) to build security master.

**Decision:** Use pyopenfigi library to access OpenFIGI API.

**Rationale:**
- Free API (no subscription required)
- Bloomberg-backed identifier standard
- Maps all major identifier types to FIGI
- MIT License
- Rate limit: 25 requests/min (free tier)

**What we DON'T build:** Identifier mapping logic, CUSIP checksum validation.

**Status:** Confirmed

---

### DECISION: Prioritize data validation pipeline

**Context:** Pre-build research revealed data quality is #1 cause of risk system failures.

**Decision:** Build data validation pipeline in Week 1, before ingestion.

**Rationale:**
- Research quote: "The biggest reason for failure in risk monitoring is data quality"
- 45% of funds struggle with inflexible systems that can't handle messy data
- Validation catches issues early, before they propagate to risk calculations

**Implementation:**
- Schema validation (required fields, data types)
- Identifier validation (using pyopenfigi)
- Range checks (prices, quantities)
- Duplicate detection
- Audit trail for rejected records

**Status:** Confirmed

---

### DECISION: FIX + CSV for MVP (not vendor APIs)

**Context:** Pre-build research revealed all major vendor APIs require client relationships.

**Decision:** Focus on FIX protocol and CSV/Excel for MVP. Defer vendor API integration.

**Rationale:**
- Enfusion API: Requires client relationship
- SS&C Eze API: Requires client relationship
- Bloomberg BLPAPI: Requires Terminal/B-PIPE subscription
- Charles River API: Requires client relationship
- FIX Protocol: Open standard, publicly documented
- CSV/Excel: Universal, every fund has this

**MVP Integration Priority:**
1. CSV/Excel/JSON file upload
2. FIX protocol (using simplefix)
3. REST API for custom integrations

**Phase 2 (when client relationships form):**
- Vendor-specific API adapters

**Status:** Confirmed

---

## 2025-01-09

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
1. **MVP (HIGH):** Excel/CSV, Enfusion, Eze Eclipse
2. **Phase 2 (MEDIUM):** Bloomberg AIM/PORT, Charles River, SimCorp
3. **Phase 3:** FIX protocol, Webhooks

**Rationale:**
- Excel/CSV = universal, every fund has this
- Enfusion = 950+ HF clients, modern API
- Eze = 200+ clients, SS&C backed
- Bloomberg = complex BLPAPI, longer sales cycle

**Status:** ✅ Confirmed

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
