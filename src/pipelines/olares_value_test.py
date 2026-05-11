"""Olares value-test pipeline (one-shot run, 2026-05-10).

Goal: get live Starmer-related rows through the Olares cluster (Ollama + Postgres)
and capture per-step metrics for a value verdict.

Source: gov.uk Search API (https://www.gov.uk/api/search.json). GREEN per the
intelpolitics catalog. Returns JSON metadata for speeches/news/statements
filtered by `filter_people=keir-starmer`.

Pipeline:
    [gov.uk API] -> list of N speeches (single call)
    for each speech:
        fetch speech page (curl_cffi, paced 3s)
        extract title + body excerpt (BeautifulSoup)
        call Olares Ollama gemma4:e4b for a one-word topic tag
        insert into pg.statements (kind='statement', confidence=1.0)
        record per-step latency

Metrics captured to a CSV at --metrics-csv.

Usage (Mac dev — SSH tunnel path):
    POSTGRES_URL=postgresql://user:pw@127.0.0.1:15432/intelpolitics_db \\
    OLLAMA_BASE_URL=http://127.0.0.1:11434 \\
    OLLAMA_MODEL=gemma4:e4b \\
    python -m src.pipelines.olares_value_test \\
        --max-rows 100 \\
        --metrics-csv /tmp/olares-value-test-metrics.csv

Usage (in-cluster Job — production path, see k8s/scrape-job.yaml):
    POSTGRES_URL=postgresql://intelpolitics_app:pw@postgres.intelpolitics-conductor.svc.cluster.local:5432/intelpolitics_db \\
    OLLAMA_BASE_URL=http://ollama.ollamaserver-shared.svc.cluster.local:11434 \\
    OLLAMA_MODEL=gemma4:e4b \\
    python -m src.pipelines.olares_value_test \\
        --max-rows 95 \\
        --metrics-csv /tmp/metrics.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import curl_cffi.requests as creq
import httpx
import psycopg
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

log = logging.getLogger(__name__)

GOV_UK_BASE = "https://www.gov.uk"
GOV_UK_SEARCH = (
    "https://www.gov.uk/api/search.json"
    "?filter_people=keir-starmer"
    "&filter_content_store_document_type=speech"
    "&count={count}"
    "&order=-public_timestamp"
)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT_SEC = float(os.environ.get("OLLAMA_TIMEOUT_SEC", "60"))

PACE_SEC = float(os.environ.get("PACE_SEC", "3.0"))
BODY_EXCERPT_CHARS = 2000

TOPIC_PROMPT = """You are tagging a UK government speech with one topic word.

Title: {title}
Excerpt: {excerpt}

Choose the single best topic word from this list:
economy, defence, health, education, housing, environment, justice, immigration,
foreign-policy, energy, technology, welfare, culture, transport, other

Reply with ONLY the single topic word, no punctuation, no explanation.
"""

TOPIC_ALLOWED = {
    "economy", "defence", "health", "education", "housing", "environment",
    "justice", "immigration", "foreign-policy", "energy", "technology",
    "welfare", "culture", "transport", "other",
}


def fetch_speech_list(count: int) -> list[dict[str, Any]]:
    url = GOV_UK_SEARCH.format(count=count)
    started = time.monotonic()
    r = httpx.get(url, timeout=30)
    elapsed = time.monotonic() - started
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    log.info("gov.uk API: total=%d returned=%d elapsed=%.2fs",
             data.get("total"), len(results), elapsed)
    return results


def fetch_speech_page(path: str) -> tuple[str | None, float, int, str | None]:
    """Fetch one speech page. Returns (body_html, elapsed_sec, status, error)."""
    url = urljoin(GOV_UK_BASE, path)
    started = time.monotonic()
    try:
        r = creq.get(url, impersonate="chrome120", timeout=30, allow_redirects=True)
        elapsed = time.monotonic() - started
        if r.status_code != 200:
            return None, elapsed, r.status_code, f"non-200: {r.status_code}"
        return r.text, elapsed, r.status_code, None
    except Exception as e:
        return None, time.monotonic() - started, 0, f"{type(e).__name__}: {e}"


_SPEECH_BODY_SELECTORS = [
    ".govspeak",
    "[data-module='govspeak']",
    "main .gem-c-govspeak",
    "main",
]


def extract_body_excerpt(html: str, *, truncate: int = BODY_EXCERPT_CHARS) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "aside", "header"]):
        tag.decompose()
    container = None
    for sel in _SPEECH_BODY_SELECTORS:
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup.body or soup
    text = container.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:truncate]


def call_ollama_topic(title: str, excerpt: str) -> tuple[str, float, int, str | None]:
    """Return (topic_word, elapsed_sec, eval_count, error)."""
    prompt = TOPIC_PROMPT.format(title=title[:200], excerpt=excerpt[:1800])
    started = time.monotonic()
    try:
        with httpx.Client(timeout=OLLAMA_TIMEOUT_SEC) as client:
            r = client.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_ctx": 4096, "num_predict": 16},
                },
            )
        elapsed = time.monotonic() - started
        if r.status_code != 200:
            return "", elapsed, 0, f"ollama HTTP {r.status_code}"
        data = r.json()
        raw = (data.get("response") or "").strip().lower()
        word = re.sub(r"[^a-z\-]", "", raw.split()[0]) if raw else ""
        if word not in TOPIC_ALLOWED:
            word = "other"
        return word, elapsed, int(data.get("eval_count", 0)), None
    except Exception as e:
        return "", time.monotonic() - started, 0, f"{type(e).__name__}: {e}"


def parse_published_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def insert_row(conn: psycopg.Connection, row: dict[str, Any]) -> tuple[str | None, float]:
    started = time.monotonic()
    q = """
    INSERT INTO statements
        (politician, statement_or_decision, source_url, published_date,
         kind, confidence, raw_html)
    VALUES
        (%(politician)s, %(statement_or_decision)s, %(source_url)s,
         %(published_date)s, %(kind)s, %(confidence)s, %(raw_html)s)
    ON CONFLICT ON CONSTRAINT statements_dedup_key DO NOTHING
    RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(q, row)
        result = cur.fetchone()
    conn.commit()
    elapsed = time.monotonic() - started
    return (str(result[0]) if result else None), elapsed


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Olares value-test pipeline")
    p.add_argument("--max-rows", type=int, default=100)
    p.add_argument("--metrics-csv", type=str, required=True)
    p.add_argument("--politician-slug", type=str, default="starmer")
    p.add_argument("--log-level", type=str, default="INFO")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    pg_url = os.environ.get("POSTGRES_URL")
    if not pg_url:
        log.error("POSTGRES_URL is required")
        return 2

    # PG_TARGET_KIND classifies the write target for the metrics summary:
    #   - explicit env override wins (set to 'olares-in-cluster' by the Job entrypoint)
    #   - else ':15432/' (SSH tunnel from Mac) -> 'olares-tunnel'
    #   - else 'local'
    # The in-cluster case is the production path (DR-17 §2.4); the tunnel case
    # is the Mac-dev fallback retained for local iteration.
    pg_target_kind_override = os.environ.get("PG_TARGET_KIND")
    if pg_target_kind_override:
        pg_target_kind = pg_target_kind_override
    elif ":15432/" in pg_url:
        pg_target_kind = "olares-tunnel"
    elif ".svc.cluster.local" in pg_url or os.environ.get("KUBERNETES_SERVICE_HOST"):
        pg_target_kind = "olares-in-cluster"
    else:
        pg_target_kind = "local"
    log.info("POSTGRES target: %s (url host:port hint=%s)",
             pg_target_kind, pg_url.split("@", 1)[-1].split("/")[0])
    log.info("OLLAMA: %s model=%s", OLLAMA_BASE_URL, OLLAMA_MODEL)
    log.info("max-rows=%d pace=%.1fs", args.max_rows, PACE_SEC)

    # 1) Fetch speech list
    list_started = time.monotonic()
    speeches = fetch_speech_list(count=args.max_rows)
    list_elapsed = time.monotonic() - list_started
    log.info("fetched %d speech metadata records in %.2fs", len(speeches), list_elapsed)

    metrics_rows: list[dict[str, Any]] = []
    counts = {
        "speeches_total": len(speeches),
        "fetch_ok": 0,
        "fetch_fail": 0,
        "ollama_ok": 0,
        "ollama_fail": 0,
        "pg_inserted": 0,
        "pg_duplicate": 0,
        "pg_fail": 0,
    }

    run_started = time.monotonic()
    with psycopg.connect(pg_url) as conn:
        before_count = 0
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM statements;")
            before_count = int(cur.fetchone()[0])
        log.info("statements row count before run: %d", before_count)

        for i, sp in enumerate(speeches, start=1):
            row_started = time.monotonic()
            link = sp.get("link") or ""
            title = sp.get("title") or ""
            description = sp.get("description") or ""
            published = parse_published_date(sp.get("public_timestamp"))
            source_url = urljoin(GOV_UK_BASE, link)

            # pace per-host
            if i > 1:
                time.sleep(PACE_SEC)

            # 2) fetch
            body_html, fetch_elapsed, status, fetch_err = fetch_speech_page(link)
            if fetch_err or not body_html:
                counts["fetch_fail"] += 1
                metrics_rows.append({
                    "i": i, "url": source_url,
                    "fetch_status": status, "fetch_sec": f"{fetch_elapsed:.3f}",
                    "fetch_err": fetch_err or "",
                    "extract_sec": "", "body_chars": "",
                    "ollama_sec": "", "ollama_eval_count": "",
                    "ollama_topic": "", "ollama_err": "",
                    "pg_sec": "", "pg_result": "skip_fetch_fail",
                    "row_total_sec": f"{time.monotonic() - row_started:.3f}",
                })
                log.warning("[%d/%d] FETCH FAIL %s status=%s err=%s",
                            i, len(speeches), link, status, fetch_err)
                continue
            counts["fetch_ok"] += 1

            # 3) extract body excerpt
            extract_started = time.monotonic()
            excerpt = extract_body_excerpt(body_html)
            extract_elapsed = time.monotonic() - extract_started

            # 4) ollama topic tag
            topic, ollama_elapsed, eval_count, ollama_err = call_ollama_topic(
                title, excerpt or description
            )
            if ollama_err:
                counts["ollama_fail"] += 1
                # we still attempt to insert with topic='other'
                topic = topic or "other"
            else:
                counts["ollama_ok"] += 1

            # Build statement text: "[topic] title — description"
            statement_text = f"[{topic}] {title}"
            if description:
                statement_text = f"{statement_text} — {description}"
            statement_text = statement_text[:380]

            # 5) insert
            try:
                row = {
                    "politician": args.politician_slug,
                    "statement_or_decision": statement_text,
                    "source_url": source_url,
                    "published_date": published,
                    "kind": "statement",
                    "confidence": 1.0,
                    "raw_html": (excerpt or "")[:2048],
                }
                new_id, pg_elapsed = insert_row(conn, row)
                if new_id:
                    counts["pg_inserted"] += 1
                    pg_result = "inserted"
                else:
                    counts["pg_duplicate"] += 1
                    pg_result = "duplicate"
            except Exception as e:
                counts["pg_fail"] += 1
                pg_elapsed = 0.0
                pg_result = f"fail:{type(e).__name__}:{e}"[:200]
                log.error("pg insert failed: %s", e)

            metrics_rows.append({
                "i": i, "url": source_url,
                "fetch_status": status, "fetch_sec": f"{fetch_elapsed:.3f}",
                "fetch_err": "",
                "extract_sec": f"{extract_elapsed:.3f}", "body_chars": len(excerpt),
                "ollama_sec": f"{ollama_elapsed:.3f}", "ollama_eval_count": eval_count,
                "ollama_topic": topic, "ollama_err": ollama_err or "",
                "pg_sec": f"{pg_elapsed:.3f}", "pg_result": pg_result,
                "row_total_sec": f"{time.monotonic() - row_started:.3f}",
            })
            log.info("[%d/%d] OK %s topic=%s ollama=%.2fs pg=%.3fs total=%.2fs",
                     i, len(speeches), link[-60:], topic,
                     ollama_elapsed, pg_elapsed, time.monotonic() - row_started)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM statements;")
            after_count = int(cur.fetchone()[0])

    run_elapsed = time.monotonic() - run_started

    # Write metrics CSV
    fieldnames = [
        "i", "url",
        "fetch_status", "fetch_sec", "fetch_err",
        "extract_sec", "body_chars",
        "ollama_sec", "ollama_eval_count", "ollama_topic", "ollama_err",
        "pg_sec", "pg_result",
        "row_total_sec",
    ]
    Path(args.metrics_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.metrics_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(metrics_rows)

    summary = {
        "run_elapsed_sec": round(run_elapsed, 2),
        "list_elapsed_sec": round(list_elapsed, 2),
        "before_count": before_count,
        "after_count": after_count,
        "delta": after_count - before_count,
        **counts,
        "metrics_csv": args.metrics_csv,
        "pg_target_kind": pg_target_kind,
    }
    log.info("DONE: %s", summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
