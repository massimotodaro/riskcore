# RISKCORE UI & Auth Architecture

> Brainstorm Session: January 10, 2026
> Status: Architecture Decision Document

---

## Executive Summary

This document defines two critical architectural decisions:

1. **UI Structure** — How the Riskboard displays risk, aggregates books/PMs, and suggests hedges
2. **Auth & Permissions** — Multi-tenant architecture with book-level access control

**Key Innovation:** RISKCORE will be the first platform to show cross-book/cross-PM correlation with drill-down to underlying trades and AI-powered hedge suggestions.

---

## Part 1: UI Architecture — The Riskboard

### 1.1 Core Concept

The **Riskboard** is RISKCORE's main dashboard showing:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RISKBOARD                                          [Book Selector ▼]   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  EQUITIES   │  │ FIXED INCOME│  │     FX      │  │   OPTIONS   │    │
│  │   RiskCard  │  │   RiskCard  │  │   RiskCard  │  │   RiskCard  │    │
│  │             │  │             │  │             │  │             │    │
│  │ Beta: $2.3M │  │ DV01: $500K │  │ EUR: -$1.2M │  │ Delta: $80K │    │
│  │ Sector: ... │  │ CS01: $120K │  │ GBP: +$400K │  │ Vega: -$45K │    │
│  │             │  │ KR01: ...   │  │ JPY: +$200K │  │ Gamma: ...  │    │
│  │ [RiskOff ▼] │  │ [RiskOff ▼] │  │ [RiskOff ▼] │  │ [RiskOff ▼] │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐                                      │
│  │   CREDIT    │  │ COMMODITIES │      ┌────────────────────────────┐  │
│  │   RiskCard  │  │   RiskCard  │      │   CORRELATION MATRIX       │  │
│  │             │  │             │      │   (between RiskCards)      │  │
│  │ CS01: $85K  │  │ Oil: +$300K │      │                            │  │
│  │ JTD: $2.1M  │  │ Gold: -$50K │      │   EQ   FI   FX   OPT  CR   │  │
│  │             │  │             │      │   1.0  0.3  0.2  0.8  0.4  │  │
│  │ [RiskOff ▼] │  │ [RiskOff ▼] │      │   ...                      │  │
│  └─────────────┘  └─────────────┘      └────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 RiskCard Component

Each **RiskCard** displays risk factors for one asset class:

```
┌─────────────────────────────────────┐
│  FIXED INCOME                    ⚙️ │
├─────────────────────────────────────┤
│                                     │
│  DV01 (Total)      $523,450    🔴   │
│  ├─ 2Y tenor       $125,000         │
│  ├─ 5Y tenor       $248,000    ⚠️   │
│  ├─ 10Y tenor      $150,450         │
│                                     │
│  CS01 (Credit)     $118,200    🟡   │
│  Convexity         +$45,000    🟢   │
│                                     │
│  [📊 View Trades]  [🎯 RiskOff]     │
│                                     │
│  ⚠️ Model Override Active (Vol)     │
└─────────────────────────────────────┘
```

**Color Coding:**
- 🔴 Red = Exceeds limit / High concentration
- 🟡 Yellow = Approaching limit
- 🟢 Green = Within tolerance

**Drill-down:** Click any risk factor → see all trades contributing to that number

### 1.3 Risk Factors by Asset Class

| Asset Class | Key Risk Factors | Unit |
|-------------|------------------|------|
| **Equities** | Beta, Sector Delta, Country Delta, Size, Value/Growth | $ per 1% move |
| **Fixed Income** | DV01, KR01 (by tenor), CS01, Convexity | $ per 1bp |
| **FX** | Delta per currency pair | $ per 1% move |
| **Options** | Delta, Gamma, Vega, Theta, Rho | $ |
| **Credit** | CS01, Jump-to-Default (JTD) | $ per 1bp / $ |
| **Commodities** | Delta per commodity | $ per 1% move |

### 1.4 Book/PM Aggregation Hierarchy

```
FIRM (Top Level - CIO/CRO view)
│
├── FUND A
│   ├── Book 1 (PM Alpha)
│   ├── Book 2 (PM Beta)
│   └── Book 3 (PM Gamma)
│
├── FUND B
│   └── Book 4 (Multiple PMs feed into one book)
│       ├── PM Delta trades
│       ├── PM Epsilon trades
│       └── PM Zeta trades
│
└── FUND C
    └── Book 5 (Single PM)
```

**Key Insight:** A book can have:
- **1 PM → 1 Book** (standard)
- **N PMs → 1 Book** (large fund with multiple PMs)

For the N:1 case, RISKCORE allows viewing:
- Book-level aggregate risk
- PM-level risk (filtered by PM within the book)

### 1.5 Book Selector Controls

```
┌─────────────────────────────────────────────────────────────┐
│  VIEW:  [All Books ▼]     FILTER BY: [Fund ▼] [PM ▼]       │
├─────────────────────────────────────────────────────────────┤
│  ☑️ Book 1 (PM Alpha)    ☑️ Book 3 (PM Gamma)              │
│  ☑️ Book 2 (PM Beta)     ☐ Book 4 (Excluded)               │
│                                                             │
│  Showing: 3 of 5 books   [Select All] [Clear] [Save View]   │
└─────────────────────────────────────────────────────────────┘
```

User can:
- Toggle books on/off for aggregation
- Save custom "views" (e.g., "Tech PMs", "Macro Books")
- Filter by Fund or PM

### 1.6 Multi-Book Comparison View

```
┌───────────────────────────────────────────────────────────────────────────┐
│  MULTI-BOOK COMPARISON                                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐       │
│  │  GROUP A        │    │  GROUP B        │    │  GROUP C        │       │
│  │  (Tech PMs)     │    │  (Macro Books)  │    │  (Credit)       │       │
│  │                 │    │                 │    │                 │       │
│  │  [Mini Riskboard]    │  [Mini Riskboard]    │  [Mini Riskboard]       │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  CROSS-GROUP CORRELATION                                            │ │
│  │                                                                     │ │
│  │           Group A    Group B    Group C                             │ │
│  │  Group A    1.00      0.45      -0.12                               │ │
│  │  Group B    0.45      1.00       0.67                               │ │
│  │  Group C   -0.12      0.67       1.00                               │ │
│  │                                                                     │ │
│  │  [Realized ◉] [Implied ○]    Lookback: [60 days ▼]                 │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  FACTOR CORRELATION BREAKDOWN                                       │ │
│  │  (How are specific risk factors correlated across groups?)          │ │
│  │                                                                     │ │
│  │  DV01 (5Y): Group A vs Group B = 0.82 🔴                            │ │
│  │  Equity Beta: Group A vs Group C = 0.23 🟢                          │ │
│  │  Vega: Group B vs Group C = 0.91 🔴                                 │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

### 1.7 Feature Name: RiskOff Suggestions

**Proposed Names for Hedge Suggestion Feature:**

| Name | Vibe | My Pick |
|------|------|---------|
| **RiskOff** | Action-oriented, clear | ⭐ Recommended |
| **HedgePilot** | AI/navigation feel | Good |
| **RiskRebalancer** | Technical, accurate | Okay |
| **AutoHedge** | Automated feel | Already used by others |
| **ShieldTrade** | Protection metaphor | Creative |
| **ExposureTune** | Fine-tuning feel | Too subtle |

**Recommendation: "RiskOff"** — Simple, memorable, action-oriented.

### 1.8 RiskOff Panel

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🎯 RISKOFF — Fixed Income Hedge Suggestions                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CURRENT EXPOSURE                                                       │
│  DV01 (5Y Tenor): $248,000                                             │
│                                                                         │
│  TARGET EXPOSURE                                                        │
│  ┌──────────────────────────────────────────────┐                       │
│  │ $230,000 ────────●──────────────── $248,000  │  or  [Enter: ____]   │
│  └──────────────────────────────────────────────┘                       │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  SUGGESTED TRADE                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Action: SELL                                                     │   │
│  │ Instrument: US Treasury 5Y Note (912810TY9)                     │   │
│  │ Notional: $18,500,000                                           │   │
│  │                                                                  │   │
│  │ Expected Impact:                                                 │   │
│  │   DV01 (5Y): -$18,000 (from $248K → $230K)                      │   │
│  │   Convexity: +$2,100                                            │   │
│  │   Carry: -$8,500/month                                          │   │
│  │                                                                  │   │
│  │ Est. Transaction Cost: $4,200 (spread + market impact)          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Copy to Clipboard] [Export to CSV] [Mark as Reviewed]                 │
│                                                                         │
│  ⚠️ Note: RISKCORE is READ-ONLY. Execute trades in your trading system.│
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.9 Trade Drill-Down View

When user clicks "View Trades" on any risk factor:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRADES CONTRIBUTING TO: DV01 (5Y Tenor) = $248,000                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Trade ID   | Instrument        | Notional    | DV01      | PM    | Book│
│  ─────────────────────────────────────────────────────────────────────  │
│  TRD-001    | US 5Y Note        | $50,000,000 | $125,000  | Alpha | B1  │
│  TRD-002    | US 5Y Note        | $30,000,000 | $75,000   | Beta  | B2  │
│  TRD-003    | Corp Bond (5Y)    | $20,000,000 | $48,000   | Alpha | B1  │
│  ─────────────────────────────────────────────────────────────────────  │
│                                          TOTAL: | $248,000  |           │
│                                                                         │
│  [Export] [Filter by PM] [Filter by Book]                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.10 Model Transparency & Override

For derivatives using models (options, swaps, etc.):

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MODEL DETAILS: AAPL Jan 2026 Call (Strike $200)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Pricing Model: Black-Scholes (FinancePy)                              │
│                                                                         │
│  INPUT PARAMETERS                                                       │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Parameter      │ Value    │ Source         │ Override          │    │
│  │────────────────────────────────────────────────────────────────│    │
│  │ Spot Price     │ $198.50  │ Market (Live)  │ [───────]        │    │
│  │ Strike         │ $200.00  │ Contract       │ [───────]        │    │
│  │ Expiry         │ 45 days  │ Contract       │ [───────]        │    │
│  │ Risk-Free Rate │ 4.25%    │ Treasury Curve │ [───────]        │    │
│  │ Volatility     │ 28.5%    │ Implied (ATM)  │ [32.0% ✏️] ⚠️    │    │
│  │ Dividend Yield │ 0.50%    │ Estimated      │ [───────]        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  CALCULATED VALUES                                                      │
│  Option Price: $8.45    Delta: 0.48    Gamma: 0.032    Vega: 0.18      │
│                                                                         │
│  ⚠️ WARNING: Volatility is USER-OVERRIDE (not market)                  │
│  [Reset to Market Values]                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**At RiskCard level, show warning:**
```
⚠️ 3 positions using User-Override inputs [View Details]
```

---

## Part 2: Auth & Permissions Architecture

### 2.1 Entity Hierarchy

```
RISKCORE (Platform)
│
├── SuperAdmin (Us - Anthropic/RISKCORE)
│   └── Creates Tenants (Firms)
│
└── TENANT (Firm) ← This is the billing/isolation unit
    │
    ├── Admin (Firm Admin)
    │   └── Creates Users, Books, Assigns Permissions
    │
    ├── Users
    │   ├── CEO/CIO Role
    │   ├── CRO Role
    │   ├── PM Role
    │   └── Analyst Role
    │
    └── Books
        ├── Book 1
        ├── Book 2
        └── Book N
```

### 2.2 Role Definitions

| Role | Description | Default Access |
|------|-------------|----------------|
| **SuperAdmin** | RISKCORE team | All tenants, all data (for support) |
| **Admin** | Firm administrator | All books in tenant, user management |
| **CIO/CEO** | C-level executive | All books in tenant (view only) |
| **CRO** | Chief Risk Officer | All books, can set limits |
| **PM** | Portfolio Manager | Own book(s) only |
| **Analyst** | Risk analyst | Assigned books (view only) |

### 2.3 Permission Matrix

| Action | SuperAdmin | Admin | CIO/CEO | CRO | PM | Analyst |
|--------|------------|-------|---------|-----|-------|---------|
| View all books | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| View assigned books | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign book access | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Set risk limits | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Override model inputs | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Export data | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| API access | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |

### 2.4 Database Schema for Auth

```sql
-- Tenants (Firms)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free', -- 'free', 'pro', 'enterprise'
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'superadmin', 'admin', 'cio', 'cro', 'pm', 'analyst'
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Books
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    fund_id UUID REFERENCES funds(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User-Book Access (Many-to-Many)
CREATE TABLE user_book_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    book_id UUID REFERENCES books(id),
    access_level VARCHAR(50) DEFAULT 'read', -- 'read', 'write', 'admin'
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, book_id)
);

-- Positions (with tenant isolation)
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    book_id UUID REFERENCES books(id),
    pm_id UUID REFERENCES users(id),
    security_id UUID REFERENCES securities(id),
    quantity DECIMAL(18, 4),
    market_value DECIMAL(18, 2),
    as_of_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.5 Row Level Security (RLS) Policies

```sql
-- Enable RLS on positions table
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see positions in their tenant
CREATE POLICY "Users see own tenant positions"
ON positions
FOR SELECT
TO authenticated
USING (
    tenant_id = (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    )
);

-- Policy: Users can only see positions in books they have access to
-- (unless they are admin/cio/cro who see all)
CREATE POLICY "Users see accessible books"
ON positions
FOR SELECT
TO authenticated
USING (
    book_id IN (
        SELECT book_id FROM user_book_access WHERE user_id = auth.uid()
    )
    OR
    (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'cio', 'ceo', 'cro')
);
```

### 2.6 Monetization Tiers

| Tier | Price | Users | Books | Features |
|------|-------|-------|-------|----------|
| **Free** | $0 | 1 | 1 | Basic Riskboard, manual upload only |
| **Pro** | $500/mo | 5 | 5 | Multi-book, API, correlation matrix |
| **Enterprise** | $5K+/mo | Unlimited | Unlimited | SSO, RiskOff, custom integrations, SLA |

**Free Tier Limits:**
- 1 user
- 1 book
- CSV upload only (no API)
- No correlation features
- No RiskOff suggestions
- "Powered by RISKCORE" branding

**This allows single traders to use RISKCORE for free, while businesses pay.**

### 2.7 JWT Claims Structure

```json
{
  "sub": "user-uuid",
  "email": "user@firm.com",
  "tenant_id": "tenant-uuid",
  "role": "pm",
  "book_ids": ["book-1-uuid", "book-2-uuid"],
  "plan": "pro",
  "iat": 1704877200,
  "exp": 1704963600
}
```

Supabase RLS can access these via `auth.jwt()`:

```sql
CREATE POLICY "Tenant isolation"
ON positions
USING (
    tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
);
```

---

## Part 3: Architecture Implications

### 3.1 Database Changes

**New Tables Needed:**

| Table | Purpose |
|-------|---------|
| `tenants` | Multi-tenant isolation |
| `funds` | Fund hierarchy under tenant |
| `books` | Books within funds |
| `user_book_access` | Permission mapping |
| `model_overrides` | Track user-modified model inputs |
| `saved_views` | User-saved book combinations |
| `risk_limits` | CRO-defined limits per book/factor |

### 3.2 API Changes

**New Endpoints:**

```
# Auth & Tenant
POST   /api/v1/auth/signup          # Create tenant + first admin
POST   /api/v1/auth/invite          # Invite user to tenant
POST   /api/v1/tenants/:id/users    # Create user in tenant

# Books & Access
GET    /api/v1/books                # List accessible books
POST   /api/v1/books                # Create book (admin only)
POST   /api/v1/books/:id/access     # Grant user access to book

# Risk Views
GET    /api/v1/risk/riskboard       # Aggregated risk view
GET    /api/v1/risk/correlation     # Cross-book correlation
GET    /api/v1/risk/drilldown/:factor  # Trades for a risk factor

# RiskOff
POST   /api/v1/riskoff/suggest      # Get hedge suggestions
POST   /api/v1/riskoff/calculate    # Calculate custom target

# Model Overrides
POST   /api/v1/models/override      # Set model input override
DELETE /api/v1/models/override/:id  # Reset to market
```

### 3.3 Frontend Components

**New Components:**

| Component | Purpose |
|-----------|---------|
| `<Riskboard />` | Main dashboard container |
| `<RiskCard />` | Individual asset class risk display |
| `<BookSelector />` | Multi-select book toggle |
| `<CorrelationMatrix />` | Heatmap of cross-book correlation |
| `<MultiBookView />` | Side-by-side book comparison |
| `<RiskOffPanel />` | Hedge suggestion interface |
| `<TradesDrilldown />` | List of trades for a risk factor |
| `<ModelDetails />` | Model inputs with override capability |
| `<UserManagement />` | Admin user/permission management |

---

## Part 4: Research Findings

### What Exists (We Can Learn From)

| Tool | What They Do | Gap |
|------|--------------|-----|
| **TradingView Correlation Heatmap** | Asset-to-asset correlation | Not book-to-book |
| **OANDA Correlation Tool** | Currency pair correlation | FX only |
| **Goldman Marquee Hedging Tools** | Factor hedging | Proprietary, not multi-PM |
| **AlternativeSoft** | Fund-of-funds analytics | Not real-time, not cross-PM |
| **Orchestrade** | Multi-asset PMS | No cross-PM correlation |

### What Doesn't Exist (Our Opportunity)

| Feature | Status | RISKCORE Opportunity |
|---------|--------|---------------------|
| Cross-book correlation matrix | ❌ No one does this | First to market |
| Book/PM-level drill-down | ❌ Limited | Deep drill-down |
| RiskOff suggestions | ❌ Goldman only (proprietary) | Democratize |
| Model input transparency | ❌ Black boxes | Full transparency |
| Multi-PM to single book | ❌ Not addressed | Unique capability |

---

## Part 5: Recommendations

### Immediate Actions

1. **Add to database schema:**
   - `tenants` table
   - `user_book_access` table
   - `model_overrides` table

2. **Implement RLS policies:**
   - Tenant isolation
   - Book-level access control

3. **Design RiskCard component:**
   - Reusable for all asset classes
   - Consistent drill-down pattern

### MVP Scope Adjustment

**Add to Week 1:**
- Multi-tenant schema design
- Basic RLS policies

**Add to Week 4:**
- Book selector with toggle
- Basic correlation (realized only)

**Add to Week 5:**
- RiskCard components
- Riskboard layout

**Defer to Phase 2:**
- RiskOff suggestions
- Implied correlation
- Model override UI

---

## Summary

| Topic | Decision |
|-------|----------|
| **Main Dashboard Name** | Riskboard |
| **Risk Display Unit** | RiskCard (per asset class) |
| **Hedge Feature Name** | RiskOff |
| **Correlation Display** | Heatmap matrix with drill-down |
| **Auth Model** | Multi-tenant with RLS |
| **Free Tier** | 1 user, 1 book, manual upload |
| **Book-PM Relationship** | Many-to-many (N PMs can feed 1 book) |

---

*Architecture decision document for RISKCORE*
*To be reviewed and incorporated into main docs*
