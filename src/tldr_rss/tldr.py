"""Everything that depends on how tldr.tech is laid out.

This is the anti-corruption layer: feed URLs, feed XML shape, and issue HTML
selectors live here and nowhere else. All functions are pure.
"""

import html
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

from .models import Article, Issue, Source

FEED_URL = "https://tldr.tech/api/rss/{slug}"

# Editorial links are tagged utm_source=tldr<newsletter> (tldrai, tldrdevops...).
# Sponsor links are tagged plain utm_source=tldr or TLDR.
SPONSOR_UTM_SOURCE = "tldr"
SPONSOR_TITLE_SUFFIX = "(sponsor)"


def feed_url(source: Source) -> str:
    """Return the RSS feed URL for a source."""
    return FEED_URL.format(slug=source.slug)


def parse_feed(xml_text: str, source: Source) -> list[Issue]:
    """Return the issues listed in a TLDR feed, newest first as published.

    TLDR feed items carry only a title, a link to the issue page, and a
    pubDate at midnight UTC on the issue date. They have no body.
    """
    channel = ET.fromstring(xml_text).find("channel")
    if channel is None:
        raise ValueError(f"{source.slug}: feed has no <channel>")

    issues = []
    for item in channel.findall("item"):
        link = _text(item, "link")
        pub_date = _text(item, "pubDate")
        if not link or not pub_date:
            continue
        issues.append(
            Issue(
                source=source,
                date=_issue_date(pub_date),
                url=link,
                title=_text(item, "title").strip(),
            )
        )
    return issues


def _text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return (child.text or "") if child is not None else ""


def _issue_date(pub_date: str) -> date:
    parsed: datetime = parsedate_to_datetime(pub_date)
    return parsed.date()


def parse_issue(html_text: str, issue: Issue) -> list[Article]:
    """Return every story on an issue page, in page order.

    An issue page is a series of <section>s, each with a <header><h3> naming
    the section and one <article> per story: an <a> wrapping the <h3> title,
    then a <div class="newsletter-html"> blurb.
    """
    doc = BeautifulSoup(html_text, "html.parser")
    articles = []
    for section in doc.find_all("section"):
        section_name = _section_name(section)
        for node in section.find_all("article"):
            article = _parse_article(node, section_name, issue)
            if article is not None:
                articles.append(article)
    return articles


def _section_name(section: Tag) -> str:
    header = section.find("header")
    heading = header.find("h3") if header else None
    return heading.get_text(strip=True) if heading else ""


def _parse_article(node: Tag, section: str, issue: Issue) -> Article | None:
    link = node.find("a", href=True)
    heading = link.find("h3") if link else None
    if link is None or heading is None:
        return None
    title = heading.get_text(strip=True)
    # TLDR double-escapes ampersands in hrefs, so one more unescape is needed.
    url = html.unescape(link["href"])
    blurb = node.find("div", class_="newsletter-html")
    return Article(
        title=title,
        url=url,
        blurb_html=blurb.decode_contents().strip() if blurb else "",
        section=section,
        source=issue.source,
        issue_date=issue.date,
        issue_url=issue.url,
        is_sponsor=_is_sponsor(title, url),
    )


def _is_sponsor(title: str, url: str) -> bool:
    if title.lower().endswith(SPONSOR_TITLE_SUFFIX):
        return True
    utm_source = parse_qs(urlsplit(url).query).get("utm_source", [""])[0]
    return utm_source.lower() == SPONSOR_UTM_SOURCE
