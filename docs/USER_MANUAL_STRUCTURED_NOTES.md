# User Manual: Structured Notes & Compositions

> How to handle structured notes and complex instruments in RISKCORE

---

## Overview

Structured notes and complex instruments (e.g., structured products, linked notes, custom baskets) often contain multiple underlying components with exposure to different asset classes. RISKCORE allows you to:

1. **Keep the position in "Other" RiskPod** - The structured note appears as a single line item
2. **Define component breakdown** - Specify what's inside for pricing and risk
3. **Get risk attribution** - See exposure breakdown across RiskPods (Equity, Rates, Credit, FX)
4. **Price from components** - Aggregate component prices for the total

---

## When to Use Compositions

Use compositions when you have:

- **Structured notes** with multiple underlying instruments
- **Custom baskets** that span asset classes
- **Complex products** that don't fit a single instrument type
- **Principal-protected notes** with bond + option components
- **Convertible bonds** (bond + equity option)
- **Multi-asset linked notes**

---

## Creating a Composition

### Via API

```bash
POST /api/v1/compositions
Content-Type: application/json

{
  "name": "ABC Structured Note",
  "description": "Multi-asset structured product with equity and credit exposure",
  "is_template": true,
  "components": [
    {
      "name": "S&P 500 Future Mar 2025",
      "type_code": "FUTURE",
      "allocation": 33.33
    },
    {
      "name": "NVIDIA Put Strike 800",
      "type_code": "EQO",
      "allocation": 33.33
    },
    {
      "name": "NVIDIA Bond 5.5% 2032",
      "type_code": "CORPBOND",
      "allocation": 33.34
    }
  ]
}
```

### Response

```json
{
  "id": "a1b2c3d4-e5f6-...",
  "status": "created"
}
```

---

## Component Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Descriptive name for the component |
| `type_code` | Yes | Instrument type code (FUTURE, EQO, CORPBOND, etc.) |
| `allocation` | Yes | Percentage allocation (must sum to 100%) |
| `allocation_type` | No | "percentage" (default) or "notional" |
| `security_id` | No | Link to actual security for live pricing |
| `delta`, `gamma`, `vega`, `theta`, `rho` | No | Override Greeks if needed |
| `duration`, `convexity`, `dv01` | No | Override fixed income metrics |

### Common Type Codes

| Code | Description | RiskPod |
|------|-------------|---------|
| `EQUITY` | Common Stock | Equity |
| `EQO` | Equity Option | Equity |
| `FUTURE` | Futures Contract | Equity/Rates |
| `ETF` | Exchange-Traded Fund | Equity |
| `CORPBOND` | Corporate Bond | Credit |
| `GOVBOND` | Government Bond | Rates |
| `IRS` | Interest Rate Swap | Rates |
| `CDS` | Credit Default Swap | Credit |
| `FX_FORWARD` | FX Forward | FX |
| `FX_OPTION` | FX Option | FX |

---

## Applying to a Position

Once you have a composition template, apply it to a position:

### Via API

```bash
POST /api/v1/positions/{position_id}/composition?composition_id={composition_id}
```

### Via Positions API

```bash
POST /api/v1/compositions/position/{position_id}?composition_id={composition_id}
```

---

## Getting Risk Attribution

After applying a composition, get the risk breakdown:

```bash
GET /api/v1/positions/{position_id}/risk-attribution
```

### Response

```json
{
  "position_id": "abc123...",
  "total_value": 30000000,
  "attribution": {
    "equity": 20000000,
    "credit": 10000000,
    "rates": 0,
    "fx": 0,
    "other": 0
  },
  "components": [
    {
      "name": "S&P 500 Future Mar 2025",
      "value": 10000000,
      "allocation": 33.33,
      "allocation_type": "percentage",
      "riskpod": "equity",
      "instrument_type": "FUTURE"
    },
    {
      "name": "NVIDIA Put Strike 800",
      "value": 10000000,
      "allocation": 33.33,
      "allocation_type": "percentage",
      "riskpod": "equity",
      "instrument_type": "EQO"
    },
    {
      "name": "NVIDIA Bond 5.5% 2032",
      "value": 10000000,
      "allocation": 33.34,
      "allocation_type": "percentage",
      "riskpod": "credit",
      "instrument_type": "CORPBOND"
    }
  ]
}
```

---

## Templates for Reuse

When `is_template: true`, the composition can be:

1. **Reused** for multiple positions with the same structure
2. **Auto-matched** when importing files with matching security names
3. **Applied retroactively** to existing positions

### Apply to Multiple Positions by Pattern

```bash
POST /api/v1/compositions/apply-by-pattern?composition_id={id}&security_name_pattern=ABC%20Structured
```

This applies the composition to all positions where the security name contains "ABC Structured".

---

## Workflow: Decomposing from Unmatched Queue

When an unknown instrument is imported and lands in the unmatched queue, you can decompose it directly:

```bash
POST /api/v1/instrument/unmatched/{unmatched_id}/decompose
Content-Type: application/json

{
  "name": "XYZ Structured Note",
  "components": [
    {"name": "Component A", "type_code": "EQUITY", "allocation": 50},
    {"name": "Component B", "type_code": "CORPBOND", "allocation": 50}
  ],
  "create_template": true,
  "apply_to_existing": true
}
```

This:
1. Creates a composition template
2. Marks the unmatched item as "decomposed"
3. Applies to any existing positions matching the name

---

## Managing Compositions

### List All Compositions

```bash
GET /api/v1/compositions?is_template=true
```

### Get Composition Details

```bash
GET /api/v1/compositions/{composition_id}
```

### Update Composition

```bash
PUT /api/v1/compositions/{composition_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Add Component

```bash
POST /api/v1/compositions/{composition_id}/components
Content-Type: application/json

{
  "name": "New Component",
  "type_code": "EQUITY",
  "allocation": 25
}
```

### Remove Component

```bash
DELETE /api/v1/compositions/{composition_id}/components/{component_id}
```

### Delete Composition

```bash
DELETE /api/v1/compositions/{composition_id}
```

---

## Best Practices

1. **Allocations must sum to 100%** - The API validates this
2. **Use meaningful component names** - They appear in reports
3. **Set `is_template: true`** for reusable compositions
4. **Link to securities when possible** - Enables live pricing
5. **Override Greeks only when necessary** - System calculates from linked securities

---

## Dashboard Integration (Future)

The CIO Dashboard will show:

- Structured note positions in "Other" RiskPod
- Component breakdown on hover/click
- Risk attribution visualization
- Drill-down to component details

---

## Example: Convertible Bond

A convertible bond has both fixed income and equity characteristics:

```json
{
  "name": "ACME Corp 3% Convertible 2027",
  "components": [
    {
      "name": "ACME Bond Floor",
      "type_code": "CORPBOND",
      "allocation": 75,
      "duration": 4.5,
      "convexity": 0.25
    },
    {
      "name": "ACME Conversion Option",
      "type_code": "EQO",
      "allocation": 25,
      "delta": 0.35,
      "gamma": 0.02
    }
  ]
}
```

Risk Attribution:
- Credit RiskPod: 75% of position value
- Equity RiskPod: 25% of position value

---

## Troubleshooting

### "Allocations must sum to 100%"

Ensure all component allocations add up to exactly 100%. Use decimals for precision (33.33, 33.33, 33.34).

### "Instrument type not found"

Check that the `type_code` exists in the instrument_types table. Use `GET /api/v1/instrument/types` to see available types.

### "Position not found"

Verify the position_id exists and is active.

---

## Related Documentation

- [User Manual: Instrument Normalization](./USER_MANUAL_INSTRUMENT_NORMALIZATION.md)
- [API Documentation](/docs) (FastAPI Swagger UI)
- [RISKPODS_AND_METRICS.md](./RISKPODS_AND_METRICS.md)
