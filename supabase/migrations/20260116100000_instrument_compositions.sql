-- ============================================
-- INSTRUMENT COMPOSITIONS
-- Structured note component breakdown for pricing and risk attribution
-- ============================================

-- Template for structured instrument compositions
CREATE TABLE IF NOT EXISTS instrument_compositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,

    -- What instrument this composition defines
    name VARCHAR(200) NOT NULL,              -- "ABC Structured Note"
    name_normalized VARCHAR(200) NOT NULL,   -- Lowercase, trimmed for matching
    description TEXT,

    -- Lifecycle
    is_template BOOLEAN DEFAULT TRUE,        -- Reusable for future imports?
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_composition_name UNIQUE(tenant_id, name_normalized)
);

-- Components within a composition
CREATE TABLE IF NOT EXISTS composition_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID NOT NULL REFERENCES instrument_compositions(id) ON DELETE CASCADE,

    -- Component definition
    instrument_type_id UUID REFERENCES instrument_types(id) ON DELETE SET NULL,
    component_name VARCHAR(200) NOT NULL,     -- "S&P 500 Future Mar 2025"

    -- Allocation
    allocation_type VARCHAR(20) DEFAULT 'percentage',  -- 'percentage' or 'notional'
    allocation_value DECIMAL(18,4) NOT NULL,  -- 33.33 (%) or 10000000 (notional)

    -- Optional: link to actual security for pricing
    security_id UUID REFERENCES securities(id) ON DELETE SET NULL,

    -- Risk parameters (can override or supplement from linked security)
    delta DECIMAL(10,6),
    gamma DECIMAL(10,6),
    vega DECIMAL(10,6),
    theta DECIMAL(10,6),
    rho DECIMAL(10,6),
    duration DECIMAL(10,4),
    convexity DECIMAL(10,4),
    dv01 DECIMAL(18,4),

    -- Ordering for display
    order_num INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Link positions to their composition (for structured positions)
CREATE TABLE IF NOT EXISTS position_compositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    composition_id UUID NOT NULL REFERENCES instrument_compositions(id) ON DELETE CASCADE,

    -- Snapshot of allocation at time of assignment
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by UUID REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT uq_position_composition UNIQUE(position_id)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_composition_tenant ON instrument_compositions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_composition_name_normalized ON instrument_compositions(name_normalized);
CREATE INDEX IF NOT EXISTS idx_composition_active ON instrument_compositions(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_components_composition ON composition_components(composition_id);
CREATE INDEX IF NOT EXISTS idx_components_type ON composition_components(instrument_type_id);
CREATE INDEX IF NOT EXISTS idx_components_security ON composition_components(security_id) WHERE security_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_position_compositions_position ON position_compositions(position_id);
CREATE INDEX IF NOT EXISTS idx_position_compositions_composition ON position_compositions(composition_id);

-- ============================================
-- TRIGGERS
-- ============================================

-- Update timestamp trigger for instrument_compositions
CREATE OR REPLACE FUNCTION update_composition_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_composition_updated_at ON instrument_compositions;
CREATE TRIGGER trigger_composition_updated_at
    BEFORE UPDATE ON instrument_compositions
    FOR EACH ROW
    EXECUTE FUNCTION update_composition_timestamp();

-- ============================================
-- VIEWS
-- ============================================

-- Composition with component details and risk attribution
CREATE OR REPLACE VIEW v_composition_details AS
SELECT
    ic.id AS composition_id,
    ic.tenant_id,
    ic.name AS composition_name,
    ic.description,
    ic.is_template,
    ic.is_active,
    COUNT(cc.id) AS component_count,
    SUM(CASE WHEN cc.allocation_type = 'percentage' THEN cc.allocation_value ELSE 0 END) AS total_percentage,
    -- Risk attribution by RiskPod
    SUM(CASE WHEN it.riskpod = 'equity' THEN cc.allocation_value ELSE 0 END) AS equity_allocation,
    SUM(CASE WHEN it.riskpod = 'rates' THEN cc.allocation_value ELSE 0 END) AS rates_allocation,
    SUM(CASE WHEN it.riskpod = 'credit' THEN cc.allocation_value ELSE 0 END) AS credit_allocation,
    SUM(CASE WHEN it.riskpod = 'fx' THEN cc.allocation_value ELSE 0 END) AS fx_allocation,
    SUM(CASE WHEN it.riskpod = 'other' THEN cc.allocation_value ELSE 0 END) AS other_allocation,
    ic.created_at,
    ic.updated_at
FROM instrument_compositions ic
LEFT JOIN composition_components cc ON cc.composition_id = ic.id
LEFT JOIN instrument_types it ON cc.instrument_type_id = it.id
GROUP BY ic.id;

-- Position risk attribution view
CREATE OR REPLACE VIEW v_position_risk_attribution AS
SELECT
    p.id AS position_id,
    p.tenant_id,
    p.book_id,
    p.security_id,
    s.name AS security_name,
    p.quantity,
    p.direction,
    COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) AS position_value,
    pc.composition_id,
    ic.name AS composition_name,
    -- Calculate attributed values by RiskPod
    CASE WHEN pc.composition_id IS NOT NULL THEN
        COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) *
        COALESCE((SELECT SUM(cc.allocation_value)/100.0 FROM composition_components cc
                  JOIN instrument_types it ON cc.instrument_type_id = it.id
                  WHERE cc.composition_id = pc.composition_id AND it.riskpod = 'equity'), 0)
    ELSE
        CASE WHEN s.asset_class IN ('equity', 'fund') OR
                  (SELECT riskpod FROM instrument_types WHERE code = UPPER(s.asset_class)) = 'equity'
             THEN COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0))
             ELSE 0
        END
    END AS equity_exposure,
    CASE WHEN pc.composition_id IS NOT NULL THEN
        COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) *
        COALESCE((SELECT SUM(cc.allocation_value)/100.0 FROM composition_components cc
                  JOIN instrument_types it ON cc.instrument_type_id = it.id
                  WHERE cc.composition_id = pc.composition_id AND it.riskpod = 'rates'), 0)
    ELSE
        CASE WHEN s.asset_class = 'fixed_income' OR s.asset_class = 'swap'
             THEN COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0))
             ELSE 0
        END
    END AS rates_exposure,
    CASE WHEN pc.composition_id IS NOT NULL THEN
        COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) *
        COALESCE((SELECT SUM(cc.allocation_value)/100.0 FROM composition_components cc
                  JOIN instrument_types it ON cc.instrument_type_id = it.id
                  WHERE cc.composition_id = pc.composition_id AND it.riskpod = 'credit'), 0)
    ELSE
        CASE WHEN s.asset_class = 'cds'
             THEN COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0))
             ELSE 0
        END
    END AS credit_exposure,
    CASE WHEN pc.composition_id IS NOT NULL THEN
        COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0)) *
        COALESCE((SELECT SUM(cc.allocation_value)/100.0 FROM composition_components cc
                  JOIN instrument_types it ON cc.instrument_type_id = it.id
                  WHERE cc.composition_id = pc.composition_id AND it.riskpod = 'fx'), 0)
    ELSE
        CASE WHEN s.asset_class = 'fx'
             THEN COALESCE(p.market_value_base, p.quantity * COALESCE(p.price, 0))
             ELSE 0
        END
    END AS fx_exposure
FROM positions p
JOIN securities s ON p.security_id = s.id
LEFT JOIN position_compositions pc ON pc.position_id = p.id
LEFT JOIN instrument_compositions ic ON pc.composition_id = ic.id
WHERE p.is_active = TRUE;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE instrument_compositions IS 'Templates for structured instrument compositions (e.g., structured notes with multiple components)';
COMMENT ON TABLE composition_components IS 'Individual components within a composition, each with allocation and optional risk parameters';
COMMENT ON TABLE position_compositions IS 'Links positions to their composition template for risk attribution';

COMMENT ON COLUMN composition_components.allocation_type IS 'percentage = % of total, notional = absolute value';
COMMENT ON COLUMN composition_components.allocation_value IS 'Value depends on allocation_type: percentage (0-100) or notional amount';
COMMENT ON COLUMN composition_components.security_id IS 'Optional link to actual security for live pricing';

COMMENT ON VIEW v_composition_details IS 'Aggregated view of compositions with component counts and RiskPod allocation breakdown';
COMMENT ON VIEW v_position_risk_attribution IS 'Position-level risk attribution across RiskPods, accounting for compositions';

-- ============================================
-- UPDATES TO UNMATCHED_INSTRUMENTS
-- ============================================

-- Add column to link decomposed instruments to their composition
ALTER TABLE unmatched_instruments
ADD COLUMN IF NOT EXISTS resolved_composition_id UUID REFERENCES instrument_compositions(id) ON DELETE SET NULL;

-- Add 'decomposed' as valid status
COMMENT ON COLUMN unmatched_instruments.status IS 'Status: pending, mapped, ignored, escalated, decomposed';
