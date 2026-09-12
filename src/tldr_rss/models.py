"""Plain data passed between pipeline stages. All types are immutable."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """One TLDR newsletter, e.g. slug="ai", name="TLDR AI"."""

    slug: str
    name: str
