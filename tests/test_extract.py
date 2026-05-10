"""Unit tests for src.extractor.extract.

Three pinned fixtures (one official site, one parliament transcript, one news
article) verify the parsing + filtering layers without hitting the live Ollama
endpoint. Live-Ollama integration tests live elsewhere and are skipped without
the OLLAMA_BASE_URL env var.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.extractor.extract import (   # noqa: E402
    CONFIDENCE_FLOOR,
    build_prompt,
    extract_from_html,
    html_to_text,
    parse_extractions,
    _coerce_json,
    _strip_think_blocks,
)


FIXTURES = Path(__file__).parent / "fixtures"


# --------------------------------------------------------------------------- #
# html_to_text                                                                #
# --------------------------------------------------------------------------- #

def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_html_to_text_strips_scripts_and_normalises_whitespace_whitehouse():
    """Official site fixture: scripts/styles stripped; visible text retained."""
    html = _read_fixture("whitehouse_briefing.html")
    text = html_to_text(html)
    assert "Vance" in text
    assert "executive order" in text
    assert "<script" not in text
    assert "  " not in text                    # whitespace collapsed
    assert "American manufacturing" in text


def test_html_to_text_handles_parliament_transcript_hansard():
    """Parliament transcript fixture: speaker attribution + dates survive."""
    html = _read_fixture("hansard_starmer.html")
    text = html_to_text(html)
    assert "Starmer" in text
    assert "£28 billion" in text
    assert "Industrial Strategy Bill" in text


def test_html_to_text_handles_news_article_bbc():
    """News fixture: byline + quoted statements both survive."""
    html = _read_fixture("bbc_meloni.html")
    text = html_to_text(html)
    assert "Meloni" in text
    assert "Dublin Regulation" in text
    assert "Albania" in text


# --------------------------------------------------------------------------- #
# parse_extractions — mocked Ollama responses against the three fixtures      #
# --------------------------------------------------------------------------- #

def test_parse_extractions_official_site_vance_decision_and_statement():
    raw = json.dumps({
        "extractions": [
            {
                "statement_or_decision": "We will rebuild American manufacturing, and I will sign every executive order necessary to bring jobs back to the heartland",
                "kind": "statement",
                "published_date": "2026-04-22",
                "confidence": 0.92,
            },
            {
                "statement_or_decision": "The administration has approved a new tariff schedule on imported steel, effective May 1, 2026",
                "kind": "decision",
                "published_date": "2026-04-22",
                "confidence": 0.88,
            },
            {
                "statement_or_decision": "Some marginally relevant aside that we are unsure attributes",
                "kind": "statement",
                "published_date": None,
                "confidence": 0.45,            # below floor → goes to skipped list
            },
        ]
    })
    result = parse_extractions(
        raw,
        politician="vance",
        source_url="https://www.whitehouse.gov/example",
    )
    assert result.error is None
    assert len(result.extractions) == 2
    assert {e.kind for e in result.extractions} == {"statement", "decision"}
    assert all(e.confidence >= CONFIDENCE_FLOOR for e in result.extractions)
    assert all(e.published_date == date(2026, 4, 22) for e in result.extractions)
    assert len(result.skipped_low_confidence) == 1
    assert result.skipped_low_confidence[0]["confidence"] == pytest.approx(0.45)


def test_parse_extractions_parliament_starmer_vote_classified_as_decision():
    raw = json.dumps({
        "extractions": [
            {
                "statement_or_decision": "This Government will deliver on its promise to invest £28 billion in clean energy by the end of this Parliament",
                "kind": "statement",
                "published_date": "2026-03-15",
                "confidence": 0.9,
            },
            {
                "statement_or_decision": "The Prime Minister voted in favour of the Industrial Strategy Bill, second reading",
                "kind": "decision",
                "published_date": "2026-03-15",
                "confidence": 0.95,
            },
        ]
    })
    result = parse_extractions(
        raw,
        politician="starmer",
        source_url="https://hansard.parliament.uk/example",
    )
    assert result.error is None
    assert len(result.extractions) == 2
    decisions = [e for e in result.extractions if e.kind == "decision"]
    assert len(decisions) == 1
    assert "voted in favour" in decisions[0].statement_or_decision
    assert decisions[0].published_date == date(2026, 3, 15)


def test_parse_extractions_news_meloni_handles_deepseek_think_block_and_short_text_filter():
    """deepseek-r1 may emit <think> reasoning before JSON. Also: items with
    text <30 chars are filtered out by parse_extractions."""
    raw = (
        "<think>I need to identify Meloni's claims and skip the journalist's "
        "framing. Two clear claims here.</think>\n"
        + json.dumps({
            "extractions": [
                {
                    "statement_or_decision": "We will protect our borders and we will defend the dignity of every Italian",
                    "kind": "statement",
                    "published_date": "2026-04-30",
                    "confidence": 0.86,
                },
                {
                    "statement_or_decision": "I propose that the European Union urgently revisits the Dublin Regulation",
                    "kind": "statement",
                    "published_date": "2026-04-30",
                    "confidence": 0.83,
                },
                {
                    "statement_or_decision": "Too short.",   # <30 chars → filtered
                    "kind": "statement",
                    "published_date": None,
                    "confidence": 0.99,
                },
            ]
        })
    )
    result = parse_extractions(
        raw,
        politician="meloni",
        source_url="https://www.bbc.com/news/example",
    )
    assert result.error is None
    assert len(result.extractions) == 2
    texts = [e.statement_or_decision for e in result.extractions]
    assert any("Dublin Regulation" in t for t in texts)
    assert any("dignity of every Italian" in t for t in texts)
    # The <think> block must not survive into the parsed payload.
    assert all("think" not in t.lower() for t in texts)


# --------------------------------------------------------------------------- #
# Lower-level helpers                                                         #
# --------------------------------------------------------------------------- #

def test_strip_think_blocks_removes_reasoning_preamble():
    s = "<think>chain of thought here</think>\n{\"extractions\": []}"
    out = _strip_think_blocks(s)
    assert "think" not in out.lower() or "extractions" in out
    assert out.startswith("{")


def test_coerce_json_tolerates_code_fence_and_trailing_text():
    s = "```json\n{\"extractions\": []}\n```\nextra trailing chatter"
    doc = _coerce_json(s)
    assert doc == {"extractions": []}


def test_build_prompt_includes_required_fields():
    p = build_prompt(politician="meloni", source_url="https://example", page_text="HELLO")
    assert "POLITICIAN: meloni" in p
    assert "SOURCE URL: https://example" in p
    assert "HELLO" in p
    assert "strict JSON" in p


# --------------------------------------------------------------------------- #
# Live integration (skipped unless OLLAMA_LIVE=1)                             #
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    os.environ.get("OLLAMA_LIVE") != "1",
    reason="set OLLAMA_LIVE=1 (and ensure tunnel to Olares Ollama) to enable",
)
def test_live_extract_from_bbc_meloni_fixture():
    html = _read_fixture("bbc_meloni.html")
    er = extract_from_html(html, politician="meloni", source_url="https://www.bbc.com/test")
    assert er.error is None, er.error
    # The model should find at least one citable Meloni claim from this fixture.
    assert len(er.extractions) >= 1
