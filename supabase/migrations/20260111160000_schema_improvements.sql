-- ============================================
-- RISKCORE Schema Improvements
-- Date: 2026-01-11
-- ============================================
-- Improvements:
-- 1. Add convexity to positions and position_history
-- 2. Add pm_id to books table
-- 3. Create snapshot_type enum
-- 4. Create validation_rules and validation_results tables
-- 5. Add index for cross-PM overlap detection
-- 6. Add user_email to audit_logs for permanent trail
-- ============================================

-- ============================================
-- 1. ADD CONVEXITY TO POSITIONS
-- ============================================

ALTER TABLE public.positions
ADD COLUMN IF NOT EXISTS convexity DECIMAL(18,6);

COMMENT ON COLUMN public.positions.convexity IS 'Bond convexity for fixed income duration risk measurement.';

ALTER TABLE public.position_history
ADD COLUMN IF NOT EXISTS convexity DECIMAL(18,6);

COMMENT ON COLUMN public.position_history.convexity IS 'Bond convexity for fixed income duration risk measurement.';


-- ============================================
-- 2. ADD PM_ID TO BOOKS
-- ============================================

ALTER TABLE public.books
ADD COLUMN IF NOT EXISTS pm_id UUID REFERENCES public.users(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.books.pm_id IS 'Primary PM responsible for this book. Used for PM-level reporting and access defaults.';

CREATE INDEX IF NOT EXISTS idx_books_pm ON public.books(pm_id) WHERE pm_id IS NOT NULL;


-- ============================================
-- 3. CREATE SNAPSHOT_TYPE ENUM
-- ============================================

-- Create the enum type
CREATE TYPE public.snapshot_type AS ENUM (
    'eod',        -- End of day snapshot
    'intraday',   -- Intraday snapshot
    'manual'      -- Manual correction/adjustment
);

ALTER TYPE public.snapshot_type OWNER TO postgres;

-- Convert the varchar column to enum (with temporary column)
-- Handle safely: default to 'eod' for any NULL or unrecognized values
ALTER TABLE public.position_history
ADD COLUMN snapshot_type_new public.snapshot_type DEFAULT 'eod'::public.snapshot_type;

UPDATE public.position_history
SET snapshot_type_new = CASE
    WHEN snapshot_type IN ('eod', 'intraday', 'manual') THEN snapshot_type::public.snapshot_type
    ELSE 'eod'::public.snapshot_type
END;

ALTER TABLE public.position_history
DROP COLUMN snapshot_type;

ALTER TABLE public.position_history
RENAME COLUMN snapshot_type_new TO snapshot_type;

ALTER TABLE public.position_history
ALTER COLUMN snapshot_type SET NOT NULL;

COMMENT ON COLUMN public.position_history.snapshot_type IS 'Type of snapshot: eod (end-of-day), intraday, manual (correction).';


-- ============================================
-- 4. VALIDATION PIPELINE TABLES
-- ============================================

-- Validation rule definitions
CREATE TABLE IF NOT EXISTS public.validation_rules (
    id UUID DEFAULT extensions.uuid_generate_v4() NOT NULL PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,  -- NULL = system-wide rule
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,  -- 'schema', 'range', 'referential', 'business', 'custom'
    target_table VARCHAR(100) NOT NULL,
    target_column VARCHAR(100),
    rule_config JSONB NOT NULL,  -- Rule-specific configuration
    severity VARCHAR(20) DEFAULT 'error' NOT NULL,  -- 'error', 'warning', 'info'
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT valid_severity CHECK (severity IN ('error', 'warning', 'info')),
    CONSTRAINT valid_rule_type CHECK (rule_type IN ('schema', 'range', 'referential', 'business', 'custom'))
);

ALTER TABLE public.validation_rules OWNER TO postgres;

COMMENT ON TABLE public.validation_rules IS 'Data validation rule definitions. NULL tenant_id = system-wide rules.';

COMMENT ON COLUMN public.validation_rules.rule_config IS 'JSONB config varies by rule_type. Examples: {"min": 0, "max": 100} for range, {"pattern": "^[A-Z]{2}"} for regex.';

CREATE INDEX idx_validation_rules_tenant ON public.validation_rules(tenant_id);
CREATE INDEX idx_validation_rules_table ON public.validation_rules(target_table);
CREATE INDEX idx_validation_rules_active ON public.validation_rules(is_active) WHERE is_active = TRUE;

-- Validation results/errors
CREATE TABLE IF NOT EXISTS public.validation_results (
    id UUID DEFAULT extensions.uuid_generate_v4() NOT NULL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES public.validation_rules(id) ON DELETE SET NULL,
    upload_id UUID REFERENCES public.uploads(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,  -- 'upload', 'api', 'fix', 'manual'
    source_reference VARCHAR(255),
    record_identifier JSONB,  -- Identifies the problematic record
    severity VARCHAR(20) NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    field_name VARCHAR(100),
    field_value TEXT,
    expected_value TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.validation_results OWNER TO postgres;

COMMENT ON TABLE public.validation_results IS 'Validation errors and warnings from data ingestion. Links to upload or API request.';

COMMENT ON COLUMN public.validation_results.record_identifier IS 'JSONB identifying the record, e.g., {"row": 15, "security": "AAPL", "book": "Tech Long"}';

CREATE INDEX idx_validation_results_tenant ON public.validation_results(tenant_id);
CREATE INDEX idx_validation_results_upload ON public.validation_results(upload_id) WHERE upload_id IS NOT NULL;
CREATE INDEX idx_validation_results_unresolved ON public.validation_results(tenant_id, is_resolved) WHERE is_resolved = FALSE;
CREATE INDEX idx_validation_results_severity ON public.validation_results(severity);
CREATE INDEX idx_validation_results_created ON public.validation_results(created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE TRIGGER validation_rules_updated_at
    BEFORE UPDATE ON public.validation_rules
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


-- ============================================
-- 5. INDEX FOR CROSS-PM OVERLAP DETECTION
-- ============================================

-- This index enables efficient queries like:
-- "Find all positions in security X across all books in tenant Y"
CREATE INDEX IF NOT EXISTS idx_positions_tenant_security
    ON public.positions(tenant_id, security_id);

-- Also useful for aggregate queries by security across tenant
CREATE INDEX IF NOT EXISTS idx_positions_security_tenant_book
    ON public.positions(security_id, tenant_id, book_id);


-- ============================================
-- 6. ADD USER_EMAIL TO AUDIT_LOGS
-- ============================================

-- Add column to preserve user email even after user deletion
ALTER TABLE public.audit_logs
ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

COMMENT ON COLUMN public.audit_logs.user_email IS 'Denormalized user email for permanent audit trail (preserved after user deletion).';

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_email
    ON public.audit_logs(user_email) WHERE user_email IS NOT NULL;

-- Function to auto-populate user_email on audit log insert
CREATE OR REPLACE FUNCTION public.audit_log_set_user_email()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- If user_id is provided but email is not, look it up
    IF NEW.user_id IS NOT NULL AND NEW.user_email IS NULL THEN
        SELECT email INTO NEW.user_email
        FROM public.users
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$;

ALTER FUNCTION public.audit_log_set_user_email() OWNER TO postgres;

CREATE OR REPLACE TRIGGER audit_logs_set_email
    BEFORE INSERT ON public.audit_logs
    FOR EACH ROW EXECUTE FUNCTION public.audit_log_set_user_email();


-- ============================================
-- 7. RLS POLICIES FOR NEW TABLES
-- ============================================

-- Enable RLS
ALTER TABLE public.validation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_results ENABLE ROW LEVEL SECURITY;

-- Validation rules: System rules (NULL tenant) visible to all, tenant rules to own tenant
CREATE POLICY "view_validation_rules" ON public.validation_rules
    FOR SELECT TO authenticated
    USING (
        tenant_id IS NULL  -- System-wide rules visible to all
        OR tenant_id = public.riskcore_tenant_id()
    );

CREATE POLICY "admin_manage_validation_rules" ON public.validation_rules
    TO authenticated
    USING (
        tenant_id = public.riskcore_tenant_id()
        AND public.riskcore_is_admin_or_higher()
    );

-- Validation results: Tenant isolation with role-based access
CREATE POLICY "view_validation_results" ON public.validation_results
    FOR SELECT TO authenticated
    USING (tenant_id = public.riskcore_tenant_id());

CREATE POLICY "admin_manage_validation_results" ON public.validation_results
    TO authenticated
    USING (
        tenant_id = public.riskcore_tenant_id()
        AND public.riskcore_is_admin_or_higher()
    );


-- ============================================
-- 8. INSERT DEFAULT VALIDATION RULES
-- ============================================

-- System-wide validation rules (tenant_id = NULL)
INSERT INTO public.validation_rules (tenant_id, name, description, rule_type, target_table, target_column, rule_config, severity)
VALUES
    -- Position validation rules
    (NULL, 'quantity_not_null', 'Position quantity must not be null', 'schema', 'positions', 'quantity', '{"required": true}', 'error'),
    (NULL, 'quantity_numeric', 'Position quantity must be a valid number', 'schema', 'positions', 'quantity', '{"type": "numeric"}', 'error'),
    (NULL, 'book_id_required', 'Position must be associated with a book', 'schema', 'positions', 'book_id', '{"required": true}', 'error'),
    (NULL, 'security_id_required', 'Position must reference a valid security', 'referential', 'positions', 'security_id', '{"table": "securities", "column": "id"}', 'error'),

    -- Trade validation rules
    (NULL, 'trade_quantity_positive', 'Trade quantity must be positive', 'range', 'trades', 'quantity', '{"min": 0.000001}', 'error'),
    (NULL, 'trade_price_positive', 'Trade price must be positive', 'range', 'trades', 'price', '{"min": 0}', 'error'),
    (NULL, 'trade_date_not_future', 'Trade date cannot be in the future', 'business', 'trades', 'trade_date', '{"max": "today"}', 'warning'),

    -- Security validation rules
    (NULL, 'security_name_required', 'Security must have a name', 'schema', 'securities', 'name', '{"required": true, "minLength": 1}', 'error'),
    (NULL, 'currency_iso', 'Currency must be valid ISO 4217 code', 'schema', 'securities', 'currency', '{"pattern": "^[A-Z]{3}$"}', 'error'),

    -- Price validation rules
    (NULL, 'price_positive', 'Price must be positive', 'range', 'security_prices', 'price', '{"min": 0}', 'error'),
    (NULL, 'price_date_required', 'Price date is required', 'schema', 'security_prices', 'price_date', '{"required": true}', 'error')
ON CONFLICT DO NOTHING;


-- ============================================
-- DONE
-- ============================================
