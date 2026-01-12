# RISKCORE Integration Research: Professional Trading Systems

> Market research on OMS/EMS/PMS systems used by multi-manager hedge funds
> **Last Updated:** 2026-01-12
> **Purpose:** Prioritize integrations for RISKCORE Phase 2

---

## Executive Summary

The multi-manager hedge fund industry manages **$428B AUM** (2025) across firms like Millennium, Citadel, Point72, and Balyasny. The largest funds (150-200 PMs each) typically build proprietary systems in-house, while Tier 2/3 funds use commercial platforms.

**Key finding:** Most commercial systems support FIX protocol and offer REST APIs, making RISKCORE integration feasible. Priority should be given to systems with public APIs and large market share.

---

## Market Landscape

### Tier 1: Mega Multi-Managers (Build In-House)

| Firm | AUM | Staff | Tech Approach |
|------|-----|-------|---------------|
| Millennium | $83.5B | 5,000+ | Proprietary systems |
| Citadel | $72B | ~3,000 | Proprietary (best tech reputation) |
| Point72 | $35B+ | ~3,000 | Proprietary systems |
| Balyasny | $31B | ~2,000 | Proprietary systems |
| D.E. Shaw | $60B+ | ~2,500 | Proprietary (quant focus) |

**RISKCORE opportunity:** These firms won't use external platforms, BUT they have multiple PMs who may use different booking systems. Central risk teams could use RISKCORE as an aggregation overlay.

### Tier 2/3: Mid-Size Hedge Funds (Use Commercial Systems)

These funds use commercial OMS/EMS/PMS platforms and are the primary target market.

---

## Commercial Platform Analysis

### 1. SS&C Eze (Eclipse)

**Market Position:** Industry leader for hedge fund OMS/EMS

| Attribute | Details |
|-----------|---------|
| **Products** | Eze OMS, Eze EMS, Eze PMA, Eclipse (combined) |
| **Target Market** | Hedge funds (all sizes), asset managers |
| **Strength** | Trading, multi-asset, fixed income |
| **FIX Support** | Yes - native |
| **API** | REST API available |
| **Integration** | Bloomberg, Tradeweb connectivity |

**RISKCORE Integration Path:**
- FIX protocol for trade/position feeds
- REST API for position snapshots
- File export (CSV/Excel) as fallback

**Complexity:** Medium - requires SS&C relationship

---

### 2. Enfusion

**Market Position:** Leading cloud-native platform for hedge funds

| Attribute | Details |
|-----------|---------|
| **Ownership** | Acquired by Clearwater Analytics (April 2025) |
| **Products** | Unified front-to-back SaaS platform |
| **Target Market** | Hedge funds (L/S equity, macro, credit) |
| **Strength** | Cloud-native, single source of truth |
| **FIX Support** | Yes - 300+ liquidity sources |
| **API** | REST APIs, real-time data feeds |
| **Integration** | Prime brokers, custodians, fund admins |

**RISKCORE Integration Path:**
- REST API (client access required)
- FIX protocol for execution data
- Direct connectivity via partnership

**Complexity:** Medium - requires Enfusion partnership

---

### 3. BlackRock Aladdin

**Market Position:** Dominant institutional platform ($21.6T AUM on platform)

| Attribute | Details |
|-----------|---------|
| **Products** | Full investment management platform |
| **Target Market** | Large asset managers, pension funds, some hedge funds |
| **Strength** | Risk analytics, scale, ecosystem |
| **FIX Support** | Yes |
| **API** | Aladdin Studio REST APIs (read/write) |
| **Tech Stack** | Java, Kubernetes, Snowflake, Azure |

**RISKCORE Integration Path:**
- Aladdin Studio REST APIs
- File exports
- FIX for trade data

**Complexity:** High - requires BlackRock relationship, expensive

---

### 4. Charles River IMS (State Street)

**Market Position:** Leading institutional OMS

| Attribute | Details |
|-----------|---------|
| **Products** | Charles River Investment Management Solution |
| **Target Market** | Institutional investors, large asset managers |
| **Strength** | Compliance, multi-asset trading |
| **FIX Support** | Yes - native |
| **API** | REST APIs for order/portfolio management |

**RISKCORE Integration Path:**
- FIX protocol
- REST APIs
- SWIFT messaging

**Complexity:** High - enterprise sales cycle

---

### 5. Bloomberg AIM/EMSX

**Market Position:** Industry standard for Bloomberg Terminal users

| Attribute | Details |
|-----------|---------|
| **Products** | AIM (Asset & Investment Manager), EMSX (EMS) |
| **Target Market** | Anyone with Bloomberg Terminal |
| **Strength** | Market data integration, liquidity |
| **FIX Support** | Yes |
| **API** | BLPAPI (requires Terminal license) |

**RISKCORE Integration Path:**
- BLPAPI (requires Bloomberg Terminal)
- FIX protocol
- File export to CSV

**Complexity:** Medium - requires Terminal access ($24K/year/user)

---

### 6. Other Notable Platforms

| Platform | Owner | Target | FIX | API | Notes |
|----------|-------|--------|-----|-----|-------|
| SimCorp Dimension | SimCorp | Large AM | Yes | REST | Enterprise |
| Advent Geneva/APX | SS&C | Asset managers | Yes | REST | Back-office |
| FactSet | FactSet | Research + PM | Yes | REST | Data strength |
| FlexTrade FlexONE | FlexTrade | Quant funds | Yes | REST | Execution focus |
| TS Imagine | TS Imagine | Active traders | Yes | REST | Risk analytics |
| Murex | Murex | Derivatives | Yes | API | Complex products |
| Calypso | Calypso | Capital markets | Yes | API | Derivatives |

---

## Prime Broker Technology

Prime brokers provide their own technology platforms:

| Prime Broker | Platform | Capabilities |
|--------------|----------|--------------|
| **Goldman Sachs** | Marquee | APIs, analytics, execution, research |
| **Morgan Stanley** | Matrix | Portfolio analytics, risk, reporting |
| **JP Morgan** | Execute | Trading, settlement, APIs |
| **UBS** | Neo | Prime services platform |

**Integration opportunity:** PBs expose position/balance data via APIs. Could pull position snapshots for reconciliation.

---

## Integration Methods Summary

### Method 1: FIX Protocol (Highest Priority)

**Pros:**
- Industry standard
- Real-time trade/position data
- Supported by all major platforms
- No vendor relationship needed

**Cons:**
- Complex to implement correctly
- Requires FIX engine
- May need certification

**RISKCORE Status:** Basic parsing implemented (simplefix). Need full FIX engine for production.

---

### Method 2: REST APIs

**Pros:**
- Modern, well-documented
- Easy to implement
- Supports all operations

**Cons:**
- Requires vendor partnership/access
- Rate limits
- Authentication complexity

**RISKCORE Status:** Ready to integrate (httpx/requests)

---

### Method 3: File-Based (CSV/Excel/SFTP)

**Pros:**
- Universal compatibility
- Simple implementation
- Works with any system

**Cons:**
- Not real-time
- Manual process
- Error-prone

**RISKCORE Status:** Fully implemented (Week 2)

---

### Method 4: Google Sheets

**Pros:**
- Free for solo traders
- Easy to use
- Real-time(ish)

**Cons:**
- Limited to small portfolios
- Requires public sharing

**RISKCORE Status:** Just implemented (this session)

---

## Recommended Integration Roadmap

### Phase 1: MVP (Current - Weeks 1-6)

| Method | Status | Priority |
|--------|--------|----------|
| CSV/Excel Upload | ✅ Done | HIGH |
| FIX Protocol (basic) | ✅ Done | HIGH |
| REST API (JSON) | ✅ Done | HIGH |
| Google Sheets | ✅ Done | HIGH |

### Phase 2: Commercial Integrations (Weeks 7-12)

| Integration | Priority | Effort | Notes |
|-------------|----------|--------|-------|
| **Enfusion API** | HIGH | Medium | Large market share, cloud-native |
| **SS&C Eze API** | HIGH | Medium | Industry leader |
| **Full FIX Engine** | HIGH | High | QuickFIX/C upgrade |
| Bloomberg EMSX | MEDIUM | Medium | Requires Terminal |

### Phase 3: Enterprise Integrations (Months 4-6)

| Integration | Priority | Effort | Notes |
|-------------|----------|--------|-------|
| BlackRock Aladdin | MEDIUM | High | Large institutional |
| Charles River IMS | MEDIUM | High | State Street partnership |
| Prime Broker APIs | MEDIUM | Medium | Goldman, Morgan Stanley |
| SimCorp Dimension | LOW | High | Enterprise only |

---

## Technical Requirements

### For Enfusion Integration

```python
# Pseudo-code for Enfusion REST API
class EnfusionClient:
    BASE_URL = "https://api.enfusion.com/v1"

    def get_positions(self, portfolio_id: str) -> List[Position]:
        """Fetch positions from Enfusion."""
        response = self.session.get(
            f"{self.BASE_URL}/portfolios/{portfolio_id}/positions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return [Position(**p) for p in response.json()]
```

### For Full FIX Engine

```python
# Upgrade from simplefix to QuickFIX/C
# Would support:
# - Logon/Logout
# - Heartbeat/TestRequest
# - ExecutionReport streaming
# - PositionReport requests
# - Batch position downloads
```

---

## Next Steps

1. **Get user input** on which systems their target clients use
2. **Contact Enfusion** for partnership/API access
3. **Contact SS&C Eze** for integration documentation
4. **Evaluate QuickFIX** for full FIX engine upgrade
5. **Build adapter framework** for pluggable integrations

---

## Sources

- [Top Portfolio Asset Management Software 2025 - Limina](https://www.limina.com/blog/best-portfolio-asset-management-software)
- [Enfusion Competitors and Alternatives - Limina](https://www.limina.com/enfusion)
- [Top Asset Management Systems 2025 - FinTech4Funds](https://fintech4funds.com/asset-management-systems-2025/)
- [How Millennium, Citadel & Point72 Structure Pods](https://navnoorbawa.substack.com/p/how-millennium-citadel-and-point72)
- [SS&C Eze Eclipse - Official](https://www.ezesoft.com/)
- [BlackRock Aladdin APIs](https://www.blackrock.com/aladdin/products/apis)
- [BlackRock Aladdin Overview](https://www.blackrock.com/aladdin)
- [Enfusion Connectivity & APIs](https://www.enfusion.com/connectivity-data-and-apis/)
- [Enfusion for Hedge Funds](https://www.enfusion.com/for-hedge-funds/)
- [Cutter Associates OMS Research](https://www.cutterassociates.com/insights/order-management-systems)
- [Hedge Fund Technology Jobs - eFinancialCareers](https://www.efinancialcareers.com/news/2021/04/technology-jobs-hedge-funds)

---

## Questions for User's Contact

When speaking with your friend in the industry, consider asking:

1. **What OMS/EMS does your firm actually use day-to-day?**
2. **How do PMs currently export/share position data with central risk?**
3. **What's the biggest pain point in aggregating risk across PMs?**
4. **Would your firm consider an external risk aggregation tool?**
5. **What file formats/protocols does your current system support?**
6. **How often do you need position updates (real-time, EOD, intraday)?**

---

*This document should be updated after gathering feedback from industry contacts.*
