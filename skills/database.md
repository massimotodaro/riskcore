# Database Skill

> Supabase/PostgreSQL conventions for RISKCORE

---

## Connection

```
Project ID: vukinjdeddwwlaumtfij
URL: https://vukinjdeddwwlaumtfij.supabase.co
```

Always use environment variables for credentials:
```python
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
```

---

## Table Conventions

### Required Columns

Every table MUST have:
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

### Naming

- Tables: `snake_case`, plural (e.g., `positions`, `portfolios`)
- Columns: `snake_case` (e.g., `market_value`, `as_of_date`)
- Foreign keys: `{table_singular}_id` (e.g., `portfolio_id`, `security_id`)
- Indexes: `idx_{table}_{column}` (e.g., `idx_positions_portfolio_id`)

---

## Data Types

| Use Case | Type | Example |
|----------|------|---------|
| IDs | `UUID` | `id UUID PRIMARY KEY` |
| Money/Prices | `DECIMAL(18, 8)` | `price DECIMAL(18, 8)` |
| Quantities | `DECIMAL(18, 8)` | `quantity DECIMAL(18, 8)` |
| Percentages | `DECIMAL(8, 6)` | `weight DECIMAL(8, 6)` |
| Short text | `VARCHAR(n)` | `ticker VARCHAR(20)` |
| Long text | `TEXT` | `description TEXT` |
| Dates | `DATE` | `as_of_date DATE` |
| Timestamps | `TIMESTAMP WITH TIME ZONE` | `created_at TIMESTAMPTZ` |
| Booleans | `BOOLEAN` | `is_active BOOLEAN DEFAULT TRUE` |
| Flexible data | `JSONB` | `metadata JSONB` |
| Enums | `VARCHAR` with CHECK | See below |

### Enums Pattern

```sql
-- Use VARCHAR with CHECK constraint (more flexible than ENUM)
asset_class VARCHAR(50) CHECK (asset_class IN ('equity', 'fixed_income', 'fx', 'option', 'cds', 'commodity'))
```

---

## Common Tables

### portfolios
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    pm_name VARCHAR(255),
    fund_id UUID REFERENCES funds(id),
    strategy VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### securities
```sql
CREATE TABLE securities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(20),
    cusip VARCHAR(9),
    isin VARCHAR(12),
    sedol VARCHAR(7),
    figi VARCHAR(12),
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL,
    sector VARCHAR(100),
    country VARCHAR(3),
    currency VARCHAR(3) DEFAULT 'USD',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX idx_securities_ticker ON securities(ticker);
CREATE INDEX idx_securities_cusip ON securities(cusip);
CREATE INDEX idx_securities_isin ON securities(isin);
CREATE INDEX idx_securities_figi ON securities(figi);
```

### positions
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    security_id UUID NOT NULL REFERENCES securities(id),
    quantity DECIMAL(18, 8) NOT NULL,
    market_value DECIMAL(18, 4),
    cost_basis DECIMAL(18, 4),
    currency VARCHAR(3) DEFAULT 'USD',
    as_of_date DATE NOT NULL,
    source_system VARCHAR(50),
    source_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(portfolio_id, security_id, as_of_date)
);

CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_positions_security ON positions(security_id);
CREATE INDEX idx_positions_date ON positions(as_of_date);
```

### prices
```sql
CREATE TABLE prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(id),
    price DECIMAL(18, 8) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    source VARCHAR(50) NOT NULL, -- 'market_feed', 'model', 'client_override', 'stale'
    as_of_date DATE NOT NULL,
    as_of_time TIMESTAMPTZ,
    is_stale BOOLEAN DEFAULT FALSE,
    assumptions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(security_id, as_of_date, source)
);

CREATE INDEX idx_prices_security_date ON prices(security_id, as_of_date);
```

---

## Query Patterns

### Insert with conflict handling
```python
# Upsert pattern
supabase.table("positions").upsert({
    "portfolio_id": portfolio_id,
    "security_id": security_id,
    "quantity": quantity,
    "as_of_date": as_of_date
}, on_conflict="portfolio_id,security_id,as_of_date").execute()
```

### Select with joins
```python
# Get positions with security details
result = supabase.table("positions") \
    .select("*, securities(ticker, name, asset_class)") \
    .eq("portfolio_id", portfolio_id) \
    .execute()
```

### Filtering
```python
# Multiple filters
result = supabase.table("positions") \
    .select("*") \
    .eq("portfolio_id", portfolio_id) \
    .gte("as_of_date", start_date) \
    .lte("as_of_date", end_date) \
    .execute()
```

---

## Don't

- ❌ Don't use auto-increment IDs (use UUID)
- ❌ Don't store prices as FLOAT (use DECIMAL)
- ❌ Don't skip foreign key constraints
- ❌ Don't store dates as strings
- ❌ Don't use `SELECT *` in production code
- ❌ Don't forget indexes on foreign keys
- ❌ Don't store credentials in code

---

## Migrations

Store migrations in `/database/migrations/`:
```
/database
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_risk_metrics.sql
│   └── 003_add_correlations.sql
└── seed.sql
```

Each migration should be idempotent when possible:
```sql
-- 001_initial_schema.sql
CREATE TABLE IF NOT EXISTS portfolios (
    ...
);
```

---

## Real-time Subscriptions

For dashboard updates:
```python
# Subscribe to position changes
supabase.table("positions") \
    .on("INSERT", handle_insert) \
    .on("UPDATE", handle_update) \
    .subscribe()
```

---

*Database patterns for RISKCORE*
