-- ventures/intelpolitics/k3s/migrations/001_statements.sql
-- Run on intelpolitics-conductor:postgres-0 inside the namespace.
--
-- Source: Vadim's Inbox/pilot-day-1-2026-05-08/d1-intelpolitics-kickoff.md §3 (verbatim).
-- Approved 2026-05-09. Apply path: scp this file to olares:/tmp/, then
-- `kubectl exec -n intelpolitics-conductor postgres-0 -- psql -U intelpolitics_app -d intelpolitics_db -f /tmp/001_statements.sql`.
-- Per DR-24 §Implications + ops-dryrun-audit-2026-05-09: the apply path runs
-- `kubectl --dry-run=server` first; live exec runs only after the diff is reviewed.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()

-- statement_kind: 'statement' (verbal claim/position) | 'decision' (vote, signed-off policy,
-- executive action, or formal directive). Per kickoff plan §4.3 evaluation rule.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statement_kind') THEN
        CREATE TYPE statement_kind AS ENUM ('statement', 'decision');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS statements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    politician      TEXT NOT NULL,
    statement_or_decision TEXT NOT NULL,
    source_url      TEXT NOT NULL,
    published_date  DATE,                              -- nullable: not all sources expose a date
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    kind            statement_kind NOT NULL,
    raw_html        TEXT,                              -- nullable: keep for re-extraction; drop after Phase 1 if storage pressures
    confidence      REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    -- de-duplication: same politician + same statement text + same source URL = same row
    CONSTRAINT statements_dedup_key UNIQUE (politician, statement_or_decision, source_url)
);

CREATE INDEX IF NOT EXISTS idx_statements_politician     ON statements (politician);
CREATE INDEX IF NOT EXISTS idx_statements_kind           ON statements (kind);
CREATE INDEX IF NOT EXISTS idx_statements_published_date ON statements (published_date);
CREATE INDEX IF NOT EXISTS idx_statements_scraped_at     ON statements (scraped_at);

-- Companion table: scrape errors (for stall detection and post-mortem).
CREATE TABLE IF NOT EXISTS scrape_errors (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url   TEXT NOT NULL,
    politician   TEXT,
    fetcher      TEXT NOT NULL,                       -- 'curl_cffi' | 'patchright'
    http_status  INTEGER,
    kind         TEXT NOT NULL,                       -- 'empty_body' | '4xx' | '5xx' | 'parse_failure' | 'extract_low_confidence'
    detail       TEXT,
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scrape_errors_kind       ON scrape_errors (kind);
CREATE INDEX IF NOT EXISTS idx_scrape_errors_occurred   ON scrape_errors (occurred_at);
