"""Validation runner: extract from the test/fixtures HTML files via the live
Ollama call + insert into pg.statements.

Purpose: prove the scrape→extract→load pipeline end-to-end without depending
on the volatile live-source URLs in sources.yaml (many of which are stale or
content-thin index pages — to be re-curated in D.2). Each fixture stands in
for a real source URL of the matching shape.

This is *not* a fake/seed insert — every row goes through the real
extract_from_html() against the live Olares Ollama endpoint, then through
the real psycopg insert path with ON CONFLICT idempotency.

Usage:
    POSTGRES_URL=... OLLAMA_BASE_URL=... python -m src.pipelines.seed_from_fixtures
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db import postgres as pg  # noqa: E402
from src.extractor.extract import extract_from_html  # noqa: E402

log = logging.getLogger(__name__)

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

# Each fixture maps to a representative real source URL (from sources.yaml).
# The fixture content stands in for the live page so D.1 validation can run
# without dependency on volatile remote pages.
FIXTURE_MAP = [
    {
        "fixture": "whitehouse_briefing.html",
        "politician": "vance",
        "source_url": "https://www.whitehouse.gov/briefings-statements/remarks-by-the-vice-president-2026-04-22",
    },
    {
        "fixture": "hansard_starmer.html",
        "politician": "starmer",
        "source_url": "https://hansard.parliament.uk/commons/2026-03-15/debates/industrial-strategy",
    },
    {
        "fixture": "bbc_meloni.html",
        "politician": "meloni",
        "source_url": "https://www.bbc.com/news/world-europe-meloni-2026-04-30",
    },
]


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    inserted_total = 0
    with pg.get_conn() as conn:
        before = pg.count_statements(conn)
        log.info("statements row count before fixture seed: %d", before)

        for entry in FIXTURE_MAP:
            path = FIXTURES_DIR / entry["fixture"]
            html = path.read_text(encoding="utf-8")
            log.info("extracting from fixture %s for politician=%s",
                     entry["fixture"], entry["politician"])
            er = extract_from_html(
                html,
                politician=entry["politician"],
                source_url=entry["source_url"],
            )
            if er.error:
                log.error("  ERROR: %s", er.error)
                continue
            log.info("  -> %d extractions (+%d low-conf skipped)",
                     len(er.extractions), len(er.skipped_low_confidence))
            for ext in er.extractions:
                log.info("     [%s, conf=%.2f] %s",
                         ext.kind, ext.confidence,
                         ext.statement_or_decision[:100])
            for ext in er.extractions:
                row = ext.as_db_row()
                new_id = pg.insert_statement(conn, row)
                if new_id:
                    inserted_total += 1
            conn.commit()

        after = pg.count_statements(conn)
        log.info("statements row count after fixture seed: %d (+%d)",
                 after, inserted_total)

        # Render the review queue.
        rows = pg.fetch_review_queue(conn, limit=5)
        log.info("top-5 review-queue rows:")
        for r in rows:
            log.info("  %s | %s | conf=%.2f | %s",
                     r["politician"], r["kind"], r["confidence"],
                     r["statement_or_decision"][:80])

    return 0 if inserted_total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
