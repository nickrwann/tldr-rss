from pathlib import Path

import pytest

from tldr_rss.config import load_config, parse_config

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_repo_feeds_toml_loads_all_sources():
    config = load_config(REPO_ROOT / "feeds.toml")
    slugs = [s.slug for s in config.sources]
    assert slugs[0] == "tech"
    assert len(slugs) == 13
    assert config.window_days == 14
    assert config.site_url == "https://nickrwann.github.io/tldr-rss"
    assert set(config.bundles["tech-engineering-and-security"]) <= set(slugs)


def test_minimal_config_uses_defaults():
    config = parse_config({"site_url": "https://x.test/", "sources": [{"slug": "a", "name": "A"}]})
    assert config.window_days == 14
    assert config.bundles == {}
    assert config.site_url == "https://x.test"


def test_bundle_with_unknown_source_is_rejected():
    with pytest.raises(ValueError, match="unknown source"):
        parse_config({"site_url": "u", "sources": [{"slug": "a", "name": "A"}], "bundles": {"b": ["a", "zzz"]}})


def test_bundle_name_cannot_shadow_source_or_all():
    base = {"site_url": "u", "sources": [{"slug": "a", "name": "A"}]}
    with pytest.raises(ValueError, match="clashes"):
        parse_config({**base, "bundles": {"a": ["a"]}})
    with pytest.raises(ValueError, match="clashes"):
        parse_config({**base, "bundles": {"all": ["a"]}})


def test_duplicate_slugs_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        parse_config({"site_url": "u", "sources": [{"slug": "a", "name": "A"}, {"slug": "a", "name": "B"}]})
