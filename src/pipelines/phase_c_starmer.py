"""Phase C Starmer pipeline — T1 ingest for Starmer end-to-end.

Replaces the Phase B `multi_politician.py` strategy_starmer (T4 press
releases) with the four T1 strategies declared in sources.v2.yaml:

  - hansard-search-contributions    statement_official / speaker
  - commons-votes-divisions         vote / voter
  - lobbying-register-quarterly-xlsx lobby_filing / lobbied
  - members-api-membership          supporting_metadata

Startup discipline (DR rule 2):
  validate_sources_v2(YAML) is called BEFORE any strategy fires; non-zero
  exit on any tier / action_class / API-vs-HTML violation.

CLI:
  python -m src.pipelines.phase_c_starmer --metrics-csv /tmp/phase-c.csv

Exit codes:
  0  — success (1+ row inserted from any strategy)
  2  — required env var missing
  3  — every strategy failed (catastrophic)
  4  — sources.v2.yaml failed validation
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
import psycopg
from psycopg.types.json import Json

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.scraper.sources_v2 import (  # noqa: E402
    TierEnforcementError, validate_sources_v2,
)
from src.scraper.strategies_starmer import (  # noqa: E402
    IngestRow, StrategyMetrics,
    strategy_starmer_commons_votes, strategy_starmer_hansard,
    strategy_starmer_lobbying_xlsx, strategy_starmer_members_api,
)

log = logging.getLogger(__name__)

# Map source_id -> strategy callable (module-level wiring; the registry in
# strategies_starmer.py is name-only to avoid a circular import).
STRATEGY_MAP: dict[str, Callable[..., list[IngestRow]]] = {
    "hansard-search-contributions": strategy_starmer_hansard,
    "commons-votes-divisions": strategy_starmer_commons_votes,
    "lobbying-register-quarterly-xlsx": strategy_starmer_lobbying_xlsx,
    "members-api-membership": strategy_starmer_members_api,
}


# ---------------------------------------------------------------------------
# Postgres helpers
# ---------------------------------------------------------------------------

def upsert_source(conn: psycopg.Connection, source) -> None:
    """Idempotent INSERT of a source into the sources table from a SourceV2."""
    q = """
    INSERT INTO sources
        (id, name, url_root, tier, action_class, default_subject_role,
         data_class, geography, access_pattern, auth_required,
         rate_limit, refresh_cadence, status, last_verified, notes)
    VALUES
        (%(id)s, %(name)s, %(url_root)s, %(tier)s, %(action_class)s, %(default_subject_role)s,
         %(data_class)s, %(geography)s, %(access_pattern)s, %(auth_required)s,
         %(rate_limit)s, %(refresh_cadence)s, %(status)s, %(last_verified)s, %(notes)s)
    ON CONFLICT (id) DO UPDATE SET
        tier = EXCLUDED.tier,
        action_class = EXCLUDED.action_class,
        default_subject_role = EXCLUDED.default_subject_role,
        access_pattern = EXCLUDED.access_pattern,
        rate_limit = EXCLUDED.rate_limit,
        refresh_cadence = EXCLUDED.refresh_cadence,
        last_verified = EXCLUDED.last_verified,
        updated_at = NOW();
    """
    last_verified = None
    if source.last_verified:
        try:
            last_verified = datetime.fromisoformat(source.last_verified[:10]).date()
        except ValueError:
            last_verified = None

    with conn.cursor() as cur:
        cur.execute(q, {
            "id": source.id,
            "name": source.id.replace("-", " ").title(),
            "url_root": source.endpoint or "",
            "tier": source.tier,
            "action_class": source.action_class,
            "default_subject_role": source.default_subject_role,
            "data_class": None,
            "geography": "UK",
            "access_pattern": source.access_pattern,
            "auth_required": source.auth not in (None, "", "none"),
            "rate_limit": source.rate_limit,
            "refresh_cadence": source.refresh_cadence,
            "status": "active",
            "last_verified": last_verified,
            "notes": "; ".join(source.gotchas)[:2000] if source.gotchas else None,
        })
    conn.commit()


def fetch_politician_id(conn: psycopg.Connection, slug: str) -> str:
    """Return the politicians.id (UUID as str) for slug. Migration 002 seeds Starmer."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM politicians WHERE slug = %s;", (slug,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(
                f"politician slug={slug!r} not found — run migration 002 first"
            )
        return str(row[0])


def insert_ingest_row(
    conn: psycopg.Connection,
    row: IngestRow,
    politician_id: str,
) -> tuple[bool, bool, str | None]:
    """Insert one row into `rows`. ON CONFLICT (source_id, ext_id) skips dup.

    Returns (inserted, duplicate, error).
    """
    content_hash = row.content_hash()
    q = """
    INSERT INTO rows
        (source_id, politician_id, tier, tier_at_ingest, action_class,
         subject_role, ext_id, occurred_at, title, summary, source_url,
         content_hash, payload_json)
    VALUES
        (%(source_id)s, %(politician_id)s, %(tier)s, %(tier_at_ingest)s, %(action_class)s,
         %(subject_role)s, %(ext_id)s, %(occurred_at)s, %(title)s, %(summary)s, %(source_url)s,
         %(content_hash)s, %(payload_json)s)
    ON CONFLICT (source_id, ext_id) DO NOTHING
    RETURNING id;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(q, {
                "source_id": row.source_id,
                "politician_id": politician_id,
                "tier": row.tier,
                "tier_at_ingest": row.tier,
                "action_class": row.action_class,
                "subject_role": row.subject_role,
                "ext_id": row.ext_id,
                "occurred_at": row.occurred_at,
                "title": row.title,
                "summary": row.summary,
                "source_url": row.source_url,
                "content_hash": content_hash,
                "payload_json": Json(row.payload_json),
            })
            result = cur.fetchone()
        conn.commit()
        return (result is not None), (result is None), None
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, False, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_starmer_phase_c(
    sources_v2_path: Path,
    pg_url: str,
    metrics_csv_path: Path,
) -> tuple[int, dict[str, Any]]:
    """Returns (exit_code, summary_dict)."""

    # Step 1 — validate sources.v2.yaml (DR rule 2 startup gate).
    try:
        sources_v2 = validate_sources_v2(sources_v2_path)
    except TierEnforcementError as e:
        log.error("sources.v2.yaml validation FAILED: %s", e)
        return 4, {"error": str(e), "phase": "validation"}

    starmer = sources_v2.for_politician("starmer")
    log.info(
        "validated sources.v2.yaml for starmer (%d sources, all T1: %s)",
        len(starmer.sources),
        all(s.tier == "T1" for s in starmer.sources),
    )

    member_id = starmer.member_ids.get("uk_parliament") or 4514

    # Step 2 — connect Postgres, seed the sources table.
    summary: dict[str, Any] = {
        "phase": "phase_c_starmer",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "sources_v2_path": str(sources_v2_path),
        "politician_slug": "starmer",
        "member_id": member_id,
        "strategies": [],
    }

    with psycopg.connect(pg_url) as conn:
        for src in starmer.sources:
            try:
                upsert_source(conn, src)
            except Exception as e:
                log.error("source upsert failed for %s: %s", src.id, e)
                return 3, {"error": f"sources upsert failed: {e}", "phase": "seed_sources"}

        politician_id = fetch_politician_id(conn, "starmer")
        log.info("starmer politician_id=%s", politician_id)

        # Step 3 — fire each strategy.
        host_last_call: dict[str, float] = {}

        with httpx.Client() as client:
            for src in starmer.sources:
                callable_ = STRATEGY_MAP.get(src.id)
                if callable_ is None:
                    log.warning(
                        "source %s declared in sources.v2.yaml but no STRATEGY_MAP entry",
                        src.id,
                    )
                    continue
                metrics = StrategyMetrics(name=src.id)

                # Strategy-specific arg shapes:
                if src.id == "hansard-search-contributions":
                    rows = callable_(
                        member_id=member_id, metrics=metrics,
                        client=client, host_last_call=host_last_call,
                    )
                elif src.id == "commons-votes-divisions":
                    rows = callable_(
                        member_id=member_id, metrics=metrics,
                        client=client, host_last_call=host_last_call,
                    )
                elif src.id == "lobbying-register-quarterly-xlsx":
                    rows = callable_(
                        metrics=metrics,
                        client=client, host_last_call=host_last_call,
                    )
                elif src.id == "members-api-membership":
                    rows = callable_(
                        member_id=member_id, metrics=metrics,
                        client=client, host_last_call=host_last_call,
                    )
                else:
                    rows = []

                # Insert.
                for row in rows:
                    inserted, duplicate, err = insert_ingest_row(conn, row, politician_id)
                    if err:
                        metrics.rows_rejected += 1
                        log.warning("[%s] row insert error: %s", src.id, err)
                    elif inserted:
                        metrics.rows_inserted += 1
                    elif duplicate:
                        metrics.rows_duplicate += 1

                summary["strategies"].append({
                    "source_id": src.id,
                    "tier": src.tier,
                    "action_class": src.action_class,
                    "subject_role_default": src.default_subject_role,
                    "rows_yielded": metrics.rows_yielded,
                    "rows_inserted": metrics.rows_inserted,
                    "rows_duplicate": metrics.rows_duplicate,
                    "rows_rejected": metrics.rows_rejected,
                    "fetch_ok": metrics.fetch_ok,
                    "fetch_fail": metrics.fetch_fail,
                    "duration_sec": round(metrics.duration_sec, 2),
                    "fatal_error": metrics.fatal_error,
                })

                # Durable per-strategy METRICS line. `kubectl logs` reads this
                # from the cluster log store, which survives pod GC (unlike the
                # EmptyDir CSV at /tmp/phase-c-metrics.csv). The "METRICS:"
                # prefix is the grep anchor for post-hoc verification:
                #   kubectl logs job/<name> | grep '^METRICS:' \
                #     | sed 's/^METRICS: //' | jq -s 'map(.rows_inserted) | add'
                # See Vadim's Inbox/builder-cronjob-metrics-durability-2026-05-13/.
                metrics_line = {
                    "strategy": src.id,
                    "rows_inserted": metrics.rows_inserted,
                    "rows_skipped_dedup": metrics.rows_duplicate,
                    "errors": metrics.rows_rejected + (1 if metrics.fatal_error else 0),
                    "duration_ms": int(metrics.duration_sec * 1000),
                    "rows_yielded": metrics.rows_yielded,
                    "fatal_error": metrics.fatal_error,
                }
                print(
                    "METRICS: " + json.dumps(metrics_line, sort_keys=True, default=str),
                    flush=True,
                )

    # Step 4 — metrics CSV.
    metrics_csv_path.parent.mkdir(parents=True, exist_ok=True)
    if summary["strategies"]:
        fieldnames = list(summary["strategies"][0].keys())
        with metrics_csv_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            for s in summary["strategies"]:
                w.writerow(s)

    total_inserted = sum(s["rows_inserted"] for s in summary["strategies"])
    summary["total_inserted"] = total_inserted
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()

    if total_inserted == 0 and all(
        (s.get("fatal_error") or s.get("rows_yielded", 0) == 0)
        for s in summary["strategies"]
    ):
        return 3, summary
    return 0, summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase C Starmer T1 ingest pipeline")
    p.add_argument(
        "--sources-v2",
        type=str,
        default=str(REPO_ROOT / "sources.v2.yaml"),
        help="Path to sources.v2.yaml",
    )
    p.add_argument(
        "--metrics-csv",
        type=str,
        default="/tmp/phase-c-starmer-metrics.csv",
    )
    p.add_argument("--log-level", type=str, default="INFO")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    pg_url = os.environ.get("POSTGRES_URL")
    if not pg_url:
        log.error("POSTGRES_URL is required")
        return 2

    started = time.monotonic()
    exit_code, summary = run_starmer_phase_c(
        Path(args.sources_v2), pg_url, Path(args.metrics_csv),
    )
    summary["run_elapsed_sec"] = round(time.monotonic() - started, 2)
    print("PHASE_C_SUMMARY=" + json.dumps(summary, sort_keys=True, default=str))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
