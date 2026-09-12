"""Plain data passed between pipeline stages. All types are immutable."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Source:
    """One TLDR newsletter, e.g. slug="ai", name="TLDR AI"."""

    slug: str
    name: str


@dataclass(frozen=True)
class Issue:
    """One published newsletter issue, e.g. https://tldr.tech/ai/2026-09-11."""

    source: Source
    date: date
    url: str
    title: str


@dataclass(frozen=True)
class Article:
    """One story inside an issue. `url` is exactly as TLDR linked it."""

    title: str
    url: str
    blurb_html: str
    section: str
    source: Source
    issue_date: date
    issue_url: str
    is_sponsor: bool
