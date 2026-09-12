import json
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from tldr_rss.config import parse_config
from tldr_rss.pipeline import run, write_outputs

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 9, 12)

CONFIG = parse_config({
    "site_url": "https://x.test/tldr-rss",
    "window_days": 2,
    "sources": [{"slug": "tech", "name": "TLDR Tech"}, {"slug": "ai", "name": "TLDR AI"}, {"slug": "devops", "name": "TLDR DevOps"}],
    "bundles": {"ml": ["ai"]},
})


def _feed_for(slug: str) -> str:
    """Rewrite the saved tech feed so every source has the same issue dates."""
    return (FIXTURES / "feed-tech.xml").read_text(encoding="utf-8").replace("tldr.tech/tech/", f"tldr.tech/{slug}/")


def fake_http(url: str) -> str:
    if url.startswith("https://tldr.tech/api/rss/"):
        return _feed_for(url.rsplit("/", 1)[1])
    slug, day = url.removeprefix("https://tldr.tech/").split("/")
    page = FIXTURES / f"issue-{slug}-{day}.html"
    if not page.exists():
        raise FileNotFoundError(url)  # only 2026-09-11 is saved; the window must exclude the rest
    return page.read_text(encoding="utf-8")


def test_run_fetches_only_issues_inside_the_window_and_dedupes_across_sources():
    articles = run(CONFIG, fake_http, today=TODAY)
    assert {a.issue_date for a in articles} == {date(2026, 9, 11)}
    assert not any(a.is_sponsor for a in articles)
    urls = [a.url.split("?")[0].rstrip("/") for a in articles]
    assert urls.count("https://openai.com/index/introducing-the-agents-api") == 1
    assert len(articles) == 40  # 52 parsed - 9 sponsors - 3 duplicates


def test_run_skips_a_source_whose_feed_fails(caplog):
    def flaky(url: str) -> str:
        if url == "https://tldr.tech/api/rss/ai":
            raise ConnectionError("boom")
        return fake_http(url)

    articles = run(CONFIG, flaky, today=TODAY)
    assert {a.source.slug for a in articles} == {"tech", "devops"}
    assert "ai: skipping source" in caplog.text


def test_write_outputs_produces_all_per_source_bundle_json_and_index(tmp_path):
    articles = run(CONFIG, fake_http, today=TODAY)
    written = write_outputs(articles, CONFIG, tmp_path)
    assert {p.name for p in written} == {"all.xml", "tech.xml", "ai.xml", "devops.xml", "ml.xml", "articles.json", "index.html"}

    def items(name):
        return ET.parse(tmp_path / name).getroot().findall("channel/item")

    assert len(items("all.xml")) == 40
    assert len(items("tech.xml")) + len(items("ai.xml")) + len(items("devops.xml")) == 40
    assert len(items("ml.xml")) == len(items("ai.xml"))
    assert ET.parse(tmp_path / "all.xml").getroot().find("channel/{http://www.w3.org/2005/Atom}link").get("href") == "https://x.test/tldr-rss/all.xml"

    data = json.loads((tmp_path / "articles.json").read_text(encoding="utf-8"))
    assert len(data) == 40
    assert data[0].keys() == {"title", "url", "source", "section", "date", "issue_url", "blurb_html"}
    assert not any("utm_" in d["url"] for d in data)

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'href="all.xml"' in index and 'href="ml.xml"' in index
