# RISKCORE Quick Start Guide

> Get up and running in 5 minutes
> **Last Updated:** 2026-01-12

---

## What is RISKCORE?

RISKCORE is a **risk aggregation platform** for multi-manager hedge funds. It solves one problem:

> **"How do I see firm-wide risk across all my PMs when each uses a different system?"**

---

## The 5-Minute Demo

### Step 1: Upload Positions (1 minute)

**From CSV/Excel:**
```
POST /api/v1/upload/import
```

**From Google Sheets:**
```
POST /api/v1/upload/google-sheets/import
```

**Via REST API:**
```python
import requests

positions = [
    {"ticker": "AAPL", "quantity": 1000, "price": 175.50, "direction": "long"},
    {"ticker": "NVDA", "quantity": 500, "price": 480.00, "direction": "long"},
    {"ticker": "TSLA", "quantity": -200, "price": 245.00, "direction": "short"},
]

requests.post(
    "http://localhost:8000/api/v1/positions/bulk",
    json={"positions": positions, "tenant_id": "...", "book_id": "..."}
)
```

### Step 2: See Firm Summary (1 minute)

```bash
curl "http://localhost:8000/api/v1/aggregation/firm/summary?tenant_id=..."
```

**Response:**
```json
{
  "gross_exposure": 1300000000,
  "net_exposure": 725000000,
  "netting_efficiency": 0.44,
  "pm_count": 10,
  "position_count": 1032
}
```

### Step 3: Check PM Correlations (1 minute)

```bash
curl "http://localhost:8000/api/v1/correlation/pm/matrix?tenant_id=...&window=21d"
```

**See which PMs are correlated:**
- High correlation (>0.7) = concentration risk
- Negative correlation = natural hedge

### Step 4: Find Overlapping Positions (1 minute)

```bash
curl "http://localhost:8000/api/v1/aggregation/overlaps?tenant_id=..."
```

**Discover:**
- Same stock held by multiple PMs
- Netting opportunities (opposing positions)
- Concentration risks (same direction)

### Step 5: Calculate VaR (1 minute)

```bash
curl "http://localhost:8000/api/v1/risk/var/firm?tenant_id=..."
```

**Get firm-wide Value at Risk** with diversification benefit across PMs.

---

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **Tenant** | Your firm (multi-tenant isolation) |
| **Book** | A PM's portfolio |
| **Overlap** | Same security held by 2+ PMs |
| **Netting** | Offsetting long vs. short across PMs |
| **Correlation** | How similar PM returns move together |
| **RiskPod** | Asset class grouping (Equity, Rates, Credit, FX, Other) |

---

## API Endpoints at a Glance

| Category | Endpoint | Purpose |
|----------|----------|---------|
| **Upload** | `POST /upload/import` | Upload CSV/Excel |
| **Upload** | `POST /upload/google-sheets/import` | Import from Google Sheets |
| **Positions** | `POST /positions/bulk` | Bulk create positions |
| **Aggregation** | `GET /aggregation/firm/summary` | Firm-wide summary |
| **Aggregation** | `GET /aggregation/overlaps` | Overlapping positions |
| **Aggregation** | `GET /aggregation/netting/summary` | Netting analysis |
| **Correlation** | `GET /correlation/pm/matrix` | PM correlation matrix |
| **Correlation** | `GET /correlation/pm/{id1}/correlation/{id2}/analysis` | PM pair analysis |
| **Risk** | `GET /risk/var/{book_id}` | Book VaR |
| **Risk** | `GET /risk/exposures/{book_id}/summary` | Exposure breakdown |

**Full API docs:** `http://localhost:8000/docs`

---

## Sample Data

Generate realistic test data:

```bash
cd RISKCORE
python scripts/generate_mock_data.py --clean --scale medium
```

This creates:
- 1 tenant
- 2 funds
- 10 PMs
- 20 books
- ~1000 positions
- 21 days of return history

---

## Next Steps

| Role | Guide |
|------|-------|
| **CTO** | [Technical Integration Guide](USER_GUIDE_CTO.md) |
| **CRO** | [Risk Officer Guide](USER_GUIDE_CRO.md) |
| **PM** | [Portfolio Manager Guide](USER_GUIDE_PM.md) |

---

## Support

- **GitHub:** https://github.com/massimotodaro/riskcore
- **Issues:** https://github.com/massimotodaro/riskcore/issues
- **Docs:** `/docs` folder in repository

---

*Built for multi-manager hedge funds who need firm-wide risk visibility without the spreadsheet chaos.*
