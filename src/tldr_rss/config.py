"""Load feeds.toml into a Config. This is the only place TOML is read."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .models import Source

DEFAULT_WINDOW_DAYS = 14


@dataclass(frozen=True)
class Config:
    """Everything a run needs. `sources` order is the dedupe priority."""

    site_url: str
    sources: tuple[Source, ...]
    bundles: dict[str, tuple[str, ...]] = field(default_factory=dict)
    window_days: int = DEFAULT_WINDOW_DAYS


def load_config(path: Path) -> Config:
    """Return the Config described by the TOML file at `path`."""
    with path.open("rb") as f:
        return parse_config(tomllib.load(f))


def parse_config(data: dict) -> Config:
    """Return a Config from already-parsed TOML data, validating references."""
    sources = tuple(Source(slug=s["slug"], name=s["name"]) for s in data["sources"])
    if not sources:
        raise ValueError("feeds.toml must list at least one [[sources]] entry")

    known = {s.slug for s in sources}
    duplicates = [s.slug for s in sources if sum(1 for t in sources if t.slug == s.slug) > 1]
    if duplicates:
        raise ValueError(f"duplicate source slug(s): {sorted(set(duplicates))}")

    bundles: dict[str, tuple[str, ...]] = {}
    for name, members in data.get("bundles", {}).items():
        unknown = [m for m in members if m not in known]
        if unknown:
            raise ValueError(f"bundle {name!r} references unknown source(s): {unknown}")
        if name in known or name == "all":
            raise ValueError(f"bundle name {name!r} clashes with a source or with 'all'")
        bundles[name] = tuple(members)

    return Config(
        site_url=data["site_url"].rstrip("/"),
        sources=sources,
        bundles=bundles,
        window_days=int(data.get("window_days", DEFAULT_WINDOW_DAYS)),
    )
