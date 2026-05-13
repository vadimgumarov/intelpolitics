-- ventures/intelpolitics/k3s/migrations/002_sources_v2.sql
--
-- Phase C migration: adds source-quality canon (T1-T4) columns + the unified
-- `rows` ingest table that Phase C scrapers write into.
--
-- Canon: framework/BKM/dr-source-quality-canon-2026-05-12.md
-- Addendum: framework/BKM/dr-source-quality-canon-addendum-2026-05-12.md
-- Spec: framework/BKM/intelpolitics-respec-2026-05-12/spec.md §2.3.1
--
-- Apply path (per migration 001 pattern):
--   scp this file to olares:/tmp/, then
--   kubectl exec -n intelpolitics-conductor postgres-0 -- psql -U intelpolitics_app \
--     -d intelpolitics_db -f /tmp/002_sources_v2.sql
--
-- Rollback: ventures/intelpolitics/k3s/migrations/002_sources_v2_rollback.sql
--
-- DR-24 dry-run gate: run psql --single-transaction -f .../002_sources_v2.sql to
-- verify clean apply against a dev Postgres before touching the cluster instance.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- 1. politicians dimension table (per re-spec §2.3 — small dim; replaces
--    free-text politician column on statements going forward).
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS politicians (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug         TEXT UNIQUE NOT NULL,        -- 'starmer', 'meloni'
    full_name    TEXT NOT NULL,
    geography    TEXT NOT NULL,               -- 'UK' | 'US' | 'EU' | 'DE' | 'IT'
    government_role TEXT,                     -- renamed from current_role (reserved keyword in Postgres)
    external_ids JSONB NOT NULL DEFAULT '{}'::jsonb,
                                              -- {"uk_parliament": 4514, ...}
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_politicians_geography ON politicians (geography);

-- Seed Starmer (Phase C scope).
INSERT INTO politicians (slug, full_name, geography, government_role, external_ids)
VALUES (
    'starmer',
    'Sir Keir Starmer',
    'UK',
    'Prime Minister',
    '{"uk_parliament": 4514, "twfy_person": 25916, "constituency": "Holborn and St Pancras", "constituency_id": 4105}'::jsonb
)
ON CONFLICT (slug) DO UPDATE
    SET full_name = EXCLUDED.full_name,
        government_role = EXCLUDED.government_role,
        external_ids = EXCLUDED.external_ids,
        updated_at = NOW();

-- ---------------------------------------------------------------------------
-- 2. sources registry (per re-spec §2.3 — replaces the per-fetcher YAML
--    discipline with a Postgres source-of-truth; sources.v2.yaml seeds this
--    table at pipeline startup).
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sources (
    id                TEXT PRIMARY KEY,         -- kebab-case (matches sources.v2.yaml `id`)
    name              TEXT NOT NULL,
    url_root          TEXT NOT NULL,
    tier              TEXT NOT NULL
                      CHECK (tier IN ('T1','T2','T3','T4')),
    action_class      TEXT NOT NULL
                      CHECK (action_class IN (
                          'vote','bill_intro','policy_publish','lobby_filing',
                          'statement_official','talking_point','supporting_metadata'
                      )),
    default_subject_role TEXT
                      CHECK (default_subject_role IS NULL OR default_subject_role IN (
                          'lobbied','lobbyist','voter','sponsor','speaker','author'
                      )),
    data_class        TEXT,                     -- legacy informational field
    geography         TEXT NOT NULL,
    access_pattern    TEXT NOT NULL
                      CHECK (access_pattern IN ('api','bulk_download','scrape')),
    auth_required     BOOLEAN NOT NULL DEFAULT FALSE,
    rate_limit        TEXT,
    refresh_cadence   TEXT,
    status            TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('candidate','validated','active','retired')),
    last_verified     DATE,
    uptime_7d_pct     NUMERIC(5,2),             -- DR rule 5; populated by SLA gate
    notes             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_tier ON sources (tier);
CREATE INDEX IF NOT EXISTS idx_sources_action_class ON sources (action_class);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources (status);

-- ---------------------------------------------------------------------------
-- 3. rows — the unified ingest landing table (per re-spec §2.3.1).
--    Phase C scrapers write here directly with tier + action_class +
--    subject_role + payload_json. Verdict-producing queries downstream filter
--    out action_class IN ('talking_point','supporting_metadata').
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS rows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       TEXT NOT NULL REFERENCES sources(id),
    politician_id   UUID NOT NULL REFERENCES politicians(id),
    tier            TEXT NOT NULL
                    CHECK (tier IN ('T1','T2','T3','T4')),
    tier_at_ingest  TEXT NOT NULL
                    CHECK (tier_at_ingest IN ('T1','T2','T3','T4')),
    action_class    TEXT NOT NULL
                    CHECK (action_class IN (
                        'vote','bill_intro','policy_publish','lobby_filing',
                        'statement_official','talking_point','supporting_metadata'
                    )),
    subject_role    TEXT
                    CHECK (subject_role IS NULL OR subject_role IN (
                        'lobbied','lobbyist','voter','sponsor','speaker','author'
                    )),
    ext_id          TEXT NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL,
    title           TEXT,                       -- denormalised for fast list rendering
    summary         TEXT,                       -- short human-readable description
    source_url      TEXT NOT NULL,              -- canonical provenance URL
    content_hash    TEXT NOT NULL,              -- sha256 of payload for content-level dedup
    payload_json    JSONB NOT NULL,             -- full upstream object
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_id, ext_id),
    -- Per addendum DR: lobby_filing rows MUST carry a subject_role (CHECK is the
    -- structural enforcement; pipeline-level rejection also runs at insert time).
    CONSTRAINT rows_lobby_filing_requires_subject_role
      CHECK (action_class <> 'lobby_filing' OR subject_role IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_rows_politician ON rows (politician_id);
CREATE INDEX IF NOT EXISTS idx_rows_action_class ON rows (action_class);
CREATE INDEX IF NOT EXISTS idx_rows_tier ON rows (tier);
CREATE INDEX IF NOT EXISTS idx_rows_occurred_at ON rows (occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_rows_source_id ON rows (source_id);
CREATE INDEX IF NOT EXISTS idx_rows_content_hash ON rows (content_hash);

-- ---------------------------------------------------------------------------
-- 4. Demote the existing statements table to supporting evidence (per re-spec
--    §2.3 keep-and-demote). We add the FK to politicians + source_id link but
--    do NOT delete data. Existing rows from D.1 stay accessible for audit.
--    These ALTERs are IF NOT EXISTS-equivalent via DO blocks since Postgres
--    lacks IF NOT EXISTS on ADD COLUMN until 9.6+ (we have it; use it).
-- ---------------------------------------------------------------------------

ALTER TABLE statements
    ADD COLUMN IF NOT EXISTS politician_id UUID REFERENCES politicians(id),
    ADD COLUMN IF NOT EXISTS topics TEXT[],
    ADD COLUMN IF NOT EXISTS source_id TEXT REFERENCES sources(id);

-- Backfill politician_id where the free-text slug matches a seeded politician.
UPDATE statements s
SET politician_id = p.id
FROM politicians p
WHERE s.politician_id IS NULL
  AND s.politician = p.slug;

COMMIT;

-- ---------------------------------------------------------------------------
-- Post-apply verification (run interactively after the COMMIT):
--   SELECT slug, full_name, government_role FROM politicians;
--   \d+ sources
--   \d+ rows
--   SELECT conname, contype FROM pg_constraint WHERE conrelid = 'rows'::regclass;
-- Expected: politicians shows 1 row (starmer); rows table exists with the
-- two CHECK constraints (tier, action_class) + the lobby_filing+subject_role
-- composite CHECK; sources table exists with tier CHECK.
-- ---------------------------------------------------------------------------
