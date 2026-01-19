# User Manual: Price Editing & Model Inputs

> How to manually override prices and edit model inputs in RISKCORE

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing the Position Drill-Down](#accessing-the-position-drill-down)
3. [Understanding Pricing Types](#understanding-pricing-types)
4. [Manual Price Override](#manual-price-override)
5. [Editing Model Inputs](#editing-model-inputs)
6. [Warning Indicators](#warning-indicators)
7. [Resetting to Defaults](#resetting-to-defaults)
8. [Audit Trail](#audit-trail)
9. [Best Practices](#best-practices)

---

## Overview

RISKCORE allows you to override prices and model inputs when the standard pricing doesn't reflect reality. This is useful for:

- **Illiquid securities** - Where market prices are stale or unavailable
- **Model calibration** - When you need to adjust model inputs for better accuracy
- **What-if analysis** - Testing impact of different assumptions
- **Dispute resolution** - When you disagree with the market price

**Important:** All manual overrides are tracked and create a warning indicator so users know the position is not using standard pricing.

---

## Accessing the Position Drill-Down

To edit prices or model inputs, you first need to open the position drill-down panel.

### Step 1: Navigate to Positions & Trades

1. Click **"Positions & Trades"** in the sidebar
2. You'll see all your positions organized by RiskPod (Equity, Rates, Credit, FX, Commodities, Other)

![Screenshot: Positions & Trades page showing RiskPod tables with position rows]

### Step 2: Click on a Position

1. Find the position you want to edit
2. Click anywhere on the row
3. The drill-down panel slides in from the right

![Screenshot: Position drill-down panel showing position details, metrics, and pricing section]

---

## Understanding Pricing Types

Each position has a pricing type that determines how its price is calculated.

### The Three Pricing Tabs

| Tab | Description | When to Use |
|-----|-------------|-------------|
| **Market** | Uses live market prices from data feeds | Default for liquid securities |
| **Model** | Uses pricing model with inputs you can edit | Derivatives, structured products, illiquid bonds |
| **Manual** | Uses a price you specify directly | Illiquid securities, dispute scenarios |

![Screenshot: Pricing section showing Market, Model, Manual tabs with Model tab selected]

### Pricing Type by Instrument

| Instrument Type | Default Pricing | Model Used |
|-----------------|-----------------|------------|
| Common Stock | Market | N/A |
| ETF | Market | N/A |
| Options | Model | Black-Scholes Model |
| Futures | Model | Cost of Carry Model |
| Bonds | Model | Discounted Cash Flow Model |
| Swaps | Model | Multi-Curve SOFR Model |
| CDS | Model | ISDA CDS Standard Model |
| Forwards | Model | Interest Rate Parity Model |

---

## Manual Price Override

Use manual price override when you want to specify an exact price for a position.

### When to Use Manual Override

- Market data feed is incorrect
- Security is illiquid with no recent trades
- You have better pricing from another source
- Testing impact of different price scenarios

### How to Set a Manual Price

1. **Open the position drill-down** by clicking on the position
2. **Click the "Manual" tab** in the Pricing section
3. **Enter your price** in the input field

![Screenshot: Manual tab showing Override Price input field with placeholder showing current price]

4. **Click "Save & Recalculate"** to apply the override

![Screenshot: Save & Recalculate button in emerald green]

### What Happens After Override

- The position's P&L and market value are recalculated using your price
- A **warning indicator** appears on the position in the table
- The drill-down panel shows a **warning banner** when opened
- All risk metrics using this position are updated

---

## Editing Model Inputs

For positions priced by a model, you can edit the inputs used in the calculation.

### When to Edit Model Inputs

- Default model inputs don't reflect current market conditions
- You want to test sensitivity to different assumptions
- Calibrating to match a benchmark price
- Corporate action has changed underlying parameters

### Accessing Model Inputs

1. **Open the position drill-down** by clicking on the position
2. **Click the "Model" tab** in the Pricing section
3. You'll see the model name and editable inputs

![Screenshot: Model tab showing "Black-Scholes Model" header in blue, "Model Inputs" label, and input fields for Implied Volatility, Risk-Free Rate, Dividend Yield, Days to Expiry]

### Model Inputs by Instrument Type

#### Options (Black-Scholes Model)

| Input | Description | Unit |
|-------|-------------|------|
| Implied Volatility | Expected volatility of underlying | % |
| Risk-Free Rate | Risk-free interest rate | % |
| Dividend Yield | Expected dividend yield | % |
| Days to Expiry | Days until option expires | days |

![Screenshot: Options model inputs showing all four fields with sample values]

---

#### Bonds (Discounted Cash Flow Model)

| Input | Description | Unit |
|-------|-------------|------|
| Yield to Maturity | Expected yield if held to maturity | % |
| Credit Spread | Spread over risk-free rate | bps |
| Recovery Rate | Expected recovery in default | % |
| OAS | Option-adjusted spread | bps |

![Screenshot: Bond model inputs showing all four fields with sample values]

---

#### Swaps (Multi-Curve SOFR Model)

| Input | Description | Unit |
|-------|-------------|------|
| Fixed Rate | Fixed leg rate | % |
| Floating Spread | Spread over floating index | bps |
| Discount Curve | Curve used for discounting | - |

![Screenshot: Swap model inputs showing three fields with sample values]

---

#### CDS (ISDA CDS Standard Model)

| Input | Description | Unit |
|-------|-------------|------|
| Credit Spread | CDS spread | bps |
| Recovery Rate | Expected recovery in default | % |
| Hazard Rate | Probability of default per year | % |

![Screenshot: CDS model inputs showing three fields with sample values]

---

#### Forwards (Interest Rate Parity Model)

| Input | Description | Unit |
|-------|-------------|------|
| Forward Rate | Contracted forward rate | - |
| Spot Rate | Current spot rate | - |
| Interest Differential | Rate differential between currencies | % |

![Screenshot: Forward model inputs showing three fields with sample values]

---

#### Futures (Cost of Carry Model)

| Input | Description | Unit |
|-------|-------------|------|
| Basis | Difference from spot price | - |
| Cost of Carry | Storage and financing costs | % |
| Conversion Factor | Bond futures delivery factor | - |

![Screenshot: Futures model inputs showing three fields with sample values]

---

### How to Edit Model Inputs

1. **Locate the input** you want to change
2. **Click in the input box** and enter your value
3. The unit (%, bps, days) appears inside the input box
4. A **"Modified"** badge appears when changes are made

![Screenshot: Model inputs with "Modified" badge showing in amber, and one input field highlighted]

5. **Click "Save & Recalculate"** to apply changes

![Screenshot: Save & Recalculate button enabled in emerald green]

### Understanding the Interface

- **Model Name** - Shown at the top in the instrument's color (e.g., amber for futures)
- **Input Labels** - White text for easy reading
- **Input Fields** - Dark background with value and unit inside
- **Modified Badge** - Amber badge appears when any input is changed
- **Save Button** - Disabled (gray) until changes are made

---

## Warning Indicators

When a position has a manual override, RISKCORE shows clear warnings so users know the pricing is non-standard.

### Warning in the Position Table

A **amber circle with "!"** appears next to the position name in the Positions & Trades table.

![Screenshot: Position row in table showing amber warning indicator next to position name]

**Hover over the indicator** to see what type of override is active:
- "Manual price override" - Direct price entry
- "Model inputs modified" - Model inputs changed from defaults

### Warning in the Drill-Down Panel

When you open a position with an override, a **warning banner** appears at the top.

![Screenshot: Drill-down panel with amber warning banner showing "Manual Price Override Active" message and Reset button]

The banner shows:
- **Override type** - "Model Inputs Modified" or "Manual Price Override Active"
- **Description** - What the override means
- **Reset button** - To restore default values

---

## Resetting to Defaults

You can remove any manual override and return to standard pricing.

### How to Reset

1. **Open the position drill-down**
2. **Look for the warning banner** at the top of the panel
3. **Click the Reset button**:
   - For model inputs: **"Reset to Defaults"**
   - For manual price: **"Reset to Market"**

![Screenshot: Warning banner with "Reset to Defaults" button highlighted]

### What Happens After Reset

- Model inputs return to their default values
- Price reverts to market or calculated model price
- Warning indicator is removed from the table
- Risk metrics are recalculated using standard pricing

---

## Audit Trail

All pricing changes are logged for compliance and audit purposes.

### What's Tracked

| Field | Description |
|-------|-------------|
| Position ID | Which position was modified |
| Change Type | Model input edit or manual price |
| Previous Value | Value before the change |
| New Value | Value after the change |
| Changed By | User who made the change |
| Changed At | Timestamp of the change |
| Reason | Optional reason for override |

### Viewing Change History

1. Open the position drill-down
2. Scroll to the **"Recent Changes"** section
3. View the history of pricing modifications

**Note:** Audit logs are retained for 5 years per regulatory requirements.

---

## Best Practices

### 1. Document Your Reasoning

Always have a clear reason for any manual override:
- Stale market data
- Better pricing source available
- Model calibration adjustment
- What-if scenario testing

### 2. Review Overrides Regularly

- Check positions with warning indicators weekly
- Verify overrides are still needed
- Reset when market data improves

### 3. Use Model Inputs Instead of Manual Price

When possible, adjust model inputs rather than overriding the price directly:
- Maintains model consistency
- Better audit trail of assumptions
- Easier to explain to stakeholders

### 4. Validate Against External Sources

Before applying a manual override:
- Check Bloomberg, Reuters, or other data vendors
- Verify with counterparty pricing
- Compare to similar securities

### 5. Communicate Overrides to Stakeholders

- Inform risk managers of significant overrides
- Include override details in reports
- Flag positions with overrides in commentary

---

## Troubleshooting

### "Save & Recalculate button is disabled"

**Cause:** No changes have been made yet.

**Solution:** Modify at least one input value. The button enables when changes are detected.

---

### "Model tab shows 'Market Priced'"

**Cause:** This instrument type doesn't use a pricing model.

**Solution:** Common stocks, ETFs, and other liquid securities use market prices directly. Use the Manual tab if you need to override.

---

### "Warning indicator not showing after save"

**Cause:** Changes may not have been saved properly.

**Solution:**
1. Make sure you clicked "Save & Recalculate"
2. Refresh the page
3. Check if the override was applied by reopening the position

---

### "Reset button not appearing"

**Cause:** The position doesn't have an active override.

**Solution:** The reset button only appears when there's an override to reset. If you see the warning banner, the reset button should be visible.

---

## Related Documentation

- [User Manual: Data Import](./USER_MANUAL_DATA_IMPORT.md)
- [User Manual: Instrument Normalization](./USER_MANUAL_INSTRUMENT_NORMALIZATION.md)
- [Riskboard User Manual](./RISKBOARD_USER_MANUAL.md)

---

*Last Updated: January 2026*
