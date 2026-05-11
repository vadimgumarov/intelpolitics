"""Multi-politician scrape pipeline (2026-05-10).

Goal: run the 5 intelpolitics politicians sequentially through the
Olares cluster (Ollama + Postgres) in a single Job.

Architecture:
    For each politician slug in --politicians:
        1. Resolve the politician's strategy (gov.uk search API for Starmer,
           per-country best-effort listing scrapes for the rest).
        2. Fetch a list of candidate items (title + URL + date + body excerpt).
        3. For each item: Ollama topic tag -> Postgres INSERT.
        4. Capture per-politician metrics: rows attempted, fetch ok/fail,
           ollama median latency, pg inserted/duplicate/fail, duration.
        5. Log failures to scrape_errors table.
    Print a final summary table at end-of-run.

Exit code semantics:
    0 — at least one politician produced >0 inserts. Per-politician failures
        are logged in scrape_errors and surfaced in stdout summary.
    3 — all 5 politicians failed (catastrophic; image/network broken).
    2 — required env var missing.

This pipeline reuses the same Ollama topic-tag + Postgres write path as
src.pipelines.olares_value_test. The Starmer strategy is a verbatim port of
that pipeline's data path, so the 95-row baseline is preserved.

Per DR-25: all LLM calls go to Olares Ollama. No external LLM SDK imports.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

import curl_cffi.requests as creq
import httpx
import psycopg
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Common config
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT_SEC = float(os.environ.get("OLLAMA_TIMEOUT_SEC", "60"))
PACE_SEC = float(os.environ.get("PACE_SEC", "3.0"))
BODY_EXCERPT_CHARS = 2000

TOPIC_PROMPT = """You are tagging a political speech / statement with one topic word.

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


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class CandidateItem:
    """One scrape candidate before Ollama + DB write."""
    title: str
    source_url: str
    published_date: date | None
    body_excerpt: str
    description: str = ""


@dataclass
class PoliticianSummary:
    slug: str
    strategy: str
    source_host: str
    candidates: int = 0
    fetch_ok: int = 0
    fetch_fail: int = 0
    ollama_ok: int = 0
    ollama_fail: int = 0
    pg_inserted: int = 0
    pg_duplicate: int = 0
    pg_fail: int = 0
    ollama_latencies: list[float] = field(default_factory=list)
    duration_sec: float = 0.0
    fatal_error: str | None = None

    def ollama_median_ms(self) -> int | None:
        if not self.ollama_latencies:
            return None
        return int(statistics.median(self.ollama_latencies) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "strategy": self.strategy,
            "source_host": self.source_host,
            "candidates": self.candidates,
            "fetch_ok": self.fetch_ok,
            "fetch_fail": self.fetch_fail,
            "ollama_ok": self.ollama_ok,
            "ollama_fail": self.ollama_fail,
            "pg_inserted": self.pg_inserted,
            "pg_duplicate": self.pg_duplicate,
            "pg_fail": self.pg_fail,
            "ollama_median_ms": self.ollama_median_ms(),
            "ollama_calls": len(self.ollama_latencies),
            "duration_sec": round(self.duration_sec, 2),
            "fatal_error": self.fatal_error,
        }


# ---------------------------------------------------------------------------
# Per-politician strategies
# ---------------------------------------------------------------------------
# Each strategy is a callable `(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]`.
# Strategies own their own fetch + parse logic; they bump summary.fetch_ok/fetch_fail.
# They must not call Ollama or Postgres — that's the common downstream.
# ---------------------------------------------------------------------------

def _http_get_json(url: str, summary: PoliticianSummary, timeout: float = 30.0) -> Any:
    started = time.monotonic()
    try:
        r = httpx.get(url, timeout=timeout, headers={"User-Agent": "intelpolitics-scraper/2026-05-10"})
        elapsed = time.monotonic() - started
        if r.status_code != 200:
            summary.fetch_fail += 1
            log.warning("[%s] JSON GET %s -> %d (%.2fs)", summary.slug, url, r.status_code, elapsed)
            return None
        summary.fetch_ok += 1
        return r.json()
    except Exception as e:
        summary.fetch_fail += 1
        log.warning("[%s] JSON GET %s -> %s: %s", summary.slug, url, type(e).__name__, e)
        return None


def _curl_get_html(url: str, summary: PoliticianSummary, timeout: float = 30.0) -> tuple[str | None, int]:
    started = time.monotonic()
    try:
        r = creq.get(url, impersonate="chrome120", timeout=timeout, allow_redirects=True)
        elapsed = time.monotonic() - started
        if r.status_code != 200:
            summary.fetch_fail += 1
            log.warning("[%s] HTML GET %s -> %d (%.2fs)", summary.slug, url, r.status_code, elapsed)
            return None, r.status_code
        summary.fetch_ok += 1
        return r.text, r.status_code
    except Exception as e:
        summary.fetch_fail += 1
        log.warning("[%s] HTML GET %s -> %s: %s", summary.slug, url, type(e).__name__, e)
        return None, 0


def _extract_body_excerpt(html: str, selectors: list[str] | None = None,
                          truncate: int = BODY_EXCERPT_CHARS) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "aside", "header"]):
        tag.decompose()
    container = None
    for sel in (selectors or []):
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup.body or soup
    text = container.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:truncate]


def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError):
        return None


# ---- Strategy: starmer (gov.uk search API — PROVEN) -----------------------

GOV_UK_BASE = "https://www.gov.uk"
GOV_UK_SEARCH = (
    "https://www.gov.uk/api/search.json"
    "?filter_people=keir-starmer"
    "&filter_content_store_document_type=speech"
    "&count={count}"
    "&order=-public_timestamp"
)
STARMER_BODY_SELECTORS = [".govspeak", "[data-module='govspeak']", "main .gem-c-govspeak", "main"]


def strategy_starmer(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]:
    """gov.uk Search API → speech pages. Validated path; 95 rows on 2026-05-10."""
    summary.strategy = "govuk-search-api"
    summary.source_host = "gov.uk"
    data = _http_get_json(GOV_UK_SEARCH.format(count=max_rows), summary)
    if not data:
        summary.fatal_error = "gov.uk search API returned no data"
        return []
    speeches = data.get("results", [])
    summary.candidates = len(speeches)
    log.info("[starmer] gov.uk API returned %d speeches", len(speeches))

    items: list[CandidateItem] = []
    for i, sp in enumerate(speeches, start=1):
        if i > 1:
            time.sleep(PACE_SEC)
        link = sp.get("link") or ""
        title = sp.get("title") or ""
        description = sp.get("description") or ""
        url = urljoin(GOV_UK_BASE, link)
        html, _ = _curl_get_html(url, summary)
        excerpt = _extract_body_excerpt(html, STARMER_BODY_SELECTORS) if html else ""
        if not excerpt:
            excerpt = description
        items.append(CandidateItem(
            title=title,
            source_url=url,
            published_date=_parse_iso_date(sp.get("public_timestamp")),
            body_excerpt=excerpt,
            description=description,
        ))
    return items


# ---- Strategy: vance (whitehouse.gov briefings — BEST-EFFORT) -------------

def strategy_vance(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]:
    """whitehouse.gov briefings & statements listing, filtered post-hoc for Vance.

    Tier-0 best-effort: scrape the briefings index, parse the listing cards,
    keep only entries mentioning 'vance' in title or excerpt. No deep fetch
    on each item — listing page already gives us title + date + url.
    """
    summary.strategy = "whitehouse-briefings-listing"
    summary.source_host = "whitehouse.gov"
    base = "https://www.whitehouse.gov/briefings-statements/"
    html, _ = _curl_get_html(base, summary)
    if not html:
        summary.fatal_error = "whitehouse.gov briefings index unreachable"
        return []
    soup = BeautifulSoup(html, "html.parser")
    # Listing cards on WH.gov use <article> tags or .news-item-style divs.
    candidates = soup.select("article, .news-item, .post, [class*='card']")
    log.info("[vance] whitehouse.gov listing parsed %d candidate cards", len(candidates))
    items: list[CandidateItem] = []
    for card in candidates[: max_rows * 3]:  # over-pull, we'll filter
        a = card.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        # Filter for Vance relevance
        excerpt = _extract_body_excerpt(str(card), truncate=BODY_EXCERPT_CHARS)
        if "vance" not in (title + " " + excerpt).lower():
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin(base, href)
        time_tag = card.find("time")
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            pub_date = _parse_iso_date(time_tag["datetime"])
        items.append(CandidateItem(
            title=title, source_url=url,
            published_date=pub_date, body_excerpt=excerpt,
        ))
        if len(items) >= max_rows:
            break
    summary.candidates = len(items)
    return items


# ---- Strategy: meloni (governo.it speeches archive — BEST-EFFORT) ---------

def strategy_meloni(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]:
    """governo.it PM speeches archive listing."""
    summary.strategy = "governoit-speeches-listing"
    summary.source_host = "governo.it"
    base = "https://www.governo.it/it/i-discorsi-del-presidente"
    html, _ = _curl_get_html(base, summary)
    if not html:
        summary.fatal_error = "governo.it speeches index unreachable"
        return []
    soup = BeautifulSoup(html, "html.parser")
    # Italian government uses .views-row or .node-articolo containers typically.
    cards = soup.select(".views-row, article, .node, .item-list li")
    log.info("[meloni] governo.it listing parsed %d candidate cards", len(cards))
    items: list[CandidateItem] = []
    for card in cards[: max_rows * 2]:
        a = card.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin(base, href)
        excerpt = _extract_body_excerpt(str(card), truncate=BODY_EXCERPT_CHARS)
        time_tag = card.find("time")
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            pub_date = _parse_iso_date(time_tag["datetime"])
        items.append(CandidateItem(
            title=title, source_url=url,
            published_date=pub_date, body_excerpt=excerpt,
        ))
        if len(items) >= max_rows:
            break
    summary.candidates = len(items)
    return items


# ---- Strategy: merz (bundeskanzler.de Reden — BEST-EFFORT) ----------------

def strategy_merz(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]:
    """bundeskanzler.de Reden (speeches) feed."""
    summary.strategy = "bundeskanzler-reden-listing"
    summary.source_host = "bundeskanzler.de"
    base = "https://www.bundeskanzler.de/bk-de/aktuelles/reden"
    html, _ = _curl_get_html(base, summary)
    if not html:
        summary.fatal_error = "bundeskanzler.de reden unreachable"
        return []
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article, .bpa-teaser, .bpa-card, li.bpa-list-item, [class*='teaser']")
    log.info("[merz] bundeskanzler.de listing parsed %d candidate cards", len(cards))
    items: list[CandidateItem] = []
    for card in cards[: max_rows * 2]:
        a = card.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin(base, href)
        excerpt = _extract_body_excerpt(str(card), truncate=BODY_EXCERPT_CHARS)
        time_tag = card.find("time")
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            pub_date = _parse_iso_date(time_tag["datetime"])
        items.append(CandidateItem(
            title=title, source_url=url,
            published_date=pub_date, body_excerpt=excerpt,
        ))
        if len(items) >= max_rows:
            break
    summary.candidates = len(items)
    return items


# ---- Strategy: von-der-leyen (ec.europa.eu presscorner — BEST-EFFORT) -----

def strategy_von_der_leyen(max_rows: int, summary: PoliticianSummary) -> list[CandidateItem]:
    """EC presscorner search by speaker = von der Leyen."""
    summary.strategy = "ec-presscorner-listing"
    summary.source_host = "ec.europa.eu"
    # Public presscorner search results page (HTML; the JSON API requires keys).
    base = "https://ec.europa.eu/commission/presscorner/home/en?speakerids=URSULA%20VON%20DER%20LEYEN"
    html, _ = _curl_get_html(base, summary)
    if not html:
        summary.fatal_error = "ec.europa.eu presscorner unreachable"
        return []
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article, .ecl-content-item, .news-item, [class*='card']")
    log.info("[von-der-leyen] EC presscorner parsed %d candidate cards", len(cards))
    items: list[CandidateItem] = []
    for card in cards[: max_rows * 2]:
        a = card.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin("https://ec.europa.eu", href)
        excerpt = _extract_body_excerpt(str(card), truncate=BODY_EXCERPT_CHARS)
        time_tag = card.find("time")
        pub_date = None
        if time_tag and time_tag.get("datetime"):
            pub_date = _parse_iso_date(time_tag["datetime"])
        items.append(CandidateItem(
            title=title, source_url=url,
            published_date=pub_date, body_excerpt=excerpt,
        ))
        if len(items) >= max_rows:
            break
    summary.candidates = len(items)
    return items


STRATEGIES: dict[str, Callable[[int, PoliticianSummary], list[CandidateItem]]] = {
    "starmer": strategy_starmer,
    "vance": strategy_vance,
    "meloni": strategy_meloni,
    "merz": strategy_merz,
    "von-der-leyen": strategy_von_der_leyen,
}


# ---------------------------------------------------------------------------
# Common downstream: Ollama tag + Postgres write
# ---------------------------------------------------------------------------

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


def insert_statement(conn: psycopg.Connection, slug: str, item: CandidateItem,
                     topic: str) -> tuple[bool, bool, str | None]:
    """Returns (inserted, duplicate, error)."""
    statement_text = f"[{topic}] {item.title}"
    if item.description:
        statement_text = f"{statement_text} — {item.description}"
    statement_text = statement_text[:380]
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
    try:
        with conn.cursor() as cur:
            cur.execute(q, {
                "politician": slug,
                "statement_or_decision": statement_text,
                "source_url": item.source_url,
                "published_date": item.published_date,
                "kind": "statement",
                "confidence": 1.0,
                "raw_html": (item.body_excerpt or "")[:2048],
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


def log_scrape_error(conn: psycopg.Connection, slug: str, url: str, kind: str, detail: str) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO scrape_errors (source_url, politician, fetcher, kind, detail)
                   VALUES (%s, %s, %s, %s, %s)""",
                (url[:1000], slug, "curl_cffi", kind, detail[:2000]),
            )
        conn.commit()
    except Exception as e:
        log.warning("scrape_errors write failed: %s", e)


# ---------------------------------------------------------------------------
# Per-politician runner
# ---------------------------------------------------------------------------

def run_politician(slug: str, max_rows: int, conn: psycopg.Connection) -> PoliticianSummary:
    summary = PoliticianSummary(slug=slug, strategy="unknown", source_host="unknown")
    strategy = STRATEGIES.get(slug)
    if strategy is None:
        summary.fatal_error = f"no strategy registered for slug={slug!r}"
        return summary

    log.info("======== START politician=%s max_rows=%d ========", slug, max_rows)
    t0 = time.monotonic()
    try:
        items = strategy(max_rows, summary)
    except Exception as e:
        summary.fatal_error = f"strategy crashed: {type(e).__name__}: {e}"
        summary.duration_sec = time.monotonic() - t0
        log.error("[%s] strategy crashed: %s", slug, e)
        log_scrape_error(conn, slug, "(strategy)", "strategy_crash", str(e))
        return summary

    if not items:
        log.warning("[%s] strategy produced 0 items (fatal_error=%s)", slug, summary.fatal_error)
        summary.duration_sec = time.monotonic() - t0
        if summary.fatal_error:
            log_scrape_error(conn, slug, "(strategy)", "empty_body", summary.fatal_error)
        return summary

    log.info("[%s] strategy produced %d candidates; tagging + inserting", slug, len(items))
    for i, item in enumerate(items, start=1):
        topic, ollama_sec, eval_count, ollama_err = call_ollama_topic(
            item.title, item.body_excerpt or item.description
        )
        if ollama_err:
            summary.ollama_fail += 1
            topic = topic or "other"
            log.warning("[%s] ollama fail: %s", slug, ollama_err)
        else:
            summary.ollama_ok += 1
        summary.ollama_latencies.append(ollama_sec)

        inserted, duplicate, pg_err = insert_statement(conn, slug, item, topic)
        if pg_err:
            summary.pg_fail += 1
            log.warning("[%s] pg fail: %s url=%s", slug, pg_err, item.source_url)
            log_scrape_error(conn, slug, item.source_url, "pg_fail", pg_err)
        elif inserted:
            summary.pg_inserted += 1
            log.info("[%s] [%d/%d] INSERT topic=%s ollama=%.2fs",
                     slug, i, len(items), topic, ollama_sec)
        elif duplicate:
            summary.pg_duplicate += 1

    summary.duration_sec = time.monotonic() - t0
    log.info("======== END politician=%s duration=%.1fs inserted=%d duplicate=%d fail=%d ========",
             slug, summary.duration_sec, summary.pg_inserted,
             summary.pg_duplicate, summary.pg_fail)
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DEFAULT_MAX_ROWS_PER_POLITICIAN = {
    "starmer": 95,        # validated upper bound
    "vance": 25,
    "meloni": 25,
    "merz": 25,
    "von-der-leyen": 25,
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Multi-politician scrape pipeline")
    p.add_argument("--politicians", type=str, default="starmer,vance,meloni,merz,von-der-leyen",
                   help="Comma-separated slugs (default: all 5)")
    p.add_argument("--max-rows-default", type=int, default=25,
                   help="Default max rows per politician if not in per-slug table")
    p.add_argument("--metrics-csv", type=str, required=True)
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

    slugs = [s.strip() for s in args.politicians.split(",") if s.strip()]
    log.info("politicians=%s ollama=%s model=%s", slugs, OLLAMA_BASE_URL, OLLAMA_MODEL)

    summaries: list[PoliticianSummary] = []
    run_started = time.monotonic()

    with psycopg.connect(pg_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM statements;")
            before_count = int(cur.fetchone()[0])

        for slug in slugs:
            max_rows = DEFAULT_MAX_ROWS_PER_POLITICIAN.get(slug, args.max_rows_default)
            try:
                s = run_politician(slug, max_rows, conn)
            except Exception as e:
                s = PoliticianSummary(slug=slug, strategy="error", source_host="error",
                                      fatal_error=f"runner crashed: {type(e).__name__}: {e}")
                log.exception("[%s] runner crashed", slug)
            summaries.append(s)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM statements;")
            after_count = int(cur.fetchone()[0])

    run_elapsed = time.monotonic() - run_started

    # Per-politician CSV
    fieldnames = list(summaries[0].to_dict().keys()) if summaries else []
    Path(args.metrics_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.metrics_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for s in summaries:
            w.writerow(s.to_dict())

    # Stdout summary
    total_inserted = sum(s.pg_inserted for s in summaries)
    summary_obj = {
        "run_elapsed_sec": round(run_elapsed, 2),
        "before_count": before_count,
        "after_count": after_count,
        "delta": after_count - before_count,
        "total_inserted_this_run": total_inserted,
        "per_politician": [s.to_dict() for s in summaries],
        "metrics_csv": args.metrics_csv,
    }
    print("PIPELINE_SUMMARY=" + json.dumps(summary_obj, sort_keys=True))
    log.info("DONE: total_inserted=%d delta=%d run_elapsed=%.1fs",
             total_inserted, after_count - before_count, run_elapsed)

    if total_inserted == 0 and all(s.fatal_error for s in summaries):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
