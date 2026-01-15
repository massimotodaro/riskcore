# User Manual: Instrument Normalization & Unmatched Queue

> How RISKCORE normalizes instrument types and handles unknown securities

---

## Overview

When clients upload position files, instrument type names vary widely:

- "CDS", "Credit Default Swap", "Credti Defualt Swp" → All should map to CDS
- "Equity", "Common Stock", "Shares" → All should map to EQUITY
- "IRS", "Interest Rate Swap", "Rate Swap 5Y" → All should map to IRS

RISKCORE's **Instrument Normalization Service** automatically:

1. Matches input to canonical instrument types
2. Extracts tenor information (5Y, 10Y, etc.)
3. Assigns the correct RiskPod (Equity, Rates, Credit, FX, Other)
4. Queues unrecognized instruments for manual review

---

## How Matching Works

The service uses a multi-tier matching algorithm:

| Priority | Method | Confidence | Example |
|----------|--------|------------|---------|
| 1 | **Exact Match** | 1.0 | "CDS" → CDS |
| 2 | **Prefix Match** | 0.95 | "CDS 5Y EUR" → CDS |
| 3 | **Fuzzy Match** | 0.85+ | "Credti Default Swap" → CDS |
| 4 | **Pattern Match** | 0.80 | "5 year credit protection" → CDS |
| 5 | **Unmatched** | 0.0 | Unknown → Queued for review |

---

## Normalizing Instruments

### Single Instrument

```bash
POST /api/v1/instrument/normalize
Content-Type: application/json

{
  "value": "CDS 5Y"
}
```

### Response

```json
{
  "success": true,
  "input_value": "CDS 5Y",
  "instrument_type_code": "CDS",
  "canonical_name": "Credit Default Swap",
  "asset_class": "cds",
  "riskpod": "credit",
  "extracted_tenor": "5Y",
  "confidence": 1.0,
  "match_method": "exact",
  "matched_alias": "CDS",
  "is_cached": false
}
```

### Batch Normalization

```bash
POST /api/v1/instrument/normalize/batch
Content-Type: application/json

{
  "values": ["CDS 5Y", "Interest Rate Swap", "Common Stock", "Unknown XYZ"]
}
```

---

## Tenor Extraction

The service automatically extracts tenor from instrument names:

| Input | Extracted Tenor |
|-------|-----------------|
| "CDS 5Y" | 5Y |
| "UST 10Y" | 10Y |
| "5-year swap" | 5Y |
| "ten year bond" | 10Y |
| "SOFR 3M" | 3M |
| "Bill 13W" | 13W |
| "30D SOFR" | 30D |

---

## Canonical Instrument Types

View all available types:

```bash
GET /api/v1/instrument/types
```

### Example Response

```json
[
  {
    "id": "uuid...",
    "code": "CDS",
    "canonical_name": "Credit Default Swap",
    "asset_class": "cds",
    "riskpod": "credit",
    "has_tenor": true,
    "default_tenor": "5Y"
  },
  {
    "id": "uuid...",
    "code": "IRS",
    "canonical_name": "Interest Rate Swap",
    "asset_class": "swap",
    "riskpod": "rates",
    "has_tenor": true,
    "default_tenor": null
  }
]
```

### Common Instrument Types

| Code | Name | RiskPod |
|------|------|---------|
| EQUITY | Common Stock | Equity |
| ETF | Exchange-Traded Fund | Equity |
| EQO | Equity Option | Equity |
| FUTURE | Futures Contract | Equity |
| IRS | Interest Rate Swap | Rates |
| GOVBOND | Government Bond | Rates |
| CORPBOND | Corporate Bond | Credit |
| CDS | Credit Default Swap | Credit |
| FX_SPOT | FX Spot | FX |
| FX_FORWARD | FX Forward | FX |

---

## Alias Management

Aliases map common variations to canonical types.

### List Aliases

```bash
GET /api/v1/instrument/aliases?instrument_type_code=CDS
```

### Create New Alias

```bash
POST /api/v1/instrument/aliases
Content-Type: application/json

{
  "instrument_type_code": "CDS",
  "alias": "Credit Protection Contract",
  "match_type": "exact",
  "priority": 90,
  "tenant_specific": false
}
```

### Match Types

| Type | Description | Example |
|------|-------------|---------|
| `exact` | Exact string match | "CDS" = "CDS" |
| `prefix` | Starts with | "CDS*" matches "CDS 5Y EUR" |
| `contains` | Contains substring | "*credit*" matches "credit default" |
| `regex` | Regular expression | Complex patterns |

---

## The Unmatched Queue

When an instrument cannot be matched, it's queued for manual review.

### List Unmatched Items

```bash
GET /api/v1/instrument/unmatched?status=pending
```

### Response

```json
[
  {
    "id": "uuid...",
    "input_value": "Unknown Product XYZ",
    "occurrence_count": 5,
    "status": "pending",
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": null
  }
]
```

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Awaiting review |
| `mapped` | Resolved to an instrument type |
| `ignored` | Marked as not applicable |
| `escalated` | Escalated for further review |
| `decomposed` | Converted to structured note composition |

---

## Resolving Unmatched Items

### Option 1: Map to Existing Type

```bash
POST /api/v1/instrument/unmatched/{unmatched_id}/resolve
Content-Type: application/json

{
  "instrument_type_code": "EQUITY",
  "create_alias": true,
  "notes": "Client uses 'Stock' for common equity"
}
```

This:
- Maps the instrument to EQUITY
- Creates an alias for future automatic matching
- Updates the status to "mapped"

### Option 2: Ignore

```bash
POST /api/v1/instrument/unmatched/{unmatched_id}/ignore?notes=Test%20data%20only
```

Use this for:
- Test data that shouldn't be processed
- Invalid or garbage entries
- Non-instrument text accidentally captured

### Option 3: Escalate

```bash
POST /api/v1/instrument/unmatched/{unmatched_id}/escalate?notes=Need%20clarification%20from%20client
```

Use this when:
- The instrument type is genuinely unclear
- Client input is required
- Subject matter expertise is needed

### Option 4: Decompose (Structured Notes)

```bash
POST /api/v1/instrument/unmatched/{unmatched_id}/decompose
Content-Type: application/json

{
  "name": "ABC Structured Note",
  "components": [
    {"name": "Equity Component", "type_code": "EQUITY", "allocation": 60},
    {"name": "Bond Component", "type_code": "CORPBOND", "allocation": 40}
  ],
  "create_template": true,
  "apply_to_existing": true
}
```

Use this for:
- Structured notes with multiple components
- Complex products spanning asset classes
- Instruments needing component breakdown for risk

See [User Manual: Structured Notes](./USER_MANUAL_STRUCTURED_NOTES.md) for details.

---

## Workflow: Processing Unmatched Queue

### Daily Review Process

1. **Check the queue:**
   ```bash
   GET /api/v1/instrument/unmatched?status=pending&page=1&page_size=50
   ```

2. **For each item, decide:**
   - Known type → **Resolve** with `create_alias: true`
   - Invalid entry → **Ignore**
   - Complex product → **Decompose**
   - Unclear → **Escalate**

3. **Monitor resolution:**
   ```bash
   GET /api/v1/instrument/unmatched?status=mapped
   ```

### Prioritization by Occurrence Count

Items with higher `occurrence_count` affect more positions and should be resolved first.

---

## Cache Management

Normalization results are cached for performance. Clear expired entries:

```bash
DELETE /api/v1/instrument/cache
```

### Response

```json
{
  "status": "cleared",
  "deleted_count": 42
}
```

---

## Integration with File Upload

When uploading position files:

1. The `instrument_type` column is auto-detected
2. Each value is normalized
3. Successful matches proceed to position creation
4. Unmatched values are queued for review
5. Positions with unmatched types are created with `asset_class: 'other'`

### Supported Column Names

The parser recognizes these column names for instrument type:

- `instrument_type`
- `product_type`
- `security_type`
- `type`
- `product`
- `asset_type`
- `asset_class`
- `inst_type`
- `sec_type`

---

## Fuzzy Matching Details

Fuzzy matching uses Levenshtein distance to handle typos:

| Input | Best Match | Similarity |
|-------|------------|------------|
| "Credti Default Swap" | "Credit Default Swap" | 0.89 |
| "Intrest Rate Swp" | "Interest Rate Swap" | 0.87 |
| "Goverment Bond" | "Government Bond" | 0.93 |

Minimum threshold: **0.85** (85% similarity)

---

## Tenant-Specific Aliases

Some clients have unique terminology. Create tenant-specific aliases:

```bash
POST /api/v1/instrument/aliases?tenant_id={uuid}
Content-Type: application/json

{
  "instrument_type_code": "EQUITY",
  "alias": "Acme Stock Position",
  "match_type": "exact",
  "priority": 100,
  "tenant_specific": true
}
```

Tenant-specific aliases:
- Only match for that tenant's data
- Take priority over global aliases
- Are isolated from other tenants

---

## Best Practices

1. **Resolve promptly** - Pending items create uncertainty in reports
2. **Create aliases** - Prevents same issue from recurring
3. **Use high priority** for tenant-specific aliases
4. **Document escalations** - Include context for resolution
5. **Review weekly** - Keep the queue clean

---

## Troubleshooting

### "No match found but should have matched"

1. Check if alias exists: `GET /api/v1/instrument/aliases?instrument_type_code=XXX`
2. Create alias if missing
3. Clear cache if recently added: `DELETE /api/v1/instrument/cache`

### "Wrong type matched"

1. Check alias priorities - higher priority wins
2. Remove incorrect alias if needed
3. Create correct alias with higher priority

### "Fuzzy match returning wrong type"

- Fuzzy matching may match unintended types
- Create an exact alias for the problematic input
- Set priority higher than fuzzy match default

---

## Related Documentation

- [User Manual: Structured Notes](./USER_MANUAL_STRUCTURED_NOTES.md)
- [API Documentation](/docs) (FastAPI Swagger UI)
- [RISKPODS_AND_METRICS.md](./RISKPODS_AND_METRICS.md)
