# RISKCORE User Guide for Portfolio Managers

> Quick guide to uploading positions and viewing your risk metrics
> **Audience:** Portfolio Managers, Traders
> **Last Updated:** 2026-01-12

---

## What You Need to Know

RISKCORE is your firm's risk aggregation platform. As a PM, you'll use it to:
1. **Upload your positions** (if not automated)
2. **View your book's risk metrics**
3. **See how you compare** to other PMs (anonymized or with permissions)
4. **Acknowledge alerts** when limits are approached

**Important:** RISKCORE is **read-only**. It never writes to your trading systems or modifies your positions. It just reads and analyzes.

---

## Uploading Your Positions

### Option 1: CSV/Excel Upload

**Step 1:** Prepare your file with these columns (column names are flexible):

| Column | Examples | Required |
|--------|----------|----------|
| Ticker/Symbol | AAPL, NVDA, TSLA | Yes |
| Quantity | 1000, -500 | Yes |
| Price | 150.00 | Yes |
| Direction | Long, Short (or use negative qty) | Optional |

**Example CSV:**
```csv
Symbol,Qty,Price,Side
AAPL,1000,175.50,Long
NVDA,500,480.25,Long
TSLA,-200,245.00,Short
```

**Step 2:** Go to **Upload → Positions**

**Step 3:** Drag & drop your file or click to browse

**Step 4:** Review the preview - RISKCORE auto-detects your columns

**Step 5:** Confirm the mapping and click **Import**

---

### Option 2: Google Sheets

*For PMs who track positions in Google Sheets*

**Step 1:** Make your sheet publicly viewable
- Share → "Anyone with the link can view"

**Step 2:** Copy the URL (looks like `https://docs.google.com/spreadsheets/d/...`)

**Step 3:** Go to **Upload → Google Sheets**

**Step 4:** Paste URL, select your sheet tab if multiple

**Step 5:** Review and import

**Note:** Your sheet must have ticker, quantity, and price columns.

---

### Option 3: Automated Export from Your OMS

If your OMS supports scheduled exports, you can automate the entire process:

**Bloomberg AIM/PORT:**
1. Set up a scheduled report in Bloomberg
2. Configure export to CSV format
3. Point export to your firm's RISKCORE import folder
4. Positions sync automatically on schedule

**Enfusion / Eze Eclipse / Other:**
1. Configure report scheduler in your OMS
2. Set output format to CSV or Excel
3. Configure delivery to SFTP or network folder
4. RISKCORE auto-imports on file arrival

**Key Benefit:** No manual work required after initial setup. Your positions update automatically whenever your OMS exports.

Check with your IT team or risk team if you're not sure whether automated imports are set up.

---

## Viewing Your Risk Metrics

### Your Book Dashboard

After logging in, you'll see your book's summary:

```
┌─────────────────────────────────────────┐
│ YOUR BOOK: Smith Alpha Fund             │
├─────────────────────────────────────────┤
│ Gross Exposure:    $32,500,000          │
│ Net Exposure:      $18,200,000 (56% L)  │
│ Long Exposure:     $25,350,000          │
│ Short Exposure:    $7,150,000           │
├─────────────────────────────────────────┤
│ VaR (95%, 1-day):  $485,000             │
│ VaR (99%, 1-day):  $720,000             │
├─────────────────────────────────────────┤
│ P&L Today:         +$125,400            │
│ P&L MTD:           +$892,000            │
└─────────────────────────────────────────┘
```

---

### Risk Metrics Explained

| Metric | What It Means | Why You Care |
|--------|---------------|--------------|
| **Gross Exposure** | Total absolute value of positions | Your total capital deployed |
| **Net Exposure** | Longs minus shorts | Your directional bet |
| **VaR 95%** | Expected worst daily loss 1 in 20 days | Risk limit trigger |
| **VaR 99%** | Expected worst daily loss 1 in 100 days | Stress scenario |

---

### Exposure Breakdown

See where your risk is concentrated:

**By Sector:**
```
Technology:     45% ████████████████░░░░
Healthcare:     22% ████████░░░░░░░░░░░░
Financials:     18% ███████░░░░░░░░░░░░░
Consumer:       10% ████░░░░░░░░░░░░░░░░
Other:           5% ██░░░░░░░░░░░░░░░░░░
```

**By Geography:**
- US: 78%
- Europe: 15%
- Asia: 7%

**Top Positions:**
| Position | Exposure | % of Gross |
|----------|----------|------------|
| AAPL | $4.5M | 13.8% |
| NVDA | $3.8M | 11.7% |
| GOOGL | $3.2M | 9.8% |

---

### Greeks (Options Only)

If you have options positions, you'll see:

| Greek | Value | What It Means |
|-------|-------|---------------|
| Delta | $1.2M | P&L per 1% underlying move |
| Gamma | $45K | Delta change per 1% move |
| Vega | $85K | P&L per 1% vol move |
| Theta | -$12K | Daily time decay |

---

## What Central Risk Sees

**Your CRO can see:**
- Your gross and net exposure
- Your top positions
- Your VaR contribution to firm
- How correlated you are with other PMs
- Overlapping positions with other PMs

**Your CRO cannot:**
- Modify your positions
- Trade on your behalf
- Share your specific positions with other PMs (without permission)

**Why this matters:**
The firm needs to understand aggregate risk. Your individual P&L and specific trades remain your domain.

---

## Alerts & Limits

### Types of Alerts

You may receive alerts when:

| Alert | Meaning | Action Required |
|-------|---------|-----------------|
| **VaR Warning** | Approaching VaR limit | Review positions |
| **Concentration** | Single name > threshold | Acknowledge or reduce |
| **Correlation** | High correlation with another PM | Informational |
| **Data Stale** | Position data not updated | Re-upload if manual |

### Acknowledging Alerts

1. Click the alert notification
2. Review the details
3. Click **Acknowledge** to confirm you've seen it
4. Optionally add a note explaining the situation

**Note:** Acknowledging doesn't resolve the alert - it just confirms you're aware.

---

## Common Questions

### "Why does my VaR look different from my internal calc?"

RISKCORE uses a standardized methodology (historical VaR, 21-day window). Your internal tools may use different parameters. Both can be correct.

### "Can I see other PMs' positions?"

Only if your firm has enabled this. By default, you see:
- Your own positions (full detail)
- Firm aggregate (anonymized)
- Your correlation with other PMs (no names unless enabled)

### "How often is data refreshed?"

Depends on your firm's setup:
- Automated feed: Real-time or every few minutes
- Manual upload: Whenever you upload
- Check "Last Updated" timestamp on dashboard

### "The data looks wrong - what do I do?"

1. Check your upload - was the column mapping correct?
2. Check the security - was it resolved correctly?
3. Contact your risk team if issues persist

---

## Quick Reference

### Upload Shortcuts

| Format | Where | Notes |
|--------|-------|-------|
| CSV | Upload → Positions | Any delimiter works |
| Excel | Upload → Positions | .xlsx or .xls |
| Google Sheets | Upload → Google Sheets | Must be public |

### Keyboard Shortcuts (Dashboard)

| Key | Action |
|-----|--------|
| `R` | Refresh data |
| `D` | Toggle dark mode |
| `?` | Show help |
| `Esc` | Close modal |

### Contact

- **Risk Team:** risk@yourfirm.internal
- **IT Support:** help@yourfirm.internal
- **RISKCORE Help:** ? icon in app

---

## Your Privacy

RISKCORE is designed to balance firm risk visibility with PM confidentiality:

- Your exact positions are visible only to you and designated risk officers
- Other PMs see only anonymized aggregate data
- Your P&L is not shared with other PMs
- All access is logged for audit purposes

---

*This platform helps the firm manage aggregate risk. It's not here to micromanage your trading - it's here to ensure the firm survives to trade another day.*
