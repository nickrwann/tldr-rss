import xml.etree.ElementTree as ET
from datetime import date

from tldr_rss.models import Article, Source
from tldr_rss.rss import render_rss

TECH = Source("tech", "TLDR Tech")


def _article(**overrides) -> Article:
    fields = dict(
        title="Introducing the Agents API (5 minute read)",
        url="https://www.openai.com/index/introducing-the-agents-api/?utm_source=tldrnewsletter",
        blurb_html="OpenAI's Agents API is now in <b>public beta</b>.",
        section="Big Tech & Startups",
        source=TECH,
        issue_date=date(2026, 9, 11),
        issue_url="https://tldr.tech/tech/2026-09-11",
        is_sponsor=False,
    )
    return Article(**{**fields, **overrides})


def _render(articles):
    return render_rss(articles, "TLDR, deduped", "All TLDR newsletters, one item per article",
                      "https://x.test/tldr-rss", "https://x.test/tldr-rss/all.xml")


def test_empty_feed_is_valid_rss_with_channel_metadata():
    root = ET.fromstring(_render([]))
    channel = root.find("channel")
    assert root.tag == "rss" and root.get("version") == "2.0"
    assert channel.findtext("title") == "TLDR, deduped"
    assert channel.findtext("link") == "https://x.test/tldr-rss"
    assert channel.find("{http://www.w3.org/2005/Atom}link").get("href") == "https://x.test/tldr-rss/all.xml"
    assert channel.findall("item") == []


def test_item_uses_canonical_url_for_link_and_guid():
    item = ET.fromstring(_render([_article()])).find("channel/item")
    assert item.findtext("title") == "Introducing the Agents API (5 minute read)"
    assert item.findtext("link") == "https://openai.com/index/introducing-the-agents-api"
    assert item.findtext("guid") == "https://openai.com/index/introducing-the-agents-api"
    assert item.find("guid").get("isPermaLink") == "true"
    assert item.findtext("pubDate") == "Fri, 11 Sep 2026 00:00:00 +0000"


def test_item_description_keeps_blurb_html_and_adds_footer():
    item = ET.fromstring(_render([_article()])).find("channel/item")
    description = item.findtext("description")
    assert description.startswith("OpenAI's Agents API is now in <b>public beta</b>.")
    assert '<a href="https://tldr.tech/tech/2026-09-11">TLDR Tech · Big Tech & Startups</a>' in description
    assert "2026-09-11" in description


def test_item_categories_and_source_point_back_to_the_issue():
    item = ET.fromstring(_render([_article()])).find("channel/item")
    assert [c.text for c in item.findall("category")] == ["TLDR Tech", "Big Tech & Startups"]
    assert item.find("source").text == "TLDR Tech"
    assert item.find("source").get("url") == "https://tldr.tech/tech/2026-09-11"


def test_items_keep_given_order_and_empty_section_is_omitted():
    first = _article(url="https://a.test/1", section="")
    second = _article(url="https://a.test/2")
    items = ET.fromstring(_render([first, second])).findall("channel/item")
    assert [i.findtext("link") for i in items] == ["https://a.test/1", "https://a.test/2"]
    assert [c.text for c in items[0].findall("category")] == ["TLDR Tech"]


def test_output_is_deterministic():
    assert _render([_article()]) == _render([_article()])
