"""The network adapter: a polite `http(url) -> str` for the pipeline's port."""

import logging
import time
import urllib.error
import urllib.request

USER_AGENT = "tldr-rss (+https://github.com/nickrwann/tldr-rss)"
TIMEOUT_SECONDS = 30
RETRY_AFTER_SECONDS = 10
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

log = logging.getLogger(__name__)


def http(url: str) -> str:
    """Return the body of `url` as text.

    Retries once on rate limits, server errors, and dropped connections;
    client errors such as 404 are raised immediately.
    """
    try:
        return _get(url)
    except urllib.error.HTTPError as error:
        if error.code not in RETRYABLE_STATUSES:
            raise
        wait = _retry_after(error) or RETRY_AFTER_SECONDS
        log.warning("%s returned %d, retrying in %ds", url, error.code, wait)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
        wait = RETRY_AFTER_SECONDS
        log.warning("%s failed (%s), retrying in %ds", url, error, wait)
    time.sleep(wait)
    return _get(url)


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8")


def _retry_after(error: urllib.error.HTTPError) -> int | None:
    value = error.headers.get("Retry-After") if error.headers else None
    return int(value) if value and value.isdigit() else None
