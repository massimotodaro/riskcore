-- Migration: Overlay Book Support
-- Adds support for CIO overlay books and valuation transparency
-- Part of Week 5: CIO/PM Role-Based Dashboard feature

-- ============================================
-- 1. Add book_type to books table
-- ============================================

-- Create book_type enum
DO $$ BEGIN
    CREATE TYPE public.book_type AS ENUM ('trading', 'overlay');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add book_type column to books table
ALTER TABLE public.books
ADD COLUMN IF NOT EXISTS book_type public.book_type DEFAULT 'trading';

COMMENT ON COLUMN public.books.book_type IS
'trading = normal PM book, overlay = CIO hedge book for firm-wide risk offset';

-- ============================================
-- 2. Create overlay_book_sources table
-- ============================================
-- Links overlay books to the source books they hedge

CREATE TABLE IF NOT EXISTS public.overlay_book_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    overlay_book_id UUID NOT NULL REFERENCES public.books(id) ON DELETE CASCADE,
    source_book_id UUID NOT NULL REFERENCES public.books(id) ON DELETE CASCADE,
    hedge_weight NUMERIC(10,4) DEFAULT 1.0,
    target_metric VARCHAR(50), -- 'delta', 'dv01', 'var_95', etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT overlay_source_different CHECK (overlay_book_id != source_book_id),
    CONSTRAINT unique_overlay_source UNIQUE (overlay_book_id, source_book_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_overlay_sources_tenant ON public.overlay_book_sources(tenant_id);
CREATE INDEX IF NOT EXISTS idx_overlay_sources_overlay_book ON public.overlay_book_sources(overlay_book_id);
CREATE INDEX IF NOT EXISTS idx_overlay_sources_source_book ON public.overlay_book_sources(source_book_id);

-- RLS for overlay_book_sources
ALTER TABLE public.overlay_book_sources ENABLE ROW LEVEL SECURITY;

-- Only CIO/CRO/Admin can view overlay relationships
CREATE POLICY "Users can view overlay sources for their tenant" ON public.overlay_book_sources
    FOR SELECT USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
        AND (SELECT role FROM public.users WHERE id = auth.uid()) IN ('superadmin', 'admin', 'cio', 'cro')
    );

-- Only CIO/CRO can manage overlay relationships
CREATE POLICY "CIO/CRO can manage overlay sources" ON public.overlay_book_sources
    FOR ALL USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
        AND (SELECT role FROM public.users WHERE id = auth.uid()) IN ('superadmin', 'admin', 'cio', 'cro')
    );

COMMENT ON TABLE public.overlay_book_sources IS
'Links overlay (hedge) books to the source books they are designed to offset';

-- ============================================
-- 3. Create model_valuation_inputs table
-- ============================================
-- For valuation transparency - shows model inputs and allows overrides

CREATE TABLE IF NOT EXISTS public.model_valuation_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    position_id UUID REFERENCES public.positions(id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES public.securities(id) ON DELETE CASCADE,

    -- Model identification
    model_name VARCHAR(100) NOT NULL, -- 'black_scholes', 'hull_white', 'binomial', etc.
    model_version VARCHAR(50),

    -- Inputs (stored as JSONB for flexibility)
    inputs JSONB NOT NULL,
    -- Example: {"spot": 150.0, "strike": 155.0, "vol": 0.25, "rate": 0.05, "time_to_expiry": 0.5}

    -- Calculated output
    model_price NUMERIC(18,6),

    -- Override tracking
    has_override BOOLEAN DEFAULT false,
    override_inputs JSONB, -- User's manual overrides
    override_by UUID REFERENCES public.users(id),
    override_at TIMESTAMPTZ,
    override_reason TEXT,

    calculated_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_model_valuation_tenant ON public.model_valuation_inputs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_model_valuation_security ON public.model_valuation_inputs(security_id);
CREATE INDEX IF NOT EXISTS idx_model_valuation_position ON public.model_valuation_inputs(position_id);
CREATE INDEX IF NOT EXISTS idx_model_valuation_model ON public.model_valuation_inputs(model_name);

-- RLS for model_valuation_inputs
ALTER TABLE public.model_valuation_inputs ENABLE ROW LEVEL SECURITY;

-- Users can view valuation inputs for positions they have access to
CREATE POLICY "Users can view model valuations for their tenant" ON public.model_valuation_inputs
    FOR SELECT USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
    );

-- Only authorized users can override valuations
CREATE POLICY "Authorized users can manage model valuations" ON public.model_valuation_inputs
    FOR ALL USING (
        tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid())
        AND (SELECT role FROM public.users WHERE id = auth.uid()) IN ('superadmin', 'admin', 'cio', 'cro', 'pm')
    );

COMMENT ON TABLE public.model_valuation_inputs IS
'Stores model pricing inputs for valuation transparency. Shows how model-derived prices are calculated and allows authorized overrides.';

-- ============================================
-- 4. Create v_risk_by_asset_class view
-- ============================================
-- Aggregates risk by asset class for RiskPod display

CREATE OR REPLACE VIEW public.v_risk_by_asset_class AS
SELECT
    p.tenant_id,
    p.book_id,
    b.name as book_name,
    b.book_type,
    b.pm_id,
    s.asset_class,
    COUNT(*) as position_count,
    SUM(ABS(p.market_value)) as gross_exposure,
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,
    SUM(COALESCE(p.delta, 0)) as total_delta,
    SUM(COALESCE(p.gamma, 0)) as total_gamma,
    SUM(COALESCE(p.vega, 0)) as total_vega,
    SUM(COALESCE(p.theta, 0)) as total_theta,
    SUM(COALESCE(p.rho, 0)) as total_rho,
    SUM(COALESCE(p.dv01, 0)) as total_dv01,
    SUM(COALESCE(p.cs01, 0)) as total_cs01,
    SUM(COALESCE(p.convexity, 0)) as total_convexity
FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
JOIN public.books b ON p.book_id = b.id
WHERE p.quantity != 0
GROUP BY p.tenant_id, p.book_id, b.name, b.book_type, b.pm_id, s.asset_class;

COMMENT ON VIEW public.v_risk_by_asset_class IS
'Aggregated risk metrics by asset class for each book. Used by RiskPod dashboard components.';

-- ============================================
-- 5. Create v_firm_risk_by_asset_class view
-- ============================================
-- Firm-wide aggregation across all books

CREATE OR REPLACE VIEW public.v_firm_risk_by_asset_class AS
SELECT
    p.tenant_id,
    s.asset_class,
    COUNT(*) as position_count,
    COUNT(DISTINCT p.book_id) as book_count,
    SUM(ABS(p.market_value)) as gross_exposure,
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,
    SUM(COALESCE(p.delta, 0)) as total_delta,
    SUM(COALESCE(p.gamma, 0)) as total_gamma,
    SUM(COALESCE(p.vega, 0)) as total_vega,
    SUM(COALESCE(p.theta, 0)) as total_theta,
    SUM(COALESCE(p.rho, 0)) as total_rho,
    SUM(COALESCE(p.dv01, 0)) as total_dv01,
    SUM(COALESCE(p.cs01, 0)) as total_cs01,
    SUM(COALESCE(p.convexity, 0)) as total_convexity
FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
WHERE p.quantity != 0
GROUP BY p.tenant_id, s.asset_class;

COMMENT ON VIEW public.v_firm_risk_by_asset_class IS
'Firm-wide aggregated risk metrics by asset class. Used by CIO dashboard Row 1.';

-- ============================================
-- 6. Create v_overlay_risk_by_asset_class view
-- ============================================
-- Overlay book risk only

CREATE OR REPLACE VIEW public.v_overlay_risk_by_asset_class AS
SELECT
    p.tenant_id,
    p.book_id,
    b.name as book_name,
    s.asset_class,
    COUNT(*) as position_count,
    SUM(ABS(p.market_value)) as gross_exposure,
    SUM(CASE WHEN p.direction = 'long' THEN p.market_value ELSE -p.market_value END) as net_exposure,
    SUM(COALESCE(p.delta, 0)) as total_delta,
    SUM(COALESCE(p.gamma, 0)) as total_gamma,
    SUM(COALESCE(p.vega, 0)) as total_vega,
    SUM(COALESCE(p.theta, 0)) as total_theta,
    SUM(COALESCE(p.rho, 0)) as total_rho,
    SUM(COALESCE(p.dv01, 0)) as total_dv01,
    SUM(COALESCE(p.cs01, 0)) as total_cs01,
    SUM(COALESCE(p.convexity, 0)) as total_convexity
FROM public.positions p
JOIN public.securities s ON p.security_id = s.id
JOIN public.books b ON p.book_id = b.id
WHERE p.quantity != 0
  AND b.book_type = 'overlay'
GROUP BY p.tenant_id, p.book_id, b.name, s.asset_class;

COMMENT ON VIEW public.v_overlay_risk_by_asset_class IS
'Risk metrics for overlay (hedge) books only by asset class. Used by CIO dashboard Row 2.';

-- ============================================
-- 7. Update trigger for overlay_book_sources
-- ============================================

CREATE OR REPLACE FUNCTION public.update_overlay_book_sources_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_overlay_book_sources_updated_at ON public.overlay_book_sources;
CREATE TRIGGER trigger_overlay_book_sources_updated_at
    BEFORE UPDATE ON public.overlay_book_sources
    FOR EACH ROW
    EXECUTE FUNCTION public.update_overlay_book_sources_updated_at();
