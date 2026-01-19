# User Manual: Data Import & Reconciliation

> Complete guide to importing data into RISKCORE

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing Import Data](#accessing-import-data)
3. [Import Modes](#import-modes)
   - [Upload Trades](#1-upload-trades)
   - [Portfolio Snapshot](#2-portfolio-snapshot)
   - [Position Updates](#3-position-updates)
   - [Connect Google Sheet](#4-connect-google-sheet)
   - [FIX Message](#5-fix-message)
4. [The Import Workflow](#the-import-workflow)
   - [Step 1: Select File](#step-1-select-file)
   - [Step 2: Map Columns](#step-2-map-columns)
   - [Step 3: Review & Apply](#step-3-review--apply)
5. [Handling Unmatched Securities](#handling-unmatched-securities)
6. [Pending Actions](#pending-actions)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

RISKCORE provides multiple ways to import your portfolio data. Whether you're adding individual trades, reconciling a full portfolio snapshot, or connecting to live data sources, the Import Data feature handles it all.

**Key Features:**
- Multiple import modes for different use cases
- Automatic column detection and mapping
- Reconciliation preview showing differences
- Unmatched security queue for unknown instruments
- Support for CSV, Excel, and Google Sheets

---

## Accessing Import Data

### From the Sidebar

1. Look at the left sidebar
2. Find the **"Data"** section near the bottom
3. Click **"Import Data"** to expand the submenu
4. Select your desired import mode

![Screenshot: Sidebar with Import Data menu expanded showing all import options]

*The Import Data menu in the sidebar shows all available import options. A badge indicates pending actions that need attention.*

### Quick Access via URL

You can also access import directly via URL with a specific mode:
- `/upload?mode=trades` - Upload Trades
- `/upload?mode=portfolio` - Portfolio Snapshot
- `/upload?mode=delta` - Position Updates
- `/upload?mode=google` - Google Sheet
- `/upload?mode=fix` - FIX Message

---

## Import Modes

RISKCORE offers five different import modes, each designed for a specific use case.

### 1. Upload Trades

**Use this when:** You want to add new trades to an existing portfolio without affecting current positions.

**What it does:**
- Adds new trades to your trade history
- Updates position quantities based on trade direction (buy/sell)
- Does NOT replace or modify existing positions directly
- Good for daily trade imports

**Best for:**
- Daily end-of-day trade reconciliation
- Adding executed trades from your OMS
- Incremental portfolio updates

![Screenshot: Upload Trades option card showing cloud upload icon and description]

---

### 2. Portfolio Snapshot

**Use this when:** You want to reconcile your entire portfolio against a file, detecting additions, deletions, and changes.

**What it does:**
- Compares the uploaded file against current positions
- Shows you exactly what's different (new, changed, removed)
- Lets you decide what to update, keep, or delete
- Creates a full audit trail of changes

**Best for:**
- Monthly portfolio reconciliation
- Prime broker statement matching
- Detecting and correcting data drift

![Screenshot: Portfolio Snapshot option card showing document icon and description]

**Reconciliation Categories:**

| Category | Description | Action Options |
|----------|-------------|----------------|
| **Matched** | Position exists and quantities match | No action needed |
| **Mismatch** | Position exists but quantity differs | Update or Keep |
| **Stale** | In system but NOT in file | Delete or Keep |
| **New** | In file but NOT in system | Add |

---

### 3. Position Updates

**Use this when:** You want to update specific positions that have changed without a full reconciliation.

**What it does:**
- Matches positions by security identifier
- Updates quantity/price for matches
- Adds new positions found in the file
- Ignores positions not in the file (doesn't delete them)

**Best for:**
- Partial portfolio updates
- Updating specific positions after corporate actions
- Quick corrections

![Screenshot: Position Updates option card showing sync/refresh icon and description]

---

### 4. Connect Google Sheet

**Use this when:** You want to link a Google Sheet for automatic syncing.

**What it does:**
- Connects to a Google Sheet URL
- Can sync positions or trades automatically
- Supports scheduled refreshes
- Maintains link for ongoing updates

**Best for:**
- Portfolios maintained in Google Sheets
- Collaborative portfolio management
- Real-time position tracking

![Screenshot: Connect Google Sheet option card showing spreadsheet icon and description]

**Setup Steps:**
1. Paste your Google Sheet URL
2. Grant RISKCORE read access
3. Map columns to RISKCORE fields
4. Set sync frequency (manual, hourly, daily)

---

### 5. FIX Message

**Use this when:** You have trade execution data in FIX protocol format.

**What it does:**
- Parses FIX protocol messages
- Extracts trade execution data
- Creates trade records automatically
- Supports FIX 4.2, 4.4, and 5.0

**Best for:**
- Broker execution reports
- OMS/EMS integration
- Automated trade capture

![Screenshot: FIX Message option card showing terminal/code icon and description]

**Supported FIX Tags:**
- Tag 35 (MsgType) - Execution Report (8)
- Tag 55 (Symbol) - Security identifier
- Tag 54 (Side) - Buy/Sell
- Tag 38 (OrderQty) - Quantity
- Tag 44 (Price) - Execution price
- Tag 60 (TransactTime) - Trade time

---

## The Import Workflow

All import modes follow a similar three-step workflow.

### Step 1: Select File

![Screenshot: Step 1 showing file drop zone with "Drop file here or click to browse" message]

**Supported File Formats:**
- CSV (.csv)
- Excel (.xlsx, .xls)
- Google Sheets (via URL)

**To upload a file:**
1. Click the upload area or drag-and-drop your file
2. Select the target portfolio from the dropdown
3. Click **"Continue to Mapping"**

**File Requirements:**
- Maximum file size: 50MB
- First row should contain column headers
- Data should start from row 2

---

### Step 2: Map Columns

![Screenshot: Step 2 showing column mapping table with File Column, Maps To dropdown, and Sample Value columns]

RISKCORE automatically detects common column names. Review and adjust mappings as needed.

**Required Fields:**
| Field | Description | Common Column Names |
|-------|-------------|---------------------|
| Security Identifier | Ticker, CUSIP, ISIN, or SEDOL | Symbol, Ticker, CUSIP, ISIN, Identifier |
| Quantity | Number of shares/units | Quantity, Shares, Units, Position, Qty |

**Optional Fields:**
| Field | Description |
|-------|-------------|
| Price | Current or entry price |
| Cost Basis | Original purchase price |
| Instrument Type | Type of security (Stock, Bond, Option, etc.) |
| Currency | Position currency |
| Portfolio | Sub-portfolio or strategy name |

**Tips:**
- Use **"-- Skip --"** for columns you don't need
- Sample values help verify correct mapping
- Unmapped required fields will show a warning

---

### Step 3: Review & Apply

![Screenshot: Step 3 showing reconciliation preview with Matched, Mismatch, Stale, and New sections]

For **Portfolio Snapshot** mode, this step shows a detailed reconciliation preview.

**Reconciliation Sections:**

#### Matched Positions
Positions that exist in both the system and the file with identical quantities.
- No action needed
- Shows count and total value
- Can be collapsed for cleaner view

#### Quantity Mismatches
Positions where the quantity differs between system and file.

![Screenshot: Mismatch section showing table with Security, System Qty, Import Qty, and Action (Update/Keep) columns]

For each mismatch, choose:
- **Update** - Change system quantity to match file
- **Keep** - Keep current system quantity

#### Stale Positions
Positions in the system but NOT in the import file.

![Screenshot: Stale section showing table with Security, Quantity, Value, and Action (Delete/Keep) columns]

For each stale position, choose:
- **Delete** - Remove from system (position was closed)
- **Keep** - Retain in system (file may be incomplete)

**Warning:** Deleting positions is permanent. Deleted positions are archived for audit but cannot be restored.

#### New Positions
Positions in the file but NOT in the system.

![Screenshot: New section showing table with Security, Quantity, Est Value, and Status columns]

New positions show:
- **Ready to add** - Security recognized, will be added
- **Unmatched** - Security not recognized, needs resolution

---

## Handling Unmatched Securities

When RISKCORE encounters a security it doesn't recognize, it's added to the **Unmatched Queue**.

![Screenshot: Unmatched security inline resolution showing options to Map, Decompose, or Skip]

**Resolution Options:**

### Option 1: Map to Existing Type

If the security is a standard instrument type:
1. Select the instrument type from the dropdown
2. Check **"Create alias for future imports"** to remember this mapping
3. Click **Apply Mapping**

### Option 2: Create as Structured Product

If the security is a complex product with multiple components:
1. Click **"Create Composition Template"**
2. Define the components and their allocations
3. See [User Manual: Structured Notes](./USER_MANUAL_STRUCTURED_NOTES.md)

### Option 3: Skip

If you want to exclude this security from the import:
1. Select **"Skip this security"**
2. The position will not be imported

**Note:** You cannot complete the import if any securities are unmatched. Resolve all unmatched items first.

---

## Pending Actions

The **Pending Actions** tab shows items requiring your attention.

![Screenshot: Pending Actions tab showing Unmatched Securities and Pending Reconciliations sections]

### Unmatched Securities

Securities from previous imports that weren't recognized.
- Click **"Resolve"** to map or skip
- Higher occurrence counts should be prioritized

### Pending Reconciliations

Reconciliation sessions that weren't completed.
- Click **"Review"** to continue where you left off
- Sessions expire after 24 hours

**Tip:** The badge on the Import Data menu shows the total pending count.

---

## Best Practices

### 1. Establish a Regular Import Schedule

- **Daily:** Upload trades at end of day
- **Weekly:** Run portfolio snapshot reconciliation
- **Monthly:** Full reconciliation against prime broker statements

### 2. Always Review Before Applying

- Check the reconciliation preview carefully
- Verify large quantity changes make sense
- Question unexpected stale positions

### 3. Resolve Unmatched Securities Promptly

- Unmatched securities affect risk calculations
- Create aliases to prevent recurring issues
- Document any unusual mappings

### 4. Use Consistent File Formats

- Standardize column names across files
- Use the same security identifiers (prefer ISIN/CUSIP)
- Include all required fields

### 5. Keep Audit Trail

- Review import history periodically
- Track who made changes and when
- Document reasons for deletions

---

## Troubleshooting

### "File upload failed"

**Possible causes:**
- File exceeds 50MB limit
- Unsupported file format
- Corrupted file

**Solutions:**
- Split large files into smaller chunks
- Save as CSV or XLSX format
- Re-export from source system

---

### "Column not recognized"

**Possible causes:**
- Non-standard column name
- Column header has extra spaces
- Header row is not row 1

**Solutions:**
- Manually map using the dropdown
- Clean up column names in source file
- Ensure header is in first row

---

### "Security not found"

**Possible causes:**
- New security not in RISKCORE database
- Ticker/identifier typo
- Different identifier format (CUSIP vs ISIN)

**Solutions:**
- Use the unmatched queue to map
- Verify identifier is correct
- Try different identifier type

---

### "Reconciliation shows unexpected differences"

**Possible causes:**
- File is from different date than system
- Corporate action not yet applied
- Partial file upload

**Solutions:**
- Verify file date matches comparison date
- Check for pending corporate actions
- Ensure file contains all positions

---

## Related Documentation

- [User Manual: Instrument Normalization](./USER_MANUAL_INSTRUMENT_NORMALIZATION.md)
- [User Manual: Structured Notes](./USER_MANUAL_STRUCTURED_NOTES.md)
- [User Manual: Price Editing](./USER_MANUAL_PRICE_EDITING.md)

---

*Last Updated: January 2026*
