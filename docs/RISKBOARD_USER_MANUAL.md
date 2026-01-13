# Riskboard User Manual

> Complete guide to RISKCORE's Riskboard dashboard
> **Version:** 1.0
> **Last Updated:** 2026-01-13

---

## Table of Contents

1. [Overview](#1-overview)
2. [Navigation](#2-navigation)
3. [Market Snapshot Bar](#3-market-snapshot-bar)
4. [RiskPods](#4-riskpods)
5. [RiskCards by Asset Class](#5-riskcards-by-asset-class)
   - [Equity Card](#51-equity-card)
   - [Rates Card](#52-rates-card)
   - [Credit Card](#53-credit-card)
   - [FX Card](#54-fx-card)
   - [Commodities Card](#55-commodities-card)
   - [Other Card](#56-other-card)
6. [Calculate/Refresh System](#6-calculaterefresh-system)
7. [Accessibility Mode](#7-accessibility-mode)
8. [Manual Price Override](#8-manual-price-override)
9. [Tooltips and Information](#9-tooltips-and-information)

---

## 1. Overview

The Riskboard is RISKCORE's main risk monitoring dashboard. It provides a **unified view of risk across all portfolios** without displaying P&L (as P&L cannot be accurately tracked between file imports).

**Key Principles:**
- **READ-ONLY** - We display risk metrics, we don't execute trades
- **Multi-Portfolio Aggregation** - Each RiskPod can aggregate multiple books
- **5 Asset Classes** - Equity, Rates, Credit, FX, Other
- **No P&L Display** - Focus on risk metrics only

---

## 2. Navigation

### Sidebar Menu
- **Riskboard** - Main risk dashboard (current page)
- **Positions** - View/search individual positions
- **Overlaps** - Cross-PM position overlap analysis
- **Correlation** - PM correlation matrix and analysis
- **Upload** - Import positions via CSV/Excel/FIX

### Top Header
- **RISKCORE** logo (left)
- **Accessibility Toggle** (right) - Switch between color and monochrome mode

---

## 3. Market Snapshot Bar

Located at the top of the Riskboard, shows live market indices:

| Index | Description |
|-------|-------------|
| **SPX** | S&P 500 Index |
| **VIX** | CBOE Volatility Index |
| **US10Y** | US 10-Year Treasury Yield |
| **EURUSD** | EUR/USD Exchange Rate |

Each index shows:
- Current value
- % change (green = up, red = down)
- Mini sparkline chart (7-day history)

---

## 4. RiskPods

A **RiskPod** is a configurable risk aggregation unit. Each Pod can:
- Select any combination of portfolios to aggregate
- Show 6 RiskCards (one per asset class)
- Be independently calculated

### Pod Header Elements (left to right)

| Element | Description |
|---------|-------------|
| **Pod N** | Pod identifier (Pod 1, Pod 2, etc.) |
| **Portfolios ▼** | Dropdown to select which portfolios to include |
| **Selected indicator** | Shows "All" or comma-separated list of selected portfolios |
| **Calculate** | Button to recalculate this pod's metrics |
| **Gross** | Total gross exposure (sum of absolute values) |
| **Net** | Total net exposure (longs - shorts) |
| **Positions** | Total number of positions |
| **Last: HH:MM:SS** | Timestamp of last calculation |
| **STALE** | Appears when selections changed but not recalculated |

### Pod Actions
- **Add RiskPod** - Create additional pods for comparison
- **Delete Pod** - Remove a pod (trash icon in top-right)
- **Refresh All Pods** - Recalculate all pods at once (top bar button)

---

## 5. RiskCards by Asset Class

Each RiskPod contains 6 RiskCards, one for each asset class. Cards share a common structure but have asset-class-specific metrics.

### Common Card Elements

| Element | Description |
|---------|-------------|
| **Title** | Asset class name (color-coded) |
| **Warning Icon (⚠)** | Appears when manual price overrides exist |
| **Change Indicator** | ▲ +X.X% (green) or ▼ -X.X% (red) since last snapshot |
| **Expand Button (⛶)** | View card in larger modal |
| **Trades Button** | View underlying positions with price override capability |
| **Primary Metric** | Main risk measure (large number) with progress bar |
| **Secondary Metrics** | Three supporting metrics |
| **Breakdown Table** | Sub-category breakdown with detailed metrics |
| **Bottom Metrics** | Positions count, VaR, CVaR |
| **Footer** | Gross and Net exposure |

---

### 5.1 Equity Card

**Color:** Blue (`#3b82f6`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Net Delta** | Net directional exposure to equity markets | Sum of (Quantity × Price × Delta) for all equity positions |
| **Beta** | Portfolio beta to S&P 500 | Covariance(Portfolio, SPX) / Variance(SPX) |
| **Vega** | Option volatility sensitivity | Sum of option vegas across all equity options |
| **Gamma** | Rate of delta change | Sum of option gammas across all equity options |

**Breakdown Table Columns:**
- **Region** - Geographic breakdown (US+CAN, Europe, Japan, SE Asia, RoW)
- **%** - Percentage of total equity exposure
- **DELTA** - Net delta by region
- **BETA** - Regional beta vs S&P 500
- **VEGA** - Option vega by region
- **CORR.** - Correlation to regional anchor (SPY, VGK, EWJ, VWO)
- **0HEDGE** - Notional required to zero exposure (negative = need to sell)

**Bottom Metrics:**
- **Positions** - Number of equity positions
- **VAR (95%)** - Value at Risk at 95% confidence
- **CVAR (95%)** - Conditional VaR (Expected Shortfall)

---

### 5.2 Rates Card

**Color:** Green (`#22c55e`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **DV01** | Dollar Value of 01 - P&L from 1 basis point yield move | Sum of (Notional × Modified Duration × 0.0001) |
| **Duration** | DV01-weighted average duration | Sum(DV01 × Duration) / Total DV01 |
| **Convexity** | Second-order rate sensitivity | DV01-weighted average convexity |
| **Yield** | Notional-weighted average yield | Sum(Notional × YTM) / Total Notional |

**Breakdown Table (by Tenor Bucket):**
- **2Y** - 0-3 year maturities (Anchor: 2Y Treasury ZT)
- **5Y** - 3-7 year maturities (Anchor: 5Y Treasury ZF)
- **10Y** - 7-15 year maturities (Anchor: 10Y Treasury ZN)
- **30Y** - 15+ year maturities (Anchor: Ultra Bond UB)

**Columns:**
- **%** - % of total rates DV01
- **DV01** - Dollar value of 01 per bucket
- **DUR** - Modified duration
- **CONV** - Convexity adjustment
- **CORR.** - Correlation to anchor
- **0HEDGE** - DV01 to hedge to zero

---

### 5.3 Credit Card

**Color:** Purple (`#a855f7`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **CS01** | Credit Spread 01 - P&L from 1bp spread widening | Sum of (Notional × Spread Duration × 0.0001) |
| **Cr. Dur** | Credit spread duration | Notional-weighted spread duration |
| **Avg PD** | Average Probability of Default | Weighted average PD across issuers |
| **Avg LGD** | Average Loss Given Default | Weighted average LGD (recovery assumption) |

**Breakdown Table (by Rating):**
- **AAA-AA** - Investment grade, highest quality (Anchor: CDX.IG)
- **A** - Upper investment grade (Anchor: CDX.IG)
- **BBB** - Lower investment grade (Anchor: CDX.IG)
- **HY** - High yield / junk bonds (Anchor: CDX.HY)
- **Distress** - Distressed credits (Idiosyncratic - no hedge)

**Columns:**
- **%** - % of total CS01
- **CS01** - Credit spread 01 per rating bucket
- **PD** - Probability of default
- **LGD** - Loss given default
- **CORR.** - Correlation to CDX anchor
- **0HEDGE** - CS01 to hedge to zero (N/A for distressed)

---

### 5.4 FX Card

**Color:** Cyan (`#06b6d4`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **FX Delta** | Net FX exposure | Sum of spot + forward + options delta in USD terms |
| **FX Vega** | FX option volatility sensitivity | Sum of FX option vegas |
| **Basis** | Average carry cost | Notional-weighted forward point basis |
| **Pairs** | Number of currency pairs traded | Count of distinct currency pairs |

**Breakdown Table (by Currency):**
- **EUR** - Euro (Anchor: EUR/USD spot)
- **JPY** - Japanese Yen (Anchor: USD/JPY spot)
- **GBP** - British Pound (Anchor: GBP/USD spot)
- **Crypto** - Crypto exposure (Anchor: BTC/USD) - HIGH VOL warning
- **Other** - Other currencies combined

**Columns:**
- **%** - % of total FX delta
- **DELTA** - Net delta by currency
- **VEGA** - Option vega by currency
- **BASIS** - Basis points cost
- **CORR.** - Correlation to DXY anchor
- **0HEDGE** - Notional to zero exposure

---

### 5.5 Commodities Card

**Color:** Yellow (`#eab308`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Net Exposure** | Net commodity exposure | Sum of long - short positions |
| **P. Sens** | Price sensitivity | P&L change per 1% commodity move |
| **Basis** | Basis risk exposure | Exposure to spot-futures basis |
| **Roll** | Roll yield impact | Expected cost/gain from contract rolls |

**Breakdown Table (by Commodity):**
- **Crude** - Crude oil (Anchor: WTI Front Month CL)
- **Gold** - Gold (Anchor: COMEX Gold GC)
- **NatGas** - Natural Gas (Anchor: Henry Hub NG)
- **Copper** - Copper (Anchor: COMEX Copper HG)
- **Other** - Other commodities

**Columns:**
- **%** - % of total commodity exposure
- **EXP** - Net exposure per commodity
- **P.SENS** - Price sensitivity
- **BASIS** - Basis risk
- **CORR.** - Correlation to anchor
- **0HEDGE** - Notional to zero exposure

---

### 5.6 Other Card

**Color:** Gray (`#94a3b8`)

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Net Exposure** | Net exposure in other categories | Sum of uncategorized positions |
| **P. Sens** | Price sensitivity | P&L per 1% move |
| **Vol Sens** | Volatility sensitivity | P&L per 1 vol point move |
| **Complx** | Complexity rating | Low/Medium/High based on instrument types |

**Breakdown Table:**
- **Volatility** - VIX products, variance swaps (Anchor: VIX)
- **Struct.** - Structured products
- **Unclass.** - Unclassified positions (MANUAL warning)

---

## 6. Calculate/Refresh System

### Purpose
Risk metrics need recalculation when:
- Portfolio selections change
- New positions are uploaded
- Prices update

### How It Works

1. **Stale Indicator**: When you change portfolio selections, the Pod shows:
   - Orange pulsing "Calculate" button
   - "STALE" label next to timestamp
   - This reminds you data needs refresh

2. **Calculate Button**: Click to recalculate that Pod
   - Button shows spinning icon during calculation
   - Timestamp updates on completion
   - Stale indicator disappears

3. **Refresh All Pods**: Top bar button recalculates all Pods at once

### Visual States

| State | Calculate Button | Timestamp |
|-------|------------------|-----------|
| **Fresh** | Green, solid | Shows time, no STALE |
| **Stale** | Orange, pulsing | Shows time + STALE label |
| **Calculating** | Spinning icon | "Calculating..." |

---

## 7. Accessibility Mode

For users with color vision deficiency (color blindness).

### How to Toggle
- Click the toggle switch in the top-right header
- **Color mode** (default): Rainbow circle indicator, all cards use asset-class colors
- **Accessibility mode**: White circle indicator, all cards use white/gray

### What Changes in Accessibility Mode
- Card titles become white
- Trade buttons become white
- Table headers become white
- Row labels become white
- Progress bars become white/gray gradient
- Change indicators keep green/red (universally recognizable)

### Persistence
Your preference is saved to browser localStorage and remembered on return visits.

---

## 8. Manual Price Override

### Purpose
Some securities (especially illiquid ones like distressed bonds, structured products) may have stale or incorrect market prices. Users can manually override prices to reflect their knowledge of true market value.

### Workflow

#### Step 1: Open Trades Modal
Click the **"Trades"** button on any RiskCard to see underlying positions.

#### Step 2: View Positions
The Trades modal shows a table with:
- Ticker
- Side (Long/Short)
- Quantity
- Price (editable input)
- P&L

#### Step 3: Edit Price
- Click on any price input field
- Enter the new price
- Click "Save" to confirm

#### Step 4: Visual Feedback
When you save an override:
- Price input shows orange border (modified indicator)
- Warning icon (⚠) appears on the card header
- Warning icon pulses orange

#### Step 5: Manage Overrides
Click the warning icon (⚠) to open the Overrides modal:
- See list of all overridden securities
- For each override:
  - **Original price** (from system/Supabase)
  - **Your override** (what you entered)
  - **Edit** button to change the override
  - **Reset** button to return to system price

### Important Notes
- Overrides are per-Pod (each Pod tracks its own overrides)
- Overrides persist until you reset them or refresh the page
- In production, overrides will be stored in database with audit trail
- Warning icon disappears when all overrides are reset

---

## 9. Tooltips and Information

### How to Access Tooltips
Hover over any metric label, table header, or info icon (ℹ) to see a tooltip explaining:
- What the metric measures
- How it's calculated
- What the anchor instrument is (for correlation)

### Common Info Icons
- **ℹ** next to table headers - explains the column
- **ℹ** next to row labels - explains the category/bucket
- **ℹ** next to bottom metrics - explains VAR/CVAR methodology

### Calculation Modals
Click on any primary metric value (e.g., "$42.5M") to open a calculation breakdown modal showing:
- Individual components
- Formula applied
- Final result

---

## Quick Reference: Key Metrics

| Metric | Asset Class | Formula | Unit |
|--------|-------------|---------|------|
| **Net Delta** | Equity | Σ(Qty × Price × Delta) | USD |
| **DV01** | Rates | Σ(Notional × ModDur × 0.0001) | USD per bp |
| **CS01** | Credit | Σ(Notional × SpreadDur × 0.0001) | USD per bp |
| **FX Delta** | FX | Σ(Spot + Fwd + OptDelta) | USD |
| **VAR (95%)** | All | -1.645 × σ × √days | USD |
| **CVAR (95%)** | All | E[Loss | Loss > VAR] | USD |
| **Beta** | Equity | Cov(Port, SPX) / Var(SPX) | Ratio |
| **Vega** | Options | ∂Price/∂σ | USD per 1 vol pt |
| **Gamma** | Options | ∂Delta/∂Price | USD per $1 move |

---

## Glossary

| Term | Definition |
|------|------------|
| **Anchor** | Benchmark instrument for hedging/correlation (e.g., SPY for US equities) |
| **0HEDGE** | Notional amount needed to zero out exposure |
| **CORR** | Correlation coefficient to anchor (-1 to +1) |
| **DV01** | Dollar Value of 01 - P&L from 1bp rate move |
| **CS01** | Credit Spread 01 - P&L from 1bp spread move |
| **PD** | Probability of Default |
| **LGD** | Loss Given Default |
| **VAR** | Value at Risk - maximum expected loss at confidence level |
| **CVAR** | Conditional VAR / Expected Shortfall - average loss beyond VAR |
| **Stale** | Data that needs recalculation |
| **RiskPod** | Configurable risk aggregation unit |
| **RiskCard** | Visual component showing risk for one asset class |

---

*End of Riskboard User Manual*
