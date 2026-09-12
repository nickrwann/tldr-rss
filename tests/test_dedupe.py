from datetime import date
from pathlib import Path

import pytest

from tldr_rss.dedupe import canonical_url, dedupe
from tldr_rss.models import Article, Issue, Source
from tldr_rss.tldr import parse_issue

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://openai.com/index/introducing-the-agents-api/?utm_source=tldrnewsletter",
         "https://openai.com/index/introducing-the-agents-api"),
        ("https://openai.com/index/introducing-the-agents-api?utm_source=tldrdevops",
         "https://openai.com/index/introducing-the-agents-api"),
        ("HTTPS://WWW.Example.com/Path/", "https://example.com/Path"),
        ("https://x.test/a?utm_campaign=c&page=2&ref=tldr&UTM_Medium=m", "https://x.test/a?page=2"),
        ("https://x.test/", "https://x.test/"),
        ("https://x.test", "https://x.test/"),
    ],
)
def test_canonical_url(url, expected):
    assert canonical_url(url) == expected


def _article(url: str, slug: str = "tech", sponsor: bool = False) -> Article:
    return Article(title=url, url=url, blurb_html="", section="", source=Source(slug, slug),
                   issue_date=date(2026, 9, 11), issue_url="", is_sponsor=sponsor)


def test_first_occurrence_wins_and_order_is_kept():
    a = _article("https://x.test/one?utm_source=tldrnewsletter", "tech")
    b = _article("https://x.test/two", "ai")
    c = _article("https://www.x.test/one/?utm_source=tldrai", "ai")
    assert dedupe([a, b, c]) == [a, b]


def test_sponsors_are_dropped_even_if_unique():
    assert dedupe([_article("https://x.test/ad", sponsor=True), _article("https://x.test/story")]) == [
        _article("https://x.test/story")
    ]


def test_real_cross_newsletter_overlap_collapses_to_one():
    articles = []
    for slug in ["tech", "ai", "devops"]:
        issue = Issue(Source(slug, slug), date(2026, 9, 11), f"https://tldr.tech/{slug}/2026-09-11", "")
        articles += parse_issue((FIXTURES / f"issue-{slug}-2026-09-11.html").read_text(encoding="utf-8"), issue)
    kept = dedupe(articles)

    agents_api = [a for a in kept if canonical_url(a.url) == "https://openai.com/index/introducing-the-agents-api"]
    assert len(agents_api) == 1
    assert agents_api[0].source.slug == "tech"  # first source listed wins

    after_git = [a for a in kept if "what-comes-after-git" in a.url]
    assert [a.source.slug for a in after_git] == ["tech"]

    assert not any(a.is_sponsor for a in kept)
    # 9 sponsors, 3 duplicates (Agents API in three feeds, after-git in two)
    assert len(kept) == len(articles) - 9 - 3
