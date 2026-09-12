from datetime import date
from pathlib import Path

from tldr_rss.models import Source
from tldr_rss.tldr import feed_url, parse_feed

FIXTURES = Path(__file__).parent / "fixtures"
TECH = Source(slug="tech", name="TLDR Tech")


def test_feed_url_uses_slug():
    assert feed_url(Source(slug="devops", name="x")) == "https://tldr.tech/api/rss/devops"


def test_parse_feed_returns_one_issue_per_item():
    issues = parse_feed((FIXTURES / "feed-tech.xml").read_text(encoding="utf-8"), TECH)
    assert len(issues) == 20
    first = issues[0]
    assert first.source is TECH
    assert first.url == "https://tldr.tech/tech/2026-09-11"
    assert first.date == date(2026, 9, 11)
    assert first.title.startswith("OpenAI Agents API")
    assert issues[-1].date < first.date


def test_parse_feed_skips_items_without_link_or_date():
    xml = """<rss><channel>
      <item><title>no link</title><pubDate>Fri, 11 Sep 2026 00:00:00 GMT</pubDate></item>
      <item><title>no date</title><link>https://tldr.tech/tech/2026-09-10</link></item>
      <item><title>ok</title><link>https://tldr.tech/tech/2026-09-09</link><pubDate>Wed, 09 Sep 2026 00:00:00 GMT</pubDate></item>
    </channel></rss>"""
    issues = parse_feed(xml, TECH)
    assert [i.title for i in issues] == ["ok"]
