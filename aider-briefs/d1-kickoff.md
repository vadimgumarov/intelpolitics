# D.1 intelpolitics scraper + extractor scaffold — Aider brief

**Date:** 2026-05-09
**Owner:** Builder (runs Aider per DR-24)
**Source:** `Vadim's Inbox/pilot-day-1-2026-05-08/d1-intelpolitics-kickoff.md` §2 (verbatim with the locked deltas applied).

Invocation:

```
cd ventures/intelpolitics
aider --model ollama/qwen3-coder:30b --read aider-briefs/d1-kickoff.md
```

Aider's coding model: `ollama/qwen3-coder:30b` (per SOP §1.3). Extraction model in the runtime pipeline: `ollama/deepseek-r1:14b` (locked per Vadim's 2026-05-09 decision on §8 #2 of the kickoff plan).

---

## Brief (the prompt Builder hands Aider)

> **D.1 intelpolitics scraper + extractor scaffold.**
>
> Build a working scrape→extract→load pipeline for the 5 politicians named below. Pipeline shape:
>
> ```
> [target URL] → fetch (Patchright OR curl_cffi) → raw_html → extract (Ollama deepseek-r1:14b) → JSON pair → INSERT into pg.statements
> ```
>
> **Politicians + sources:** see `ventures/intelpolitics/sources.yaml` (40 URLs across 5 politicians, 33 scrape-targets + 7 reference-only).
>
> **Target schema:** `pg.statements` per the DDL in `ventures/intelpolitics/k3s/migrations/001_statements.sql` (= §3 of `Vadim's Inbox/pilot-day-1-2026-05-08/d1-intelpolitics-kickoff.md`). Connection string is in env var `POSTGRES_URL` (sourced from `pg-creds` secret).
>
> **Extraction model:** `deepseek-r1:14b` (locked per Vadim's 2026-05-09 decision on §8 #2 of the kickoff plan — the reasoning-heavy variant wins on the statement-vs-decision classification accuracy that drives §1.4's "would I cite this?" bar; throughput cost is acceptable for D.1's volume).
>
> **Local LLM only.** Every LLM call in this pipeline (Aider's coding model, the extraction prompt, any future stall analysis) routes to Olares Ollama via the `ssh -N -L 11434:10.233.21.66:11434 olares` tunnel. **No `anthropic` / Claude SDK imports anywhere in the venture's code.** Use `httpx` (or stdlib `urllib`) for the Ollama HTTP call. The CI guard at `ventures/intelpolitics/.importlinter` enforces this — adding `anthropic` to the import graph fails CI per DR-25.
>
> **Patchright vs curl_cffi switch criterion:**
> - Default to `curl_cffi` (faster, cheaper). Use it for: government/parliament/manifesto static-asset CDNs (gov.uk, whitehouse.gov, congress.gov, hansard.parliament.uk, bundestag.de, parliament.it, europarl.europa.eu, state-of-the-union.ec.europa.eu, fratelli-italia.it, labour.org.uk, cdu.de).
> - Switch to `Patchright` when curl_cffi gets a 403 / 429 / Cloudflare challenge / empty body. Use it for: BBC, Guardian, FT, NYT, POLITICO, DW, governo.it Council-of-Ministers index. Do NOT use Patchright pre-emptively — verify failure first.
>
> **Pacing rule (SOP §1.6):** 3–5 s per request to the same host (use `tenacity` retry-with-backoff). Cap 200 reqs/hour/host. On 4xx, back off 5 minutes. Implement as a per-host token bucket, not a global sleep.
>
> **Error handling:**
> - 4xx soft block: log to `pg.scrape_errors`, back off, retry once after the 5-min cooldown, then surface to Builder if still failing.
> - 5xx server error: retry up to 3× with exponential backoff (1s → 5s → 15s).
> - Empty body / no match: log row to `pg.scrape_errors` with `kind='empty_body'`, do not retry; surface to Builder if >3 in a row from the same host (selector-hallucination indicator per SOP §1.4 stall criteria).
> - Postgres write failure: do NOT retry-and-pray; halt the run, write the failure mode to `aider-briefs/d1-error.md`, surface to Builder.
>
> **What you produce:**
> 1. `src/scraper/fetch.py` — Patchright + curl_cffi wrapper with the switch logic above.
> 2. `src/scraper/sources.py` — loads `sources.yaml`, returns iterator of (politician, url, kind, fetcher).
> 3. `src/extractor/extract.py` — calls Ollama `deepseek-r1:14b` with the extraction prompt skeleton in §4 of the kickoff plan; returns list of `{statement_or_decision, source_url, published_date, kind, confidence, raw_html}`. Uses `httpx` (or stdlib `urllib`); **no `anthropic` SDK** per DR-25.
> 4. `src/pipelines/d1_run.py` — the end-to-end runner; one source URL at a time; commits per-row to Postgres.
> 5. `tests/test_extract.py` — at least 3 unit tests with fixture HTML pinned (one official site, one parliament transcript, one news article).
> 6. `aider-briefs/d1-progress.md` — running progress log Aider updates each iteration with what it did, what worked, what failed.
>
> **Stop conditions (per session):** iteration cap 12; wall-clock soft 8 h; hard kill 12 h. Stall flags surfaced immediately to Builder (see §6 of the kickoff plan): >3 consecutive empty-body fetches from the same host, 5+ identical extraction outputs, any Postgres write failure.
>
> **Acceptance for D.1 EOD:** ≥10 inserted statement/decision rows in `pg.statements` (across any subset of politicians). Coverage gap is OK on D.1 — D.2 is the day to balance per-politician counts. Confidence floor: skip extraction if confidence < 0.6.

---

## Reference

- Full kickoff plan: `Vadim's Inbox/pilot-day-1-2026-05-08/d1-intelpolitics-kickoff.md`.
- Extraction prompt template: §4 of the same plan.
- DDL: `ventures/intelpolitics/k3s/migrations/001_statements.sql`.
- Source inventory: `ventures/intelpolitics/sources.yaml`.
- DR-24 (Builder runs Aider): `framework/BKM/dr-default-autonomy-24-2026-05-09.md`.
- DR-25 (local-LLM-only invariant): referenced in the constraints above; venture-level enforcement at `.importlinter`.
- SOP: `framework/BKM/SOP/sop-olares-integration-2026-05-08.md`.
