from datetime import date
from pathlib import Path

import pytest

from tldr_rss.models import Article, Issue, Source
from tldr_rss.tldr import feed_url, parse_feed, parse_issue

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


def _issue(slug: str) -> Issue:
    return Issue(source=Source(slug=slug, name=f"TLDR {slug}"), date=date(2026, 9, 11),
                 url=f"https://tldr.tech/{slug}/2026-09-11", title="")


def _articles(slug: str) -> list[Article]:
    return parse_issue((FIXTURES / f"issue-{slug}-2026-09-11.html").read_text(encoding="utf-8"), _issue(slug))


@pytest.mark.parametrize("slug,total,sponsors", [("tech", 17, 3), ("ai", 20, 3), ("devops", 15, 3), ("hardware", 14, 0)])
def test_parse_issue_finds_every_story_and_flags_sponsors(slug, total, sponsors):
    articles = _articles(slug)
    assert len(articles) == total
    assert sum(a.is_sponsor for a in articles) == sponsors


def test_parse_issue_reads_title_url_section_and_blurb():
    story = _articles("tech")[1]
    assert story.title == "Introducing the Agents API (5 minute read)"
    assert story.url == "https://openai.com/index/introducing-the-agents-api/?utm_source=tldrnewsletter"
    assert story.section == "Big Tech & Startups"
    assert story.blurb_html.startswith("OpenAI's Agents API is now in public beta.")
    assert story.source.slug == "tech"
    assert story.issue_date == date(2026, 9, 11)
    assert story.issue_url == "https://tldr.tech/tech/2026-09-11"
    assert not story.is_sponsor


def test_parse_issue_unescapes_double_encoded_hrefs():
    sponsor = next(a for a in _articles("tech") if a.title.startswith("Your buyers ask AI"))
    assert "&amp;" not in sponsor.url
    assert sponsor.url == "https://ahrefs.com/brand-radar?utm_source=tldr&utm_medium=newsletter&utm_campaign=partnerships"
    assert sponsor.is_sponsor


def test_sponsor_detected_by_utm_source_even_without_title_suffix():
    issue = _issue("tech")
    page = """<section><header><h3>Quick Links</h3></header>
      <article><a href="https://x.test/?utm_source=TLDR&utm_medium=newsletter"><h3>Buy stuff</h3></a><div class="newsletter-html">ad</div></article>
      <article><a href="https://y.test/?utm_source=tldrnewsletter"><h3>Real story (3 minute read)</h3></a><div class="newsletter-html">news</div></article>
    </section>"""
    flags = [(a.title, a.is_sponsor) for a in parse_issue(page, issue)]
    assert flags == [("Buy stuff", True), ("Real story (3 minute read)", False)]


def test_sections_follow_page_order():
    sections = []
    for a in _articles("tech"):
        if a.section not in sections:
            sections.append(a.section)
    assert sections == ["", "Big Tech & Startups", "Science & Futuristic Technology",
                        "Programming, Design & Data Science", "Miscellaneous", "Quick Links"]
