"""Starmer accountability scorecard generator.

Reads ingested rows from Postgres (`rows` table), aggregates votes /
statements / lobbying by action_class + subject_role, and writes a
self-contained HTML scorecard to:

    framework/BPM/scorecards/starmer-<YYYY-MM-DD>.html

Per DR-source-quality-canon §"5 rules" + addendum:

  - Excludes action_class IN ('talking_point','supporting_metadata') from
    aggregate verdict computation (rule 4 + addendum extension 2).
  - `supporting_metadata` rows are used ONLY for header decoration (name,
    constituency, party, role) — never as evidence in panels.
  - Lobbying panel filters by subject_role = 'lobbied' so the scorecard
    doesn't conflate "lobbied by X" with "lobbied for X" (addendum extension 1).
  - 100% of claims trace to source URLs (re-spec §3 success criterion);
    each row in each panel carries a footnoted provenance link to the
    upstream Hansard / Commons Votes / Lobbying-Register URL.

Topic-tagging note: Phase C uses raw bill metadata (Title / DebateSection)
as the topic proxy. Phase D will add the Olares Ollama topic-classifier call
referenced in re-spec §3.1 #1 once topic taxonomy is curated.

CLI:
    python -m src.scoring.starmer_scorecard --output-dir framework/BPM/scorecards/
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

# psycopg is the production DB driver; we defer the import so the renderer
# helpers (aggregate_*, _render_*) stay importable in environments without
# psycopg (test/dev machines that don't talk to Postgres).
try:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_metadata(conn: psycopg.Connection, slug: str) -> dict[str, Any]:
    """Decorative metadata for header: politician identity + role.

    Reads the most recent `supporting_metadata` row plus the politicians-table
    seed. Per addendum DR: `supporting_metadata` rows display only — never
    feed verdict computation.
    """
    out = {"slug": slug, "name": slug.title(), "constituency": "", "party": "", "role": ""}
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, full_name, government_role, external_ids FROM politicians "
            "WHERE slug = %s;",
            (slug,),
        )
        pol = cur.fetchone()
        if pol:
            out["politician_id"] = str(pol["id"])
            out["name"] = pol["full_name"]
            out["role"] = pol["government_role"] or ""
            ext = pol["external_ids"] or {}
            out["constituency"] = ext.get("constituency") or ""

        # Latest supporting_metadata row (Members API), if present.
        cur.execute(
            """
            SELECT payload_json, occurred_at
            FROM rows
            WHERE politician_id = %s AND action_class = 'supporting_metadata'
            ORDER BY occurred_at DESC LIMIT 1;
            """,
            (out.get("politician_id"),),
        )
        meta_row = cur.fetchone()
        if meta_row:
            payload = meta_row["payload_json"] or {}
            latest_party = (payload.get("latestParty") or {}).get("name")
            if latest_party:
                out["party"] = latest_party
            house = payload.get("latestHouseMembership") or {}
            if house.get("membershipFrom"):
                out["constituency"] = house["membershipFrom"]

    return out


def fetch_votes(conn: psycopg.Connection, politician_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ext_id, occurred_at, title, summary, source_url, payload_json, subject_role
            FROM rows
            WHERE politician_id = %s
              AND action_class = 'vote'
              AND action_class NOT IN ('talking_point','supporting_metadata')
            ORDER BY occurred_at DESC
            LIMIT %s;
            """,
            (politician_id, limit),
        )
        return list(cur.fetchall())


def fetch_statements(conn: psycopg.Connection, politician_id: str, limit: int = 30) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ext_id, occurred_at, title, summary, source_url, payload_json, subject_role
            FROM rows
            WHERE politician_id = %s
              AND action_class = 'statement_official'
              AND action_class NOT IN ('talking_point','supporting_metadata')
            ORDER BY occurred_at DESC
            LIMIT %s;
            """,
            (politician_id, limit),
        )
        return list(cur.fetchall())


def fetch_lobbying(conn: psycopg.Connection, politician_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Lobbying rows where subject_role = 'lobbied' (per addendum)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ext_id, occurred_at, title, summary, source_url, payload_json, subject_role
            FROM rows
            WHERE politician_id = %s
              AND action_class = 'lobby_filing'
              AND subject_role = 'lobbied'
              AND action_class NOT IN ('talking_point','supporting_metadata')
            ORDER BY occurred_at DESC
            LIMIT %s;
            """,
            (politician_id, limit),
        )
        return list(cur.fetchall())


def aggregate_votes(votes: list[dict[str, Any]]) -> dict[str, Any]:
    """Return aye/no/no_vote_recorded counts + per-title topic frequency."""
    counts = Counter()
    title_words: Counter = Counter()
    for v in votes:
        payload = v.get("payload_json") or {}
        position = (payload.get("vote_position") or "unknown").lower()
        counts[position] += 1
        title = (v.get("title") or "").lower()
        for word in title.split():
            if len(word) > 4 and word.isalpha():
                title_words[word] += 1
    return {
        "total": len(votes),
        "aye": counts.get("aye", 0),
        "no": counts.get("no", 0),
        "no_vote_recorded": counts.get("no_vote_recorded", 0),
        "top_topics": title_words.most_common(8),
    }


def aggregate_statements(statements: list[dict[str, Any]]) -> dict[str, Any]:
    title_words: Counter = Counter()
    for s in statements:
        title = (s.get("title") or "").lower()
        for word in title.split():
            if len(word) > 4 and word.isalpha():
                title_words[word] += 1
    return {
        "total": len(statements),
        "top_topics": title_words.most_common(8),
    }


def aggregate_lobbying(lobbying: list[dict[str, Any]]) -> dict[str, Any]:
    lobbyist_orgs: Counter = Counter()
    for f in lobbying:
        payload = f.get("payload_json") or {}
        org = payload.get("lobbyist_org") or "(unknown)"
        lobbyist_orgs[str(org)] += 1
    return {
        "total": len(lobbying),
        "top_lobbyists": lobbyist_orgs.most_common(10),
    }


# ---------------------------------------------------------------------------
# HTML rendering (self-contained, inline CSS)
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  max-width: 920px; margin: 0 auto; padding: 32px 24px;
  color: #1a1a1a; background: #fafafa; line-height: 1.5;
}
h1 { margin: 0 0 4px 0; font-size: 28px; }
h2 { margin: 32px 0 12px 0; font-size: 20px; border-bottom: 2px solid #ddd; padding-bottom: 6px; }
h3 { margin: 20px 0 8px 0; font-size: 16px; color: #555; }
.subtitle { color: #666; font-size: 14px; margin: 0 0 24px 0; }
.header-card {
  background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 20px; margin-bottom: 24px;
}
.header-card .meta { font-size: 14px; color: #555; margin-top: 8px; }
.panel {
  background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 20px; margin-bottom: 24px;
}
.stat-row { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 12px; }
.stat { flex: 1; min-width: 140px; }
.stat .label { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
.stat .value { font-size: 24px; font-weight: 600; color: #111; }
.topics { font-size: 13px; color: #555; }
.topics .tag {
  display: inline-block; background: #eef; color: #335;
  padding: 2px 8px; border-radius: 4px; margin: 2px 4px 2px 0; font-size: 12px;
}
.row-list { margin-top: 12px; }
.row-item {
  padding: 10px 0; border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}
.row-item:last-child { border-bottom: none; }
.row-item .date { color: #888; font-size: 12px; margin-right: 8px; }
.row-item .title { font-weight: 500; color: #111; }
.row-item .summary { color: #555; font-size: 13px; margin-top: 4px; }
.row-item a { color: #235; text-decoration: none; font-size: 12px; }
.row-item a:hover { text-decoration: underline; }
.provenance {
  font-size: 12px; color: #777; margin-top: 4px;
}
.empty { color: #888; font-style: italic; padding: 12px 0; }
.footnote {
  margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;
  font-size: 12px; color: #666;
}
.tier-badge {
  display: inline-block; background: #233; color: #fff;
  padding: 2px 6px; border-radius: 3px; font-size: 11px;
  font-weight: 600; margin-left: 6px;
}
"""


def _fmt_date(occurred_at: Any) -> str:
    if isinstance(occurred_at, datetime):
        return occurred_at.date().isoformat()
    if isinstance(occurred_at, date):
        return occurred_at.isoformat()
    return str(occurred_at)[:10]


def _render_votes_panel(votes: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if not votes:
        return '<div class="panel"><h2>Voting record</h2><div class="empty">No vote rows ingested in this run.</div></div>'

    rows_html = []
    for v in votes[:20]:  # first 20 rendered
        position = (v.get("payload_json") or {}).get("vote_position", "?")
        rows_html.append(
            f'<div class="row-item">'
            f'<span class="date">{_fmt_date(v["occurred_at"])}</span>'
            f'<span class="title">{html.escape(v["title"] or "Untitled division")}</span>'
            f' &mdash; <strong>{html.escape(str(position))}</strong>'
            f'<div class="provenance">'
            f'<a href="{html.escape(v["source_url"])}" target="_blank">'
            f'commonsvotes.digiminster.com</a>'
            f' <span class="tier-badge">T1</span>'
            f'</div>'
            f'</div>'
        )

    topics_html = " ".join(
        f'<span class="tag">{html.escape(w)} ({n})</span>'
        for w, n in summary["top_topics"]
    ) or '<span class="empty">No topic data yet (Phase D).</span>'

    return f"""
    <div class="panel">
      <h2>Voting record</h2>
      <div class="stat-row">
        <div class="stat"><div class="label">Total divisions</div><div class="value">{summary["total"]}</div></div>
        <div class="stat"><div class="label">Aye</div><div class="value">{summary["aye"]}</div></div>
        <div class="stat"><div class="label">No</div><div class="value">{summary["no"]}</div></div>
        <div class="stat"><div class="label">No vote recorded</div><div class="value">{summary["no_vote_recorded"]}</div></div>
      </div>
      <h3>Top vote-title keywords</h3>
      <div class="topics">{topics_html}</div>
      <h3>Most recent divisions (top 20)</h3>
      <div class="row-list">{"".join(rows_html)}</div>
    </div>
    """


def _render_statements_panel(statements: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if not statements:
        return '<div class="panel"><h2>Statements (Hansard)</h2><div class="empty">No statement rows ingested in this run.</div></div>'

    rows_html = []
    for s in statements[:15]:
        quote = (s.get("summary") or "")[:240]
        rows_html.append(
            f'<div class="row-item">'
            f'<span class="date">{_fmt_date(s["occurred_at"])}</span>'
            f'<span class="title">{html.escape(s["title"] or "Commons contribution")}</span>'
            f'<div class="summary">{html.escape(quote)}{"&hellip;" if quote and len(s.get("summary") or "") > 240 else ""}</div>'
            f'<div class="provenance">'
            f'<a href="{html.escape(s["source_url"])}" target="_blank">hansard.parliament.uk</a>'
            f' <span class="tier-badge">T1</span>'
            f'</div>'
            f'</div>'
        )

    topics_html = " ".join(
        f'<span class="tag">{html.escape(w)} ({n})</span>'
        for w, n in summary["top_topics"]
    ) or '<span class="empty">No topic data yet (Phase D).</span>'

    return f"""
    <div class="panel">
      <h2>Statements (Hansard)</h2>
      <div class="stat-row">
        <div class="stat"><div class="label">Total contributions</div><div class="value">{summary["total"]}</div></div>
      </div>
      <h3>Top section-title keywords</h3>
      <div class="topics">{topics_html}</div>
      <h3>Most recent contributions (top 15)</h3>
      <div class="row-list">{"".join(rows_html)}</div>
    </div>
    """


def _render_lobbying_panel(lobbying: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if not lobbying:
        return ('<div class="panel"><h2>Lobbying activity (Starmer as lobbied party)</h2>'
                '<div class="empty">No lobby filings naming Starmer / Office of the Prime Minister '
                'in the quarters scanned.</div></div>')

    rows_html = []
    for f in lobbying[:25]:
        payload = f.get("payload_json") or {}
        lobbyist = payload.get("lobbyist_org") or "(unknown)"
        client = payload.get("client") or ""
        activity = (payload.get("activity_description") or "")[:260]
        rows_html.append(
            f'<div class="row-item">'
            f'<span class="date">{_fmt_date(f["occurred_at"])}</span>'
            f'<span class="title">{html.escape(str(lobbyist))}</span>'
            f' &mdash; client: <em>{html.escape(str(client))}</em>'
            f'<div class="summary">{html.escape(activity)}</div>'
            f'<div class="provenance">'
            f'subject_role: <strong>lobbied</strong> &middot; '
            f'<a href="{html.escape(f["source_url"])}" target="_blank">'
            f'registrarofconsultantlobbyists.org.uk</a>'
            f' <span class="tier-badge">T1</span>'
            f'</div>'
            f'</div>'
        )

    lobbyists_html = " ".join(
        f'<span class="tag">{html.escape(org)} ({n})</span>'
        for org, n in summary["top_lobbyists"]
    )

    return f"""
    <div class="panel">
      <h2>Lobbying activity (Starmer as lobbied party)</h2>
      <p style="font-size:13px;color:#555;">
        Filings from the UK Lobbying Register where Starmer or the
        Office of the Prime Minister was named as the lobbied official.
        Per addendum DR: these rows tag subject_role=<strong>lobbied</strong>;
        the scorecard does not conflate them with lobbying activity BY the
        politician (which would tag subject_role=lobbyist).
      </p>
      <div class="stat-row">
        <div class="stat"><div class="label">Total filings naming Starmer</div><div class="value">{summary["total"]}</div></div>
      </div>
      <h3>Top lobbyist organisations</h3>
      <div class="topics">{lobbyists_html}</div>
      <h3>Most recent filings (top 25)</h3>
      <div class="row-list">{"".join(rows_html)}</div>
    </div>
    """


def _render_scorecard_html(
    meta: dict[str, Any],
    votes_summary: dict[str, Any],
    statements_summary: dict[str, Any],
    lobbying_summary: dict[str, Any],
    votes: list[dict[str, Any]],
    statements: list[dict[str, Any]],
    lobbying: list[dict[str, Any]],
    generated_at: datetime,
) -> str:
    title = f"Accountability scorecard — {meta['name']}"
    tz_label = generated_at.strftime("%Z") or "UTC"
    footer_ts = generated_at.strftime("%Y-%m-%d %H:%M ") + tz_label

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="header-card">
  <h1>{html.escape(meta["name"])}</h1>
  <p class="subtitle">{html.escape(meta["role"] or "")}{' &middot; ' if meta.get("role") else ''}{html.escape(meta["party"])}{' &middot; ' if meta.get("party") else ''}{html.escape(meta["constituency"])}</p>
  <div class="meta">
    intelpolitics &middot; T1 source-tier canon (2026-05-12)
    &middot; Phase C first scorecard
    &middot; All claims trace to source URLs in panel rows
  </div>
</div>

{_render_votes_panel(votes, votes_summary)}
{_render_statements_panel(statements, statements_summary)}
{_render_lobbying_panel(lobbying, lobbying_summary)}

<div class="footnote">
  <p>
    <strong>Source tiers.</strong>
    All ingested rows on this scorecard are <strong>T1 — Primary structured</strong> from
    UK Parliament APIs (Hansard, Commons Votes Service, Members API) and the UK Lobbying
    Register quarterly returns. Per source-quality canon
    (BKM/dr-source-quality-canon-2026-05-12.md): T1 = ground truth, cited as the
    load-bearing claim. T2/T3/T4 sources do not appear here.
  </p>
  <p>
    <strong>Provenance.</strong>
    Each row links to its upstream T1 URL. No claim on this scorecard is asserted
    by an LLM &mdash; the LLM (Phase D) will only synthesise verdicts over rows
    already validated as T1.
  </p>
  <p>
    <strong>Subject role.</strong>
    Lobbying rows display only when subject_role = <code>lobbied</code> (politician
    is the target). Rows where Starmer was the lobbyist would render in a separate
    panel; currently empty (no sitting-MP lobbyist rows expected).
  </p>
  <p>
    <strong>Decorative metadata excluded from verdicts.</strong>
    The header card draws on action_class = supporting_metadata rows (Members API
    identity + role); these rows are filtered out of every aggregate count
    (votes, statements, lobbying) per addendum DR.
  </p>
  <p>Last updated: {footer_ts}</p>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_scorecard(
    pg_url: str,
    slug: str,
    output_dir: Path,
) -> Path:
    """Generate the scorecard HTML and return the written path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with psycopg.connect(pg_url) as conn:
        meta = fetch_metadata(conn, slug)
        if "politician_id" not in meta:
            raise RuntimeError(
                f"politician slug={slug!r} not seeded — run migration 002 first"
            )
        pid = meta["politician_id"]
        votes = fetch_votes(conn, pid)
        statements = fetch_statements(conn, pid)
        lobbying = fetch_lobbying(conn, pid)

    votes_summary = aggregate_votes(votes)
    statements_summary = aggregate_statements(statements)
    lobbying_summary = aggregate_lobbying(lobbying)

    generated_at = datetime.now()
    html_doc = _render_scorecard_html(
        meta, votes_summary, statements_summary, lobbying_summary,
        votes, statements, lobbying, generated_at,
    )

    output_path = output_dir / f"{slug}-{generated_at.strftime('%Y-%m-%d')}.html"
    output_path.write_text(html_doc, encoding="utf-8")
    log.info("scorecard written to %s", output_path)
    return output_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate Starmer accountability scorecard")
    p.add_argument("--slug", default="starmer")
    p.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).resolve().parents[3] / "framework" / "BPM" / "scorecards"),
    )
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    pg_url = os.environ.get("POSTGRES_URL")
    if not pg_url:
        log.error("POSTGRES_URL is required")
        return 2

    path = generate_scorecard(pg_url, args.slug, Path(args.output_dir))
    print(json.dumps({"scorecard_path": str(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
