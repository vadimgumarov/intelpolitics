"""Loads sources.yaml and yields scrape-target rows.

Reference-only entries are filtered out by default for the D.1 pipeline.
Schema documented at the top of ventures/intelpolitics/sources.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlparse

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES_YAML = REPO_ROOT / "sources.yaml"


@dataclass(frozen=True)
class Source:
    politician_name: str
    politician_slug: str
    politician_country: str
    politician_role: str
    url: str
    kind: str          # 'scrape-target' | 'reference-only'
    klass: str         # 'official' | 'parliament' | 'manifesto' | 'press'
    fetcher: str       # 'curl_cffi' | 'patchright'
    note: str

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc.lower()


def load_sources(
    path: Path | None = None,
    *,
    include_reference_only: bool = False,
    only_politicians: Iterable[str] | None = None,
) -> list[Source]:
    """Load sources.yaml and return a flat list of Source rows.

    `only_politicians`: iterable of slugs to include (None = all).
    """
    p = Path(path) if path else DEFAULT_SOURCES_YAML
    with p.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    if doc.get("version") != 1:
        raise ValueError(f"unsupported sources.yaml version: {doc.get('version')}")

    wanted = set(only_politicians) if only_politicians else None
    out: list[Source] = []
    for politician in doc.get("politicians", []):
        slug = politician["slug"]
        if wanted and slug not in wanted:
            continue
        for src in politician.get("sources", []):
            if not include_reference_only and src.get("kind") == "reference-only":
                continue
            out.append(
                Source(
                    politician_name=politician["name"],
                    politician_slug=slug,
                    politician_country=politician["country"],
                    politician_role=politician["role"],
                    url=src["url"],
                    kind=src["kind"],
                    klass=src["class"],
                    fetcher=src.get("fetcher", "curl_cffi"),
                    note=src.get("note", ""),
                )
            )
    return out


def iter_sources(*args, **kwargs) -> Iterator[Source]:
    """Convenience iterator over load_sources()."""
    yield from load_sources(*args, **kwargs)
