


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."access_level" AS ENUM (
    'read',
    'write',
    'admin'
);


ALTER TYPE "public"."access_level" OWNER TO "postgres";


CREATE TYPE "public"."api_key_status" AS ENUM (
    'active',
    'revoked',
    'expired'
);


ALTER TYPE "public"."api_key_status" OWNER TO "postgres";


CREATE TYPE "public"."asset_class" AS ENUM (
    'equity',
    'fixed_income',
    'fx',
    'option',
    'future',
    'swap',
    'cds',
    'commodity',
    'crypto',
    'fund',
    'other'
);


ALTER TYPE "public"."asset_class" OWNER TO "postgres";


CREATE TYPE "public"."audit_category" AS ENUM (
    'authentication',
    'authorization',
    'data_export',
    'configuration',
    'limit_events',
    'data_import',
    'user_management',
    'system'
);


ALTER TYPE "public"."audit_category" OWNER TO "postgres";


CREATE TYPE "public"."breach_status" AS ENUM (
    'active',
    'acknowledged',
    'resolved',
    'waived'
);


ALTER TYPE "public"."breach_status" OWNER TO "postgres";


CREATE TYPE "public"."correlation_type" AS ENUM (
    'realized',
    'implied'
);


ALTER TYPE "public"."correlation_type" OWNER TO "postgres";


CREATE TYPE "public"."identifier_type" AS ENUM (
    'figi',
    'isin',
    'cusip',
    'sedol',
    'ticker',
    'ric',
    'bbg_ticker',
    'internal'
);


ALTER TYPE "public"."identifier_type" OWNER TO "postgres";


CREATE TYPE "public"."limit_scope" AS ENUM (
    'book',
    'fund',
    'tenant',
    'asset_class',
    'sector',
    'security'
);


ALTER TYPE "public"."limit_scope" OWNER TO "postgres";


CREATE TYPE "public"."limit_type" AS ENUM (
    'soft',
    'hard'
);


ALTER TYPE "public"."limit_type" OWNER TO "postgres";


CREATE TYPE "public"."metric_level" AS ENUM (
    'position',
    'book',
    'fund',
    'tenant'
);


ALTER TYPE "public"."metric_level" OWNER TO "postgres";


CREATE TYPE "public"."plan_type" AS ENUM (
    'free',
    'pro',
    'enterprise'
);


ALTER TYPE "public"."plan_type" OWNER TO "postgres";


CREATE TYPE "public"."position_direction" AS ENUM (
    'long',
    'short',
    'flat'
);


ALTER TYPE "public"."position_direction" OWNER TO "postgres";


CREATE TYPE "public"."position_source" AS ENUM (
    'file_upload',
    'api',
    'fix',
    'calculated'
);


ALTER TYPE "public"."position_source" OWNER TO "postgres";


CREATE TYPE "public"."price_source" AS ENUM (
    'market',
    'model',
    'client_override',
    'stale'
);


ALTER TYPE "public"."price_source" OWNER TO "postgres";


CREATE TYPE "public"."risk_metric_type" AS ENUM (
    'var_95',
    'var_99',
    'var_95_1d',
    'var_99_1d',
    'var_95_10d',
    'var_99_10d',
    'cvar_95',
    'cvar_99',
    'gross_exposure',
    'net_exposure',
    'long_exposure',
    'short_exposure',
    'net_delta',
    'net_gamma',
    'net_vega',
    'net_theta',
    'net_rho',
    'total_dv01',
    'total_cs01',
    'total_convexity',
    'top_10_concentration',
    'sector_concentration',
    'single_name_max',
    'sharpe_ratio',
    'sortino_ratio',
    'max_drawdown',
    'portfolio_beta',
    'custom'
);


ALTER TYPE "public"."risk_metric_type" OWNER TO "postgres";


CREATE TYPE "public"."trade_side" AS ENUM (
    'buy',
    'sell',
    'short',
    'cover'
);


ALTER TYPE "public"."trade_side" OWNER TO "postgres";


CREATE TYPE "public"."upload_file_type" AS ENUM (
    'positions_csv',
    'positions_xlsx',
    'trades_csv',
    'trades_xlsx',
    'fix_message',
    'other'
);


ALTER TYPE "public"."upload_file_type" OWNER TO "postgres";


CREATE TYPE "public"."upload_status" AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled'
);


ALTER TYPE "public"."upload_status" OWNER TO "postgres";


CREATE TYPE "public"."user_role" AS ENUM (
    'superadmin',
    'admin',
    'cio',
    'cro',
    'pm',
    'analyst'
);


ALTER TYPE "public"."user_role" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."calculate_direction"("p_quantity" numeric) RETURNS "public"."position_direction"
    LANGUAGE "plpgsql" IMMUTABLE
    AS $$
BEGIN
    IF p_quantity > 0 THEN
        RETURN 'long';
    ELSIF p_quantity < 0 THEN
        RETURN 'short';
    ELSE
        RETURN 'flat';
    END IF;
END;
$$;


ALTER FUNCTION "public"."calculate_direction"("p_quantity" numeric) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."check_limit_breach"("p_limit_id" "uuid", "p_current_value" numeric) RETURNS TABLE("is_breached" boolean, "is_warning" boolean, "breach_amount" numeric)
    LANGUAGE "plpgsql" STABLE
    AS $$
DECLARE
    v_limit RECORD;
BEGIN
    SELECT * INTO v_limit FROM limits WHERE id = p_limit_id AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, FALSE, 0::DECIMAL(18,6);
        RETURN;
    END IF;
    
    IF v_limit.is_upper_limit THEN
        -- Upper limit: breach if current > limit
        RETURN QUERY SELECT 
            p_current_value > v_limit.limit_value,
            p_current_value > COALESCE(v_limit.warning_threshold, v_limit.limit_value),
            GREATEST(0, p_current_value - v_limit.limit_value)::DECIMAL(18,6);
    ELSE
        -- Lower limit: breach if current < limit
        RETURN QUERY SELECT 
            p_current_value < v_limit.limit_value,
            p_current_value < COALESCE(v_limit.warning_threshold, v_limit.limit_value),
            GREATEST(0, v_limit.limit_value - p_current_value)::DECIMAL(18,6);
    END IF;
END;
$$;


ALTER FUNCTION "public"."check_limit_breach"("p_limit_id" "uuid", "p_current_value" numeric) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."deactivate_user"("p_user_id" "uuid") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_tenant_id UUID;
    v_caller_role user_role;
BEGIN
    -- Get caller's role
    SELECT role INTO v_caller_role FROM public.users WHERE id = auth.uid();
    
    -- Only admin or superadmin can deactivate users
    IF v_caller_role NOT IN ('admin', 'superadmin') THEN
        RAISE EXCEPTION 'Permission denied: only admins can deactivate users';
    END IF;
    
    -- Can't deactivate yourself
    IF p_user_id = auth.uid() THEN
        RAISE EXCEPTION 'Cannot deactivate yourself';
    END IF;
    
    -- Get user's tenant (must be same tenant unless superadmin)
    SELECT tenant_id INTO v_tenant_id FROM public.users WHERE id = p_user_id;
    
    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'User not found';
    END IF;
    
    -- Check same tenant (unless superadmin)
    IF v_caller_role != 'superadmin' THEN
        IF v_tenant_id != (SELECT tenant_id FROM public.users WHERE id = auth.uid()) THEN
            RAISE EXCEPTION 'Cannot deactivate user from different tenant';
        END IF;
    END IF;
    
    -- Soft delete
    UPDATE public.users
    SET is_active = FALSE,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    -- Log it
    INSERT INTO public.audit_logs (tenant_id, user_id, action, category, details)
    VALUES (
        v_tenant_id,
        auth.uid(),
        'USER_DEACTIVATED',
        'authentication',
        jsonb_build_object(
            'deactivated_user_id', p_user_id,
            'deactivated_by', auth.uid()
        )
    );
    
    RETURN TRUE;
END;
$$;


ALTER FUNCTION "public"."deactivate_user"("p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."find_security_by_identifier"("p_identifier_type" "public"."identifier_type", "p_identifier_value" character varying, "p_exchange_code" character varying DEFAULT NULL::character varying) RETURNS "uuid"
    LANGUAGE "plpgsql" STABLE
    AS $$
DECLARE
    v_security_id UUID;
BEGIN
    SELECT security_id INTO v_security_id
    FROM security_identifiers
    WHERE identifier_type = p_identifier_type
      AND identifier_value = UPPER(p_identifier_value)
      AND (p_exchange_code IS NULL OR exchange_code = p_exchange_code)
    LIMIT 1;
    
    RETURN v_security_id;
END;
$$;


ALTER FUNCTION "public"."find_security_by_identifier"("p_identifier_type" "public"."identifier_type", "p_identifier_value" character varying, "p_exchange_code" character varying) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_active_breaches"("p_tenant_id" "uuid") RETURNS TABLE("breach_id" "uuid", "limit_name" character varying, "limit_type" "public"."limit_type", "scope" "public"."limit_scope", "book_name" character varying, "limit_value" numeric, "actual_value" numeric, "breach_percentage" numeric, "breach_timestamp" timestamp with time zone, "status" "public"."breach_status")
    LANGUAGE "plpgsql" STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lb.id AS breach_id,
        l.name AS limit_name,
        l.limit_type,
        l.scope,
        b.name AS book_name,
        lb.limit_value,
        lb.actual_value,
        lb.breach_percentage,
        lb.breach_timestamp,
        lb.status
    FROM limit_breaches lb
    JOIN limits l ON l.id = lb.limit_id
    LEFT JOIN books b ON b.id = l.book_id
    WHERE lb.tenant_id = p_tenant_id
      AND lb.status IN ('active', 'acknowledged')
    ORDER BY lb.breach_timestamp DESC;
END;
$$;


ALTER FUNCTION "public"."get_active_breaches"("p_tenant_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_book_summary"("p_book_id" "uuid") RETURNS TABLE("total_positions" bigint, "total_long_positions" bigint, "total_short_positions" bigint, "total_market_value" numeric, "total_unrealized_pnl" numeric, "net_delta" numeric, "total_dv01" numeric)
    LANGUAGE "plpgsql" STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) AS total_positions,
        COUNT(*) FILTER (WHERE direction = 'long') AS total_long_positions,
        COUNT(*) FILTER (WHERE direction = 'short') AS total_short_positions,
        COALESCE(SUM(market_value_base), 0) AS total_market_value,
        COALESCE(SUM(unrealized_pnl), 0) AS total_unrealized_pnl,
        COALESCE(SUM(delta), 0) AS net_delta,
        COALESCE(SUM(dv01), 0) AS total_dv01
    FROM positions
    WHERE book_id = p_book_id;
END;
$$;


ALTER FUNCTION "public"."get_book_summary"("p_book_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_current_user_profile"() RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'user', json_build_object(
            'id', u.id,
            'email', u.email,
            'name', u.name,
            'role', u.role,
            'is_active', u.is_active,
            'created_at', u.created_at
        ),
        'tenant', json_build_object(
            'id', t.id,
            'name', t.name,
            'slug', t.slug,
            'plan', t.plan,
            'is_active', t.is_active
        )
    ) INTO v_result
    FROM public.users u
    JOIN public.tenants t ON t.id = u.tenant_id
    WHERE u.id = auth.uid();
    
    RETURN v_result;
END;
$$;


ALTER FUNCTION "public"."get_current_user_profile"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_latest_price"("p_security_id" "uuid") RETURNS TABLE("price" numeric, "price_date" "date", "source" "public"."price_source", "is_stale" boolean)
    LANGUAGE "plpgsql" STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.price,
        sp.price_date,
        sp.source,
        (sp.price_date < CURRENT_DATE - INTERVAL '2 days') AS is_stale
    FROM security_prices sp
    WHERE sp.security_id = p_security_id
    ORDER BY sp.price_date DESC, sp.price_time DESC NULLS LAST
    LIMIT 1;
END;
$$;


ALTER FUNCTION "public"."get_latest_price"("p_security_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_position_at_time"("p_book_id" "uuid", "p_security_id" "uuid", "p_timestamp" timestamp with time zone) RETURNS TABLE("quantity" numeric, "market_value" numeric, "snapshot_timestamp" timestamp with time zone)
    LANGUAGE "plpgsql" STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ph.quantity,
        ph.market_value,
        ph.snapshot_timestamp
    FROM position_history ph
    WHERE ph.book_id = p_book_id
      AND ph.security_id = p_security_id
      AND ph.snapshot_timestamp <= p_timestamp
    ORDER BY ph.snapshot_timestamp DESC
    LIMIT 1;
END;
$$;


ALTER FUNCTION "public"."get_position_at_time"("p_book_id" "uuid", "p_security_id" "uuid", "p_timestamp" timestamp with time zone) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_tenant_id UUID;
    v_role user_role;
    v_invited_tenant_id UUID;
    v_invited_role TEXT;
BEGIN
    -- Check if user was invited to an existing tenant (via user metadata)
    v_invited_tenant_id := (NEW.raw_user_meta_data->>'tenant_id')::UUID;
    v_invited_role := NEW.raw_user_meta_data->>'role';
    
    IF v_invited_tenant_id IS NOT NULL THEN
        -- FLOW B: Invited user - join existing tenant
        v_tenant_id := v_invited_tenant_id;
        v_role := COALESCE(v_invited_role, 'analyst')::user_role;
    ELSE
        -- FLOW A: New signup - create new tenant
        INSERT INTO public.tenants (name, slug, plan)
        VALUES (
            COALESCE(NEW.raw_user_meta_data->>'company_name', 'My Organization'),
            'tenant-' || SUBSTRING(NEW.id::TEXT, 1, 8),
            'free'
        )
        RETURNING id INTO v_tenant_id;
        
        -- First user of tenant becomes admin
        v_role := 'admin';
    END IF;
    
    -- Create user profile
    INSERT INTO public.users (id, tenant_id, email, name, role)
    VALUES (
        NEW.id,
        v_tenant_id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        v_role
    );
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_user_deleted"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
    -- Soft delete: mark as inactive, preserve the record
    UPDATE public.users
    SET is_active = FALSE,
        updated_at = NOW()
    WHERE id = OLD.id;
    
    -- Log the deletion for audit
    INSERT INTO public.audit_logs (tenant_id, user_id, action, category, details)
    SELECT 
        tenant_id,
        id,
        'USER_DEACTIVATED',
        'authentication',
        jsonb_build_object(
            'reason', 'auth.users deleted',
            'email', email,
            'deleted_at', NOW()
        )
    FROM public.users
    WHERE id = OLD.id;
    
    RETURN OLD;
END;
$$;


ALTER FUNCTION "public"."handle_user_deleted"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_user_updated"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
    -- Update email if it changed
    IF NEW.email IS DISTINCT FROM OLD.email THEN
        UPDATE public.users
        SET email = NEW.email,
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    
    -- Update name if provided in metadata
    IF NEW.raw_user_meta_data->>'full_name' IS DISTINCT FROM OLD.raw_user_meta_data->>'full_name' THEN
        UPDATE public.users
        SET name = NEW.raw_user_meta_data->>'full_name',
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_user_updated"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."invite_user"("p_email" "text", "p_role" "public"."user_role" DEFAULT 'analyst'::"public"."user_role", "p_name" "text" DEFAULT NULL::"text") RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_tenant_id UUID;
    v_inviter_role user_role;
BEGIN
    -- Get inviter's tenant and role
    SELECT tenant_id, role INTO v_tenant_id, v_inviter_role
    FROM public.users
    WHERE id = auth.uid();
    
    -- Check permission (only admin can invite)
    IF v_inviter_role NOT IN ('admin', 'superadmin') THEN
        RAISE EXCEPTION 'Only admins can invite users';
    END IF;
    
    -- Check role hierarchy (can't invite someone with higher role)
    IF p_role = 'admin' AND v_inviter_role != 'superadmin' THEN
        RAISE EXCEPTION 'Only superadmins can invite admins';
    END IF;
    
    -- Return invitation metadata (to be used with Supabase invite)
    RETURN json_build_object(
        'tenant_id', v_tenant_id,
        'role', p_role,
        'name', p_name,
        'invited_by', auth.uid(),
        'invited_at', NOW()
    );
END;
$$;


ALTER FUNCTION "public"."invite_user"("p_email" "text", "p_role" "public"."user_role", "p_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."log_audit_event"("p_tenant_id" "uuid", "p_user_id" "uuid", "p_action" character varying, "p_category" "public"."audit_category", "p_resource_type" character varying DEFAULT NULL::character varying, "p_resource_id" "uuid" DEFAULT NULL::"uuid", "p_details" "jsonb" DEFAULT NULL::"jsonb", "p_ip_address" "inet" DEFAULT NULL::"inet", "p_user_agent" "text" DEFAULT NULL::"text", "p_success" boolean DEFAULT true, "p_error_message" "text" DEFAULT NULL::"text") RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO audit_logs (
        tenant_id, user_id, action, category,
        resource_type, resource_id, details,
        ip_address, user_agent, success, error_message
    ) VALUES (
        p_tenant_id, p_user_id, p_action, p_category,
        p_resource_type, p_resource_id, p_details,
        p_ip_address, p_user_agent, p_success, p_error_message
    )
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$;


ALTER FUNCTION "public"."log_audit_event"("p_tenant_id" "uuid", "p_user_id" "uuid", "p_action" character varying, "p_category" "public"."audit_category", "p_resource_type" character varying, "p_resource_id" "uuid", "p_details" "jsonb", "p_ip_address" "inet", "p_user_agent" "text", "p_success" boolean, "p_error_message" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."reactivate_user"("p_user_id" "uuid") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_tenant_id UUID;
    v_caller_role user_role;
BEGIN
    SELECT role INTO v_caller_role FROM public.users WHERE id = auth.uid();
    
    IF v_caller_role NOT IN ('admin', 'superadmin') THEN
        RAISE EXCEPTION 'Permission denied: only admins can reactivate users';
    END IF;
    
    SELECT tenant_id INTO v_tenant_id FROM public.users WHERE id = p_user_id;
    
    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'User not found';
    END IF;
    
    IF v_caller_role != 'superadmin' THEN
        IF v_tenant_id != (SELECT tenant_id FROM public.users WHERE id = auth.uid()) THEN
            RAISE EXCEPTION 'Cannot reactivate user from different tenant';
        END IF;
    END IF;
    
    UPDATE public.users
    SET is_active = TRUE,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    INSERT INTO public.audit_logs (tenant_id, user_id, action, category, details)
    VALUES (
        v_tenant_id,
        auth.uid(),
        'USER_REACTIVATED',
        'authentication',
        jsonb_build_object(
            'reactivated_user_id', p_user_id,
            'reactivated_by', auth.uid()
        )
    );
    
    RETURN TRUE;
END;
$$;


ALTER FUNCTION "public"."reactivate_user"("p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."riskcore_can_view_firm_wide"() RETURNS boolean
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN public.riskcore_user_role() IN ('superadmin', 'admin', 'cio', 'cro');
END;
$$;


ALTER FUNCTION "public"."riskcore_can_view_firm_wide"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."riskcore_can_view_firm_wide"() IS 'Check if current user can view firm-wide data (Admin, CIO, CRO).';



CREATE OR REPLACE FUNCTION "public"."riskcore_current_user_id"() RETURNS "uuid"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
    SELECT auth.uid();
$$;


ALTER FUNCTION "public"."riskcore_current_user_id"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") RETURNS boolean
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
DECLARE
    v_role user_role;
BEGIN
    v_role := public.riskcore_user_role();
    
    -- SuperAdmin, Admin, CIO, CRO see all books in their tenant
    IF v_role IN ('superadmin', 'admin', 'cio', 'cro') THEN
        RETURN TRUE;
    END IF;
    
    -- PM and Analyst need explicit access
    RETURN EXISTS (
        SELECT 1 FROM book_user_access 
        WHERE book_id = p_book_id 
          AND user_id = auth.uid()
    );
END;
$$;


ALTER FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") IS 'Check if current user has access to specified book.';



CREATE OR REPLACE FUNCTION "public"."riskcore_is_admin_or_higher"() RETURNS boolean
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN public.riskcore_user_role() IN ('superadmin', 'admin');
END;
$$;


ALTER FUNCTION "public"."riskcore_is_admin_or_higher"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."riskcore_is_cro_or_higher"() RETURNS boolean
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN public.riskcore_user_role() IN ('superadmin', 'admin', 'cro');
END;
$$;


ALTER FUNCTION "public"."riskcore_is_cro_or_higher"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."riskcore_tenant_id"() RETURNS "uuid"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
    SELECT tenant_id FROM public.users WHERE id = auth.uid();
$$;


ALTER FUNCTION "public"."riskcore_tenant_id"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."riskcore_tenant_id"() IS 'Extract tenant_id from JWT claims. Returns NULL if not authenticated.';



CREATE OR REPLACE FUNCTION "public"."riskcore_user_role"() RETURNS "public"."user_role"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
    SELECT role FROM public.users WHERE id = auth.uid();
$$;


ALTER FUNCTION "public"."riskcore_user_role"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."riskcore_user_role"() IS 'Extract user role from JWT claims.';



CREATE OR REPLACE FUNCTION "public"."update_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."api_keys" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "key_hash" character varying(255) NOT NULL,
    "key_prefix" character varying(10) NOT NULL,
    "scopes" character varying(100)[] DEFAULT ARRAY['read'::"text"],
    "allowed_ips" "inet"[],
    "rate_limit" integer,
    "status" "public"."api_key_status" DEFAULT 'active'::"public"."api_key_status" NOT NULL,
    "expires_at" timestamp with time zone,
    "last_used_at" timestamp with time zone,
    "use_count" bigint DEFAULT 0,
    "created_by" "uuid",
    "revoked_by" "uuid",
    "revoked_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."api_keys" OWNER TO "postgres";


COMMENT ON TABLE "public"."api_keys" IS 'API key management. Keys are hashed, never stored in plain text.';



COMMENT ON COLUMN "public"."api_keys"."key_hash" IS 'SHA-256 hash of the API key. Original key shown once at creation.';



COMMENT ON COLUMN "public"."api_keys"."key_prefix" IS 'First few characters of key for identification in logs/UI.';



CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "user_id" "uuid",
    "action" character varying(100) NOT NULL,
    "category" "public"."audit_category" NOT NULL,
    "resource_type" character varying(50),
    "resource_id" "uuid",
    "details" "jsonb",
    "ip_address" "inet",
    "user_agent" "text",
    "request_id" character varying(100),
    "success" boolean DEFAULT true NOT NULL,
    "error_message" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."audit_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."audit_logs" IS 'Audit trail for sensitive actions. 3-year retention. Immutable.';



COMMENT ON COLUMN "public"."audit_logs"."details" IS 'JSONB with action-specific details. Structure varies by action type.';



CREATE TABLE IF NOT EXISTS "public"."book_user_access" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "book_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "access_level" "public"."access_level" DEFAULT 'read'::"public"."access_level" NOT NULL,
    "granted_by" "uuid",
    "granted_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."book_user_access" OWNER TO "postgres";


COMMENT ON TABLE "public"."book_user_access" IS 'Granular access control for PM and Analyst roles to specific books.';



CREATE TABLE IF NOT EXISTS "public"."books" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "fund_id" "uuid",
    "name" character varying(255) NOT NULL,
    "description" "text",
    "strategy" character varying(100),
    "asset_class_focus" character varying(100),
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."books" OWNER TO "postgres";


COMMENT ON TABLE "public"."books" IS 'Trading books/portfolios. Core entity for position aggregation.';



COMMENT ON COLUMN "public"."books"."strategy" IS 'Investment strategy classification for filtering and reporting.';



CREATE TABLE IF NOT EXISTS "public"."correlation_matrices" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "correlation_type" "public"."correlation_type" NOT NULL,
    "lookback_days" integer DEFAULT 60 NOT NULL,
    "matrix_data" "jsonb" NOT NULL,
    "book_ids" "uuid"[] NOT NULL,
    "calculation_method" character varying(100),
    "as_of_date" "date" NOT NULL,
    "calculated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."correlation_matrices" OWNER TO "postgres";


COMMENT ON TABLE "public"."correlation_matrices" IS 'Cross-book correlation data. Realized (MVP) and implied (Phase 2).';



COMMENT ON COLUMN "public"."correlation_matrices"."matrix_data" IS 'JSONB storing pairwise correlations: {"book1": {"book2": 0.45, ...}, ...}';



CREATE TABLE IF NOT EXISTS "public"."cv_profile" (
    "id" integer NOT NULL,
    "profile_name" "text" DEFAULT 'default'::"text",
    "skills" "text"[],
    "preferred_roles" "text"[],
    "preferred_companies" "text"[],
    "min_experience_years" integer,
    "max_experience_years" integer,
    "preferred_sectors" "text"[],
    "deal_breakers" "text"[],
    "strengths" "text",
    "weaknesses" "text",
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."cv_profile" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."cv_profile_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."cv_profile_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."cv_profile_id_seq" OWNED BY "public"."cv_profile"."id";



CREATE TABLE IF NOT EXISTS "public"."factor_exposures" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "book_id" "uuid" NOT NULL,
    "factor_category" character varying(100) NOT NULL,
    "factor_name" character varying(255) NOT NULL,
    "exposure_value" numeric(18,6) NOT NULL,
    "exposure_unit" character varying(50),
    "as_of_date" "date" NOT NULL,
    "calculated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."factor_exposures" OWNER TO "postgres";


COMMENT ON TABLE "public"."factor_exposures" IS 'Factor exposures per book for implied correlation calculation (Phase 2).';



CREATE TABLE IF NOT EXISTS "public"."funds" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "fund_type" character varying(100),
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."funds" OWNER TO "postgres";


COMMENT ON TABLE "public"."funds" IS 'Organizational grouping of books (optional hierarchy level).';



CREATE TABLE IF NOT EXISTS "public"."jobs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "raw_id" "uuid",
    "title" "text",
    "company" "text",
    "location" "text",
    "salary_range" "text",
    "description" "text",
    "requirements" "text",
    "source_site" "text",
    "source_url" "text",
    "posted_date" "date",
    "grade" integer,
    "grade_reasoning" "text",
    "status" "text" DEFAULT 'new'::"text",
    "notion_page_id" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."jobs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."jobs_raw" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "source_url" "text" NOT NULL,
    "source_site" "text" NOT NULL,
    "raw_content" "text",
    "scraped_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."jobs_raw" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."limit_breaches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "limit_id" "uuid" NOT NULL,
    "breach_timestamp" timestamp with time zone NOT NULL,
    "limit_value" numeric(18,6) NOT NULL,
    "actual_value" numeric(18,6) NOT NULL,
    "breach_amount" numeric(18,6) NOT NULL,
    "breach_percentage" numeric(10,4),
    "status" "public"."breach_status" DEFAULT 'active'::"public"."breach_status" NOT NULL,
    "resolved_at" timestamp with time zone,
    "resolved_value" numeric(18,6),
    "acknowledged_by" "uuid",
    "acknowledged_at" timestamp with time zone,
    "acknowledgment_notes" "text",
    "waived_by" "uuid",
    "waived_at" timestamp with time zone,
    "waiver_reason" "text",
    "waiver_expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."limit_breaches" OWNER TO "postgres";


COMMENT ON TABLE "public"."limit_breaches" IS 'Record of limit breaches for compliance and audit. 5-year retention.';



COMMENT ON COLUMN "public"."limit_breaches"."status" IS 'Breach lifecycle: active → acknowledged → resolved/waived.';



CREATE TABLE IF NOT EXISTS "public"."limits" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "scope" "public"."limit_scope" NOT NULL,
    "book_id" "uuid",
    "fund_id" "uuid",
    "metric_type" "public"."risk_metric_type" NOT NULL,
    "filter_dimension" character varying(100),
    "filter_value" character varying(255),
    "limit_type" "public"."limit_type" DEFAULT 'hard'::"public"."limit_type" NOT NULL,
    "limit_value" numeric(18,6) NOT NULL,
    "warning_threshold" numeric(18,6),
    "is_upper_limit" boolean DEFAULT true NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_by" "uuid",
    "approved_by" "uuid",
    "approved_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "effective_from" timestamp with time zone DEFAULT "now"() NOT NULL,
    "effective_to" timestamp with time zone,
    CONSTRAINT "valid_limit_scope" CHECK (((("scope" = 'book'::"public"."limit_scope") AND ("book_id" IS NOT NULL)) OR (("scope" = 'fund'::"public"."limit_scope") AND ("fund_id" IS NOT NULL)) OR ("scope" = ANY (ARRAY['tenant'::"public"."limit_scope", 'asset_class'::"public"."limit_scope", 'sector'::"public"."limit_scope", 'security'::"public"."limit_scope"]))))
);


ALTER TABLE "public"."limits" OWNER TO "postgres";


COMMENT ON TABLE "public"."limits" IS 'Risk limit definitions. Supports soft/hard limits at various scopes.';



COMMENT ON COLUMN "public"."limits"."warning_threshold" IS 'Early warning level before hard/soft limit (e.g., 80% of limit).';



CREATE TABLE IF NOT EXISTS "public"."model_overrides" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "security_id" "uuid" NOT NULL,
    "book_id" "uuid",
    "parameter_name" character varying(100) NOT NULL,
    "override_value" numeric(18,6) NOT NULL,
    "original_value" numeric(18,6),
    "reason" "text",
    "is_active" boolean DEFAULT true,
    "created_by" "uuid" NOT NULL,
    "approved_by" "uuid",
    "approved_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "expires_at" timestamp with time zone
);


ALTER TABLE "public"."model_overrides" OWNER TO "postgres";


COMMENT ON TABLE "public"."model_overrides" IS 'User-specified overrides for model inputs (e.g., custom volatility).';



COMMENT ON COLUMN "public"."model_overrides"."parameter_name" IS 'Model input being overridden: volatility, risk_free_rate, dividend_yield, etc.';



CREATE TABLE IF NOT EXISTS "public"."notifications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "title" character varying(255) NOT NULL,
    "message" "text" NOT NULL,
    "category" character varying(50) NOT NULL,
    "severity" character varying(20) DEFAULT 'info'::character varying NOT NULL,
    "resource_type" character varying(50),
    "resource_id" "uuid",
    "action_url" character varying(500),
    "is_read" boolean DEFAULT false,
    "read_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "expires_at" timestamp with time zone
);


ALTER TABLE "public"."notifications" OWNER TO "postgres";


COMMENT ON TABLE "public"."notifications" IS 'User notifications for limit breaches, imports, and system events.';



CREATE TABLE IF NOT EXISTS "public"."pending_invitations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "role" "public"."user_role" DEFAULT 'analyst'::"public"."user_role" NOT NULL,
    "invited_by" "uuid",
    "token" "uuid" DEFAULT "gen_random_uuid"(),
    "expires_at" timestamp with time zone DEFAULT ("now"() + '7 days'::interval),
    "accepted_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."pending_invitations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."position_changes" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "position_id" "uuid",
    "change_type" character varying(50) NOT NULL,
    "quantity_before" numeric(18,6),
    "quantity_after" numeric(18,6) NOT NULL,
    "quantity_change" numeric(18,6) NOT NULL,
    "trade_id" "uuid",
    "source_reference" character varying(255),
    "notes" "text",
    "changed_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "changed_by" "uuid"
);


ALTER TABLE "public"."position_changes" OWNER TO "postgres";


COMMENT ON TABLE "public"."position_changes" IS 'Event log of all position changes for complete audit trail.';



CREATE TABLE IF NOT EXISTS "public"."position_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "position_id" "uuid",
    "tenant_id" "uuid" NOT NULL,
    "book_id" "uuid" NOT NULL,
    "security_id" "uuid" NOT NULL,
    "snapshot_timestamp" timestamp with time zone NOT NULL,
    "snapshot_type" character varying(20) DEFAULT 'eod'::character varying NOT NULL,
    "quantity" numeric(18,6) NOT NULL,
    "direction" "public"."position_direction" NOT NULL,
    "market_value" numeric(18,2),
    "cost_basis" numeric(18,2),
    "unrealized_pnl" numeric(18,2),
    "price" numeric(18,6),
    "price_source" "public"."price_source",
    "local_currency" character varying(3),
    "base_currency" character varying(3),
    "fx_rate" numeric(18,6),
    "market_value_base" numeric(18,2),
    "beta" numeric(10,6),
    "delta" numeric(18,6),
    "gamma" numeric(18,6),
    "vega" numeric(18,6),
    "theta" numeric(18,6),
    "rho" numeric(18,6),
    "dv01" numeric(18,2),
    "cs01" numeric(18,2),
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."position_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."position_history" IS 'Historical position snapshots for time-travel queries and regression analysis. 5-year retention.';



COMMENT ON COLUMN "public"."position_history"."snapshot_type" IS 'Type of snapshot: eod (end-of-day), intraday, manual (correction).';



CREATE TABLE IF NOT EXISTS "public"."positions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "book_id" "uuid" NOT NULL,
    "security_id" "uuid" NOT NULL,
    "quantity" numeric(18,6) NOT NULL,
    "direction" "public"."position_direction" NOT NULL,
    "market_value" numeric(18,2),
    "cost_basis" numeric(18,2),
    "unrealized_pnl" numeric(18,2),
    "price" numeric(18,6),
    "price_source" "public"."price_source" DEFAULT 'market'::"public"."price_source",
    "price_as_of" timestamp with time zone,
    "local_currency" character varying(3),
    "base_currency" character varying(3) DEFAULT 'USD'::character varying,
    "fx_rate" numeric(18,6),
    "market_value_base" numeric(18,2),
    "beta" numeric(10,6),
    "delta" numeric(18,6),
    "gamma" numeric(18,6),
    "vega" numeric(18,6),
    "theta" numeric(18,6),
    "rho" numeric(18,6),
    "dv01" numeric(18,2),
    "cs01" numeric(18,2),
    "source" "public"."position_source" NOT NULL,
    "source_reference" character varying(255),
    "as_of_timestamp" timestamp with time zone NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."positions" OWNER TO "postgres";


COMMENT ON TABLE "public"."positions" IS 'Current positions - latest state per book/security. Primary table for risk calculations.';



COMMENT ON COLUMN "public"."positions"."source_reference" IS 'Reference to data source: upload_id for files, request_id for API, etc.';



COMMENT ON COLUMN "public"."positions"."as_of_timestamp" IS 'When this position state was valid. Used for point-in-time queries.';



CREATE TABLE IF NOT EXISTS "public"."research_articles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "source_site" "text" NOT NULL,
    "url" "text" NOT NULL,
    "title" "text" NOT NULL,
    "date_published" "date",
    "author" "text",
    "summary" "text",
    "full_text" "text",
    "tags" "text"[] DEFAULT '{}'::"text"[],
    "relevance_score" integer,
    "is_paywalled" boolean DEFAULT false,
    "scraped_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "research_articles_relevance_score_check" CHECK ((("relevance_score" >= 1) AND ("relevance_score" <= 5)))
);


ALTER TABLE "public"."research_articles" OWNER TO "postgres";


COMMENT ON TABLE "public"."research_articles" IS 'Market research articles for competitive intelligence';



COMMENT ON COLUMN "public"."research_articles"."relevance_score" IS '1-5 score: how relevant to multi-manager risk aggregation';



CREATE TABLE IF NOT EXISTS "public"."risk_metric_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "level" "public"."metric_level" NOT NULL,
    "book_id" "uuid",
    "fund_id" "uuid",
    "metric_type" "public"."risk_metric_type" NOT NULL,
    "value" numeric(18,6) NOT NULL,
    "dimension" character varying(100),
    "dimension_value" character varying(255),
    "snapshot_date" "date" NOT NULL,
    "snapshot_time" time without time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."risk_metric_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."risk_metric_history" IS 'Historical risk metrics for trend analysis and reporting.';



CREATE TABLE IF NOT EXISTS "public"."risk_metrics" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "level" "public"."metric_level" NOT NULL,
    "book_id" "uuid",
    "fund_id" "uuid",
    "position_id" "uuid",
    "metric_type" "public"."risk_metric_type" NOT NULL,
    "metric_name" character varying(100),
    "value" numeric(18,6) NOT NULL,
    "unit" character varying(50),
    "dimension" character varying(100),
    "dimension_value" character varying(255),
    "calculation_method" character varying(100),
    "calculation_params" "jsonb",
    "as_of_timestamp" timestamp with time zone NOT NULL,
    "calculated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "is_valid" boolean DEFAULT true,
    "validation_notes" "text"
);


ALTER TABLE "public"."risk_metrics" OWNER TO "postgres";


COMMENT ON TABLE "public"."risk_metrics" IS 'Pre-calculated risk metrics at position, book, fund, and tenant levels.';



COMMENT ON COLUMN "public"."risk_metrics"."dimension" IS 'Optional dimension for metric breakdown (e.g., by sector, asset_class).';



CREATE TABLE IF NOT EXISTS "public"."saved_views" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "book_ids" "uuid"[] NOT NULL,
    "config" "jsonb" DEFAULT '{}'::"jsonb",
    "is_shared" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."saved_views" OWNER TO "postgres";


COMMENT ON TABLE "public"."saved_views" IS 'User-saved book combinations and dashboard configurations.';



CREATE TABLE IF NOT EXISTS "public"."scrape_sources" (
    "id" integer NOT NULL,
    "site_name" "text" NOT NULL,
    "site_url" "text" NOT NULL,
    "is_active" boolean DEFAULT true,
    "last_scraped" timestamp with time zone,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."scrape_sources" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."scrape_sources_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."scrape_sources_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."scrape_sources_id_seq" OWNED BY "public"."scrape_sources"."id";



CREATE TABLE IF NOT EXISTS "public"."securities" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "figi" character varying(12),
    "name" character varying(500) NOT NULL,
    "description" "text",
    "asset_class" "public"."asset_class" NOT NULL,
    "security_type" character varying(100),
    "country_of_risk" character varying(3),
    "country_of_domicile" character varying(3),
    "region" character varying(100),
    "sector" character varying(100),
    "industry_group" character varying(100),
    "industry" character varying(100),
    "sub_industry" character varying(100),
    "currency" character varying(3) NOT NULL,
    "exchange_code" character varying(20),
    "exchange_name" character varying(255),
    "maturity_date" "date",
    "coupon_rate" numeric(10,6),
    "coupon_frequency" character varying(20),
    "credit_rating" character varying(10),
    "underlying_security_id" "uuid",
    "expiry_date" "date",
    "strike_price" numeric(18,6),
    "option_type" character varying(10),
    "contract_size" numeric(18,6),
    "data_source" character varying(100),
    "last_enriched_at" timestamp with time zone,
    "is_verified" boolean DEFAULT false,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."securities" OWNER TO "postgres";


COMMENT ON TABLE "public"."securities" IS 'Global security master. NOT tenant-scoped. Stores all securities ever seen. Indefinite retention.';



COMMENT ON COLUMN "public"."securities"."figi" IS 'Bloomberg Financial Instrument Global Identifier - preferred canonical ID.';



COMMENT ON COLUMN "public"."securities"."country_of_risk" IS 'ISO 3166-1 alpha-3 country code for risk attribution.';



COMMENT ON COLUMN "public"."securities"."last_enriched_at" IS 'Last time this security was enriched from OpenFIGI or other data source.';



CREATE TABLE IF NOT EXISTS "public"."security_identifiers" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "security_id" "uuid" NOT NULL,
    "identifier_type" "public"."identifier_type" NOT NULL,
    "identifier_value" character varying(50) NOT NULL,
    "exchange_code" character varying(20),
    "is_primary" boolean DEFAULT false,
    "source" character varying(100),
    "verified_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."security_identifiers" OWNER TO "postgres";


COMMENT ON TABLE "public"."security_identifiers" IS 'Multiple identifiers per security for flexible lookup. Maps CUSIP, ISIN, SEDOL, ticker, etc. to canonical security.';



CREATE TABLE IF NOT EXISTS "public"."security_prices" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "security_id" "uuid" NOT NULL,
    "price_date" "date" NOT NULL,
    "price_time" time without time zone,
    "price" numeric(18,6) NOT NULL,
    "bid_price" numeric(18,6),
    "ask_price" numeric(18,6),
    "volume" bigint,
    "source" "public"."price_source" DEFAULT 'market'::"public"."price_source" NOT NULL,
    "source_detail" character varying(255),
    "is_adjusted" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."security_prices" OWNER TO "postgres";


COMMENT ON TABLE "public"."security_prices" IS 'Historical price data. Used for risk calculations, P&L, and historical analysis. 5 year retention.';



COMMENT ON COLUMN "public"."security_prices"."is_adjusted" IS 'Whether price is adjusted for corporate actions (splits, dividends).';



CREATE TABLE IF NOT EXISTS "public"."tenants" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying(255) NOT NULL,
    "slug" character varying(100) NOT NULL,
    "plan" "public"."plan_type" DEFAULT 'free'::"public"."plan_type" NOT NULL,
    "max_users" integer DEFAULT 1 NOT NULL,
    "max_books" integer DEFAULT 1 NOT NULL,
    "api_enabled" boolean DEFAULT false NOT NULL,
    "api_rate_limit" integer,
    "settings" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "deactivated_at" timestamp with time zone,
    CONSTRAINT "valid_max_books" CHECK (("max_books" > 0)),
    CONSTRAINT "valid_max_users" CHECK (("max_users" > 0)),
    CONSTRAINT "valid_slug" CHECK ((("slug")::"text" ~ '^[a-z0-9-]+$'::"text"))
);


ALTER TABLE "public"."tenants" OWNER TO "postgres";


COMMENT ON TABLE "public"."tenants" IS 'Root entity for multi-tenancy. All data is scoped to a tenant.';



COMMENT ON COLUMN "public"."tenants"."slug" IS 'URL-friendly unique identifier for the tenant.';



COMMENT ON COLUMN "public"."tenants"."api_rate_limit" IS 'API rate limit in requests per minute. NULL means no API access.';



CREATE TABLE IF NOT EXISTS "public"."trades" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "book_id" "uuid" NOT NULL,
    "security_id" "uuid" NOT NULL,
    "trade_id_external" character varying(100),
    "order_id_external" character varying(100),
    "side" "public"."trade_side" NOT NULL,
    "quantity" numeric(18,6) NOT NULL,
    "price" numeric(18,6) NOT NULL,
    "notional" numeric(18,2),
    "currency" character varying(3) NOT NULL,
    "trade_date" "date" NOT NULL,
    "trade_time" time without time zone,
    "settlement_date" "date",
    "broker" character varying(255),
    "counterparty" character varying(255),
    "commission" numeric(18,6),
    "fees" numeric(18,6),
    "source" "public"."position_source" NOT NULL,
    "source_reference" character varying(255),
    "is_cancelled" boolean DEFAULT false,
    "cancelled_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."trades" OWNER TO "postgres";


COMMENT ON TABLE "public"."trades" IS 'Individual trade transactions. Full audit trail. 5-year retention.';



COMMENT ON COLUMN "public"."trades"."trade_id_external" IS 'Client trade ID from source system for reconciliation.';



CREATE TABLE IF NOT EXISTS "public"."upload_records" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "upload_id" "uuid" NOT NULL,
    "row_number" integer NOT NULL,
    "raw_data" "jsonb" NOT NULL,
    "is_processed" boolean DEFAULT false,
    "is_valid" boolean,
    "validation_errors" "jsonb",
    "position_id" "uuid",
    "trade_id" "uuid",
    "processed_at" timestamp with time zone
);


ALTER TABLE "public"."upload_records" OWNER TO "postgres";


COMMENT ON TABLE "public"."upload_records" IS 'Individual records from uploads for detailed audit and troubleshooting.';



CREATE TABLE IF NOT EXISTS "public"."uploads" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "uploaded_by" "uuid" NOT NULL,
    "file_name" character varying(500) NOT NULL,
    "file_type" "public"."upload_file_type" NOT NULL,
    "file_size_bytes" bigint,
    "mime_type" character varying(100),
    "storage_bucket" character varying(100) DEFAULT 'uploads'::character varying NOT NULL,
    "storage_path" character varying(1000) NOT NULL,
    "target_book_id" "uuid",
    "status" "public"."upload_status" DEFAULT 'pending'::"public"."upload_status" NOT NULL,
    "processing_started_at" timestamp with time zone,
    "processing_completed_at" timestamp with time zone,
    "records_total" integer,
    "records_processed" integer,
    "records_failed" integer,
    "error_message" "text",
    "processing_log" "jsonb",
    "validation_errors" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."uploads" OWNER TO "postgres";


COMMENT ON TABLE "public"."uploads" IS 'File upload tracking. Links to files in Supabase Storage. 5-year retention.';



COMMENT ON COLUMN "public"."uploads"."storage_path" IS 'Path in Supabase Storage bucket. Format: tenant_id/year/month/filename';



CREATE TABLE IF NOT EXISTS "public"."user_profile" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "target_roles" "text"[],
    "target_companies" "text"[],
    "skills" "text"[],
    "experience_summary" "text",
    "preferences" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_profile" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" NOT NULL,
    "tenant_id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "name" character varying(255),
    "role" "public"."user_role" DEFAULT 'analyst'::"public"."user_role" NOT NULL,
    "mfa_enabled" boolean DEFAULT false NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "last_login_at" timestamp with time zone
);


ALTER TABLE "public"."users" OWNER TO "postgres";


COMMENT ON TABLE "public"."users" IS 'RISKCORE users, extending Supabase auth.users with roles and tenant association.';



COMMENT ON COLUMN "public"."users"."role" IS 'User role determining permissions. See RLS policies for access rules.';



ALTER TABLE ONLY "public"."cv_profile" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."cv_profile_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."scrape_sources" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."scrape_sources_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."book_user_access"
    ADD CONSTRAINT "book_user_access_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."books"
    ADD CONSTRAINT "books_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."correlation_matrices"
    ADD CONSTRAINT "correlation_matrices_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."cv_profile"
    ADD CONSTRAINT "cv_profile_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."factor_exposures"
    ADD CONSTRAINT "factor_exposures_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."funds"
    ADD CONSTRAINT "funds_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."jobs"
    ADD CONSTRAINT "jobs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."jobs_raw"
    ADD CONSTRAINT "jobs_raw_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."jobs_raw"
    ADD CONSTRAINT "jobs_raw_source_url_key" UNIQUE ("source_url");



ALTER TABLE ONLY "public"."jobs"
    ADD CONSTRAINT "jobs_source_url_key" UNIQUE ("source_url");



ALTER TABLE ONLY "public"."limit_breaches"
    ADD CONSTRAINT "limit_breaches_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pending_invitations"
    ADD CONSTRAINT "pending_invitations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pending_invitations"
    ADD CONSTRAINT "pending_invitations_tenant_id_email_key" UNIQUE ("tenant_id", "email");



ALTER TABLE ONLY "public"."position_changes"
    ADD CONSTRAINT "position_changes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "position_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."positions"
    ADD CONSTRAINT "positions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."research_articles"
    ADD CONSTRAINT "research_articles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."research_articles"
    ADD CONSTRAINT "research_articles_url_key" UNIQUE ("url");



ALTER TABLE ONLY "public"."risk_metric_history"
    ADD CONSTRAINT "risk_metric_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."risk_metrics"
    ADD CONSTRAINT "risk_metrics_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."saved_views"
    ADD CONSTRAINT "saved_views_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."scrape_sources"
    ADD CONSTRAINT "scrape_sources_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."securities"
    ADD CONSTRAINT "securities_figi_key" UNIQUE ("figi");



ALTER TABLE ONLY "public"."securities"
    ADD CONSTRAINT "securities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."security_identifiers"
    ADD CONSTRAINT "security_identifiers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."security_prices"
    ADD CONSTRAINT "security_prices_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tenants"
    ADD CONSTRAINT "tenants_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tenants"
    ADD CONSTRAINT "tenants_slug_key" UNIQUE ("slug");



ALTER TABLE ONLY "public"."trades"
    ADD CONSTRAINT "trades_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."books"
    ADD CONSTRAINT "unique_book_name_per_tenant" UNIQUE ("tenant_id", "name");



ALTER TABLE ONLY "public"."book_user_access"
    ADD CONSTRAINT "unique_book_user" UNIQUE ("book_id", "user_id");



ALTER TABLE ONLY "public"."correlation_matrices"
    ADD CONSTRAINT "unique_correlation_matrix" UNIQUE ("tenant_id", "correlation_type", "as_of_date", "lookback_days");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "unique_email_per_tenant" UNIQUE ("tenant_id", "email");



ALTER TABLE ONLY "public"."trades"
    ADD CONSTRAINT "unique_external_trade" UNIQUE ("tenant_id", "trade_id_external");



ALTER TABLE ONLY "public"."factor_exposures"
    ADD CONSTRAINT "unique_factor_exposure" UNIQUE ("book_id", "factor_name", "as_of_date");



ALTER TABLE ONLY "public"."funds"
    ADD CONSTRAINT "unique_fund_name_per_tenant" UNIQUE ("tenant_id", "name");



ALTER TABLE ONLY "public"."security_identifiers"
    ADD CONSTRAINT "unique_identifier" UNIQUE ("identifier_type", "identifier_value", "exchange_code");



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "unique_override" UNIQUE ("tenant_id", "security_id", "book_id", "parameter_name");



ALTER TABLE ONLY "public"."positions"
    ADD CONSTRAINT "unique_position_per_book_security" UNIQUE ("book_id", "security_id");



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "unique_position_snapshot" UNIQUE ("book_id", "security_id", "snapshot_timestamp");



ALTER TABLE ONLY "public"."security_prices"
    ADD CONSTRAINT "unique_security_price_date" UNIQUE ("security_id", "price_date", "price_time");



ALTER TABLE ONLY "public"."saved_views"
    ADD CONSTRAINT "unique_view_name_per_user" UNIQUE ("user_id", "name");



ALTER TABLE ONLY "public"."upload_records"
    ADD CONSTRAINT "upload_records_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."uploads"
    ADD CONSTRAINT "uploads_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_profile"
    ADD CONSTRAINT "user_profile_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_api_keys_prefix" ON "public"."api_keys" USING "btree" ("key_prefix");



CREATE INDEX "idx_api_keys_status" ON "public"."api_keys" USING "btree" ("status") WHERE ("status" = 'active'::"public"."api_key_status");



CREATE INDEX "idx_api_keys_tenant" ON "public"."api_keys" USING "btree" ("tenant_id");



CREATE INDEX "idx_audit_logs_action" ON "public"."audit_logs" USING "btree" ("action");



CREATE INDEX "idx_audit_logs_category" ON "public"."audit_logs" USING "btree" ("category");



CREATE INDEX "idx_audit_logs_created" ON "public"."audit_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_audit_logs_failed" ON "public"."audit_logs" USING "btree" ("tenant_id", "created_at" DESC) WHERE ("success" = false);



CREATE INDEX "idx_audit_logs_tenant" ON "public"."audit_logs" USING "btree" ("tenant_id");



CREATE INDEX "idx_audit_logs_tenant_date" ON "public"."audit_logs" USING "btree" ("tenant_id", "created_at" DESC);



CREATE INDEX "idx_audit_logs_user" ON "public"."audit_logs" USING "btree" ("user_id") WHERE ("user_id" IS NOT NULL);



CREATE INDEX "idx_book_user_access_book" ON "public"."book_user_access" USING "btree" ("book_id");



CREATE INDEX "idx_book_user_access_user" ON "public"."book_user_access" USING "btree" ("user_id");



CREATE INDEX "idx_books_fund" ON "public"."books" USING "btree" ("fund_id");



CREATE INDEX "idx_books_tenant" ON "public"."books" USING "btree" ("tenant_id");



CREATE INDEX "idx_correlation_matrices_date" ON "public"."correlation_matrices" USING "btree" ("as_of_date" DESC);



CREATE INDEX "idx_correlation_matrices_tenant" ON "public"."correlation_matrices" USING "btree" ("tenant_id");



CREATE INDEX "idx_factor_exposures_book" ON "public"."factor_exposures" USING "btree" ("book_id");



CREATE INDEX "idx_factor_exposures_date" ON "public"."factor_exposures" USING "btree" ("as_of_date" DESC);



CREATE INDEX "idx_factor_exposures_factor" ON "public"."factor_exposures" USING "btree" ("factor_name");



CREATE INDEX "idx_funds_tenant" ON "public"."funds" USING "btree" ("tenant_id");



CREATE INDEX "idx_limit_breaches_limit" ON "public"."limit_breaches" USING "btree" ("limit_id");



CREATE INDEX "idx_limit_breaches_status" ON "public"."limit_breaches" USING "btree" ("status") WHERE ("status" = 'active'::"public"."breach_status");



CREATE INDEX "idx_limit_breaches_tenant" ON "public"."limit_breaches" USING "btree" ("tenant_id");



CREATE INDEX "idx_limit_breaches_timestamp" ON "public"."limit_breaches" USING "btree" ("breach_timestamp" DESC);



CREATE INDEX "idx_limits_active" ON "public"."limits" USING "btree" ("tenant_id") WHERE ("is_active" = true);



CREATE INDEX "idx_limits_book" ON "public"."limits" USING "btree" ("book_id") WHERE ("book_id" IS NOT NULL);



CREATE INDEX "idx_limits_fund" ON "public"."limits" USING "btree" ("fund_id") WHERE ("fund_id" IS NOT NULL);



CREATE INDEX "idx_limits_metric" ON "public"."limits" USING "btree" ("metric_type");



CREATE INDEX "idx_limits_tenant" ON "public"."limits" USING "btree" ("tenant_id");



CREATE INDEX "idx_model_overrides_active" ON "public"."model_overrides" USING "btree" ("tenant_id") WHERE ("is_active" = true);



CREATE INDEX "idx_model_overrides_security" ON "public"."model_overrides" USING "btree" ("security_id");



CREATE INDEX "idx_model_overrides_tenant" ON "public"."model_overrides" USING "btree" ("tenant_id");



CREATE INDEX "idx_notifications_created" ON "public"."notifications" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_notifications_unread" ON "public"."notifications" USING "btree" ("user_id", "is_read") WHERE ("is_read" = false);



CREATE INDEX "idx_notifications_user" ON "public"."notifications" USING "btree" ("user_id");



CREATE INDEX "idx_pending_invitations_email" ON "public"."pending_invitations" USING "btree" ("email");



CREATE INDEX "idx_pending_invitations_token" ON "public"."pending_invitations" USING "btree" ("token");



CREATE INDEX "idx_position_changes_changed_at" ON "public"."position_changes" USING "btree" ("changed_at" DESC);



CREATE INDEX "idx_position_changes_position" ON "public"."position_changes" USING "btree" ("position_id");



CREATE INDEX "idx_position_changes_tenant" ON "public"."position_changes" USING "btree" ("tenant_id");



CREATE INDEX "idx_position_history_book" ON "public"."position_history" USING "btree" ("book_id");



CREATE INDEX "idx_position_history_book_snapshot" ON "public"."position_history" USING "btree" ("book_id", "snapshot_timestamp" DESC);



CREATE INDEX "idx_position_history_security" ON "public"."position_history" USING "btree" ("security_id");



CREATE INDEX "idx_position_history_snapshot" ON "public"."position_history" USING "btree" ("snapshot_timestamp" DESC);



CREATE INDEX "idx_position_history_tenant" ON "public"."position_history" USING "btree" ("tenant_id");



CREATE INDEX "idx_positions_as_of" ON "public"."positions" USING "btree" ("as_of_timestamp" DESC);



CREATE INDEX "idx_positions_book" ON "public"."positions" USING "btree" ("book_id");



CREATE INDEX "idx_positions_book_security" ON "public"."positions" USING "btree" ("book_id", "security_id");



CREATE INDEX "idx_positions_direction" ON "public"."positions" USING "btree" ("book_id", "direction") WHERE ("direction" <> 'flat'::"public"."position_direction");



CREATE INDEX "idx_positions_security" ON "public"."positions" USING "btree" ("security_id");



CREATE INDEX "idx_positions_tenant" ON "public"."positions" USING "btree" ("tenant_id");



CREATE INDEX "idx_research_date" ON "public"."research_articles" USING "btree" ("date_published" DESC);



CREATE INDEX "idx_research_fts" ON "public"."research_articles" USING "gin" ("to_tsvector"('"english"'::"regconfig", ((((COALESCE("title", ''::"text") || ' '::"text") || COALESCE("summary", ''::"text")) || ' '::"text") || COALESCE("full_text", ''::"text"))));



CREATE INDEX "idx_research_relevance" ON "public"."research_articles" USING "btree" ("relevance_score" DESC);



CREATE INDEX "idx_research_source" ON "public"."research_articles" USING "btree" ("source_site");



CREATE INDEX "idx_research_tags" ON "public"."research_articles" USING "gin" ("tags");



CREATE INDEX "idx_risk_metric_history_book_date" ON "public"."risk_metric_history" USING "btree" ("book_id", "snapshot_date" DESC);



CREATE INDEX "idx_risk_metric_history_type_date" ON "public"."risk_metric_history" USING "btree" ("metric_type", "snapshot_date" DESC);



CREATE INDEX "idx_risk_metrics_as_of" ON "public"."risk_metrics" USING "btree" ("as_of_timestamp" DESC);



CREATE INDEX "idx_risk_metrics_book" ON "public"."risk_metrics" USING "btree" ("book_id") WHERE ("book_id" IS NOT NULL);



CREATE INDEX "idx_risk_metrics_book_type" ON "public"."risk_metrics" USING "btree" ("book_id", "metric_type", "as_of_timestamp" DESC);



CREATE INDEX "idx_risk_metrics_fund" ON "public"."risk_metrics" USING "btree" ("fund_id") WHERE ("fund_id" IS NOT NULL);



CREATE INDEX "idx_risk_metrics_latest" ON "public"."risk_metrics" USING "btree" ("tenant_id", "level", "metric_type", "as_of_timestamp" DESC);



CREATE INDEX "idx_risk_metrics_level" ON "public"."risk_metrics" USING "btree" ("level");



CREATE INDEX "idx_risk_metrics_tenant" ON "public"."risk_metrics" USING "btree" ("tenant_id");



CREATE INDEX "idx_risk_metrics_type" ON "public"."risk_metrics" USING "btree" ("metric_type");



CREATE INDEX "idx_saved_views_shared" ON "public"."saved_views" USING "btree" ("tenant_id") WHERE ("is_shared" = true);



CREATE INDEX "idx_saved_views_user" ON "public"."saved_views" USING "btree" ("user_id");



CREATE INDEX "idx_securities_asset_class" ON "public"."securities" USING "btree" ("asset_class");



CREATE INDEX "idx_securities_country" ON "public"."securities" USING "btree" ("country_of_risk");



CREATE INDEX "idx_securities_currency" ON "public"."securities" USING "btree" ("currency");



CREATE INDEX "idx_securities_figi" ON "public"."securities" USING "btree" ("figi");



CREATE INDEX "idx_securities_name_search" ON "public"."securities" USING "gin" ("to_tsvector"('"english"'::"regconfig", ("name")::"text"));



CREATE INDEX "idx_securities_sector" ON "public"."securities" USING "btree" ("sector");



CREATE INDEX "idx_securities_underlying" ON "public"."securities" USING "btree" ("underlying_security_id");



CREATE INDEX "idx_security_identifiers_lookup" ON "public"."security_identifiers" USING "btree" ("identifier_type", "identifier_value");



CREATE INDEX "idx_security_identifiers_security" ON "public"."security_identifiers" USING "btree" ("security_id");



CREATE INDEX "idx_security_identifiers_value" ON "public"."security_identifiers" USING "btree" ("identifier_value");



CREATE INDEX "idx_security_prices_date" ON "public"."security_prices" USING "btree" ("price_date" DESC);



CREATE INDEX "idx_security_prices_security_date" ON "public"."security_prices" USING "btree" ("security_id", "price_date" DESC);



CREATE INDEX "idx_trades_book" ON "public"."trades" USING "btree" ("book_id");



CREATE INDEX "idx_trades_book_date" ON "public"."trades" USING "btree" ("book_id", "trade_date" DESC);



CREATE INDEX "idx_trades_external_id" ON "public"."trades" USING "btree" ("trade_id_external") WHERE ("trade_id_external" IS NOT NULL);



CREATE INDEX "idx_trades_security" ON "public"."trades" USING "btree" ("security_id");



CREATE INDEX "idx_trades_tenant" ON "public"."trades" USING "btree" ("tenant_id");



CREATE INDEX "idx_trades_trade_date" ON "public"."trades" USING "btree" ("trade_date" DESC);



CREATE INDEX "idx_upload_records_position" ON "public"."upload_records" USING "btree" ("position_id") WHERE ("position_id" IS NOT NULL);



CREATE INDEX "idx_upload_records_trade" ON "public"."upload_records" USING "btree" ("trade_id") WHERE ("trade_id" IS NOT NULL);



CREATE INDEX "idx_upload_records_upload" ON "public"."upload_records" USING "btree" ("upload_id");



CREATE INDEX "idx_uploads_book" ON "public"."uploads" USING "btree" ("target_book_id") WHERE ("target_book_id" IS NOT NULL);



CREATE INDEX "idx_uploads_created" ON "public"."uploads" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_uploads_status" ON "public"."uploads" USING "btree" ("status");



CREATE INDEX "idx_uploads_tenant" ON "public"."uploads" USING "btree" ("tenant_id");



CREATE INDEX "idx_uploads_user" ON "public"."uploads" USING "btree" ("uploaded_by");



CREATE INDEX "idx_users_email" ON "public"."users" USING "btree" ("email");



CREATE INDEX "idx_users_role" ON "public"."users" USING "btree" ("tenant_id", "role");



CREATE INDEX "idx_users_tenant" ON "public"."users" USING "btree" ("tenant_id");



CREATE OR REPLACE TRIGGER "books_updated_at" BEFORE UPDATE ON "public"."books" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "funds_updated_at" BEFORE UPDATE ON "public"."funds" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "limit_breaches_updated_at" BEFORE UPDATE ON "public"."limit_breaches" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "limits_updated_at" BEFORE UPDATE ON "public"."limits" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "model_overrides_updated_at" BEFORE UPDATE ON "public"."model_overrides" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "positions_updated_at" BEFORE UPDATE ON "public"."positions" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "saved_views_updated_at" BEFORE UPDATE ON "public"."saved_views" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "securities_updated_at" BEFORE UPDATE ON "public"."securities" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "tenants_updated_at" BEFORE UPDATE ON "public"."tenants" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "uploads_updated_at" BEFORE UPDATE ON "public"."uploads" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "users_updated_at" BEFORE UPDATE ON "public"."users" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_revoked_by_fkey" FOREIGN KEY ("revoked_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."book_user_access"
    ADD CONSTRAINT "book_user_access_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."book_user_access"
    ADD CONSTRAINT "book_user_access_granted_by_fkey" FOREIGN KEY ("granted_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."book_user_access"
    ADD CONSTRAINT "book_user_access_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."books"
    ADD CONSTRAINT "books_fund_id_fkey" FOREIGN KEY ("fund_id") REFERENCES "public"."funds"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."books"
    ADD CONSTRAINT "books_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."correlation_matrices"
    ADD CONSTRAINT "correlation_matrices_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."factor_exposures"
    ADD CONSTRAINT "factor_exposures_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."factor_exposures"
    ADD CONSTRAINT "factor_exposures_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."funds"
    ADD CONSTRAINT "funds_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."jobs"
    ADD CONSTRAINT "jobs_raw_id_fkey" FOREIGN KEY ("raw_id") REFERENCES "public"."jobs_raw"("id");



ALTER TABLE ONLY "public"."limit_breaches"
    ADD CONSTRAINT "limit_breaches_acknowledged_by_fkey" FOREIGN KEY ("acknowledged_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."limit_breaches"
    ADD CONSTRAINT "limit_breaches_limit_id_fkey" FOREIGN KEY ("limit_id") REFERENCES "public"."limits"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."limit_breaches"
    ADD CONSTRAINT "limit_breaches_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."limit_breaches"
    ADD CONSTRAINT "limit_breaches_waived_by_fkey" FOREIGN KEY ("waived_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_approved_by_fkey" FOREIGN KEY ("approved_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_fund_id_fkey" FOREIGN KEY ("fund_id") REFERENCES "public"."funds"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."limits"
    ADD CONSTRAINT "limits_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_approved_by_fkey" FOREIGN KEY ("approved_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."model_overrides"
    ADD CONSTRAINT "model_overrides_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pending_invitations"
    ADD CONSTRAINT "pending_invitations_invited_by_fkey" FOREIGN KEY ("invited_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."pending_invitations"
    ADD CONSTRAINT "pending_invitations_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."position_changes"
    ADD CONSTRAINT "position_changes_changed_by_fkey" FOREIGN KEY ("changed_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."position_changes"
    ADD CONSTRAINT "position_changes_position_id_fkey" FOREIGN KEY ("position_id") REFERENCES "public"."positions"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."position_changes"
    ADD CONSTRAINT "position_changes_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."position_changes"
    ADD CONSTRAINT "position_changes_trade_id_fkey" FOREIGN KEY ("trade_id") REFERENCES "public"."trades"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "position_history_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "position_history_position_id_fkey" FOREIGN KEY ("position_id") REFERENCES "public"."positions"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "position_history_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."position_history"
    ADD CONSTRAINT "position_history_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."positions"
    ADD CONSTRAINT "positions_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."positions"
    ADD CONSTRAINT "positions_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."positions"
    ADD CONSTRAINT "positions_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metric_history"
    ADD CONSTRAINT "risk_metric_history_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metric_history"
    ADD CONSTRAINT "risk_metric_history_fund_id_fkey" FOREIGN KEY ("fund_id") REFERENCES "public"."funds"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metric_history"
    ADD CONSTRAINT "risk_metric_history_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metrics"
    ADD CONSTRAINT "risk_metrics_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metrics"
    ADD CONSTRAINT "risk_metrics_fund_id_fkey" FOREIGN KEY ("fund_id") REFERENCES "public"."funds"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metrics"
    ADD CONSTRAINT "risk_metrics_position_id_fkey" FOREIGN KEY ("position_id") REFERENCES "public"."positions"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."risk_metrics"
    ADD CONSTRAINT "risk_metrics_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."saved_views"
    ADD CONSTRAINT "saved_views_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."saved_views"
    ADD CONSTRAINT "saved_views_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."securities"
    ADD CONSTRAINT "securities_underlying_security_id_fkey" FOREIGN KEY ("underlying_security_id") REFERENCES "public"."securities"("id");



ALTER TABLE ONLY "public"."security_identifiers"
    ADD CONSTRAINT "security_identifiers_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."security_prices"
    ADD CONSTRAINT "security_prices_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."trades"
    ADD CONSTRAINT "trades_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "public"."books"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."trades"
    ADD CONSTRAINT "trades_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "public"."securities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."trades"
    ADD CONSTRAINT "trades_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."upload_records"
    ADD CONSTRAINT "upload_records_position_id_fkey" FOREIGN KEY ("position_id") REFERENCES "public"."positions"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."upload_records"
    ADD CONSTRAINT "upload_records_trade_id_fkey" FOREIGN KEY ("trade_id") REFERENCES "public"."trades"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."upload_records"
    ADD CONSTRAINT "upload_records_upload_id_fkey" FOREIGN KEY ("upload_id") REFERENCES "public"."uploads"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."uploads"
    ADD CONSTRAINT "uploads_target_book_id_fkey" FOREIGN KEY ("target_book_id") REFERENCES "public"."books"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."uploads"
    ADD CONSTRAINT "uploads_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."uploads"
    ADD CONSTRAINT "uploads_uploaded_by_fkey" FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



CREATE POLICY "Admins manage invitations" ON "public"."pending_invitations" USING (("tenant_id" IN ( SELECT "users"."tenant_id"
   FROM "public"."users"
  WHERE (("users"."id" = "auth"."uid"()) AND ("users"."role" = ANY (ARRAY['superadmin'::"public"."user_role", 'admin'::"public"."user_role"])) AND ("users"."is_active" = true)))));



CREATE POLICY "Allow all on cv_profile" ON "public"."cv_profile" USING (true);



CREATE POLICY "Allow all on scrape_sources" ON "public"."scrape_sources" USING (true);



CREATE POLICY "admin_manage_api_keys" ON "public"."api_keys" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_book_access" ON "public"."book_user_access" TO "authenticated" USING (((EXISTS ( SELECT 1
   FROM "public"."books" "b"
  WHERE (("b"."id" = "book_user_access"."book_id") AND ("b"."tenant_id" = "public"."riskcore_tenant_id"())))) AND ("public"."riskcore_is_admin_or_higher"() OR ("public"."riskcore_user_role"() = 'cro'::"public"."user_role"))));



CREATE POLICY "admin_manage_books" ON "public"."books" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_correlations" ON "public"."correlation_matrices" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_position_history" ON "public"."position_history" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_positions" ON "public"."positions" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_risk_metrics" ON "public"."risk_metrics" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_securities" ON "public"."securities" TO "authenticated" USING ("public"."riskcore_is_admin_or_higher"());



CREATE POLICY "admin_manage_security_identifiers" ON "public"."security_identifiers" TO "authenticated" USING ("public"."riskcore_is_admin_or_higher"());



CREATE POLICY "admin_manage_security_prices" ON "public"."security_prices" TO "authenticated" USING ("public"."riskcore_is_admin_or_higher"());



CREATE POLICY "admin_manage_trades" ON "public"."trades" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_upload_records" ON "public"."upload_records" TO "authenticated" USING (((EXISTS ( SELECT 1
   FROM "public"."uploads" "u"
  WHERE (("u"."id" = "upload_records"."upload_id") AND ("u"."tenant_id" = "public"."riskcore_tenant_id"())))) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_uploads" ON "public"."uploads" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_manage_users" ON "public"."users" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "admin_read_audit_logs" ON "public"."audit_logs" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_admin_or_higher"()));



CREATE POLICY "all_read_securities" ON "public"."securities" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "all_read_security_identifiers" ON "public"."security_identifiers" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "all_read_security_prices" ON "public"."security_prices" FOR SELECT TO "authenticated" USING (true);



ALTER TABLE "public"."api_keys" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "assigned_access_books" ON "public"."books" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_has_book_access"("id")));



ALTER TABLE "public"."audit_logs" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "book_access_position_history" ON "public"."position_history" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_has_book_access"("book_id")));



CREATE POLICY "book_access_positions" ON "public"."positions" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_has_book_access"("book_id")));



CREATE POLICY "book_access_risk_metrics" ON "public"."risk_metrics" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND (("book_id" IS NULL) OR "public"."riskcore_has_book_access"("book_id"))));



CREATE POLICY "book_access_trades" ON "public"."trades" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_has_book_access"("book_id")));



ALTER TABLE "public"."book_user_access" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."books" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."correlation_matrices" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "cro_manage_limit_breaches" ON "public"."limit_breaches" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_cro_or_higher"()));



CREATE POLICY "cro_manage_limits" ON "public"."limits" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_cro_or_higher"()));



CREATE POLICY "cro_manage_model_overrides" ON "public"."model_overrides" TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_is_cro_or_higher"()));



ALTER TABLE "public"."cv_profile" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."factor_exposures" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "firm_wide_access_books" ON "public"."books" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



CREATE POLICY "firm_wide_access_position_history" ON "public"."position_history" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



CREATE POLICY "firm_wide_access_positions" ON "public"."positions" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



CREATE POLICY "firm_wide_access_trades" ON "public"."trades" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



CREATE POLICY "firm_wide_correlations" ON "public"."correlation_matrices" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



CREATE POLICY "firm_wide_risk_metrics" ON "public"."risk_metrics" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND "public"."riskcore_can_view_firm_wide"()));



ALTER TABLE "public"."funds" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."limit_breaches" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."limits" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."model_overrides" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."notifications" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."pending_invitations" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "pm_create_model_overrides" ON "public"."model_overrides" FOR INSERT TO "authenticated" WITH CHECK ((("tenant_id" = "public"."riskcore_tenant_id"()) AND (("book_id" IS NULL) OR "public"."riskcore_has_book_access"("book_id"))));



ALTER TABLE "public"."position_changes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."position_history" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."positions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."risk_metric_history" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."risk_metrics" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."saved_views" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."scrape_sources" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."securities" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."security_identifiers" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."security_prices" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "superadmin_all_tenants" ON "public"."tenants" TO "authenticated" USING (("public"."riskcore_user_role"() = 'superadmin'::"public"."user_role"));



CREATE POLICY "tenant_isolation_factor_exposures" ON "public"."factor_exposures" TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_isolation_funds" ON "public"."funds" TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_isolation_position_changes" ON "public"."position_changes" TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_isolation_risk_metric_history" ON "public"."risk_metric_history" TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_read_limit_breaches" ON "public"."limit_breaches" FOR SELECT TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_read_limits" ON "public"."limits" FOR SELECT TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "tenant_read_model_overrides" ON "public"."model_overrides" FOR SELECT TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



ALTER TABLE "public"."tenants" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."trades" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."upload_records" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."uploads" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "users_manage_own_views" ON "public"."saved_views" TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "users_own_notifications" ON "public"."notifications" TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "users_own_tenant" ON "public"."tenants" FOR SELECT TO "authenticated" USING (("id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "users_see_colleagues" ON "public"."users" FOR SELECT TO "authenticated" USING (("tenant_id" = "public"."riskcore_tenant_id"()));



CREATE POLICY "users_see_own_access" ON "public"."book_user_access" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "users_see_own_uploads" ON "public"."uploads" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND ("uploaded_by" = "auth"."uid"())));



CREATE POLICY "users_see_shared_views" ON "public"."saved_views" FOR SELECT TO "authenticated" USING ((("tenant_id" = "public"."riskcore_tenant_id"()) AND ("is_shared" = true)));



CREATE POLICY "users_update_self" ON "public"."users" FOR UPDATE TO "authenticated" USING (("id" = "auth"."uid"())) WITH CHECK ((("id" = "auth"."uid"()) AND ("tenant_id" = "public"."riskcore_tenant_id"())));





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."calculate_direction"("p_quantity" numeric) TO "anon";
GRANT ALL ON FUNCTION "public"."calculate_direction"("p_quantity" numeric) TO "authenticated";
GRANT ALL ON FUNCTION "public"."calculate_direction"("p_quantity" numeric) TO "service_role";



GRANT ALL ON FUNCTION "public"."check_limit_breach"("p_limit_id" "uuid", "p_current_value" numeric) TO "anon";
GRANT ALL ON FUNCTION "public"."check_limit_breach"("p_limit_id" "uuid", "p_current_value" numeric) TO "authenticated";
GRANT ALL ON FUNCTION "public"."check_limit_breach"("p_limit_id" "uuid", "p_current_value" numeric) TO "service_role";



GRANT ALL ON FUNCTION "public"."deactivate_user"("p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."deactivate_user"("p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."deactivate_user"("p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."find_security_by_identifier"("p_identifier_type" "public"."identifier_type", "p_identifier_value" character varying, "p_exchange_code" character varying) TO "anon";
GRANT ALL ON FUNCTION "public"."find_security_by_identifier"("p_identifier_type" "public"."identifier_type", "p_identifier_value" character varying, "p_exchange_code" character varying) TO "authenticated";
GRANT ALL ON FUNCTION "public"."find_security_by_identifier"("p_identifier_type" "public"."identifier_type", "p_identifier_value" character varying, "p_exchange_code" character varying) TO "service_role";



GRANT ALL ON FUNCTION "public"."get_active_breaches"("p_tenant_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_active_breaches"("p_tenant_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_active_breaches"("p_tenant_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_book_summary"("p_book_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_book_summary"("p_book_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_book_summary"("p_book_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_current_user_profile"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_current_user_profile"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_current_user_profile"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_latest_price"("p_security_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_latest_price"("p_security_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_latest_price"("p_security_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_position_at_time"("p_book_id" "uuid", "p_security_id" "uuid", "p_timestamp" timestamp with time zone) TO "anon";
GRANT ALL ON FUNCTION "public"."get_position_at_time"("p_book_id" "uuid", "p_security_id" "uuid", "p_timestamp" timestamp with time zone) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_position_at_time"("p_book_id" "uuid", "p_security_id" "uuid", "p_timestamp" timestamp with time zone) TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_user_deleted"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_user_deleted"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_user_deleted"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_user_updated"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_user_updated"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_user_updated"() TO "service_role";



GRANT ALL ON FUNCTION "public"."invite_user"("p_email" "text", "p_role" "public"."user_role", "p_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."invite_user"("p_email" "text", "p_role" "public"."user_role", "p_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."invite_user"("p_email" "text", "p_role" "public"."user_role", "p_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."log_audit_event"("p_tenant_id" "uuid", "p_user_id" "uuid", "p_action" character varying, "p_category" "public"."audit_category", "p_resource_type" character varying, "p_resource_id" "uuid", "p_details" "jsonb", "p_ip_address" "inet", "p_user_agent" "text", "p_success" boolean, "p_error_message" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."log_audit_event"("p_tenant_id" "uuid", "p_user_id" "uuid", "p_action" character varying, "p_category" "public"."audit_category", "p_resource_type" character varying, "p_resource_id" "uuid", "p_details" "jsonb", "p_ip_address" "inet", "p_user_agent" "text", "p_success" boolean, "p_error_message" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."log_audit_event"("p_tenant_id" "uuid", "p_user_id" "uuid", "p_action" character varying, "p_category" "public"."audit_category", "p_resource_type" character varying, "p_resource_id" "uuid", "p_details" "jsonb", "p_ip_address" "inet", "p_user_agent" "text", "p_success" boolean, "p_error_message" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."reactivate_user"("p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."reactivate_user"("p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."reactivate_user"("p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_can_view_firm_wide"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_can_view_firm_wide"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_can_view_firm_wide"() TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_current_user_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_current_user_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_current_user_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_has_book_access"("p_book_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_is_admin_or_higher"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_is_admin_or_higher"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_is_admin_or_higher"() TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_is_cro_or_higher"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_is_cro_or_higher"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_is_cro_or_higher"() TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_tenant_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_tenant_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_tenant_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."riskcore_user_role"() TO "anon";
GRANT ALL ON FUNCTION "public"."riskcore_user_role"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."riskcore_user_role"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "service_role";


















GRANT ALL ON TABLE "public"."api_keys" TO "anon";
GRANT ALL ON TABLE "public"."api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."audit_logs" TO "anon";
GRANT ALL ON TABLE "public"."audit_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_logs" TO "service_role";



GRANT ALL ON TABLE "public"."book_user_access" TO "anon";
GRANT ALL ON TABLE "public"."book_user_access" TO "authenticated";
GRANT ALL ON TABLE "public"."book_user_access" TO "service_role";



GRANT ALL ON TABLE "public"."books" TO "anon";
GRANT ALL ON TABLE "public"."books" TO "authenticated";
GRANT ALL ON TABLE "public"."books" TO "service_role";



GRANT ALL ON TABLE "public"."correlation_matrices" TO "anon";
GRANT ALL ON TABLE "public"."correlation_matrices" TO "authenticated";
GRANT ALL ON TABLE "public"."correlation_matrices" TO "service_role";



GRANT ALL ON TABLE "public"."cv_profile" TO "anon";
GRANT ALL ON TABLE "public"."cv_profile" TO "authenticated";
GRANT ALL ON TABLE "public"."cv_profile" TO "service_role";



GRANT ALL ON SEQUENCE "public"."cv_profile_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."cv_profile_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."cv_profile_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."factor_exposures" TO "anon";
GRANT ALL ON TABLE "public"."factor_exposures" TO "authenticated";
GRANT ALL ON TABLE "public"."factor_exposures" TO "service_role";



GRANT ALL ON TABLE "public"."funds" TO "anon";
GRANT ALL ON TABLE "public"."funds" TO "authenticated";
GRANT ALL ON TABLE "public"."funds" TO "service_role";



GRANT ALL ON TABLE "public"."jobs" TO "anon";
GRANT ALL ON TABLE "public"."jobs" TO "authenticated";
GRANT ALL ON TABLE "public"."jobs" TO "service_role";



GRANT ALL ON TABLE "public"."jobs_raw" TO "anon";
GRANT ALL ON TABLE "public"."jobs_raw" TO "authenticated";
GRANT ALL ON TABLE "public"."jobs_raw" TO "service_role";



GRANT ALL ON TABLE "public"."limit_breaches" TO "anon";
GRANT ALL ON TABLE "public"."limit_breaches" TO "authenticated";
GRANT ALL ON TABLE "public"."limit_breaches" TO "service_role";



GRANT ALL ON TABLE "public"."limits" TO "anon";
GRANT ALL ON TABLE "public"."limits" TO "authenticated";
GRANT ALL ON TABLE "public"."limits" TO "service_role";



GRANT ALL ON TABLE "public"."model_overrides" TO "anon";
GRANT ALL ON TABLE "public"."model_overrides" TO "authenticated";
GRANT ALL ON TABLE "public"."model_overrides" TO "service_role";



GRANT ALL ON TABLE "public"."notifications" TO "anon";
GRANT ALL ON TABLE "public"."notifications" TO "authenticated";
GRANT ALL ON TABLE "public"."notifications" TO "service_role";



GRANT ALL ON TABLE "public"."pending_invitations" TO "anon";
GRANT ALL ON TABLE "public"."pending_invitations" TO "authenticated";
GRANT ALL ON TABLE "public"."pending_invitations" TO "service_role";



GRANT ALL ON TABLE "public"."position_changes" TO "anon";
GRANT ALL ON TABLE "public"."position_changes" TO "authenticated";
GRANT ALL ON TABLE "public"."position_changes" TO "service_role";



GRANT ALL ON TABLE "public"."position_history" TO "anon";
GRANT ALL ON TABLE "public"."position_history" TO "authenticated";
GRANT ALL ON TABLE "public"."position_history" TO "service_role";



GRANT ALL ON TABLE "public"."positions" TO "anon";
GRANT ALL ON TABLE "public"."positions" TO "authenticated";
GRANT ALL ON TABLE "public"."positions" TO "service_role";



GRANT ALL ON TABLE "public"."research_articles" TO "anon";
GRANT ALL ON TABLE "public"."research_articles" TO "authenticated";
GRANT ALL ON TABLE "public"."research_articles" TO "service_role";



GRANT ALL ON TABLE "public"."risk_metric_history" TO "anon";
GRANT ALL ON TABLE "public"."risk_metric_history" TO "authenticated";
GRANT ALL ON TABLE "public"."risk_metric_history" TO "service_role";



GRANT ALL ON TABLE "public"."risk_metrics" TO "anon";
GRANT ALL ON TABLE "public"."risk_metrics" TO "authenticated";
GRANT ALL ON TABLE "public"."risk_metrics" TO "service_role";



GRANT ALL ON TABLE "public"."saved_views" TO "anon";
GRANT ALL ON TABLE "public"."saved_views" TO "authenticated";
GRANT ALL ON TABLE "public"."saved_views" TO "service_role";



GRANT ALL ON TABLE "public"."scrape_sources" TO "anon";
GRANT ALL ON TABLE "public"."scrape_sources" TO "authenticated";
GRANT ALL ON TABLE "public"."scrape_sources" TO "service_role";



GRANT ALL ON SEQUENCE "public"."scrape_sources_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."scrape_sources_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."scrape_sources_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."securities" TO "anon";
GRANT ALL ON TABLE "public"."securities" TO "authenticated";
GRANT ALL ON TABLE "public"."securities" TO "service_role";



GRANT ALL ON TABLE "public"."security_identifiers" TO "anon";
GRANT ALL ON TABLE "public"."security_identifiers" TO "authenticated";
GRANT ALL ON TABLE "public"."security_identifiers" TO "service_role";



GRANT ALL ON TABLE "public"."security_prices" TO "anon";
GRANT ALL ON TABLE "public"."security_prices" TO "authenticated";
GRANT ALL ON TABLE "public"."security_prices" TO "service_role";



GRANT ALL ON TABLE "public"."tenants" TO "anon";
GRANT ALL ON TABLE "public"."tenants" TO "authenticated";
GRANT ALL ON TABLE "public"."tenants" TO "service_role";



GRANT ALL ON TABLE "public"."trades" TO "anon";
GRANT ALL ON TABLE "public"."trades" TO "authenticated";
GRANT ALL ON TABLE "public"."trades" TO "service_role";



GRANT ALL ON TABLE "public"."upload_records" TO "anon";
GRANT ALL ON TABLE "public"."upload_records" TO "authenticated";
GRANT ALL ON TABLE "public"."upload_records" TO "service_role";



GRANT ALL ON TABLE "public"."uploads" TO "anon";
GRANT ALL ON TABLE "public"."uploads" TO "authenticated";
GRANT ALL ON TABLE "public"."uploads" TO "service_role";



GRANT ALL ON TABLE "public"."user_profile" TO "anon";
GRANT ALL ON TABLE "public"."user_profile" TO "authenticated";
GRANT ALL ON TABLE "public"."user_profile" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































