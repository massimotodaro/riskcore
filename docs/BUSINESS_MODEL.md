# RISKCORE Business Model

> Last Updated: 2025-01-09
> Status: Strategic Planning
> Author: Massimo Todaro

---

## Executive Summary

RISKCORE is an **open-source first** product with multiple monetization paths. The strategy is:

1. **Build trust** through open source and thought leadership
2. **Acquire users** with a free, high-quality core product
3. **Monetize** through hosted SaaS, enterprise features, and services
4. **Exit options** include strategic acquisition or sustainable SaaS business

---

## Why Open Source?

| Benefit | Impact |
|---------|--------|
| **Trust** | Funds can audit the code, no black box |
| **Adoption** | Lower barrier to entry, faster growth |
| **Community** | Contributors improve the product |
| **Visibility** | GitHub stars, LinkedIn content, thought leadership |
| **Differentiation** | Competitors are all proprietary |
| **Talent** | Attracts developers who want to work on open source |

**Risk:** Competitors can fork. **Mitigation:** Move fast, build community, offer better support.

---

## Monetization Models

### Model 1: Open Core

The most common model for developer tools (GitLab, Supabase, n8n, Metabase).

| Tier | Price | Features |
|------|-------|----------|
| **Community (Free)** | $0 | Core platform, single user, CSV upload, basic risk metrics, self-hosted |
| **Pro** | $500-2K/month | Multi-user, API access, priority support, more integrations |
| **Enterprise** | $5K-25K/month | SSO/SAML, multi-tenant, SLA, dedicated support, custom integrations, compliance features |

**Free Tier Includes:**
- Position aggregation engine
- Security master
- Basic risk metrics (VaR, exposures)
- CSV/Excel upload
- Single-user dashboard
- Community support (GitHub issues)

**Pro Tier Adds:**
- Multi-user access (up to 10)
- API access
- FIX protocol adapter
- Email support (48hr response)
- Basic integrations

**Enterprise Tier Adds:**
- Unlimited users
- SSO/SAML authentication
- Correlation Framework
- Hedge Overlay Suggestions
- Custom integrations
- Dedicated support (4hr response)
- SLA (99.9% uptime)
- Regulatory reporting templates
- Audit logs
- On-premise deployment option

---

### Model 2: Hosted SaaS

"We run it, you use it" — no DevOps required.

| Tier | Price | Target Customer |
|------|-------|-----------------|
| **Starter** | $1,000/month | Small funds (<$500M AUM), family offices |
| **Growth** | $3,000-5,000/month | Mid-size funds ($500M-$5B AUM) |
| **Enterprise** | $10,000-25,000/month | Large funds ($5B+ AUM), fund-of-funds |

**What's Included:**
- Fully managed hosting (AWS/GCP)
- Automatic updates
- Daily backups
- Security patches
- Monitoring & alerting
- Support

**Margins:** 70-80% gross margin (hosting costs are low)

---

### Model 3: Enterprise Licenses + Services

For large institutions that want on-premise or private cloud.

| Revenue Stream | Price Range | Notes |
|----------------|-------------|-------|
| **Annual License** | $50K-200K/year | Based on users or AUM |
| **Implementation** | $25K-100K one-time | Setup, configuration, training |
| **Custom Integrations** | $10K-50K per connector | Bloomberg, Enfusion, Eze, internal systems |
| **Training** | $5K-15K | On-site or virtual |
| **Support Contract** | 15-20% of license/year | Ongoing support and updates |

**Example Enterprise Deal:**
- License: $100K/year
- Implementation: $50K
- 2 custom integrations: $40K
- Training: $10K
- **Year 1 Total: $200K**
- **Year 2+ Total: $120K/year** (license + support)

---

### Model 4: Premium Features (Upsell)

Features that justify premium pricing:

| Feature | Tier | Why They'd Pay |
|---------|------|----------------|
| **Correlation Framework** | Enterprise | Unique — no competitor has this |
| **Hedge Overlay Suggestions** | Enterprise | AI-powered, saves hours of analysis |
| **Regulatory Reporting** | Pro/Enterprise | CCAR, Basel, Form PF templates |
| **Real-time Streaming** | Enterprise | WebSocket, sub-second updates |
| **White-labeling** | Enterprise | Fund admins resell to their clients |
| **Advanced AI Queries** | Pro/Enterprise | Complex natural language analysis |
| **Stress Testing** | Enterprise | Crisis scenarios (2008, COVID) |
| **API Rate Limits** | Pro/Enterprise | Higher limits for heavy usage |

---

### Model 5: Marketplace / Ecosystem

Build a platform others extend.

| Revenue Stream | Model | Take Rate |
|----------------|-------|-----------|
| **Connector Marketplace** | Third parties build integrations | 20-30% |
| **Data Provider Partnerships** | Bloomberg/Refinitiv pay for distribution | Revenue share |
| **Fund Admin Partnerships** | They resell RISKCORE to clients | 30-40% to them |
| **Consulting Partner Network** | Implementation partners | Referral fees |

---

## Pricing Philosophy

### Value-Based Pricing

RISKCORE saves:
- **Time:** 10+ hours/week of manual spreadsheet work
- **Risk:** Catch concentration issues before they blow up
- **Headcount:** Don't need to hire a quant to build internal tools

**Pricing anchor:** If we save a $2B fund 1 basis point of losses, that's $200K/year. Our $25K license is cheap.

### Competitor Pricing Reference

| Competitor | Entry Price | Enterprise Price |
|------------|-------------|------------------|
| RiskVal | $75K+ | $300K+ |
| Imagine | $100K+ | $500K+ |
| Enfusion | $50K+ | $300K+ |
| Eze Eclipse | $75K+ | $400K+ |

**RISKCORE positioning:** 50-70% cheaper than incumbents, with unique features (correlation, AI).

---

## Go-To-Market Strategy

### Phase 1: Build & Launch (Months 1-6)

- Build MVP (open source)
- Publish to GitHub
- LinkedIn content series
- Get 100 GitHub stars
- First 5 beta users (free)

**Revenue: $0**

### Phase 2: Early Adopters (Months 6-12)

- Launch hosted SaaS
- Convert beta users to paid
- Target: 5-10 paying customers
- Price: $1-3K/month

**Revenue: $50-150K ARR**

### Phase 3: Growth (Year 2)

- Enterprise features (Correlation Framework)
- First enterprise deals
- Fund admin partnerships
- Target: 20-50 customers

**Revenue: $300K-1M ARR**

### Phase 4: Scale (Year 3+)

- Marketplace launch
- International expansion
- Strategic partnerships
- Target: 50-100+ customers

**Revenue: $1-3M+ ARR**

---

## Target Customers

### Primary Targets

| Segment | Size | Pain Point | Willingness to Pay |
|---------|------|------------|-------------------|
| Multi-manager HFs | $1B-$50B AUM | No cross-PM view | High |
| Fund-of-funds | $500M-$10B | Portfolio-level risk | High |
| Family offices | $100M-$5B | Multiple managers | Medium |
| Emerging managers | $50M-$500M | Can't afford Enfusion | Medium |

### Secondary Targets

| Segment | Opportunity |
|---------|-------------|
| Fund administrators | Resell to their clients |
| Prime brokers | Add to service offering |
| Outsourced CIO | Serve their clients |
| Prop trading firms | Multiple desk aggregation |

---

## Sales Strategy

### Self-Serve (Starter/Pro)

- Website signup
- Free trial (14 days)
- Credit card payment
- Automated onboarding
- Help docs + chat support

**Target:** <$5K/month deals

### Sales-Assisted (Growth/Enterprise)

- Demo request
- Discovery call
- Custom demo
- Proposal
- Negotiation
- Contract

**Target:** >$5K/month deals

### Channel Partners

- Fund administrators
- Prime brokers
- Consultants
- System integrators

**Model:** They sell, we deliver, revenue share

---

## Financial Projections

### Conservative Case

| Year | Customers | ARR | Notes |
|------|-----------|-----|-------|
| 1 | 5 | $75K | Beta + early adopters |
| 2 | 25 | $400K | SaaS growth |
| 3 | 60 | $1.2M | Enterprise deals |
| 4 | 100 | $2.5M | Channel partnerships |
| 5 | 150 | $4M | Market expansion |

### Optimistic Case

| Year | Customers | ARR | Notes |
|------|-----------|-----|-------|
| 1 | 10 | $150K | Strong launch |
| 2 | 50 | $1M | Viral growth |
| 3 | 120 | $3M | Enterprise momentum |
| 4 | 200 | $6M | Market leader |
| 5 | 300 | $10M | Platform ecosystem |

---

## Exit Opportunities

### Strategic Acquisition

| Potential Acquirer | Why They'd Buy | Estimated Value |
|--------------------|----------------|-----------------|
| SS&C | Add to Eze/Geneva suite | $10-50M |
| Enfusion | Competitive threat | $10-30M |
| Bloomberg | Expand PORT offering | $20-100M |
| State Street | Add to Alpha platform | $20-50M |
| Clearwater | Post-Enfusion acquisition | $15-40M |

**Valuation basis:** 5-10x ARR for strategic, higher for competitive/defensive

### Private Equity

- Roll-up into financial software portfolio
- Typical: 4-8x ARR
- Requires: $2M+ ARR, growth trajectory

### IPO (Unlikely but Possible)

- Requires: $20M+ ARR, 30%+ growth
- Comparable: nCino, Q2 Holdings, Clearwater Analytics

### Lifestyle Business

- Stay private, profitable
- $2-5M ARR, 70% margins
- Owner salary + distributions: $1-2M/year

---

## Competitive Moat

### What Makes RISKCORE Defensible

| Moat | Description |
|------|-------------|
| **Open Source Community** | Contributors, ecosystem, brand loyalty |
| **Correlation Framework** | Unique feature, no competitor has |
| **AI Integration** | Natural language risk queries |
| **Network Effects** | More users → more integrations → more users |
| **Switching Costs** | Data, workflows, training invested |
| **Brand/Thought Leadership** | LinkedIn presence, industry recognition |

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Incumbent builds similar | Medium | High | Move fast, build community |
| Open source fork competes | Low | Medium | Better support, enterprise features |
| Sales cycle too long | High | Medium | Self-serve tier, content marketing |
| Technical challenges | Medium | Medium | Use proven libraries, hire experts |
| Market too small | Low | High | Expand to adjacent segments |

---

## Key Metrics to Track

| Metric | Target (Year 1) | Target (Year 3) |
|--------|-----------------|-----------------|
| GitHub Stars | 500 | 5,000 |
| Monthly Active Users | 50 | 500 |
| Paying Customers | 5 | 60 |
| ARR | $75K | $1.2M |
| Net Revenue Retention | N/A | 120%+ |
| CAC Payback | <12 months | <6 months |
| Gross Margin | 70% | 80% |

---

## The Real Monetization

**Honest assessment:** The most likely outcomes are:

1. **Acqui-hire (40%)** — Big vendor buys for team + tech ($5-20M)
2. **Strategic acquisition (30%)** — Competitor buys to eliminate threat ($10-50M)
3. **Sustainable SaaS (20%)** — Build to $2-5M ARR, profitable lifestyle business
4. **Big exit (10%)** — Rapid growth to $50M+ exit

**Regardless of outcome:** The open-source visibility + LinkedIn thought leadership makes **Massimo** highly valuable. Even if RISKCORE doesn't become a huge business, it positions him for:
- Board roles
- Advisory positions
- Speaking engagements
- Executive roles at larger firms
- Consulting opportunities ($500-1,000/hour)

---

## Next Steps

1. **Build MVP** — Prove the product works
2. **Get beta users** — Prove people want it
3. **Publish content** — Build audience and credibility
4. **Launch SaaS** — Prove people will pay
5. **Iterate** — Find product-market fit
6. **Scale or exit** — Based on traction and opportunities

---

*Business model strategy for RISKCORE*
