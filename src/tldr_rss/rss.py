"""Render Articles as an RSS 2.0 document. Pure: same input, same bytes."""

import xml.etree.ElementTree as ET
from datetime import datetime, time, timezone
from email.utils import format_datetime

from .dedupe import canonical_url
from .models import Article

ATOM_NS = "http://www.w3.org/2005/Atom"


def render_rss(articles: list[Article], title: str, description: str, site_url: str, self_url: str) -> str:
    """Return an RSS 2.0 document with one <item> per article, in the order given.

    guid and link are the canonical URL so readers keep read state across
    regenerations and never see TLDR's tracking parameters.
    """
    ET.register_namespace("atom", ATOM_NS)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    _child(channel, "title", title)
    _child(channel, "link", site_url)
    _child(channel, "description", description)
    _child(channel, "language", "en")
    ET.SubElement(channel, f"{{{ATOM_NS}}}link", href=self_url, rel="self", type="application/rss+xml")
    for article in articles:
        channel.append(_item(article))
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n"


def _item(article: Article) -> ET.Element:
    url = canonical_url(article.url)
    item = ET.Element("item")
    _child(item, "title", article.title)
    _child(item, "link", url)
    _child(item, "guid", url, isPermaLink="true")
    _child(item, "pubDate", _rfc822(article))
    _child(item, "description", _description(article))
    _child(item, "category", article.source.name)
    if article.section:
        _child(item, "category", article.section)
    _child(item, "source", article.source.name, url=article.issue_url)
    return item


def _description(article: Article) -> str:
    where = article.source.name + (f" · {article.section}" if article.section else "")
    footer = f'<p><small>From <a href="{article.issue_url}">{where}</a>, {article.issue_date.isoformat()}</small></p>'
    return f"{article.blurb_html}\n{footer}" if article.blurb_html else footer


def _rfc822(article: Article) -> str:
    return format_datetime(datetime.combine(article.issue_date, time(), tzinfo=timezone.utc))


def _child(parent: ET.Element, tag: str, text: str, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, tag, **attrs)
    element.text = text
    return element
