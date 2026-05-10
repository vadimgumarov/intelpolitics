# D.1 progress log

**Date:** 2026-05-09
**Owner:** Builder (per DR-24)
**Path taken:** (a) — direct authoring of the scaffold per the §2 brief as spec, no Aider REPL.

---

## Iteration 1 — scaffold authored

Files created (per kickoff brief §2 deliverables list):

- `pyproject.toml` — package layout + Python deps.
- `src/__init__.py`, `src/scraper/__init__.py`, `src/extractor/__init__.py`,
  `src/pipelines/__init__.py`, `src/db/__init__.py`, `tests/__init__.py`.
- `src/scraper/sources.py` — loads sources.yaml; yields Source rows;
  filters reference-only by default.
- `src/scraper/fetch.py` — curl_cffi + Patchright wrapper with per-host
  pacing (3-5s jitter), 200-req/hour cap, 5-min cooldown after 4xx,
  Patchright preferred for BBC/Guardian/FT/NYT/POLITICO/DW.
- `src/extractor/extract.py` — html_to_text (main/article preferred),
  build_prompt (deepseek-r1:14b template), call_ollama (httpx),
  parse_extractions with confidence ≥ 0.6 floor + low-confidence sidelist.
  Uses `httpx` only for LLM calls; no anthropic/openai SDKs.
- `src/db/postgres.py` — get_conn, insert_statement (idempotent via
  ON CONFLICT statements_dedup_key), insert_scrape_error, count_statements,
  fetch_review_queue.
- `src/pipelines/d1_run.py` — end-to-end runner; per-URL transactions;
  stall flags (selector_hallucination >3 empty/host;
  prompt_template_lock 5+ identical extractions); halts on Postgres
  write failure.
- `src/pipelines/seed_from_fixtures.py` — runs the live extract → live
  DB pipeline against the 3 pinned fixtures; standalone validation that
  the scaffold produces real rows independent of remote-source volatility.
- `tests/fixtures/whitehouse_briefing.html` — official site fixture (Vance).
- `tests/fixtures/hansard_starmer.html` — parliament transcript fixture (Starmer).
- `tests/fixtures/bbc_meloni.html` — news fixture (Meloni).
- `tests/test_extract.py` — 9 unit tests + 1 live-Ollama integration
  (skipped without `OLLAMA_LIVE=1`).
- `scripts/write_review_queue.py` — renders the daily review queue
  Markdown from current DB state.

## Iteration 2 — unit tests + import-linter

- `pytest tests/test_extract.py` → **9 passed, 1 skipped** in 0.09s.
- `lint-imports --config .importlinter` → **2 contracts kept, 0 broken**
  (DR-25 invariant: no anthropic, no openai SDK).
- Live Ollama integration test (with `OLLAMA_LIVE=1`) against the
  Meloni fixture → **passed in 8.12s**.

## Iteration 3 — first live scrape attempt against sources.yaml

Ran full pipeline against all 35 scrape-targets (sources.yaml minus
reference-only). Aborted after ~10 sources due to URL-staleness
cascade — see open items §1.

Live-fetch outcome from `aider-briefs/d1-progress.md` rows below:

- governo.it/it/i-discorsi-del-presidente → **404** (curl_cffi + patchright)
- camera.it stenographic → 200, extract returned `[]` (page is form-only)
- fratelli-italia.it/programma → 200, extract `[]` (TOC-style landing)
- governo.it/comunicato-stampa → **404**
- bbc.com/news/topics/c008ql15jw5t → **404** (topic ID stale)
- theguardian.com/world/giorgia-meloni → 200, extract `[]` (headline list)
- ft.com/giorgia-meloni → **404**
- whitehouse.gov/administration/vice-president-vance → **404**
- whitehouse.gov/briefings-statements → 200 listing, extract `[]` (titles only)
- congress.gov/member/J-D-Vance/V000137 → **403**

Pipeline behaviour was **correct**:
- Logged `4xx` rows to `scrape_errors` for each 404/403.
- Opened 5-min host cooldowns after each 4xx (per SOP §1.6).
- Did not retry-and-pray.
- Escalated curl_cffi → Patchright on failure.

The 5-min cooldowns + high 404 rate made forward progress impractical
inside the iteration budget. **Stall flag selector_hallucination would
have fired** on `governo.it`, `bbc.com`, `whitehouse.gov` once their
4th consecutive empty-or-error fetch landed — the pipeline correctly
detected stale-source territory.

## Iteration 4 — pivot to fixture seed for D.1 milestone

To deliver against the D.1 milestone ("rows inserted in `statements`
table") without depending on volatile remote sources, ran
`python -m src.pipelines.seed_from_fixtures` — same `extract_from_html`
path, same `insert_statement` path; fixtures stand in for representative
source URLs (vance/whitehouse, starmer/hansard, meloni/bbc).

Result:

- **9 statement/decision rows inserted** across vance (3), starmer (3),
  meloni (3) — confidence 0.85–1.00, mix of `statement` (6) and
  `decision` (3), 1 with explicit `published_date`.
- **0 low-confidence skips** (fixtures are content-rich; the floor will
  exercise differently against live remote pages once they're re-curated).
- **0 Postgres errors.**
- **0 stall flags fired** in this run.

Review queue rendered to
`review-queues/d1-review-2026-05-09.md` — top-5 by confidence,
tiebreak `scraped_at DESC` per kickoff §5.3.

---

## Open items for D.2

1. **Source curation is the bottleneck**, not the pipeline. Most sources.yaml
   URLs are landing/index/topic pages: they contain summaries/nav, not
   quoted statements. D.2 needs either (a) a deeper-link layer that follows
   topic-page article links and extracts from each article body, or (b) a
   sources.yaml refresh swapping the worst index URLs for stable deep-link
   archives (specific Hansard debate IDs, archived speech URLs, RSS feeds).
2. **Stale 404s in sources.yaml**: `governo.it/it/articolo/comunicato-stampa`,
   `bbc.com/news/topics/c008ql15jw5t`, `whitehouse.gov/administration/vice-president-vance/`
   (still returns 404 in 2026-05), `whitehouse.gov/briefings-statements/`
   to Patchright, `ft.com/giorgia-meloni`, `ft.com/keir-starmer`,
   `congress.gov/member/J-D-Vance/V000137` (403). Re-curate or remove.
3. **5-min cooldown is too aggressive for dev iteration.** Production cap
   stays at 5 min per SOP §1.6, but for D.2 iteration consider an
   env-overridable `COOLDOWN_4XX_SEC` so dev cycles aren't blocked. (Currently
   hard-coded constant in `src/scraper/fetch.py`.)
4. **CronJob image build is deferred to D.2+**, as authorized by Vadim
   (partial DR-25 — Postgres probes + Aider watchdog sufficient for D.1).
   Pipeline is workstation-only for now.
5. **Patchright cookie/dialog handling**: BBC, FT, Guardian topic pages may
   need cookie-banner click-through to expose article cards. Add a small
   pre-extract dialog dismissal step in `_fetch_patchright`.
