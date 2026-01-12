# RISKCORE User Guide for Chief Risk Officers

> Your complete guide to firm-wide risk visibility
> **Audience:** CROs, Risk Managers, Risk Analysts
> **Last Updated:** 2026-01-12

---

## Why RISKCORE?

As a CRO at a multi-manager fund, you face a unique challenge: **aggregating risk across PMs who use different systems, strategies, and workflows.**

RISKCORE solves this by:
- **Consolidating positions** from any source into one view
- **Detecting hidden correlations** between PMs
- **Identifying overlapping positions** that create concentration risk
- **Calculating firm-wide VaR** with cross-PM diversification benefits
- **Providing real-time visibility** without disrupting PM workflows

---

## Getting Started

### First Login

1. Navigate to `https://riskcore.yourfirm.internal`
2. Enter your email and password
3. Select your firm (tenant) if prompted
4. You'll land on the **Firm Dashboard**

### Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     RISKCORE DASHBOARD                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ FIRM GROSS    │  │ FIRM NET      │  │ FIRM VaR      │       │
│  │ $1.3B         │  │ $725M         │  │ $12.5M (95%)  │       │
│  │ ▲ 2.3%        │  │ ▼ 1.1%        │  │ ▲ 0.8%        │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ PM EXPOSURE BREAKDOWN                                   │    │
│  │ ████████████████████████░░░░ Smith    $320M  24.6%     │    │
│  │ ██████████████████░░░░░░░░░░ Jones    $250M  19.2%     │    │
│  │ ████████████████░░░░░░░░░░░░ Davis    $220M  16.9%     │    │
│  │ ██████████████░░░░░░░░░░░░░░ Wilson   $180M  13.8%     │    │
│  │ ████████████░░░░░░░░░░░░░░░░ Others   $330M  25.5%     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ HIGH CORRELATIONS   │  │ OVERLAPPING POSITIONS│              │
│  │ Smith↔Jones: 0.73   │  │ AAPL: 5 PMs ($45M)  │              │
│  │ Davis↔Wilson: 0.68  │  │ NVDA: 4 PMs ($38M)  │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. Firm-Wide Summary

**What it shows:**
- Total gross exposure across all PMs
- Net exposure (after cross-PM netting)
- Netting efficiency percentage
- Firm VaR at 95% and 99% confidence

**Why it matters:**
- Gross tells you total capital at risk
- Net shows your actual directional exposure
- Netting efficiency shows diversification benefit

**API Access:**
```
GET /api/v1/aggregation/firm/summary?tenant_id={your_tenant_id}
```

---

### 2. Cross-PM Correlation Matrix

**What it shows:**
A heatmap of realized correlations between every PM pair.

```
          Smith   Jones   Davis   Wilson   Chen
Smith     1.00    0.73    0.45    0.12   -0.08
Jones     0.73    1.00    0.38    0.22    0.15
Davis     0.45    0.38    1.00    0.68    0.31
Wilson    0.12    0.22    0.68    1.00    0.41
Chen     -0.08    0.15    0.31    0.41    1.00
```

**Color coding:**
- 🔴 Red (>0.7): High correlation - concentration risk
- 🟡 Yellow (0.4-0.7): Moderate correlation - monitor
- 🟢 Green (<0.4): Low correlation - diversified
- 🔵 Blue (<0): Negative correlation - natural hedge

**Why it matters:**
- High correlation = if one PM loses, others likely lose too
- Negative correlation = natural offset, reduces firm VaR

**How to use:**
1. Sort by highest correlation pairs
2. Investigate why Smith and Jones are 0.73 correlated
3. Decide if this is intentional or accidental concentration

**API Access:**
```
GET /api/v1/correlation/pm/matrix?tenant_id={id}&window=21d
```

---

### 3. Overlap Detection

**What it shows:**
Securities held by multiple PMs with their combined exposure.

| Security | # PMs | Long Exposure | Short Exposure | Net | Type |
|----------|-------|---------------|----------------|-----|------|
| AAPL | 5 | $38M | $7M | $31M Long | Concentration |
| NVDA | 4 | $25M | $13M | $12M Long | Netting Opp. |
| TSLA | 3 | $0M | $22M | $22M Short | Concentration |
| META | 6 | $18M | $19M | $1M | Offset |

**Overlap Types:**
- **Concentration Risk:** Same direction, amplifies losses
- **Netting Opportunity:** Opposing directions, could net to reduce risk
- **Natural Offset:** Already balanced, low firm-level risk

**Why it matters:**
- Multiple PMs holding same stock = hidden concentration
- You may be paying for "diversification" but getting correlation

**Actions to take:**
1. Review concentration risks with relevant PMs
2. Consider netting opportunities for margin efficiency
3. Set limits on firm-wide single-name exposure

**API Access:**
```
GET /api/v1/aggregation/overlaps?tenant_id={id}&severity=high
```

---

### 4. Netting Analysis

**What it shows:**
How much risk reduction you get from offsetting positions.

**Example:**
```
Gross Exposure:   $1,300,000,000
Net Exposure:     $  725,000,000
────────────────────────────────
Netting Benefit:  $  575,000,000
Efficiency:       44.2%
```

**By PM contribution:**

| PM | Gross | Contribution to Netting | Net Impact |
|----|-------|------------------------|------------|
| Smith | $320M | -$85M | Adds correlation |
| Jones | $250M | +$120M | Provides offset |
| Davis | $220M | +$45M | Provides offset |

**Why it matters:**
- High netting efficiency = good diversification
- Low efficiency = PMs are trading in same direction (intentional?)

**API Access:**
```
GET /api/v1/aggregation/netting/summary?tenant_id={id}
```

---

### 5. PM Drill-Down

Click on any PM to see their individual risk profile:

**PM Summary Card:**
```
┌─────────────────────────────────────────┐
│ PM: Sarah Smith                         │
│ Strategy: L/S Equity - Tech Focus       │
├─────────────────────────────────────────┤
│ Gross Exposure: $320M                   │
│ Net Exposure: $180M (56% long)          │
│ VaR (95%, 1d): $3.2M                    │
├─────────────────────────────────────────┤
│ Top Holdings:                           │
│   AAPL  $45M  14.1%                     │
│   NVDA  $38M  11.9%                     │
│   GOOGL $32M  10.0%                     │
├─────────────────────────────────────────┤
│ Sector Breakdown:                       │
│   Tech: 68%  Healthcare: 15%  Fin: 12%  │
├─────────────────────────────────────────┤
│ Correlation with Firm: 0.72             │
│ Overlaps with Other PMs: 8 securities   │
└─────────────────────────────────────────┘
```

**Why it matters:**
- Understand each PM's contribution to firm risk
- Identify PMs who are highly correlated with the firm
- Spot concentrated positions

---

### 6. RiskPod View

Group risk by asset class "pod" for a different perspective:

| RiskPod | Gross | VaR | Key Metric |
|---------|-------|-----|------------|
| **Equity** | $850M | $8.5M | Beta: 1.2 |
| **Rates** | $280M | $2.1M | DV01: $45K |
| **Credit** | $120M | $1.8M | CS01: $32K |
| **FX** | $35M | $0.4M | EUR: 60% |
| **Other** | $15M | $0.2M | - |

**Firm VaR Decomposition:**
```
Sum of Pod VaRs:     $13.0M
Diversification:     -$0.5M
Firm VaR (corr-adj): $12.5M
```

**Why it matters:**
- See risk by asset class, not just by PM
- Understand cross-asset diversification benefit
- Identify which pod is driving most risk

---

## Common Workflows

### Morning Risk Check (5 minutes)

1. Open Firm Dashboard
2. Check firm VaR vs. yesterday - any big changes?
3. Scan high correlation pairs - anyone new?
4. Review overlaps - any new concentrations?
5. Check PM exposure breakdown - anyone outsized?

### Investigating High Correlation

**Scenario:** You notice Smith and Jones have 0.73 correlation

1. Click on Smith↔Jones correlation pair
2. View their shared holdings (overlaps)
3. View their RiskPod exposure similarity
4. Check implied correlation (forward-looking) vs realized
5. Decide: Is this intentional? Talk to PMs?

### Setting Limits

1. Go to **Settings → Limits**
2. Configure:
   - Max single PM gross exposure: $500M
   - Max firm VaR: $20M
   - Max PM correlation: 0.7
   - Max single-name concentration: 5%
3. Enable alerts for breaches

### Stress Testing (Future Feature)

1. Select stress scenario (2008 Crisis, March 2020, Custom)
2. View firm P&L under scenario
3. See which PMs contribute most to loss
4. Identify hedging needs

---

## Reading the Data

### Correlation Interpretation

| Range | Meaning | Action |
|-------|---------|--------|
| 0.9-1.0 | Near identical | Immediate review |
| 0.7-0.9 | High | Monitor closely |
| 0.4-0.7 | Moderate | Normal for related strategies |
| 0.0-0.4 | Low | Good diversification |
| <0 | Negative | Natural hedge |

### VaR Interpretation

| VaR Type | What It Means |
|----------|---------------|
| VaR 95% | You expect to lose more than this 1 in 20 days |
| VaR 99% | You expect to lose more than this 1 in 100 days |
| CVaR (ES) | Average loss when VaR is breached |

### Overlap Severity

| Severity | Criteria | Action |
|----------|----------|--------|
| **High** | 4+ PMs, >$50M | Immediate review |
| **Medium** | 2-3 PMs, $20-50M | Monitor |
| **Low** | 2 PMs, <$20M | Informational |

---

## Best Practices

### Daily

- [ ] Check firm VaR change from prior day
- [ ] Review any new high correlation alerts
- [ ] Scan top 10 overlapping positions

### Weekly

- [ ] Review full PM correlation matrix
- [ ] Check netting efficiency trend
- [ ] Meet with PMs showing high firm correlation

### Monthly

- [ ] Full overlap analysis with PM team
- [ ] Review and adjust risk limits
- [ ] Analyze correlation trends over time

### Quarterly

- [ ] Stress test firm portfolio
- [ ] Present risk report to investment committee
- [ ] Review and update risk policies

---

## Alerts & Notifications

Configure alerts for:

| Alert Type | Trigger | Priority |
|------------|---------|----------|
| Correlation Spike | PM pair > 0.7 | High |
| VaR Breach | Firm VaR > limit | Critical |
| Concentration | Single name > 5% | High |
| New Overlap | 3+ PMs on same name | Medium |
| Data Stale | No update in 4 hours | Medium |

**Notification channels:**
- In-app notification bell
- Email digest (configurable)
- Slack integration (Enterprise)

---

## Glossary

| Term | Definition |
|------|------------|
| **Gross Exposure** | Sum of absolute values of all positions |
| **Net Exposure** | Long minus short (directional) |
| **Netting** | Offsetting long vs. short in same security across PMs |
| **Overlap** | Same security held by multiple PMs |
| **VaR** | Value at Risk - max expected loss at confidence level |
| **CVaR** | Conditional VaR - average loss beyond VaR |
| **Correlation** | Statistical measure of how PMs move together |
| **RiskPod** | Asset class grouping (Equity, Rates, Credit, FX, Other) |
| **DV01** | Dollar change per 1bp rate move |
| **CS01** | Dollar change per 1bp spread move |

---

## Getting Help

### Support

- **In-app:** Click "?" for contextual help
- **Email:** risk-support@yourfirm.internal
- **Documentation:** This guide + API docs at `/docs`

### Common Issues

| Issue | Solution |
|-------|----------|
| Data not updating | Check PM upload status |
| Correlation looks wrong | Verify return data quality |
| PM missing | Ensure PM has positions uploaded |
| VaR seems high | Check for outlier positions |

---

*Questions? Contact your RISKCORE administrator or risk technology team.*
