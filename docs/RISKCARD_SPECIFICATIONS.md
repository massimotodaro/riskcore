# RiskCard Specifications

> Definitive reference for all RiskCard designs, sub-categories, anchors, and metrics.
> **Last Updated:** 2026-01-13
> **Status:** APPROVED

---

## Overview

RISKCORE displays risk through **6 RiskCards**, each representing a major asset class. Each RiskCard is subdivided into **sub-categories** that map to specific **Anchor instruments** for correlation and hedging calculations.

### Core Principles

1. **Every instrument maps to exactly one Anchor** within its asset class
2. **Anchors are always on-the-run futures** (front-month, most liquid)
3. **Rolling correlations** calculated at 1-week, 1-month, and 3-month windows
4. **Zero Hedge (0Hedge)** = theoretical notional to neutralize exposure using 1-month correlation
5. **Info popouts (ⓘ)** explain every metric and sub-category
6. **Trades button** in top-right corner for drill-down to underlying positions

---

## RiskCard Layout (Universal Structure)

```
┌─────────────────────────────────────────────────────────────────┐
│  [ASSET CLASS]                          [▲/▼ %]   [⛶] [Trades] │
│  ─────────────────────────────────────────────────────────────  │
│  [PRIMARY METRIC] (Primary)                                     │
│  [VALUE]                                                        │
│  [████████████████████░░░░░░░░░░░░░░] progress bar             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ [METRIC 2]  │  │ [METRIC 3]  │  │ [METRIC 4]  │             │
│  │   [value]   │  │   [value]   │  │   [value]   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │     %ⓘ    [M1]ⓘ   [M2]ⓘ   [M3]ⓘ   CORR.ⓘ   0HEDGEⓘ     │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ [Sub-Cat 1]ⓘ  │  val  │  val  │  val  │  0.XX  │  $XXM   │ │
│  │ [Sub-Cat 2]ⓘ  │  val  │  val  │  val  │  0.XX  │  $XXM   │ │
│  │ [Sub-Cat 3]ⓘ  │  val  │  val  │  val  │  0.XX  │  $XXM   │ │
│  │ [Sub-Cat 4]ⓘ  │  val  │  val  │  val  │  0.XX  │  $XXM   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  CONCENTRATIONⓘ      VAR (95%)ⓘ         CVAR (95%)ⓘ           │
│  Top 10: XX%         $X.XM               $X.XM                  │
│                                                                 │
│  Positions: XXX      Gross: $XXXM        Net: $XXXM             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. EQUITY RiskCard

### Primary Metric: **DELTA**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| GAMMA | Convexity of delta (options) |
| VEGA | Volatility sensitivity (options) |
| BETA | Portfolio beta to market |

### Sub-Categories & Anchors

| Sub-Category | Includes | Anchor | Symbol | Info Popout |
|--------------|----------|--------|--------|-------------|
| **US** | United States, Canada | S&P 500 E-mini Future | ES | "United States and Canadian equities. Anchor: S&P 500 E-mini (ES)" |
| **Europe** | EU, UK, Switzerland | Euro STOXX 50 Future | FESX | "European equities including UK and Switzerland. Anchor: Euro STOXX 50 (FESX)" |
| **Japan** | Japan | Nikkei 225 Mini Future | NKM | "Japanese equities. Anchor: Nikkei 225 Mini (NKM)" |
| **RoW** | All other (EM, APAC ex-Japan, LATAM, Africa) | MSCI EM ETF | EEM | "Rest of World: Emerging Markets, APAC ex-Japan, LATAM, Africa. Anchor: MSCI EM ETF (EEM)" |

### Table Columns
| % | DELTA | BETA | GAMMA | CORR. | 0HEDGE |
|---|-------|------|-------|-------|--------|

### Info Popouts
- **%**: "Percentage of total equity exposure in this geography"
- **DELTA**: "Dollar delta - price sensitivity to 1% move in underlying"
- **BETA**: "Sensitivity to the Anchor index. Beta > 1 = more volatile than market"
- **GAMMA**: "Rate of change of delta. Higher gamma = delta changes faster"
- **CORR.**: "1-month rolling correlation to Anchor. Range: -1 to +1"
- **0HEDGE**: "Notional of Anchor to trade for theoretical zero exposure. Formula: Exposure × Beta × -1"
- **VAR (95%)**: "Value at Risk - maximum expected loss over 1 day with 95% confidence"
- **CVAR (95%)**: "Conditional VaR - expected loss when VaR is exceeded (tail risk)"

---

## 2. RATES RiskCard

### Primary Metric: **DV01**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| DURATION | Modified duration (price sensitivity to rate changes) |
| CONVEXITY | Second-order sensitivity (curvature) |
| YIELD | Weighted average yield to maturity |

### Sub-Categories & Anchors

| Sub-Category | Tenor Range | Anchor | Symbol | Info Popout |
|--------------|-------------|--------|--------|-------------|
| **2Y** | 0-3 years | 2-Year T-Note Future | ZT | "Short duration bonds (0-3 years). Anchor: 2-Year Treasury Note Future (ZT)" |
| **5Y** | 3-7 years | 5-Year T-Note Future | ZF | "Medium duration bonds (3-7 years). Anchor: 5-Year Treasury Note Future (ZF)" |
| **10Y** | 7-15 years | 10-Year T-Note Future | ZN | "Long duration bonds (7-15 years). Anchor: 10-Year Treasury Note Future (ZN)" |
| **30Y** | 15+ years | Ultra Bond Future | UB | "Ultra-long duration bonds (15+ years). Anchor: Ultra Bond Future (UB)" |

**Note:** ALL sovereign bonds (US Treasuries, UK Gilts, German Bunds, Italian BTPs, JGBs) map to US Treasury anchors by duration. Cross-currency basis risk captured in correlation.

### Table Columns
| % | DV01 | DURATION | CONVEXITY | CORR. | 0HEDGE |
|---|------|----------|-----------|-------|--------|

### Info Popouts
- **DV01**: "Dollar Value of 01 - P&L from 1 basis point move in rates"
- **DURATION**: "Modified duration in years. Higher = more rate sensitive"
- **CONVEXITY**: "Curvature adjustment for large rate moves"

---

## 3. CREDIT RiskCard

### Primary Metric: **CS01**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| CREDIT DUR | Credit spread duration |
| DEFAULT PD | Probability of default (weighted average) |
| RECOVERY | Recovery rate assumption (LGD = 1 - Recovery) |

### Sub-Categories & Anchors

| Sub-Category | Rating Range | Anchor | Symbol | 0HEDGE? | Info Popout |
|--------------|--------------|--------|--------|---------|-------------|
| **AAA-AA** | AAA, AA+, AA, AA- | CDX NA Investment Grade | CDX.NA.IG | ✅ Yes | "Highest quality investment grade. Anchor: CDX NA IG Index" |
| **A** | A+, A, A- | CDX NA Investment Grade | CDX.NA.IG | ✅ Yes | "Upper-medium investment grade. Anchor: CDX NA IG Index" |
| **BBB** | BBB+, BBB, BBB- | CDX NA Investment Grade | CDX.NA.IG | ✅ Yes | "Lower investment grade (crossover risk). Anchor: CDX NA IG Index" |
| **HY** | BB+, BB, BB-, B+, B, B- | CDX NA High Yield | CDX.NA.HY | ✅ Yes | "High Yield (BB to B-). Anchor: CDX NA HY Index" |
| **Distressed** | CCC+, CCC, CCC-, CC, C, D | CDX NA High Yield | CDX.NA.HY | ❌ N/A | "Distressed credit (CCC and below). Idiosyncratic risk dominant - no market hedge recommended. Focus on PD/LGD." |

### Table Columns
| % | CS01 | PD | LGD | CORR. | 0HEDGE |
|---|------|-----|-----|-------|--------|

### Info Popouts
- **CS01**: "Credit Spread 01 - P&L from 1 basis point move in credit spreads"
- **PD**: "Probability of Default - likelihood of issuer default within 1 year"
- **LGD**: "Loss Given Default - expected loss if default occurs (1 - Recovery Rate)"
- **Distressed 0HEDGE**: "N/A - Idiosyncratic risk dominant. Market hedges ineffective for CCC and below."

---

## 4. COMMODITIES RiskCard

### Primary Metric: **NET EXPOSURE**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| PRICE SENS | Dollar P&L per 1% price move |
| BASIS RISK | Spot-futures spread exposure |
| ROLL YIELD | Contango/backwardation impact |

### Sub-Categories & Anchors

| Sub-Category | Instruments | Anchor | Symbol | Info Popout |
|--------------|-------------|--------|--------|-------------|
| **Crude** | WTI, Brent, heating oil, gasoline, jet fuel | WTI Crude Future | CL | "Energy/petroleum products. Anchor: WTI Crude Oil Future (CL)" |
| **Gold** | Gold, silver, platinum, palladium | Gold Future | GC | "Precious metals. Anchor: Gold Future (GC)" |
| **NatGas** | Natural gas, LNG | Natural Gas Future | NG | "Natural gas and LNG. Anchor: Natural Gas Future (NG)" |
| **Copper** | Copper, aluminum, zinc, nickel, lead | Copper Future | HG | "Base/industrial metals. Anchor: Copper Future (HG)" |
| **Other** | Agriculture, softs, livestock | Bloomberg Commodity Index | BCOM | "Agricultural commodities, softs, livestock. Anchor: Bloomberg Commodity Index (BCOM)" |

### Table Columns
| % | EXPOSURE | PRICE SENS | BASIS | CORR. | 0HEDGE |
|---|----------|------------|-------|-------|--------|

---

## 5. FX RiskCard

### Primary Metric: **FX DELTA**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| FX VEGA | FX option volatility sensitivity |
| BASIS PTS | Forward basis point exposure |

### Sub-Categories & Anchors

| Sub-Category | Currencies | Anchor | Symbol | Info Popout |
|--------------|------------|--------|--------|-------------|
| **EUR** | EUR/USD, EUR/GBP, EUR/CHF, EUR/JPY | Euro FX Future | 6E | "Euro-denominated FX exposure. Anchor: Euro FX Future (6E)" |
| **JPY** | USD/JPY, EUR/JPY, GBP/JPY | Japanese Yen Future | 6J | "Japanese Yen exposure. Anchor: Japanese Yen Future (6J)" |
| **GBP** | GBP/USD, GBP/EUR | British Pound Future | 6B | "British Pound exposure. Anchor: British Pound Future (6B)" |
| **Crypto** | BTC, ETH, all cryptocurrencies | Bitcoin Future | BTC | "Cryptocurrency exposure. Anchor: CME Bitcoin Future (BTC)" |
| **Other** | AUD, CHF, CAD, EM currencies, other | US Dollar Index | DX | "Other currencies (AUD, CHF, CAD, EM). Anchor: US Dollar Index (DX)" |

### Table Columns
| % | FX DELTA | FX VEGA | BASIS | CORR. | 0HEDGE |
|---|----------|---------|-------|-------|--------|

---

## 6. OTHER RiskCard

### Primary Metric: **NET EXPOSURE**

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| PRICE SENS | Dollar P&L per unit move |
| VOL SENS | Volatility sensitivity |

### Sub-Categories & Anchors

| Sub-Category | Instruments | Anchor | Symbol | Info Popout |
|--------------|-------------|--------|--------|-------------|
| **Volatility** | VIX products, variance swaps, vol swaps | VIX Future | VX | "Volatility products. Anchor: VIX Future (VX)" |
| **Structured** | Exotic derivatives, structured notes | S&P 500 E-mini | ES | "Structured products. Anchor: S&P 500 E-mini (ES) - default equity beta" |
| **Unclassified** | Cannot be categorized | Manual | — | "Unclassified instruments require manual anchor assignment" |

### Table Columns
| % | EXPOSURE | PRICE SENS | VOL SENS | CORR. | 0HEDGE |
|---|----------|------------|----------|-------|--------|

---

## Anchor Contract Rolling

### On-the-Run Contract Rule

**Anchors are ALWAYS the front-month (most liquid) futures contract.**

| Contract | Roll Schedule | Roll Window |
|----------|---------------|-------------|
| ES, NQ, FESX | Quarterly (Mar, Jun, Sep, Dec) | 8 days before expiry |
| ZT, ZF, ZN, UB | Quarterly | 7 days before expiry |
| CL, NG | Monthly | 3 days before expiry |
| GC, HG | Bi-monthly | 5 days before expiry |
| 6E, 6J, 6B | Quarterly | 5 days before expiry |
| BTC | Monthly | 2 days before expiry |
| VX | Monthly (weekly available) | 4 days before expiry |

### Roll Logic
```
IF days_to_expiry(current_contract) <= roll_window:
    anchor = next_contract
ELSE:
    anchor = current_contract
```

### Correlation Continuity
When contracts roll, correlations are calculated using **spliced continuous series** (back-adjusted) to maintain statistical validity across roll dates.

---

## Database Schema Reference

See `supabase/migrations/YYYYMMDD_anchor_correlation_tables.sql` for:
- `anchor_instruments` - Master list of anchors
- `security_anchor_mapping` - Which anchor hedges which security
- `security_anchor_correlations` - Rolling correlations (1W, 1M, 3M)
- `book_anchor_correlations` - Aggregated book-level correlations
- `anchor_price_history` - Daily prices for correlation calculation

---

## Info Popout Reference (Universal)

| Element | Popout Text |
|---------|-------------|
| **CORR.** | "1-month rolling realized correlation to Anchor. Updated daily. Range: -1.00 to +1.00" |
| **0HEDGE** | "Zero Hedge - notional amount of Anchor instrument to trade for theoretical zero exposure. Formula: Exposure × Beta × -1. Uses 1-month rolling correlation." |
| **VAR (95%)** | "Value at Risk - maximum expected 1-day loss with 95% confidence. 1 in 20 days, losses may exceed this." |
| **CVAR (95%)** | "Conditional Value at Risk (Expected Shortfall) - average loss on days when VaR is exceeded. Measures tail risk." |
| **CONCENTRATION** | "Top 10 holdings as percentage of total exposure. Higher = more concentrated risk." |

---

## UI Elements

### Top-Right Button Group

Located in the top-right corner of each RiskCard:

```
[ASSET CLASS]                              [▲ +2.3%]   [⛶] [Trades]
```

### Enlarge Button (⛶)
- **Location:** Top-right corner, before Trades button
- **Icon:** Expand/fullscreen icon (⛶ or ↗ or ⤢)
- **Action:** Expands RiskCard to modal/fullscreen view
- **Enlarged View Features:**
  - Larger fonts for better readability
  - Full sub-category table without scrolling
  - Additional detail columns if available
  - Charts/visualizations (exposure over time, correlation history)
  - Export options (CSV, PDF)
- **Dismissal:** Close button (✕), click outside, or press Escape
- **Keyboard:** `Esc` to close

### Trades Button
- **Location:** Top-right corner of each RiskCard (after Enlarge button)
- **Action:** Opens drill-down view showing all underlying positions/trades for that asset class
- **Filter:** Pre-filtered to selected Pod's books and the clicked RiskCard's asset class

### Info Icons (ⓘ)
- **Style:** Small circle with "i", subtle gray, hover turns blue
- **Trigger:** Click or hover (configurable)
- **Content:** Context-specific explanation (see tables above)
- **Dismissal:** Click outside or press Escape

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-13 | Initial specification |

