"""Everything that depends on how tldr.tech is laid out.

This is the anti-corruption layer: feed URLs, feed XML shape, and issue HTML
selectors live here and nowhere else. All functions are pure.
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime

from .models import Issue, Source

FEED_URL = "https://tldr.tech/api/rss/{slug}"


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
