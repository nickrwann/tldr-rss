import io
import urllib.error
from email.message import Message

import pytest

from tldr_rss import fetch


def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = Message()
    if retry_after:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://x.test", code, "err", headers, io.BytesIO())


def test_retries_once_on_rate_limit_using_retry_after(monkeypatch):
    calls = []
    responses = [_http_error(429, "3"), "body"]

    def fake_get(url):
        calls.append(url)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    slept = []
    monkeypatch.setattr(fetch, "_get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", slept.append)
    assert fetch.http("https://x.test") == "body"
    assert calls == ["https://x.test"] * 2
    assert slept == [3]


def test_does_not_retry_client_errors(monkeypatch):
    def fake_get(url):
        raise _http_error(404)

    monkeypatch.setattr(fetch, "_get", fake_get)
    with pytest.raises(urllib.error.HTTPError):
        fetch.http("https://x.test")


def test_gives_up_after_second_failure(monkeypatch):
    def fake_get(url):
        raise _http_error(503)

    monkeypatch.setattr(fetch, "_get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    with pytest.raises(urllib.error.HTTPError):
        fetch.http("https://x.test")


def test_retries_once_on_dropped_connection(monkeypatch):
    responses = [urllib.error.URLError("EOF occurred in violation of protocol"), "body"]

    def fake_get(url):
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(fetch, "_get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    assert fetch.http("https://x.test") == "body"
