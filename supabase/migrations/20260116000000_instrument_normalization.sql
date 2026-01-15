-- ============================================================
-- INSTRUMENT NAME NORMALIZATION LAYER
-- Migration: 20260116000000_instrument_normalization.sql
--
-- Purpose: Enable translation of varied client instrument names
-- to canonical forms for correct RiskPod assignment.
-- ============================================================

-- ============================================================
-- CANONICAL INSTRUMENT TYPES
-- ============================================================
-- Master list of instrument types with their canonical names.
-- Global scope (not tenant-specific).

CREATE TABLE IF NOT EXISTS instrument_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,           -- 'CDS', 'IRS', 'FRA', etc.
    canonical_name VARCHAR(100) NOT NULL,       -- 'Credit Default Swap'
    asset_class asset_class NOT NULL,           -- Maps to existing enum
    riskpod VARCHAR(20) NOT NULL,               -- 'equity', 'rates', 'credit', 'fx', 'other'
    description TEXT,
    has_tenor BOOLEAN DEFAULT FALSE,            -- Does this type have tenor/maturity?
    default_tenor VARCHAR(20),                  -- Default tenor if not specified
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instrument_types_code ON instrument_types(code);
CREATE INDEX IF NOT EXISTS idx_instrument_types_asset_class ON instrument_types(asset_class);
CREATE INDEX IF NOT EXISTS idx_instrument_types_riskpod ON instrument_types(riskpod);

-- ============================================================
-- INSTRUMENT ALIASES (SYNONYMS)
-- ============================================================
-- Aliases/synonyms that map to canonical instrument types.
-- Can be global (tenant_id NULL) or tenant-specific override.

CREATE TABLE IF NOT EXISTS instrument_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_type_id UUID NOT NULL REFERENCES instrument_types(id) ON DELETE CASCADE,
    alias VARCHAR(200) NOT NULL,                -- 'Credit Default Swap', 'CDS 5Y', etc.
    alias_normalized VARCHAR(200) NOT NULL,     -- Lowercase, stripped for matching
    match_type VARCHAR(20) DEFAULT 'exact',     -- 'exact', 'prefix', 'contains', 'regex'
    priority INTEGER DEFAULT 100,               -- Higher = preferred (for conflicts)
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL = global
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique per normalized alias per tenant scope
    CONSTRAINT uq_alias_per_tenant UNIQUE(alias_normalized, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_instrument_aliases_normalized ON instrument_aliases(alias_normalized);
CREATE INDEX IF NOT EXISTS idx_instrument_aliases_type_id ON instrument_aliases(instrument_type_id);
CREATE INDEX IF NOT EXISTS idx_instrument_aliases_tenant ON instrument_aliases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_instrument_aliases_match_type ON instrument_aliases(match_type);

-- ============================================================
-- TENOR PATTERNS
-- ============================================================
-- Regex patterns for extracting tenor from instrument names.

CREATE TABLE IF NOT EXISTS tenor_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern VARCHAR(300) NOT NULL,              -- Regex pattern
    tenor_group INTEGER DEFAULT 1,              -- Capture group for tenor value
    unit_group INTEGER,                         -- Capture group for unit (Y/M/D)
    example VARCHAR(150),                       -- Example match
    priority INTEGER DEFAULT 100,               -- Higher = try first
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- NORMALIZATION RESULTS CACHE
-- ============================================================
-- Cache of normalization results for performance.
-- Also serves as audit trail.

CREATE TABLE IF NOT EXISTS instrument_normalization_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    input_value VARCHAR(300) NOT NULL,          -- Original input
    input_normalized VARCHAR(300) NOT NULL,     -- Normalized for lookup
    matched_alias_id UUID REFERENCES instrument_aliases(id) ON DELETE SET NULL,
    instrument_type_id UUID REFERENCES instrument_types(id) ON DELETE SET NULL,
    asset_class VARCHAR(50),
    riskpod VARCHAR(20),
    extracted_tenor VARCHAR(20),
    confidence_score DECIMAL(5,4),              -- 0.0000 to 1.0000
    match_method VARCHAR(20),                   -- 'exact', 'fuzzy', 'pattern', 'unmatched'
    is_manual_override BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',

    -- Cache key: tenant + normalized input
    CONSTRAINT uq_cache_key UNIQUE(tenant_id, input_normalized)
);

CREATE INDEX IF NOT EXISTS idx_normalization_cache_input ON instrument_normalization_cache(input_normalized);
CREATE INDEX IF NOT EXISTS idx_normalization_cache_tenant ON instrument_normalization_cache(tenant_id);
CREATE INDEX IF NOT EXISTS idx_normalization_cache_expires ON instrument_normalization_cache(expires_at);

-- ============================================================
-- UNMATCHED INSTRUMENTS QUEUE
-- ============================================================
-- Queue of instruments that couldn't be normalized.
-- For manual review and mapping creation.

CREATE TABLE IF NOT EXISTS unmatched_instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    input_value VARCHAR(300) NOT NULL,
    input_normalized VARCHAR(300),
    source_file VARCHAR(300),
    source_column VARCHAR(100),
    occurrence_count INTEGER DEFAULT 1,
    suggested_type_id UUID REFERENCES instrument_types(id) ON DELETE SET NULL,
    suggested_confidence DECIMAL(5,4),
    status VARCHAR(20) DEFAULT 'pending',       -- 'pending', 'mapped', 'ignored', 'escalated'
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- One entry per unique input per tenant
    CONSTRAINT uq_unmatched_per_tenant UNIQUE(tenant_id, input_value)
);

CREATE INDEX IF NOT EXISTS idx_unmatched_status ON unmatched_instruments(status);
CREATE INDEX IF NOT EXISTS idx_unmatched_tenant ON unmatched_instruments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_unmatched_created ON unmatched_instruments(created_at);

-- ============================================================
-- SEED DATA: CANONICAL INSTRUMENT TYPES
-- ============================================================

INSERT INTO instrument_types (code, canonical_name, asset_class, riskpod, has_tenor, default_tenor, description) VALUES
-- Credit Instruments
('CDS', 'Credit Default Swap', 'cds', 'credit', true, '5Y', 'Single-name credit default swap'),
('CDX', 'CDX Credit Index', 'cds', 'credit', true, '5Y', 'CDX North America IG/HY'),
('ITRAXX', 'iTraxx Credit Index', 'cds', 'credit', true, '5Y', 'iTraxx Europe/Asia'),
('CDSIDX', 'CDS Index', 'cds', 'credit', true, '5Y', 'Generic credit index'),
('CLO', 'Collateralized Loan Obligation', 'fixed_income', 'credit', false, NULL, 'Structured credit CLO'),
('CDO', 'Collateralized Debt Obligation', 'fixed_income', 'credit', false, NULL, 'Structured credit CDO'),
('ABS', 'Asset-Backed Security', 'fixed_income', 'credit', false, NULL, 'Consumer/auto/other ABS'),
('CMBS', 'Commercial Mortgage-Backed Security', 'fixed_income', 'credit', false, NULL, 'Commercial real estate MBS'),
('CORP', 'Corporate Bond', 'fixed_income', 'credit', false, NULL, 'Corporate debt - IG or HY'),
('HY', 'High Yield Bond', 'fixed_income', 'credit', false, NULL, 'High yield corporate bond'),
('IG', 'Investment Grade Bond', 'fixed_income', 'credit', false, NULL, 'Investment grade corporate bond'),
('LOAN', 'Leveraged Loan', 'fixed_income', 'credit', false, NULL, 'Syndicated leveraged loan'),
('DISTRESSED', 'Distressed Debt', 'fixed_income', 'credit', false, NULL, 'Distressed/defaulted debt'),
('CLN', 'Credit-Linked Note', 'fixed_income', 'credit', true, '5Y', 'Credit-linked structured note'),
('TRS_CREDIT', 'Credit Total Return Swap', 'swap', 'credit', true, '1Y', 'Total return swap on credit'),

-- Rates Instruments
('IRS', 'Interest Rate Swap', 'swap', 'rates', true, '10Y', 'Plain vanilla interest rate swap'),
('OIS', 'Overnight Index Swap', 'swap', 'rates', true, '1Y', 'OIS swap (SOFR, ESTR, etc.)'),
('FRA', 'Forward Rate Agreement', 'swap', 'rates', true, '3M', 'Forward rate agreement'),
('XCCY', 'Cross-Currency Swap', 'swap', 'rates', true, '5Y', 'Cross-currency basis swap'),
('BASIS', 'Basis Swap', 'swap', 'rates', true, '5Y', 'Floating-floating basis swap'),
('CAP', 'Interest Rate Cap', 'option', 'rates', true, '5Y', 'Interest rate cap'),
('FLOOR', 'Interest Rate Floor', 'option', 'rates', true, '5Y', 'Interest rate floor'),
('COLLAR', 'Interest Rate Collar', 'option', 'rates', true, '5Y', 'Cap + floor combination'),
('SWAPTION', 'Swaption', 'option', 'rates', true, '10Y', 'Option on interest rate swap'),
('TNOTE', 'Treasury Note', 'fixed_income', 'rates', false, NULL, 'US Treasury 2-10Y'),
('TBOND', 'Treasury Bond', 'fixed_income', 'rates', false, NULL, 'US Treasury 10-30Y'),
('TBILL', 'Treasury Bill', 'fixed_income', 'rates', false, NULL, 'US Treasury <1Y'),
('TIPS', 'Treasury Inflation Protected', 'fixed_income', 'rates', false, NULL, 'US TIPS'),
('GOVT', 'Government Bond', 'fixed_income', 'rates', false, NULL, 'Sovereign debt generic'),
('GILT', 'UK Gilt', 'fixed_income', 'rates', false, NULL, 'UK government bond'),
('BUND', 'German Bund', 'fixed_income', 'rates', false, NULL, 'German government bond'),
('JGB', 'Japanese Government Bond', 'fixed_income', 'rates', false, NULL, 'Japanese government bond'),
('MUNI', 'Municipal Bond', 'fixed_income', 'rates', false, NULL, 'US municipal bond'),
('AGENCY', 'Agency Bond', 'fixed_income', 'rates', false, NULL, 'US agency debt'),
('MBS', 'Mortgage-Backed Security', 'fixed_income', 'rates', false, NULL, 'Agency MBS'),
('BONDFUT', 'Bond Future', 'future', 'rates', true, '3M', 'Treasury/bond futures'),
('STIRFUT', 'Short-Term Interest Rate Future', 'future', 'rates', true, '3M', 'SOFR/Euribor futures'),
('INFLATION', 'Inflation Swap', 'swap', 'rates', true, '5Y', 'CPI/RPI inflation swap'),

-- Equity Instruments
('STOCK', 'Common Stock', 'equity', 'equity', false, NULL, 'Common equity shares'),
('PREF', 'Preferred Stock', 'equity', 'equity', false, NULL, 'Preferred equity'),
('ADR', 'American Depositary Receipt', 'equity', 'equity', false, NULL, 'ADR'),
('GDR', 'Global Depositary Receipt', 'equity', 'equity', false, NULL, 'GDR'),
('REIT', 'Real Estate Investment Trust', 'equity', 'equity', false, NULL, 'Equity REIT'),
('ETF', 'Exchange-Traded Fund', 'fund', 'equity', false, NULL, 'Equity ETF'),
('WARRANT', 'Warrant', 'equity', 'equity', true, '1Y', 'Equity warrant'),
('RIGHTS', 'Rights Issue', 'equity', 'equity', false, NULL, 'Subscription rights'),
('EQO', 'Equity Option', 'option', 'equity', true, '1M', 'Single-stock or index option'),
('IDXOPT', 'Index Option', 'option', 'equity', true, '1M', 'Equity index option'),
('EQF', 'Equity Future', 'future', 'equity', true, '3M', 'Equity index future'),
('SSF', 'Single Stock Future', 'future', 'equity', true, '3M', 'Single stock future'),
('CFD', 'Contract for Difference', 'other', 'equity', false, NULL, 'Equity CFD'),
('TRS', 'Total Return Swap', 'swap', 'equity', true, '1Y', 'Equity total return swap'),
('VARIANCE', 'Variance Swap', 'swap', 'equity', true, '1Y', 'Realized variance swap'),
('VOLSWAP', 'Volatility Swap', 'swap', 'equity', true, '1Y', 'Realized volatility swap'),
('CONVERT', 'Convertible Bond', 'fixed_income', 'equity', false, NULL, 'Convertible debt'),

-- FX Instruments
('SPOT', 'FX Spot', 'fx', 'fx', false, NULL, 'FX spot trade'),
('FWD', 'FX Forward', 'fx', 'fx', true, '1M', 'FX outright forward'),
('NDF', 'Non-Deliverable Forward', 'fx', 'fx', true, '1M', 'FX NDF (EM currencies)'),
('FXS', 'FX Swap', 'swap', 'fx', true, '1M', 'FX swap near/far'),
('FXO', 'FX Option', 'option', 'fx', true, '1M', 'FX vanilla option'),
('FXBARRIER', 'FX Barrier Option', 'option', 'fx', true, '1M', 'FX barrier option'),
('FXDIGITAL', 'FX Digital Option', 'option', 'fx', true, '1M', 'FX digital/binary option'),
('FXFUT', 'FX Future', 'future', 'fx', true, '3M', 'Currency future'),

-- Commodity Instruments
('COMMOD', 'Commodity', 'commodity', 'other', false, NULL, 'Physical commodity'),
('COMF', 'Commodity Future', 'future', 'other', true, '1M', 'Commodity future'),
('COMO', 'Commodity Option', 'option', 'other', true, '1M', 'Commodity option'),
('COMSWAP', 'Commodity Swap', 'swap', 'other', true, '1Y', 'Commodity swap'),
('GOLD', 'Gold', 'commodity', 'other', false, NULL, 'Gold/precious metals'),
('OIL', 'Crude Oil', 'commodity', 'other', false, NULL, 'Crude oil'),
('NATGAS', 'Natural Gas', 'commodity', 'other', false, NULL, 'Natural gas'),
('POWER', 'Power/Electricity', 'commodity', 'other', false, NULL, 'Power futures'),

-- Volatility Instruments
('VIX', 'VIX Futures', 'future', 'other', true, '1M', 'VIX volatility futures'),
('VIXOPT', 'VIX Options', 'option', 'other', true, '1M', 'VIX options'),
('VARFUT', 'Variance Futures', 'future', 'other', true, '3M', 'Variance futures'),

-- Other/Alternatives
('FUND', 'Fund Investment', 'fund', 'other', false, NULL, 'Mutual fund/hedge fund'),
('PE', 'Private Equity', 'other', 'other', false, NULL, 'Private equity investment'),
('CRYPTO', 'Cryptocurrency', 'crypto', 'other', false, NULL, 'Digital assets'),
('STRUCTURED', 'Structured Product', 'other', 'other', false, NULL, 'Complex structured product'),
('ILS', 'Insurance-Linked Security', 'other', 'other', false, NULL, 'Cat bonds, ILS'),
('REPO', 'Repurchase Agreement', 'fixed_income', 'rates', false, NULL, 'Repo/reverse repo')
ON CONFLICT (code) DO NOTHING;


-- ============================================================
-- SEED DATA: INSTRUMENT ALIASES
-- ============================================================
-- Global aliases (tenant_id = NULL) for common variations.

-- Helper function to insert aliases safely
DO $$
DECLARE
    v_cds_id UUID;
    v_cdx_id UUID;
    v_itraxx_id UUID;
    v_irs_id UUID;
    v_fra_id UUID;
    v_ois_id UUID;
    v_xccy_id UUID;
    v_swaption_id UUID;
    v_cap_id UUID;
    v_floor_id UUID;
    v_tnote_id UUID;
    v_tbond_id UUID;
    v_tbill_id UUID;
    v_govt_id UUID;
    v_gilt_id UUID;
    v_bund_id UUID;
    v_jgb_id UUID;
    v_corp_id UUID;
    v_hy_id UUID;
    v_ig_id UUID;
    v_stock_id UUID;
    v_etf_id UUID;
    v_eqo_id UUID;
    v_eqf_id UUID;
    v_trs_id UUID;
    v_variance_id UUID;
    v_convert_id UUID;
    v_spot_id UUID;
    v_fwd_id UUID;
    v_ndf_id UUID;
    v_fxo_id UUID;
    v_fxs_id UUID;
    v_comf_id UUID;
    v_gold_id UUID;
    v_oil_id UUID;
    v_mbs_id UUID;
    v_clo_id UUID;
    v_abs_id UUID;
    v_loan_id UUID;
BEGIN
    -- Get type IDs
    SELECT id INTO v_cds_id FROM instrument_types WHERE code = 'CDS';
    SELECT id INTO v_cdx_id FROM instrument_types WHERE code = 'CDX';
    SELECT id INTO v_itraxx_id FROM instrument_types WHERE code = 'ITRAXX';
    SELECT id INTO v_irs_id FROM instrument_types WHERE code = 'IRS';
    SELECT id INTO v_fra_id FROM instrument_types WHERE code = 'FRA';
    SELECT id INTO v_ois_id FROM instrument_types WHERE code = 'OIS';
    SELECT id INTO v_xccy_id FROM instrument_types WHERE code = 'XCCY';
    SELECT id INTO v_swaption_id FROM instrument_types WHERE code = 'SWAPTION';
    SELECT id INTO v_cap_id FROM instrument_types WHERE code = 'CAP';
    SELECT id INTO v_floor_id FROM instrument_types WHERE code = 'FLOOR';
    SELECT id INTO v_tnote_id FROM instrument_types WHERE code = 'TNOTE';
    SELECT id INTO v_tbond_id FROM instrument_types WHERE code = 'TBOND';
    SELECT id INTO v_tbill_id FROM instrument_types WHERE code = 'TBILL';
    SELECT id INTO v_govt_id FROM instrument_types WHERE code = 'GOVT';
    SELECT id INTO v_gilt_id FROM instrument_types WHERE code = 'GILT';
    SELECT id INTO v_bund_id FROM instrument_types WHERE code = 'BUND';
    SELECT id INTO v_jgb_id FROM instrument_types WHERE code = 'JGB';
    SELECT id INTO v_corp_id FROM instrument_types WHERE code = 'CORP';
    SELECT id INTO v_hy_id FROM instrument_types WHERE code = 'HY';
    SELECT id INTO v_ig_id FROM instrument_types WHERE code = 'IG';
    SELECT id INTO v_stock_id FROM instrument_types WHERE code = 'STOCK';
    SELECT id INTO v_etf_id FROM instrument_types WHERE code = 'ETF';
    SELECT id INTO v_eqo_id FROM instrument_types WHERE code = 'EQO';
    SELECT id INTO v_eqf_id FROM instrument_types WHERE code = 'EQF';
    SELECT id INTO v_trs_id FROM instrument_types WHERE code = 'TRS';
    SELECT id INTO v_variance_id FROM instrument_types WHERE code = 'VARIANCE';
    SELECT id INTO v_convert_id FROM instrument_types WHERE code = 'CONVERT';
    SELECT id INTO v_spot_id FROM instrument_types WHERE code = 'SPOT';
    SELECT id INTO v_fwd_id FROM instrument_types WHERE code = 'FWD';
    SELECT id INTO v_ndf_id FROM instrument_types WHERE code = 'NDF';
    SELECT id INTO v_fxo_id FROM instrument_types WHERE code = 'FXO';
    SELECT id INTO v_fxs_id FROM instrument_types WHERE code = 'FXS';
    SELECT id INTO v_comf_id FROM instrument_types WHERE code = 'COMF';
    SELECT id INTO v_gold_id FROM instrument_types WHERE code = 'GOLD';
    SELECT id INTO v_oil_id FROM instrument_types WHERE code = 'OIL';
    SELECT id INTO v_mbs_id FROM instrument_types WHERE code = 'MBS';
    SELECT id INTO v_clo_id FROM instrument_types WHERE code = 'CLO';
    SELECT id INTO v_abs_id FROM instrument_types WHERE code = 'ABS';
    SELECT id INTO v_loan_id FROM instrument_types WHERE code = 'LOAN';

    -- CDS Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_cds_id, 'CDS', 'cds', 'exact', 100),
    (v_cds_id, 'Credit Default Swap', 'credit default swap', 'exact', 100),
    (v_cds_id, 'Credit Default Swaps', 'credit default swaps', 'exact', 100),
    (v_cds_id, 'CDS 5Y', 'cds 5y', 'exact', 90),
    (v_cds_id, 'CDS 5-Year', 'cds 5-year', 'exact', 90),
    (v_cds_id, 'CDS 5 Year', 'cds 5 year', 'exact', 90),
    (v_cds_id, 'CDS five-year', 'cds five-year', 'exact', 85),
    (v_cds_id, 'CDS five year', 'cds five year', 'exact', 85),
    (v_cds_id, '5Y CDS', '5y cds', 'exact', 90),
    (v_cds_id, '5-Year CDS', '5-year cds', 'exact', 90),
    (v_cds_id, 'Single Name CDS', 'single name cds', 'exact', 95),
    (v_cds_id, 'SN CDS', 'sn cds', 'exact', 90),
    (v_cds_id, 'Credit Protection', 'credit protection', 'exact', 80)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- CDX Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_cdx_id, 'CDX', 'cdx', 'prefix', 100),
    (v_cdx_id, 'CDX IG', 'cdx ig', 'exact', 95),
    (v_cdx_id, 'CDX HY', 'cdx hy', 'exact', 95),
    (v_cdx_id, 'CDX NA IG', 'cdx na ig', 'exact', 95),
    (v_cdx_id, 'CDX NA HY', 'cdx na hy', 'exact', 95),
    (v_cdx_id, 'CDX Investment Grade', 'cdx investment grade', 'exact', 90),
    (v_cdx_id, 'CDX High Yield', 'cdx high yield', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- iTraxx Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_itraxx_id, 'iTraxx', 'itraxx', 'prefix', 100),
    (v_itraxx_id, 'ITRAXX', 'itraxx', 'prefix', 100),
    (v_itraxx_id, 'iTraxx Europe', 'itraxx europe', 'exact', 95),
    (v_itraxx_id, 'iTraxx Main', 'itraxx main', 'exact', 95),
    (v_itraxx_id, 'iTraxx Crossover', 'itraxx crossover', 'exact', 95),
    (v_itraxx_id, 'iTraxx Xover', 'itraxx xover', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- IRS Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_irs_id, 'IRS', 'irs', 'exact', 100),
    (v_irs_id, 'Interest Rate Swap', 'interest rate swap', 'exact', 100),
    (v_irs_id, 'Interest Rate Swaps', 'interest rate swaps', 'exact', 100),
    (v_irs_id, 'IR Swap', 'ir swap', 'exact', 95),
    (v_irs_id, 'IR Swaps', 'ir swaps', 'exact', 95),
    (v_irs_id, 'Fixed-Float Swap', 'fixed-float swap', 'exact', 90),
    (v_irs_id, 'Fixed Float Swap', 'fixed float swap', 'exact', 90),
    (v_irs_id, 'Vanilla Swap', 'vanilla swap', 'exact', 85),
    (v_irs_id, 'Plain Vanilla IRS', 'plain vanilla irs', 'exact', 85),
    (v_irs_id, 'Pay Fixed', 'pay fixed', 'exact', 80),
    (v_irs_id, 'Receive Fixed', 'receive fixed', 'exact', 80),
    (v_irs_id, 'Fixed for Float', 'fixed for float', 'exact', 85),
    (v_irs_id, 'Fixed vs Float', 'fixed vs float', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- OIS Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_ois_id, 'OIS', 'ois', 'exact', 100),
    (v_ois_id, 'Overnight Index Swap', 'overnight index swap', 'exact', 100),
    (v_ois_id, 'SOFR Swap', 'sofr swap', 'exact', 95),
    (v_ois_id, 'ESTR Swap', 'estr swap', 'exact', 95),
    (v_ois_id, 'Fed Funds Swap', 'fed funds swap', 'exact', 90),
    (v_ois_id, 'SONIA Swap', 'sonia swap', 'exact', 95)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- FRA Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_fra_id, 'FRA', 'fra', 'exact', 100),
    (v_fra_id, 'Forward Rate Agreement', 'forward rate agreement', 'exact', 100),
    (v_fra_id, 'Forward Rate Agreements', 'forward rate agreements', 'exact', 100)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Cross-Currency Swap Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_xccy_id, 'XCCY', 'xccy', 'exact', 100),
    (v_xccy_id, 'Cross Currency Swap', 'cross currency swap', 'exact', 100),
    (v_xccy_id, 'Cross-Currency Swap', 'cross-currency swap', 'exact', 100),
    (v_xccy_id, 'XCCY Swap', 'xccy swap', 'exact', 95),
    (v_xccy_id, 'XCCY Basis', 'xccy basis', 'exact', 95),
    (v_xccy_id, 'Cross Currency Basis', 'cross currency basis', 'exact', 90),
    (v_xccy_id, 'Basis Swap', 'basis swap', 'exact', 80),
    (v_xccy_id, 'Currency Swap', 'currency swap', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Swaption Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_swaption_id, 'Swaption', 'swaption', 'exact', 100),
    (v_swaption_id, 'Swaptions', 'swaptions', 'exact', 100),
    (v_swaption_id, 'Swap Option', 'swap option', 'exact', 95),
    (v_swaption_id, 'Swap Options', 'swap options', 'exact', 95),
    (v_swaption_id, 'Payer Swaption', 'payer swaption', 'exact', 90),
    (v_swaption_id, 'Receiver Swaption', 'receiver swaption', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Cap/Floor Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_cap_id, 'Cap', 'cap', 'exact', 100),
    (v_cap_id, 'Interest Rate Cap', 'interest rate cap', 'exact', 100),
    (v_cap_id, 'IR Cap', 'ir cap', 'exact', 95),
    (v_cap_id, 'Rate Cap', 'rate cap', 'exact', 90),
    (v_floor_id, 'Floor', 'floor', 'exact', 100),
    (v_floor_id, 'Interest Rate Floor', 'interest rate floor', 'exact', 100),
    (v_floor_id, 'IR Floor', 'ir floor', 'exact', 95),
    (v_floor_id, 'Rate Floor', 'rate floor', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Treasury Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_tnote_id, 'Treasury Note', 'treasury note', 'exact', 100),
    (v_tnote_id, 'T-Note', 't-note', 'exact', 95),
    (v_tnote_id, 'TNote', 'tnote', 'exact', 95),
    (v_tnote_id, 'UST', 'ust', 'prefix', 90),
    (v_tnote_id, 'US Treasury', 'us treasury', 'prefix', 85),
    (v_tnote_id, '10Y Treasury', '10y treasury', 'exact', 90),
    (v_tnote_id, '10-Year Treasury', '10-year treasury', 'exact', 90),
    (v_tnote_id, '5Y Treasury', '5y treasury', 'exact', 90),
    (v_tnote_id, '2Y Treasury', '2y treasury', 'exact', 90),
    (v_tbond_id, 'Treasury Bond', 'treasury bond', 'exact', 100),
    (v_tbond_id, 'T-Bond', 't-bond', 'exact', 95),
    (v_tbond_id, 'TBond', 'tbond', 'exact', 95),
    (v_tbond_id, '30Y Treasury', '30y treasury', 'exact', 90),
    (v_tbond_id, '30-Year Treasury', '30-year treasury', 'exact', 90),
    (v_tbond_id, 'Long Bond', 'long bond', 'exact', 85),
    (v_tbill_id, 'Treasury Bill', 'treasury bill', 'exact', 100),
    (v_tbill_id, 'T-Bill', 't-bill', 'exact', 95),
    (v_tbill_id, 'TBill', 'tbill', 'exact', 95),
    (v_tbill_id, '3M Treasury', '3m treasury', 'exact', 90),
    (v_tbill_id, '6M Treasury', '6m treasury', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Government Bond Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_govt_id, 'Government Bond', 'government bond', 'exact', 100),
    (v_govt_id, 'Govt Bond', 'govt bond', 'exact', 95),
    (v_govt_id, 'Sovereign', 'sovereign', 'exact', 90),
    (v_govt_id, 'Sovereign Bond', 'sovereign bond', 'exact', 95),
    (v_gilt_id, 'Gilt', 'gilt', 'exact', 100),
    (v_gilt_id, 'Gilts', 'gilts', 'exact', 100),
    (v_gilt_id, 'UK Gilt', 'uk gilt', 'exact', 95),
    (v_gilt_id, 'UK Government Bond', 'uk government bond', 'exact', 90),
    (v_bund_id, 'Bund', 'bund', 'exact', 100),
    (v_bund_id, 'Bunds', 'bunds', 'exact', 100),
    (v_bund_id, 'German Bund', 'german bund', 'exact', 95),
    (v_bund_id, 'DBR', 'dbr', 'exact', 90),
    (v_jgb_id, 'JGB', 'jgb', 'exact', 100),
    (v_jgb_id, 'JGBs', 'jgbs', 'exact', 100),
    (v_jgb_id, 'Japanese Government Bond', 'japanese government bond', 'exact', 95)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Corporate Bond Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_corp_id, 'Corporate Bond', 'corporate bond', 'exact', 100),
    (v_corp_id, 'Corporate Bonds', 'corporate bonds', 'exact', 100),
    (v_corp_id, 'Corp Bond', 'corp bond', 'exact', 95),
    (v_corp_id, 'Corporate', 'corporate', 'exact', 80),
    (v_hy_id, 'High Yield', 'high yield', 'exact', 100),
    (v_hy_id, 'High Yield Bond', 'high yield bond', 'exact', 100),
    (v_hy_id, 'HY Bond', 'hy bond', 'exact', 95),
    (v_hy_id, 'Junk Bond', 'junk bond', 'exact', 90),
    (v_hy_id, 'Junk', 'junk', 'exact', 85),
    (v_ig_id, 'Investment Grade', 'investment grade', 'exact', 100),
    (v_ig_id, 'IG Bond', 'ig bond', 'exact', 95),
    (v_ig_id, 'IG Corporate', 'ig corporate', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Equity Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_stock_id, 'Stock', 'stock', 'exact', 100),
    (v_stock_id, 'Stocks', 'stocks', 'exact', 100),
    (v_stock_id, 'Common Stock', 'common stock', 'exact', 100),
    (v_stock_id, 'Equity', 'equity', 'exact', 95),
    (v_stock_id, 'Equities', 'equities', 'exact', 95),
    (v_stock_id, 'Share', 'share', 'exact', 90),
    (v_stock_id, 'Shares', 'shares', 'exact', 90),
    (v_stock_id, 'Ordinary Share', 'ordinary share', 'exact', 90),
    (v_etf_id, 'ETF', 'etf', 'exact', 100),
    (v_etf_id, 'ETFs', 'etfs', 'exact', 100),
    (v_etf_id, 'Exchange Traded Fund', 'exchange traded fund', 'exact', 100),
    (v_etf_id, 'Exchange-Traded Fund', 'exchange-traded fund', 'exact', 100),
    (v_etf_id, 'ETP', 'etp', 'exact', 95),
    (v_etf_id, 'Index Fund', 'index fund', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Equity Derivatives Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_eqo_id, 'Equity Option', 'equity option', 'exact', 100),
    (v_eqo_id, 'Equity Options', 'equity options', 'exact', 100),
    (v_eqo_id, 'Stock Option', 'stock option', 'exact', 95),
    (v_eqo_id, 'Stock Options', 'stock options', 'exact', 95),
    (v_eqo_id, 'Call Option', 'call option', 'exact', 90),
    (v_eqo_id, 'Put Option', 'put option', 'exact', 90),
    (v_eqo_id, 'Call', 'call', 'exact', 80),
    (v_eqo_id, 'Put', 'put', 'exact', 80),
    (v_eqf_id, 'Equity Future', 'equity future', 'exact', 100),
    (v_eqf_id, 'Equity Futures', 'equity futures', 'exact', 100),
    (v_eqf_id, 'Index Future', 'index future', 'exact', 95),
    (v_eqf_id, 'Index Futures', 'index futures', 'exact', 95),
    (v_eqf_id, 'Stock Index Future', 'stock index future', 'exact', 90),
    (v_trs_id, 'Total Return Swap', 'total return swap', 'exact', 100),
    (v_trs_id, 'TRS', 'trs', 'exact', 100),
    (v_trs_id, 'Equity TRS', 'equity trs', 'exact', 95),
    (v_trs_id, 'Equity Swap', 'equity swap', 'exact', 90),
    (v_variance_id, 'Variance Swap', 'variance swap', 'exact', 100),
    (v_variance_id, 'Var Swap', 'var swap', 'exact', 95),
    (v_variance_id, 'Realized Variance', 'realized variance', 'exact', 90),
    (v_convert_id, 'Convertible', 'convertible', 'exact', 100),
    (v_convert_id, 'Convertible Bond', 'convertible bond', 'exact', 100),
    (v_convert_id, 'Convert', 'convert', 'exact', 90),
    (v_convert_id, 'CB', 'cb', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- FX Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_spot_id, 'FX Spot', 'fx spot', 'exact', 100),
    (v_spot_id, 'Spot FX', 'spot fx', 'exact', 100),
    (v_spot_id, 'Spot', 'spot', 'exact', 80),
    (v_spot_id, 'Currency Spot', 'currency spot', 'exact', 90),
    (v_fwd_id, 'FX Forward', 'fx forward', 'exact', 100),
    (v_fwd_id, 'FX Fwd', 'fx fwd', 'exact', 95),
    (v_fwd_id, 'Forward', 'forward', 'exact', 80),
    (v_fwd_id, 'FX Outright', 'fx outright', 'exact', 90),
    (v_fwd_id, 'Outright Forward', 'outright forward', 'exact', 90),
    (v_ndf_id, 'NDF', 'ndf', 'exact', 100),
    (v_ndf_id, 'Non-Deliverable Forward', 'non-deliverable forward', 'exact', 100),
    (v_ndf_id, 'Non Deliverable Forward', 'non deliverable forward', 'exact', 100),
    (v_fxo_id, 'FX Option', 'fx option', 'exact', 100),
    (v_fxo_id, 'FX Options', 'fx options', 'exact', 100),
    (v_fxo_id, 'Currency Option', 'currency option', 'exact', 95),
    (v_fxo_id, 'FX Call', 'fx call', 'exact', 90),
    (v_fxo_id, 'FX Put', 'fx put', 'exact', 90),
    (v_fxs_id, 'FX Swap', 'fx swap', 'exact', 100),
    (v_fxs_id, 'FX Swaps', 'fx swaps', 'exact', 100),
    (v_fxs_id, 'Currency Swap', 'currency swap', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Commodity Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_comf_id, 'Commodity Future', 'commodity future', 'exact', 100),
    (v_comf_id, 'Commodity Futures', 'commodity futures', 'exact', 100),
    (v_comf_id, 'Commod Future', 'commod future', 'exact', 90),
    (v_gold_id, 'Gold', 'gold', 'exact', 100),
    (v_gold_id, 'XAU', 'xau', 'exact', 95),
    (v_gold_id, 'Gold Futures', 'gold futures', 'exact', 95),
    (v_gold_id, 'GC', 'gc', 'exact', 90),
    (v_oil_id, 'Oil', 'oil', 'exact', 100),
    (v_oil_id, 'Crude', 'crude', 'exact', 95),
    (v_oil_id, 'Crude Oil', 'crude oil', 'exact', 100),
    (v_oil_id, 'WTI', 'wti', 'exact', 95),
    (v_oil_id, 'Brent', 'brent', 'exact', 95),
    (v_oil_id, 'CL', 'cl', 'exact', 90)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

    -- Structured Credit Aliases
    INSERT INTO instrument_aliases (instrument_type_id, alias, alias_normalized, match_type, priority) VALUES
    (v_mbs_id, 'MBS', 'mbs', 'exact', 100),
    (v_mbs_id, 'Mortgage Backed Security', 'mortgage backed security', 'exact', 100),
    (v_mbs_id, 'Mortgage-Backed Security', 'mortgage-backed security', 'exact', 100),
    (v_mbs_id, 'Agency MBS', 'agency mbs', 'exact', 95),
    (v_mbs_id, 'RMBS', 'rmbs', 'exact', 90),
    (v_clo_id, 'CLO', 'clo', 'exact', 100),
    (v_clo_id, 'Collateralized Loan Obligation', 'collateralized loan obligation', 'exact', 100),
    (v_abs_id, 'ABS', 'abs', 'exact', 100),
    (v_abs_id, 'Asset Backed Security', 'asset backed security', 'exact', 100),
    (v_abs_id, 'Asset-Backed Security', 'asset-backed security', 'exact', 100),
    (v_abs_id, 'Auto ABS', 'auto abs', 'exact', 90),
    (v_loan_id, 'Leveraged Loan', 'leveraged loan', 'exact', 100),
    (v_loan_id, 'Lev Loan', 'lev loan', 'exact', 95),
    (v_loan_id, 'Bank Loan', 'bank loan', 'exact', 90),
    (v_loan_id, 'Syndicated Loan', 'syndicated loan', 'exact', 90),
    (v_loan_id, 'Term Loan', 'term loan', 'exact', 85)
    ON CONFLICT (alias_normalized, tenant_id) DO NOTHING;

END $$;


-- ============================================================
-- SEED DATA: TENOR PATTERNS
-- ============================================================

INSERT INTO tenor_patterns (pattern, tenor_group, unit_group, example, priority) VALUES
-- Year patterns
('^.*?(\d+)\s*[yY](?:ear|r)?(?:s)?.*$', 1, NULL, 'CDS 5Y, CDS 5 Year, 5yr swap', 100),
('^.*?(\d+)\s*-\s*[yY](?:ear|r)?(?:s)?.*$', 1, NULL, 'CDS 5-Year, 10-year note', 95),
-- Month patterns
('^.*?(\d+)\s*[mM](?:onth)?(?:s)?.*$', 1, NULL, 'IRS 6M, 3 Month SOFR', 100),
('^.*?(\d+)\s*-\s*[mM](?:onth)?(?:s)?.*$', 1, NULL, 'FRA 3-Month', 95),
-- Week patterns
('^.*?(\d+)\s*[wW](?:eek)?(?:s)?.*$', 1, NULL, '2W forward', 80),
-- Day patterns
('^.*?(\d+)\s*[dD](?:ay)?(?:s)?.*$', 1, NULL, '30D SOFR', 80),
-- Combined number+unit
('^.*?(\d+)([YMDWymwdw]).*$', 1, 2, '5Y, 3M, 30D', 90),
-- Written numbers (one through ten)
('^.*?\b(one|two|three|four|five|six|seven|eight|nine|ten)\s*[yY]ear.*$', 1, NULL, 'five year CDS', 60),
('^.*?\b(one|two|three|four|five|six|seven|eight|nine|ten)\s*[mM]onth.*$', 1, NULL, 'three month swap', 60)
ON CONFLICT DO NOTHING;


-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_instrument_types_updated
    BEFORE UPDATE ON instrument_types
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_unmatched_instruments_updated
    BEFORE UPDATE ON unmatched_instruments
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();


-- ============================================================
-- CLEANUP FUNCTION FOR EXPIRED CACHE
-- ============================================================

CREATE OR REPLACE FUNCTION cleanup_normalization_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM instrument_normalization_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comment for documentation
COMMENT ON TABLE instrument_types IS 'Canonical instrument type definitions for normalization layer';
COMMENT ON TABLE instrument_aliases IS 'Aliases/synonyms mapping to canonical instrument types';
COMMENT ON TABLE instrument_normalization_cache IS 'Cache of normalization results with 7-day TTL';
COMMENT ON TABLE unmatched_instruments IS 'Queue of unrecognized instruments for manual review';
COMMENT ON TABLE tenor_patterns IS 'Regex patterns for extracting tenor from instrument names';
