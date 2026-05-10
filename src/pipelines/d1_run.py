"""D.1 end-to-end runner.

Pipeline shape:
    [target URL] → fetch → raw_html → extract → parse → INSERT into pg.statements

Per-iteration commit (one source URL = one transaction). Halts on Postgres
write failure, surfaces stall flags to stdout + writes them to
aider-briefs/d1-error.md.

Usage:
    POSTGRES_URL=... OLLAMA_BASE_URL=... python -m src.pipelines.d1_run \\
        [--politicians meloni,vance] \\
        [--max-sources 5] \\
        [--write-progress aider-briefs/d1-progress.md] \\
        [--review-queue review-queues/d1-review-2026-05-09.md]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# Path setup so `python -m src.pipelines.d1_run` and direct invocation both work.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db import postgres as pg                           # noqa: E402
from src.extractor.extract import extract_from_html, CONFIDENCE_FLOOR    # noqa: E402
from src.scraper.fetch import fetch, EMPTY_BODY_THRESHOLD   # noqa: E402
from src.scraper.sources import load_sources                # noqa: E402

log = logging.getLogger(__name__)

# Stall flags (kickoff §6).
EMPTY_BODY_HOST_THRESHOLD = 3        # >3 consecutive empty-body fetches from same host
IDENTICAL_EXTRACTION_THRESHOLD = 5    # 5+ identical extraction outputs in a row


class StallFlag(Exception):
    pass


class PostgresHalt(Exception):
    pass


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _write_review_queue(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# intelpolitics — D.1 review queue",
        "",
        f"Generated {date.today().isoformat()} per kickoff §5.3.",
        "Top-5 by confidence, tiebreak scraped_at DESC.",
        "Vadim: fill the `tag` column with one of `real-and-usable` | `noise` | `borderline`.",
        "",
        "| id | politician | kind | published_date | confidence | statement_or_decision | source_url | tag |",
        "|----|------------|------|----------------|-----------:|-----------------------|------------|-----|",
    ]
    for r in rows:
        pub = r["published_date"].isoformat() if r.get("published_date") else ""
        conf = f"{r['confidence']:.2f}" if r.get("confidence") is not None else ""
        text = _truncate((r.get("statement_or_decision") or "").replace("|", "\\|").replace("\n", " "), 200)
        lines.append(
            f"| {r['id']} | {r['politician']} | {r['kind']} | {pub} | {conf} | {text} | {r['source_url']} | |"
        )
    if not rows:
        lines.append("| _no rows yet_ | | | | | | | |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _append_progress(path: Path | None, msg: str) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(msg.rstrip() + "\n")


def run(
    *,
    politician_filter: list[str] | None,
    max_sources: int | None,
    progress_path: Path | None,
    review_queue_path: Path | None,
    error_path: Path | None,
    review_limit: int = 5,
) -> dict:
    sources = load_sources(only_politicians=politician_filter)
    if max_sources:
        sources = sources[:max_sources]

    log.info("d1_run start: %d sources queued", len(sources))
    _append_progress(progress_path, f"\n## Run started — {len(sources)} sources")

    inserted_total = 0
    processed = 0
    stall_flags: list[str] = []

    # Stall trackers.
    consecutive_empty_per_host: dict[str, int] = defaultdict(int)
    last_extractions: deque[str] = deque(maxlen=IDENTICAL_EXTRACTION_THRESHOLD)

    with pg.get_conn() as conn:
        before = pg.count_statements(conn)
        log.info("statements row count before run: %d", before)

        for src in sources:
            processed += 1
            host = urlparse(src.url).netloc.lower()
            log.info("[%d/%d] %s ← %s", processed, len(sources), src.politician_slug, src.url)

            result = fetch(src.url, preferred_fetcher=src.fetcher)
            log.info(
                "  fetch: status=%s body_len=%d fetcher=%s elapsed=%.1fs",
                result.status, len(result.body), result.fetcher, result.elapsed_sec,
            )

            # Empty-body / non-ok handling.
            if not result.ok:
                consecutive_empty_per_host[host] += 1
                kind = "empty_body" if (result.status and 200 <= result.status < 300) else (
                    "4xx" if result.status and 400 <= result.status < 500 else
                    "5xx" if result.status and 500 <= result.status else
                    "parse_failure"
                )
                try:
                    pg.insert_scrape_error(
                        conn,
                        source_url=src.url, politician=src.politician_slug,
                        fetcher=result.fetcher, http_status=result.status,
                        kind=kind, detail=(result.error or "")[:1000],
                    )
                    conn.commit()
                except Exception as e:
                    raise PostgresHalt(f"scrape_errors insert failed: {e}") from e
                _append_progress(progress_path, f"- FAIL {src.politician_slug} {src.url} kind={kind} status={result.status}")

                if consecutive_empty_per_host[host] > EMPTY_BODY_HOST_THRESHOLD:
                    flag = f"selector_hallucination: host={host} consecutive_empty={consecutive_empty_per_host[host]}"
                    stall_flags.append(flag)
                    log.warning("STALL: %s", flag)
                    if error_path:
                        _append_progress(error_path, f"STALL {flag}")
                continue
            else:
                consecutive_empty_per_host[host] = 0

            # Extract.
            er = extract_from_html(
                result.body,
                politician=src.politician_slug,
                source_url=src.url,
            )
            if er.error:
                log.warning("  extractor error: %s", er.error)
                try:
                    pg.insert_scrape_error(
                        conn,
                        source_url=src.url, politician=src.politician_slug,
                        fetcher=result.fetcher, http_status=result.status,
                        kind="parse_failure", detail=er.error[:1000],
                    )
                    conn.commit()
                except Exception as e:
                    raise PostgresHalt(f"scrape_errors insert failed: {e}") from e
                _append_progress(progress_path, f"- FAIL extractor {src.politician_slug} {src.url} {er.error[:120]}")
                continue

            # Low-confidence skips → scrape_errors rows.
            for skipped in er.skipped_low_confidence:
                try:
                    pg.insert_scrape_error(
                        conn,
                        source_url=src.url, politician=src.politician_slug,
                        fetcher=result.fetcher, http_status=result.status,
                        kind="extract_low_confidence",
                        detail=f"conf={skipped['confidence']:.2f} text={skipped['statement_or_decision'][:200]}",
                    )
                except Exception as e:
                    raise PostgresHalt(f"scrape_errors insert failed: {e}") from e

            # Insert extractions.
            inserted_this_url = 0
            for ext in er.extractions:
                row = ext.as_db_row()
                try:
                    new_id = pg.insert_statement(conn, row)
                except Exception as e:
                    raise PostgresHalt(f"statements insert failed for url={src.url}: {e}") from e
                if new_id:
                    inserted_this_url += 1
                    inserted_total += 1
                last_extractions.append(ext.statement_or_decision)
            try:
                conn.commit()
            except Exception as e:
                raise PostgresHalt(f"commit failed for url={src.url}: {e}") from e

            log.info(
                "  extract: %d valid (+%d low-conf); inserted=%d",
                len(er.extractions), len(er.skipped_low_confidence), inserted_this_url,
            )
            _append_progress(
                progress_path,
                f"- OK {src.politician_slug} {src.url} extracts={len(er.extractions)} "
                f"low_conf={len(er.skipped_low_confidence)} inserted={inserted_this_url}",
            )

            # 5+ identical extraction-output stall flag.
            if (
                len(last_extractions) == IDENTICAL_EXTRACTION_THRESHOLD
                and len(set(last_extractions)) == 1
            ):
                flag = f"prompt_template_lock: last {IDENTICAL_EXTRACTION_THRESHOLD} extractions identical"
                stall_flags.append(flag)
                log.warning("STALL: %s", flag)
                if error_path:
                    _append_progress(error_path, f"STALL {flag}")

        # End of run — write review queue.
        after = pg.count_statements(conn)
        if review_queue_path:
            rows = pg.fetch_review_queue(conn, limit=review_limit)
            _write_review_queue(review_queue_path, rows)
            log.info("review queue written to %s (%d rows)", review_queue_path, len(rows))

    summary = {
        "processed_sources": processed,
        "inserted_total": inserted_total,
        "statements_count_before": before,
        "statements_count_after": after,
        "stall_flags": stall_flags,
    }
    log.info("d1_run done: %s", summary)
    _append_progress(
        progress_path,
        f"\n## Run finished — processed={processed} inserted={inserted_total} "
        f"before={before} after={after} stall_flags={stall_flags or 'none'}",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="intelpolitics D.1 pipeline runner")
    p.add_argument("--politicians", type=str, default=None,
                   help="comma-separated slugs; default = all")
    p.add_argument("--max-sources", type=int, default=None,
                   help="cap on number of sources processed (debug)")
    p.add_argument("--write-progress", type=str, default="aider-briefs/d1-progress.md")
    p.add_argument("--review-queue", type=str, default=None,
                   help="path for the daily review queue Markdown; default = none")
    p.add_argument("--review-limit", type=int, default=5)
    p.add_argument("--error-log", type=str, default="aider-briefs/d1-error.md")
    p.add_argument("--log-level", type=str, default=os.environ.get("LOG_LEVEL", "INFO"))
    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    politician_filter = (
        [s.strip() for s in args.politicians.split(",") if s.strip()]
        if args.politicians else None
    )

    progress_path = Path(args.write_progress) if args.write_progress else None
    review_queue_path = Path(args.review_queue) if args.review_queue else None
    error_path = Path(args.error_log) if args.error_log else None

    try:
        summary = run(
            politician_filter=politician_filter,
            max_sources=args.max_sources,
            progress_path=progress_path,
            review_queue_path=review_queue_path,
            error_path=error_path,
            review_limit=args.review_limit,
        )
    except PostgresHalt as e:
        log.error("HALT: %s", e)
        if error_path:
            _append_progress(error_path, f"HALT: {e}")
        return 2

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
