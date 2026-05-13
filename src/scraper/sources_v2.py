"""sources.v2.yaml loader + tier-enforcement validator.

Implements DR rules 1-5 from framework/BKM/dr-source-quality-canon-2026-05-12.md
+ addendum (subject_role + supporting_metadata).

The single public entry point is `validate_sources_v2(yaml_path)`. It is called
from every Phase C pipeline `__main__` BEFORE any strategy fires. Refusal is
fatal (SystemExit with non-zero) — startup-time error, never a runtime warning.

Refusal conditions (DR rule 2 + rule 3 + rule 4 + addendum):
    - Any politician's source missing `tier`.
    - Any politician's source missing `action_class`.
    - Any source with `tier=T1` and `access_pattern=scrape` (DR rule 3 API > HTML).
    - Any source with `action_class=lobby_filing` lacking `default_subject_role`
      AND no per-row parser override declared (per addendum constraint).
    - Any tier value not in {T1,T2,T3,T4}.
    - Any action_class value not in the 7-value enum.
    - Any subject_role value not in the 6-value enum.

Acceptance: when validation passes the loader returns a SourcesV2 object
exposing per-politician + per-source data shaped for the strategy layer.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)


# DR rule 2 + 4 + addendum enums (locked).
ALLOWED_TIERS = {"T1", "T2", "T3", "T4"}
ALLOWED_ACTION_CLASSES = {
    "vote", "bill_intro", "policy_publish", "lobby_filing",
    "statement_official", "talking_point", "supporting_metadata",
}
ALLOWED_SUBJECT_ROLES = {
    "lobbied", "lobbyist", "voter", "sponsor", "speaker", "author",
}
ALLOWED_ACCESS_PATTERNS = {"api", "bulk_download", "scrape"}


class TierEnforcementError(Exception):
    """Raised when sources.v2.yaml fails the DR rule 1-5 + addendum validation."""


@dataclass(frozen=True)
class SourceV2:
    id: str
    tier: str
    action_class: str
    politician_slug: str
    endpoint: str
    auth: str
    rate_limit: str
    refresh_cadence: str
    last_verified: str
    default_subject_role: str | None = None
    access_pattern: str = "api"
    auth_env_var: str | None = None
    gotchas: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PoliticianV2:
    slug: str
    geography: str
    member_ids: dict[str, Any]
    sources: list[SourceV2]


@dataclass(frozen=True)
class SourcesV2:
    version: int
    generated_at: str
    scope: str
    politicians: dict[str, PoliticianV2]

    def for_politician(self, slug: str) -> PoliticianV2:
        if slug not in self.politicians:
            raise KeyError(f"politician {slug!r} not in sources.v2.yaml")
        return self.politicians[slug]


def _infer_access_pattern(source_dict: dict[str, Any]) -> str:
    """Infer access pattern from endpoint + source metadata.

    Rule: a source is `api` if its endpoint is a structured-JSON / OpenAPI surface.
    `bulk_download` if it points to XLSX/CSV/XML files. `scrape` only if HTML
    parsing is the explicit access path. The infer is conservative — we treat
    parliament.uk API roots as `api`, the lobbying register quarterly XLSX as
    `bulk_download`, and anything else as `scrape` (which then trips DR rule 3
    if the tier is T1).
    """
    if "access_pattern" in source_dict:
        return source_dict["access_pattern"]
    endpoint = (source_dict.get("endpoint") or "").lower()
    # Explicit XLSX/CSV/XML extensions or "/uploads/" paths → bulk_download.
    if (".xlsx" in endpoint or ".csv" in endpoint or ".xml" in endpoint
            or "/uploads/" in endpoint or "/publications" in endpoint):
        return "bulk_download"
    # *-api.* hosts or /api/ paths → api.
    if "-api." in endpoint or "/api/" in endpoint or "api.parliament" in endpoint:
        return "api"
    # Endpoint pattern is XLSX template.
    pattern = (source_dict.get("endpoint_pattern") or "").lower()
    if ".xlsx" in pattern or ".csv" in pattern:
        return "bulk_download"
    # Default conservative: scrape (will trip rule 3 if tier=T1).
    return "scrape"


def _validate_one_source(src: dict[str, Any], politician_slug: str) -> SourceV2:
    sid = src.get("id")
    if not sid:
        raise TierEnforcementError(
            f"politician={politician_slug}: a source entry is missing `id`"
        )

    tier = src.get("tier")
    if tier is None:
        raise TierEnforcementError(
            f"source {sid}: missing `tier` field (DR rule 2 — tier-at-registration)"
        )
    if tier not in ALLOWED_TIERS:
        raise TierEnforcementError(
            f"source {sid}: tier={tier!r} not in {sorted(ALLOWED_TIERS)}"
        )

    action_class = src.get("action_class")
    if action_class is None:
        raise TierEnforcementError(
            f"source {sid}: missing `action_class` field (DR rule 4)"
        )
    if action_class not in ALLOWED_ACTION_CLASSES:
        raise TierEnforcementError(
            f"source {sid}: action_class={action_class!r} not in "
            f"{sorted(ALLOWED_ACTION_CLASSES)}"
        )

    default_subject_role = src.get("default_subject_role")
    if default_subject_role is not None and default_subject_role not in ALLOWED_SUBJECT_ROLES:
        raise TierEnforcementError(
            f"source {sid}: default_subject_role={default_subject_role!r} not in "
            f"{sorted(ALLOWED_SUBJECT_ROLES)}"
        )

    access_pattern = _infer_access_pattern(src)
    if access_pattern not in ALLOWED_ACCESS_PATTERNS:
        raise TierEnforcementError(
            f"source {sid}: inferred access_pattern={access_pattern!r} not in "
            f"{sorted(ALLOWED_ACCESS_PATTERNS)}"
        )

    # DR rule 3: T1 sources MUST NOT use HTML-selector scraping.
    if tier == "T1" and access_pattern == "scrape":
        raise TierEnforcementError(
            f"source {sid}: tier=T1 with access_pattern=scrape violates DR rule 3 "
            f"(API > HTML preference). T1 sources must use API or bulk_download."
        )

    # Addendum: lobby_filing requires subject_role (default or per-row override).
    # At validation time we only check that the source provides the default
    # (the per-row override path lives in the parser). A lobby_filing source
    # WITHOUT a default_subject_role would have no path to populate the field
    # and is rejected here.
    if action_class == "lobby_filing" and not default_subject_role:
        raise TierEnforcementError(
            f"source {sid}: action_class=lobby_filing requires `default_subject_role` "
            f"per addendum DR (lobby_filing rows MUST carry subject_role)."
        )

    return SourceV2(
        id=sid,
        tier=tier,
        action_class=action_class,
        politician_slug=politician_slug,
        endpoint=src.get("endpoint", ""),
        auth=src.get("auth", "none"),
        rate_limit=src.get("rate_limit", ""),
        refresh_cadence=src.get("refresh_cadence", ""),
        last_verified=str(src.get("last_verified", "")),
        default_subject_role=default_subject_role,
        access_pattern=access_pattern,
        auth_env_var=src.get("auth_env_var"),
        gotchas=list(src.get("gotchas") or []),
        extra={k: v for k, v in src.items() if k not in {
            "id", "tier", "action_class", "endpoint", "auth", "rate_limit",
            "refresh_cadence", "last_verified", "default_subject_role",
            "access_pattern", "auth_env_var", "gotchas",
        }},
    )


def validate_sources_v2(yaml_path: str | Path) -> SourcesV2:
    """Load + validate sources.v2.yaml. Raises TierEnforcementError on any
    rule 2/3/4 + addendum violation. Returns a SourcesV2 on success.

    This function MUST be called from every Phase C pipeline `__main__`
    BEFORE any strategy runs (DR rule 2: startup error, not runtime warning).
    """
    path = Path(yaml_path)
    if not path.exists():
        raise TierEnforcementError(f"sources.v2.yaml not found at {path}")

    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    if not isinstance(doc, dict):
        raise TierEnforcementError(f"{path}: root is not a mapping")

    version = doc.get("version")
    if version != 2:
        raise TierEnforcementError(
            f"{path}: version={version!r} (expected 2 for sources.v2)"
        )

    politicians_doc = doc.get("politicians", {})
    if not isinstance(politicians_doc, dict):
        raise TierEnforcementError(
            f"{path}: `politicians` must be a mapping of slug -> entry"
        )

    politicians_out: dict[str, PoliticianV2] = {}
    for slug, pol in politicians_doc.items():
        if not isinstance(pol, dict):
            raise TierEnforcementError(f"politician {slug}: entry is not a mapping")
        geography = pol.get("geography")
        if not geography:
            raise TierEnforcementError(f"politician {slug}: missing `geography`")
        member_ids = pol.get("member_ids", {}) or {}
        sources_in = pol.get("sources", []) or []
        if not sources_in:
            raise TierEnforcementError(f"politician {slug}: no sources defined")
        sources_out = [_validate_one_source(s, slug) for s in sources_in]
        politicians_out[slug] = PoliticianV2(
            slug=slug,
            geography=geography,
            member_ids=member_ids,
            sources=sources_out,
        )

    result = SourcesV2(
        version=version,
        generated_at=str(doc.get("generated_at", "")),
        scope=str(doc.get("scope", "")),
        politicians=politicians_out,
    )

    # Log validation pass (DR rule 2 requires this for audit).
    total_sources = sum(len(p.sources) for p in result.politicians.values())
    t1_sources = sum(
        1 for p in result.politicians.values() for s in p.sources if s.tier == "T1"
    )
    log.info(
        "sources.v2.yaml validation PASS: %d politicians, %d sources (%d T1), "
        "scope=%s, generated_at=%s",
        len(result.politicians), total_sources, t1_sources,
        result.scope, result.generated_at,
    )
    return result
