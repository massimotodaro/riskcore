-- RISKCORE Returns and Correlation Tables
-- Tracks daily P&L at book level and pre-computed correlations
-- Week 4 Enhancement: Foundation for AI-native correlation queries

-- =============================================================================
-- BOOK DAILY RETURNS
-- =============================================================================
-- Stores daily P&L and return metrics per book
-- This is the foundation for all correlation calculations

CREATE TABLE IF NOT EXISTS book_daily_returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,

    -- Date (one record per book per day)
    return_date DATE NOT NULL,

    -- P&L figures
    daily_pnl DECIMAL(20, 2) NOT NULL DEFAULT 0,           -- Absolute P&L in base currency
    daily_return_pct DECIMAL(10, 6),                        -- Return as percentage

    -- Position context (for attribution)
    start_of_day_nav DECIMAL(20, 2),                        -- NAV at start of day
    end_of_day_nav DECIMAL(20, 2),                          -- NAV at end of day

    -- Breakdown by RiskPod (for pod-level correlation)
    pnl_equity DECIMAL(20, 2) DEFAULT 0,
    pnl_rates DECIMAL(20, 2) DEFAULT 0,
    pnl_credit DECIMAL(20, 2) DEFAULT 0,
    pnl_fx DECIMAL(20, 2) DEFAULT 0,
    pnl_other DECIMAL(20, 2) DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one record per book per day
    CONSTRAINT unique_book_daily_return UNIQUE (tenant_id, book_id, return_date)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_book_daily_returns_tenant_date
    ON book_daily_returns(tenant_id, return_date DESC);
CREATE INDEX IF NOT EXISTS idx_book_daily_returns_book_date
    ON book_daily_returns(book_id, return_date DESC);
CREATE INDEX IF NOT EXISTS idx_book_daily_returns_date
    ON book_daily_returns(return_date DESC);

-- RLS Policy
ALTER TABLE book_daily_returns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for book_daily_returns"
    ON book_daily_returns
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);


-- =============================================================================
-- PM DAILY RETURNS (Aggregated from books)
-- =============================================================================
-- Stores daily P&L aggregated at PM level
-- Used for PM-to-PM correlation analysis

CREATE TABLE IF NOT EXISTS pm_daily_returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pm_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Date
    return_date DATE NOT NULL,

    -- Aggregated P&L
    daily_pnl DECIMAL(20, 2) NOT NULL DEFAULT 0,
    daily_return_pct DECIMAL(10, 6),

    -- NAV
    start_of_day_nav DECIMAL(20, 2),
    end_of_day_nav DECIMAL(20, 2),

    -- Breakdown by RiskPod
    pnl_equity DECIMAL(20, 2) DEFAULT 0,
    pnl_rates DECIMAL(20, 2) DEFAULT 0,
    pnl_credit DECIMAL(20, 2) DEFAULT 0,
    pnl_fx DECIMAL(20, 2) DEFAULT 0,
    pnl_other DECIMAL(20, 2) DEFAULT 0,

    -- Number of books contributing
    book_count INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_pm_daily_return UNIQUE (tenant_id, pm_id, return_date)
);

CREATE INDEX IF NOT EXISTS idx_pm_daily_returns_tenant_date
    ON pm_daily_returns(tenant_id, return_date DESC);
CREATE INDEX IF NOT EXISTS idx_pm_daily_returns_pm_date
    ON pm_daily_returns(pm_id, return_date DESC);

ALTER TABLE pm_daily_returns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for pm_daily_returns"
    ON pm_daily_returns
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);


-- =============================================================================
-- CORRELATION CACHE
-- =============================================================================
-- Pre-computed correlations for efficient querying
-- Recalculated daily (or on-demand)

DO $$ BEGIN
    CREATE TYPE correlation_entity_type AS ENUM ('book', 'pm', 'fund', 'pod');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE correlation_window AS ENUM ('1d', '5d', '21d', '63d', '252d');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE correlation_type AS ENUM ('realized', 'implied');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS correlation_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- What entities are being correlated
    entity_type correlation_entity_type NOT NULL,
    entity1_id UUID NOT NULL,                              -- Book/PM/Fund/Pod ID
    entity1_name VARCHAR(255),                             -- Denormalized for display
    entity2_id UUID NOT NULL,
    entity2_name VARCHAR(255),

    -- Correlation details
    correlation_type correlation_type NOT NULL DEFAULT 'realized',
    time_window correlation_window NOT NULL,

    -- The correlation value (-1 to 1)
    correlation_value DECIMAL(6, 4) NOT NULL,

    -- Statistical confidence
    data_points INT,                                       -- Number of observations
    p_value DECIMAL(10, 8),                               -- Statistical significance

    -- When was this calculated
    as_of_date DATE NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one correlation per pair per window per date
    CONSTRAINT unique_correlation UNIQUE (
        tenant_id, entity_type, entity1_id, entity2_id,
        correlation_type, time_window, as_of_date
    )
);

CREATE INDEX IF NOT EXISTS idx_correlation_cache_lookup
    ON correlation_cache(tenant_id, entity_type, entity1_id, entity2_id, time_window);
CREATE INDEX IF NOT EXISTS idx_correlation_cache_date
    ON correlation_cache(as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_correlation_cache_entity1
    ON correlation_cache(entity1_id, time_window);

ALTER TABLE correlation_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for correlation_cache"
    ON correlation_cache
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);


-- =============================================================================
-- POD DAILY RETURNS (Firm-level by RiskPod)
-- =============================================================================
-- Aggregated returns at the RiskPod level for cross-asset correlation

CREATE TABLE IF NOT EXISTS pod_daily_returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- RiskPod (stored as string to match our enum)
    pod VARCHAR(20) NOT NULL CHECK (pod IN ('equity', 'rates', 'credit', 'fx', 'other')),

    -- Date
    return_date DATE NOT NULL,

    -- Aggregated P&L
    daily_pnl DECIMAL(20, 2) NOT NULL DEFAULT 0,
    daily_return_pct DECIMAL(10, 6),

    -- Exposure context
    start_of_day_exposure DECIMAL(20, 2),
    end_of_day_exposure DECIMAL(20, 2),

    -- Contributing entities
    pm_count INT DEFAULT 0,
    book_count INT DEFAULT 0,
    position_count INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_pod_daily_return UNIQUE (tenant_id, pod, return_date)
);

CREATE INDEX IF NOT EXISTS idx_pod_daily_returns_tenant_date
    ON pod_daily_returns(tenant_id, return_date DESC);
CREATE INDEX IF NOT EXISTS idx_pod_daily_returns_pod_date
    ON pod_daily_returns(pod, return_date DESC);

ALTER TABLE pod_daily_returns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for pod_daily_returns"
    ON pod_daily_returns
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);


-- =============================================================================
-- BENCHMARK RETURNS (for comparison)
-- =============================================================================
-- Store benchmark returns for correlation vs market

CREATE TABLE IF NOT EXISTS benchmark_returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Benchmark identification
    benchmark_code VARCHAR(20) NOT NULL,                   -- SPY, AGG, HYG, DXY, etc.
    benchmark_name VARCHAR(100),

    -- Date
    return_date DATE NOT NULL,

    -- Return data
    daily_return_pct DECIMAL(10, 6) NOT NULL,
    price_close DECIMAL(20, 6),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_benchmark_return UNIQUE (benchmark_code, return_date)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_returns_code_date
    ON benchmark_returns(benchmark_code, return_date DESC);

-- Seed common benchmarks
INSERT INTO benchmark_returns (benchmark_code, benchmark_name, return_date, daily_return_pct)
VALUES
    ('SPY', 'S&P 500 ETF', CURRENT_DATE, 0),
    ('AGG', 'US Aggregate Bond ETF', CURRENT_DATE, 0),
    ('HYG', 'High Yield Corporate Bond ETF', CURRENT_DATE, 0),
    ('DXY', 'US Dollar Index', CURRENT_DATE, 0),
    ('GLD', 'Gold ETF', CURRENT_DATE, 0),
    ('VIX', 'Volatility Index', CURRENT_DATE, 0)
ON CONFLICT (benchmark_code, return_date) DO NOTHING;


-- =============================================================================
-- HELPER FUNCTION: Calculate correlation between two return series
-- =============================================================================

CREATE OR REPLACE FUNCTION calculate_correlation(
    returns1 DECIMAL[],
    returns2 DECIMAL[]
) RETURNS DECIMAL AS $$
DECLARE
    n INT;
    mean1 DECIMAL;
    mean2 DECIMAL;
    sum_xy DECIMAL := 0;
    sum_x2 DECIMAL := 0;
    sum_y2 DECIMAL := 0;
    i INT;
    dx DECIMAL;
    dy DECIMAL;
BEGIN
    n := LEAST(array_length(returns1, 1), array_length(returns2, 1));

    IF n IS NULL OR n < 2 THEN
        RETURN NULL;
    END IF;

    -- Calculate means
    SELECT AVG(val) INTO mean1 FROM unnest(returns1[1:n]) AS val;
    SELECT AVG(val) INTO mean2 FROM unnest(returns2[1:n]) AS val;

    -- Calculate correlation components
    FOR i IN 1..n LOOP
        dx := returns1[i] - mean1;
        dy := returns2[i] - mean2;
        sum_xy := sum_xy + (dx * dy);
        sum_x2 := sum_x2 + (dx * dx);
        sum_y2 := sum_y2 + (dy * dy);
    END LOOP;

    -- Avoid division by zero
    IF sum_x2 = 0 OR sum_y2 = 0 THEN
        RETURN 0;
    END IF;

    RETURN sum_xy / SQRT(sum_x2 * sum_y2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- =============================================================================
-- TRIGGER: Update updated_at timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_returns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER book_daily_returns_updated_at
    BEFORE UPDATE ON book_daily_returns
    FOR EACH ROW
    EXECUTE FUNCTION update_returns_updated_at();

CREATE TRIGGER pm_daily_returns_updated_at
    BEFORE UPDATE ON pm_daily_returns
    FOR EACH ROW
    EXECUTE FUNCTION update_returns_updated_at();


-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE book_daily_returns IS 'Daily P&L and returns per trading book - foundation for correlation analysis';
COMMENT ON TABLE pm_daily_returns IS 'Daily P&L aggregated at PM level - for PM-to-PM correlation';
COMMENT ON TABLE correlation_cache IS 'Pre-computed correlations for efficient AI queries';
COMMENT ON TABLE pod_daily_returns IS 'Daily returns by RiskPod for cross-asset correlation';
COMMENT ON TABLE benchmark_returns IS 'Market benchmark returns for comparison';
COMMENT ON FUNCTION calculate_correlation IS 'Pearson correlation between two return arrays';
