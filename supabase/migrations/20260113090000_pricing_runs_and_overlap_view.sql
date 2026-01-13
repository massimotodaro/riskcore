-- Migration: Pricing Runs and Position Overlap View
-- Part of Riskboard Dashboard feature
-- Adds pricing job tracking and position overlap detection for correlation panel

-- ============================================
-- 1. Create pricing_runs table
-- ============================================
-- Tracks pricing jobs (scheduled, manual, single security)

CREATE TABLE IF NOT EXISTS public.pricing_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,

    -- Who triggered this run
    triggered_by UUID REFERENCES public.users(id),  -- NULL if scheduled
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('scheduled', 'manual', 'single_security')),

    -- Timing
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,

    -- Results
    securities_priced INT DEFAULT 0,
    securities_failed INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),

    -- Error details (if failed)
    error_details JSONB,

    -- Configuration used for this run
    config JSONB,  -- {"price_source": "openbb", "provider": "yahoo", etc.}

    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pricing_runs_tenant ON public.pricing_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pricing_runs_status ON public.pricing_runs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_pricing_runs_started ON public.pricing_runs(started_at DESC);

-- RLS
ALTER TABLE public.pricing_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view pricing runs for their tenant" ON public.pricing_runs
    FOR SELECT USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
    );

CREATE POLICY "Authorized users can trigger pricing runs" ON public.pricing_runs
    FOR INSERT WITH CHECK (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
        AND (SELECT role FROM public.users WHERE id = auth.uid()) IN ('superadmin', 'admin', 'cio', 'cro')
    );

CREATE POLICY "System can update pricing runs" ON public.pricing_runs
    FOR UPDATE USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
    );

COMMENT ON TABLE public.pricing_runs IS
'Tracks pricing jobs - scheduled daily repricing or manual reprice-all triggers. Used for Riskboard "Last Priced" timestamp.';

-- ============================================
-- 2. Create v_position_overlap view
-- ============================================
-- Identifies positions held across multiple books (for correlation panel)
-- Note: ticker is stored in security_identifiers table, not securities

CREATE OR REPLACE VIEW public.v_position_overlap AS
SELECT
    p.tenant_id,
    p.security_id,
    COALESCE(si.identifier_value, s.figi) as ticker,
    s.name as security_name,
    s.asset_class,

    -- How many books hold this security
    COUNT(DISTINCT p.book_id) as book_count,

    -- Which books hold it
    ARRAY_AGG(DISTINCT b.name ORDER BY b.name) as books,
    ARRAY_AGG(DISTINCT p.book_id) as book_ids,

    -- Net position across all books
    SUM(CASE WHEN p.direction = 'long' THEN p.quantity ELSE -p.quantity END) as net_quantity,

    -- Gross exposure (absolute sum)
    SUM(ABS(p.market_value)) as gross_exposure,

    -- Net exposure
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,

    -- Netting opportunity: difference between gross and net (what cancels out)
    SUM(ABS(p.market_value)) - ABS(SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END)) as netting_opportunity,

    -- Risk metrics
    SUM(COALESCE(p.delta, 0)) as net_delta,
    SUM(COALESCE(p.dv01, 0)) as net_dv01,
    SUM(COALESCE(p.cs01, 0)) as net_cs01

FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
JOIN public.books b ON p.book_id = b.id
LEFT JOIN public.security_identifiers si ON p.security_id = si.security_id AND si.identifier_type = 'ticker'
WHERE p.quantity != 0
GROUP BY p.tenant_id, p.security_id, si.identifier_value, s.figi, s.name, s.asset_class
HAVING COUNT(DISTINCT p.book_id) > 1;

COMMENT ON VIEW public.v_position_overlap IS
'Shows positions held by multiple books - identifies netting opportunities and concentration. Used by Correlation Panel in Riskboard.';

-- ============================================
-- 3. Create v_concentration_by_sector view
-- ============================================
-- Identifies sector concentration for correlation panel

CREATE OR REPLACE VIEW public.v_concentration_by_sector AS
WITH tenant_totals AS (
    SELECT
        tenant_id,
        SUM(ABS(market_value)) as total_exposure
    FROM public.positions
    WHERE quantity != 0
    GROUP BY tenant_id
)
SELECT
    p.tenant_id,
    s.sector,
    COUNT(DISTINCT p.security_id) as security_count,
    COUNT(DISTINCT p.book_id) as book_count,
    SUM(ABS(p.market_value)) as gross_exposure,
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,

    -- Percentage of total firm exposure
    ROUND(
        (SUM(ABS(p.market_value)) / NULLIF(t.total_exposure, 0) * 100)::numeric,
        2
    ) as percentage,

    -- Warning flag: sector > 40% is high concentration
    CASE WHEN (SUM(ABS(p.market_value)) / NULLIF(t.total_exposure, 0) * 100) > 40 THEN true ELSE false END as is_warning

FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
JOIN tenant_totals t ON p.tenant_id = t.tenant_id
WHERE p.quantity != 0
  AND s.sector IS NOT NULL
GROUP BY p.tenant_id, s.sector, t.total_exposure
ORDER BY gross_exposure DESC;

COMMENT ON VIEW public.v_concentration_by_sector IS
'Sector concentration analysis for Correlation Panel. Flags sectors with >40% exposure.';

-- ============================================
-- 4. Create v_concentration_by_security view
-- ============================================
-- Identifies single-name concentration

CREATE OR REPLACE VIEW public.v_concentration_by_security AS
WITH tenant_totals AS (
    SELECT
        tenant_id,
        SUM(ABS(market_value)) as total_exposure
    FROM public.positions
    WHERE quantity != 0
    GROUP BY tenant_id
)
SELECT
    p.tenant_id,
    p.security_id,
    COALESCE(si.identifier_value, s.figi) as ticker,
    s.name as security_name,
    s.sector,
    s.asset_class,
    COUNT(DISTINCT p.book_id) as book_count,
    SUM(ABS(p.market_value)) as gross_exposure,
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,

    -- Percentage of total firm exposure
    ROUND(
        (SUM(ABS(p.market_value)) / NULLIF(t.total_exposure, 0) * 100)::numeric,
        2
    ) as percentage,

    -- Warning flag: single name > 10% is high concentration
    CASE WHEN (SUM(ABS(p.market_value)) / NULLIF(t.total_exposure, 0) * 100) > 10 THEN true ELSE false END as is_warning

FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
JOIN tenant_totals t ON p.tenant_id = t.tenant_id
LEFT JOIN public.security_identifiers si ON p.security_id = si.security_id AND si.identifier_type = 'ticker'
WHERE p.quantity != 0
GROUP BY p.tenant_id, p.security_id, si.identifier_value, s.figi, s.name, s.sector, s.asset_class, t.total_exposure
ORDER BY gross_exposure DESC;

COMMENT ON VIEW public.v_concentration_by_security IS
'Single-name concentration analysis for Correlation Panel. Flags securities with >10% exposure.';

-- ============================================
-- 5. Create v_risk_summary view
-- ============================================
-- Top bar summary (NAV, Gross, Net)

CREATE OR REPLACE VIEW public.v_risk_summary AS
SELECT
    tenant_id,

    -- NAV (net asset value = net exposure)
    SUM(CASE WHEN direction = 'long' THEN market_value ELSE -market_value END) as nav,

    -- Gross exposure (absolute sum)
    SUM(ABS(market_value)) as gross_exposure,

    -- Net exposure
    SUM(CASE WHEN direction = 'long' THEN market_value ELSE -market_value END) as net_exposure,

    -- Long/Short breakdown
    SUM(CASE WHEN direction = 'long' THEN market_value ELSE 0 END) as long_exposure,
    SUM(CASE WHEN direction = 'short' THEN ABS(market_value) ELSE 0 END) as short_exposure,

    -- Position counts
    COUNT(*) as position_count,
    COUNT(DISTINCT security_id) as security_count,
    COUNT(DISTINCT book_id) as book_count,

    -- Risk metrics
    SUM(COALESCE(delta, 0)) as total_delta,
    SUM(COALESCE(dv01, 0)) as total_dv01,
    SUM(COALESCE(cs01, 0)) as total_cs01

FROM public.positions
WHERE quantity != 0
GROUP BY tenant_id;

COMMENT ON VIEW public.v_risk_summary IS
'Top bar summary metrics: NAV, Gross Exposure, Net Exposure. Used by Riskboard TopBar component.';

-- ============================================
-- 6. Add model_id reference to security_prices
-- ============================================
-- Link to model_valuation_inputs for model-derived prices

ALTER TABLE public.security_prices
ADD COLUMN IF NOT EXISTS model_id UUID REFERENCES public.model_valuation_inputs(id);

COMMENT ON COLUMN public.security_prices.model_id IS
'Reference to model_valuation_inputs for model-derived prices. NULL for market prices.';
