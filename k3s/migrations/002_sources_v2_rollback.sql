-- ventures/intelpolitics/k3s/migrations/002_sources_v2_rollback.sql
--
-- Rollback for 002_sources_v2.sql.
--
-- WARNING: this DROPs the rows + sources + politicians tables. Any Phase C
-- ingest data accumulated in rows will be lost. Use only when reverting the
-- Phase C migration in full (see DR-source-quality-canon §Revert).
--
-- The legacy `statements` table is preserved; this rollback only drops the
-- FK columns added by 002 (politician_id, topics, source_id) without dropping
-- existing rows.

BEGIN;

-- 1. Drop FK columns from statements (preserves row data).
ALTER TABLE statements
    DROP COLUMN IF EXISTS source_id,
    DROP COLUMN IF EXISTS topics,
    DROP COLUMN IF EXISTS politician_id;

-- 2. Drop the new tables in dependency order.
DROP TABLE IF EXISTS rows;
DROP TABLE IF EXISTS sources;
DROP TABLE IF EXISTS politicians;

COMMIT;
