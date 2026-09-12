"""Composition root: wire fetch → parse → dedupe → render → write for one run.

`run` is given an `http` callable (the only port to the network) so it can be
driven from saved fixtures in tests and from a real fetcher in production.
"""

import json
import logging
from collections.abc import Callable
from datetime import date, timedelta
from html import escape
from importlib.resources import files
from pathlib import Path

from .config import Config
from .dedupe import canonical_url, dedupe
from .models import Article, Source
from .rss import render_rss
from .tldr import feed_url, parse_feed, parse_issue

Http = Callable[[str], str]

log = logging.getLogger(__name__)


def run(config: Config, http: Http, today: date | None = None) -> list[Article]:
    """Return the deduped articles from every source's issues inside the window.

    Newest issue first; within a day, sources keep their feeds.toml order.
    A source or issue that fails to fetch or parse is logged and skipped so
    one bad page never blocks the rest.
    """
    cutoff = (today or date.today()) - timedelta(days=config.window_days)
    articles: list[Article] = []
    for source in config.sources:
        articles += _articles_for_source(source, http, cutoff)
    kept = dedupe(articles)
    log.info("%d articles, %d after dedupe and sponsor removal", len(articles), len(kept))
    return sorted(kept, key=lambda a: a.issue_date, reverse=True)


def _articles_for_source(source: Source, http: Http, cutoff: date) -> list[Article]:
    try:
        issues = parse_feed(http(feed_url(source)), source)
    except Exception as error:  # noqa: BLE001 - isolate one bad source
        log.warning("%s: skipping source, feed failed: %s", source.slug, error)
        return []

    articles: list[Article] = []
    for issue in issues:
        if issue.date < cutoff:
            continue
        try:
            articles += parse_issue(http(issue.url), issue)
        except Exception as error:  # noqa: BLE001 - isolate one bad issue
            log.warning("%s: skipping issue %s: %s", source.slug, issue.url, error)
    log.info("%s: %d issues in window, %d articles", source.slug, len([i for i in issues if i.date >= cutoff]), len(articles))
    return articles


def write_outputs(articles: list[Article], config: Config, out_dir: Path) -> list[Path]:
    """Write feeds, article data, the index, and its icon; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    feeds = _feed_definitions(config)
    written = []
    for filename, title, description, members in feeds:
        selected = [a for a in articles if members is None or a.source.slug in members]
        path = out_dir / filename
        path.write_text(render_rss(selected, title, description, config.site_url, f"{config.site_url}/{filename}"), encoding="utf-8")
        written.append(path)

    json_path = out_dir / "articles.json"
    json_path.write_text(json.dumps([_as_json(a) for a in articles], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(json_path)

    index_path = out_dir / "index.html"
    index_path.write_text(_index_html(feeds, config.site_url), encoding="utf-8")
    written.append(index_path)
    icon_path = out_dir / "icon.png"
    icon_path.write_bytes(files("tldr_rss").joinpath("assets/icon.png").read_bytes())
    written.append(icon_path)
    return written


FeedDefinition = tuple[str, str, str, frozenset[str] | None]  # filename, title, description, member slugs


def _feed_definitions(config: Config) -> list[FeedDefinition]:
    feeds: list[FeedDefinition] = [
        ("all.xml", "TLDR, all newsletters", "Every TLDR newsletter, one item per article, duplicates and sponsors removed", None)
    ]
    for source in config.sources:
        feeds.append((f"{source.slug}.xml", source.name, f"{source.name}, one item per article", frozenset({source.slug})))
    names = {s.slug: s.name for s in config.sources}
    for bundle, members in sorted(config.bundles.items()):
        listed = ", ".join(names[m] for m in members)
        label = " ".join(word.upper() if word.lower() in {"ai", "ml"} else
                         word.lower() if word.lower() == "and" else word.capitalize()
                         for word in bundle.replace("_", "-").split("-"))
        feeds.append((f"{bundle}.xml", f"TLDR {label}", f"{listed}, one item per article, duplicates removed", frozenset(members)))
    return feeds


def _as_json(article: Article) -> dict:
    return {
        "title": article.title,
        "url": canonical_url(article.url),
        "source": article.source.slug,
        "section": article.section,
        "date": article.issue_date.isoformat(),
        "issue_url": article.issue_url,
        "blurb_html": article.blurb_html,
    }


def _index_html(feeds: list[FeedDefinition], site_url: str) -> str:
    rows = "\n".join(
        f'  <li><a href="{escape(filename)}">{escape(filename)}</a> — {escape(description)}</li>'
        for filename, _, description, _ in feeds
    )
    return (
        "<!doctype html>\n<meta charset=\"utf-8\">\n<title>TLDR RSS feeds</title>\n"
        '<link rel="icon" type="image/png" sizes="144x144" href="icon.png">\n'
        "<h1>TLDR RSS feeds</h1>\n<p>One item per article, duplicates and sponsors removed. "
        f"Subscribe to any of these in your reader; <a href=\"articles.json\">articles.json</a> has the raw data.</p>\n"
        f"<ul>\n{rows}\n</ul>\n"
    )
