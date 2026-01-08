-- ============================================================================
-- RESEARCH ARTICLES TABLE
-- Market research and competitive intelligence for RISKCORE
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_articles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_site     TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    date_published  DATE,
    author          TEXT,
    summary         TEXT,
    full_text       TEXT,
    tags            TEXT[] DEFAULT '{}',
    relevance_score INTEGER CHECK (relevance_score >= 1 AND relevance_score <= 5),
    is_paywalled    BOOLEAN DEFAULT FALSE,
    scraped_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_research_source ON research_articles(source_site);
CREATE INDEX IF NOT EXISTS idx_research_date ON research_articles(date_published DESC);
CREATE INDEX IF NOT EXISTS idx_research_relevance ON research_articles(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_research_tags ON research_articles USING GIN(tags);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_research_fts ON research_articles
    USING GIN(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(summary, '') || ' ' || COALESCE(full_text, '')));

COMMENT ON TABLE research_articles IS 'Market research articles for competitive intelligence';
COMMENT ON COLUMN research_articles.relevance_score IS '1-5 score: how relevant to multi-manager risk aggregation';
