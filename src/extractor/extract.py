"""Ollama-backed extractor.

Calls Olares Ollama (via the SSH tunnel at http://127.0.0.1:11434) using the
deepseek-r1:14b reasoning model with strict JSON output. Returns a list of
extraction dicts shaped for the pg.statements schema.

DR-25: only `httpx` (HTTP) is used to call the model. No `anthropic`, no
`openai`, no Claude SDK. The .importlinter contract enforces this at lint time.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:14b")
OLLAMA_TIMEOUT_SEC = float(os.environ.get("OLLAMA_TIMEOUT_SEC", "180"))

# Per kickoff §4.4 — anything below this is logged as extract_low_confidence
# and skipped from the insert path.
CONFIDENCE_FLOOR = 0.6

# Per kickoff §4.1 — keep page_text under ~6000 chars so the prompt + output
# stays inside the 8192 num_ctx window.
PAGE_TEXT_TRUNCATE_CHARS = 6000


@dataclass
class Extraction:
    statement_or_decision: str
    kind: str                       # 'statement' | 'decision'
    published_date: date | None
    confidence: float
    raw_html_excerpt: str = ""      # first ~2KB of raw_html for audit
    politician: str = ""
    source_url: str = ""

    def as_db_row(self) -> dict[str, Any]:
        return {
            "politician": self.politician,
            "statement_or_decision": self.statement_or_decision,
            "source_url": self.source_url,
            "published_date": self.published_date,
            "kind": self.kind,
            "confidence": self.confidence,
            "raw_html": self.raw_html_excerpt,
        }


@dataclass
class ExtractionResult:
    extractions: list[Extraction] = field(default_factory=list)
    skipped_low_confidence: list[dict[str, Any]] = field(default_factory=list)
    raw_response: str = ""
    error: str | None = None


# --------------------------------------------------------------------------- #
# HTML → plain text                                                           #
# --------------------------------------------------------------------------- #

def html_to_text(html: str, *, truncate: int = PAGE_TEXT_TRUNCATE_CHARS) -> str:
    """BeautifulSoup → plain text, biased toward content regions.

    Strategy:
      1. Drop nav/footer/aside/script/style and common chrome containers.
      2. If a <main>, <article>, or [role=main] element exists, use only that.
      3. Otherwise fall back to the body.
      4. Normalise whitespace and truncate.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer",
                     "aside", "header", "form", "iframe"]):
        tag.decompose()
    # Drop common cookie-banner / nav containers by class hint.
    for sel in [
        "[role='navigation']", "[role='banner']", "[role='contentinfo']",
        ".cookie", ".cookies", ".nav", ".navigation", ".menu", ".sidebar",
        ".breadcrumb", ".breadcrumbs", ".global-header", ".global-footer",
        ".gem-c-cookie-banner", ".gem-c-layout-super-navigation-header",
    ]:
        for el in soup.select(sel):
            el.decompose()

    # Prefer main / article regions.
    container = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )
    text = container.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > truncate:
        text = text[:truncate]
    return text


# --------------------------------------------------------------------------- #
# Prompt                                                                      #
# --------------------------------------------------------------------------- #

EXTRACTION_PROMPT_TEMPLATE = """You extract political statements and decisions from a web page.

POLITICIAN: {politician}
SOURCE URL: {source_url}

PAGE TEXT:
\"\"\"
{page_text}
\"\"\"

INSTRUCTIONS:
1. Read the page text above carefully.
2. Identify discrete claims attributable to {politician}. Acceptable forms:
   a. Direct quotes: "..." or '...' followed by attribution to {politician}.
   b. Reported speech with explicit attribution: "{politician} said/announced/pledged/argued/promised that ...".
   c. Headlines or article titles that explicitly attribute a claim to {politician} (e.g. "{politician}: we must ...").
   d. Voting records, signed legislation, executive orders attributed to {politician}.
3. For each accepted claim, output:
   - "statement_or_decision": the verbatim or near-verbatim claim, 30 to 400 characters. Preserve the original wording where possible; if it is reported speech, keep the full reported clause.
   - "kind": "statement" if it is a verbal claim, position, pledge, or opinion; "decision" if it is a vote, signed-off policy, executive action, or formal directive.
   - "published_date": ISO 8601 date (YYYY-MM-DD) if explicitly present in the page text near the claim; null otherwise. Do NOT infer.
   - "confidence": a number in [0, 1] for how confident you are this is genuinely attributable to {politician} (not someone else, not editorial framing).
4. Use confidence ≥ 0.6 only when attribution is explicit. Use < 0.6 when the page only mentions {politician} but does not attribute a specific claim to them.
5. Skip claims with confidence < 0.6.
6. If the page contains no attributable claims, return an empty array.
7. AIM for 3-10 extractions per page when the content supports it; do not artificially limit yourself to one per page.

OUTPUT (strict JSON, no markdown):
{{
  "extractions": [
    {{
      "statement_or_decision": "...",
      "kind": "statement" | "decision",
      "published_date": "YYYY-MM-DD" | null,
      "confidence": 0.0 to 1.0
    }}
  ]
}}
"""


def build_prompt(politician: str, source_url: str, page_text: str) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(
        politician=politician,
        source_url=source_url,
        page_text=page_text,
    )


# --------------------------------------------------------------------------- #
# Ollama call                                                                 #
# --------------------------------------------------------------------------- #

def call_ollama(prompt: str, *, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL) -> str:
    """POST /api/generate; return the model's `response` string.

    We pass `format='json'` so Ollama enforces JSON-mode at the sampler level.
    """
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    with httpx.Client(timeout=OLLAMA_TIMEOUT_SEC) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return data.get("response", "")


# --------------------------------------------------------------------------- #
# Response parsing                                                            #
# --------------------------------------------------------------------------- #

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_think_blocks(s: str) -> str:
    """deepseek-r1 may emit <think>...</think> reasoning before the JSON.
    Strip those before json-parsing.
    """
    return _THINK_BLOCK.sub("", s).strip()


def _coerce_json(s: str) -> dict[str, Any]:
    """Tolerate model preambles, code-fences, trailing text — extract the
    largest top-level JSON object in `s`.
    """
    s = _strip_think_blocks(s)
    s = s.strip()
    # Strip code fences if any.
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Find first { and matching closing brace by depth-walk.
        start = s.find("{")
        if start == -1:
            raise
        depth = 0
        for i in range(start, len(s)):
            c = s[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(s[start : i + 1])
        raise


def _parse_published_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s or s.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_extractions(
    raw_response: str,
    *,
    politician: str,
    source_url: str,
    raw_html_excerpt: str = "",
) -> ExtractionResult:
    """Parse Ollama's JSON response into Extraction objects + a low-confidence
    sidelist for `scrape_errors` logging.
    """
    out = ExtractionResult(raw_response=raw_response)
    try:
        doc = _coerce_json(raw_response)
    except Exception as e:
        out.error = f"json_parse_failure: {type(e).__name__}: {e}"
        return out

    items = doc.get("extractions") or []
    if not isinstance(items, list):
        out.error = f"extractions field is not a list: {type(items).__name__}"
        return out

    for item in items:
        if not isinstance(item, dict):
            continue
        text = (item.get("statement_or_decision") or "").strip()
        if not text or len(text) < 30 or len(text) > 400:
            continue
        kind_val = (item.get("kind") or "statement").strip().lower()
        if kind_val not in {"statement", "decision"}:
            kind_val = "statement"
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        published = _parse_published_date(item.get("published_date"))

        if confidence < CONFIDENCE_FLOOR:
            out.skipped_low_confidence.append(
                {
                    "statement_or_decision": text,
                    "confidence": confidence,
                    "politician": politician,
                    "source_url": source_url,
                }
            )
            continue

        out.extractions.append(
            Extraction(
                statement_or_decision=text,
                kind=kind_val,
                published_date=published,
                confidence=confidence,
                raw_html_excerpt=raw_html_excerpt[:2048],
                politician=politician,
                source_url=source_url,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# High-level entry                                                            #
# --------------------------------------------------------------------------- #

def extract_from_html(
    html: str,
    *,
    politician: str,
    source_url: str,
    model: str = OLLAMA_MODEL,
    base_url: str = OLLAMA_BASE_URL,
) -> ExtractionResult:
    """Convenience: html → text → prompt → Ollama → parsed extractions."""
    page_text = html_to_text(html)
    if not page_text:
        return ExtractionResult(error="empty_page_text")
    prompt = build_prompt(politician=politician, source_url=source_url, page_text=page_text)
    try:
        raw = call_ollama(prompt, model=model, base_url=base_url)
    except Exception as e:
        return ExtractionResult(error=f"ollama_call_failure: {type(e).__name__}: {e}")
    return parse_extractions(
        raw,
        politician=politician,
        source_url=source_url,
        raw_html_excerpt=html,
    )
