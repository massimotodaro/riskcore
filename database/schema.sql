-- ============================================================================
-- RISKCORE DATABASE SCHEMA
-- Multi-strategy risk aggregation platform
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PORTFOLIOS
-- Represents each PM's book or strategy sleeve
-- ============================================================================

CREATE TABLE portfolios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    pm_name         VARCHAR(100) NOT NULL,
    strategy        VARCHAR(50),  -- 'long_short_equity', 'macro', 'quant', 'credit', etc.
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE portfolios IS 'Portfolio managers and their strategy books';

CREATE INDEX idx_portfolios_pm ON portfolios(pm_name);
CREATE INDEX idx_portfolios_strategy ON portfolios(strategy);

-- ============================================================================
-- SECURITIES
-- Reference data for tradeable instruments
-- ============================================================================

CREATE TABLE securities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    asset_class     VARCHAR(50) NOT NULL,  -- 'equity', 'fixed_income', 'fx', 'commodity', 'derivative'
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    country         VARCHAR(3),  -- ISO country code
    exchange        VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE securities IS 'Security master with reference data';

CREATE INDEX idx_securities_symbol ON securities(symbol);
CREATE INDEX idx_securities_asset_class ON securities(asset_class);
CREATE INDEX idx_securities_sector ON securities(sector);

-- ============================================================================
-- POSITIONS
-- Point-in-time position snapshots per portfolio
-- ============================================================================

CREATE TABLE positions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,
    quantity        DECIMAL(18, 6) NOT NULL,
    price           DECIMAL(18, 6) NOT NULL,
    market_value    DECIMAL(18, 2) GENERATED ALWAYS AS (quantity * price) STORED,
    cost_basis      DECIMAL(18, 2),
    asset_class     VARCHAR(50),
    sector          VARCHAR(100),
    currency        VARCHAR(3) DEFAULT 'USD',
    as_of_date      DATE NOT NULL,
    source_system   VARCHAR(50),  -- 'bloomberg', 'internal', 'manual', etc.
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE positions IS 'Daily position snapshots by portfolio';

CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_date ON positions(as_of_date);
CREATE INDEX idx_positions_sector ON positions(sector);
CREATE UNIQUE INDEX idx_positions_unique ON positions(portfolio_id, symbol, as_of_date);

-- ============================================================================
-- TRADES
-- Transaction history for audit and P&L attribution
-- ============================================================================

CREATE TABLE trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,
    side            VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity        DECIMAL(18, 6) NOT NULL,
    price           DECIMAL(18, 6) NOT NULL,
    notional        DECIMAL(18, 2) GENERATED ALWAYS AS (quantity * price) STORED,
    trade_date      DATE NOT NULL,
    settle_date     DATE,
    status          VARCHAR(20) DEFAULT 'confirmed',  -- 'pending', 'confirmed', 'settled', 'cancelled'
    counterparty    VARCHAR(100),
    broker          VARCHAR(100),
    commission      DECIMAL(12, 2),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE trades IS 'Trade blotter with execution details';

CREATE INDEX idx_trades_portfolio ON trades(portfolio_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_date ON trades(trade_date);
CREATE INDEX idx_trades_status ON trades(status);

-- ============================================================================
-- RISK METRICS
-- Portfolio-level risk calculations
-- ============================================================================

CREATE TABLE risk_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    var_95          DECIMAL(18, 2),  -- 95% Value at Risk
    var_99          DECIMAL(18, 2),  -- 99% Value at Risk
    expected_shortfall DECIMAL(18, 2),  -- CVaR / Expected Shortfall
    beta            DECIMAL(8, 4),   -- Portfolio beta to benchmark
    delta           DECIMAL(18, 2),  -- Net delta exposure ($ terms)
    gamma           DECIMAL(18, 2),  -- Gamma exposure
    vega            DECIMAL(18, 2),  -- Vega exposure
    theta           DECIMAL(18, 2),  -- Theta (time decay)
    sharpe_ratio    DECIMAL(8, 4),
    volatility      DECIMAL(8, 4),   -- Annualized volatility
    gross_exposure  DECIMAL(18, 2),
    net_exposure    DECIMAL(18, 2),
    long_exposure   DECIMAL(18, 2),
    short_exposure  DECIMAL(18, 2),
    as_of_date      DATE NOT NULL,
    calculation_method VARCHAR(50),  -- 'historical', 'parametric', 'monte_carlo'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE risk_metrics IS 'Daily risk metrics per portfolio';

CREATE INDEX idx_risk_portfolio ON risk_metrics(portfolio_id);
CREATE INDEX idx_risk_date ON risk_metrics(as_of_date);
CREATE UNIQUE INDEX idx_risk_unique ON risk_metrics(portfolio_id, as_of_date);

-- ============================================================================
-- FIRM AGGREGATES
-- Firm-wide aggregated risk and exposure data
-- ============================================================================

CREATE TABLE firm_aggregates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    total_aum           DECIMAL(18, 2) NOT NULL,
    total_nav           DECIMAL(18, 2),
    firm_var_95         DECIMAL(18, 2),
    firm_var_99         DECIMAL(18, 2),
    firm_beta           DECIMAL(8, 4),
    gross_exposure      DECIMAL(18, 2),
    net_exposure        DECIMAL(18, 2),
    long_exposure       DECIMAL(18, 2),
    short_exposure      DECIMAL(18, 2),
    sector_exposures    JSONB DEFAULT '{}',   -- {"Technology": 1500000, "Healthcare": -200000, ...}
    country_exposures   JSONB DEFAULT '{}',   -- {"US": 5000000, "UK": 1000000, ...}
    asset_class_exposures JSONB DEFAULT '{}', -- {"equity": 4000000, "fixed_income": 1000000, ...}
    top_positions       JSONB DEFAULT '[]',   -- [{symbol, market_value, pct_nav}, ...]
    concentration_metrics JSONB DEFAULT '{}', -- Herfindahl index, top 10 concentration, etc.
    as_of_date          DATE NOT NULL UNIQUE,
    generated_at        TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE firm_aggregates IS 'Daily firm-wide aggregated metrics';

CREATE INDEX idx_firm_agg_date ON firm_aggregates(as_of_date);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER portfolios_updated
    BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER securities_updated
    BEFORE UPDATE ON securities
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Aggregated positions across all portfolios
CREATE VIEW v_firm_positions AS
SELECT
    symbol,
    SUM(quantity) AS total_quantity,
    SUM(market_value) AS total_market_value,
    COUNT(DISTINCT portfolio_id) AS num_portfolios,
    MAX(as_of_date) AS as_of_date
FROM positions
WHERE as_of_date = (SELECT MAX(as_of_date) FROM positions)
GROUP BY symbol;

-- Net exposures by sector
CREATE VIEW v_sector_exposure AS
SELECT
    sector,
    SUM(market_value) AS net_exposure,
    SUM(CASE WHEN market_value > 0 THEN market_value ELSE 0 END) AS long_exposure,
    SUM(CASE WHEN market_value < 0 THEN ABS(market_value) ELSE 0 END) AS short_exposure,
    MAX(as_of_date) AS as_of_date
FROM positions
WHERE as_of_date = (SELECT MAX(as_of_date) FROM positions)
GROUP BY sector;

-- PM performance summary
CREATE VIEW v_pm_summary AS
SELECT
    p.pm_name,
    p.strategy,
    COUNT(DISTINCT p.id) AS num_portfolios,
    SUM(pos.market_value) AS total_aum,
    MAX(r.var_95) AS var_95,
    MAX(r.sharpe_ratio) AS sharpe_ratio,
    MAX(pos.as_of_date) AS as_of_date
FROM portfolios p
LEFT JOIN positions pos ON p.id = pos.portfolio_id
LEFT JOIN risk_metrics r ON p.id = r.portfolio_id
WHERE pos.as_of_date = (SELECT MAX(as_of_date) FROM positions)
  AND r.as_of_date = (SELECT MAX(as_of_date) FROM risk_metrics)
GROUP BY p.pm_name, p.strategy;
