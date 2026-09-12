"""Collapse the same story linked from several newsletters into one Article."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Article

# Query parameters that only track where a click came from.
TRACKING_PARAMS = {"ref", "bk_pid"}
TRACKING_PREFIXES = ("utm_",)


def canonical_url(url: str) -> str:
    """Return `url` with tracking parameters, `www.`, and a trailing slash removed.

    Two links to the same page from different newsletters differ only in these
    details, so this is the identity used for deduplication and as the RSS guid.
    """
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in TRACKING_PARAMS and not key.lower().startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(query), ""))


def dedupe(articles: list[Article]) -> list[Article]:
    """Return `articles` without sponsors and with one entry per canonical URL.

    Order is preserved and the first occurrence wins, so callers control
    priority by the order they pass articles in.
    """
    seen: set[str] = set()
    kept = []
    for article in articles:
        if article.is_sponsor:
            continue
        key = canonical_url(article.url)
        if key in seen:
            continue
        seen.add(key)
        kept.append(article)
    return kept
