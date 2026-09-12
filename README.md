# tldr-rss

RSS feeds for the [TLDR](https://tldr.tech) newsletters with one item per
article instead of one item per issue. Stories that appear in several
newsletters show up once, and sponsor items are removed. Rebuilt every three
hours and served as plain files from GitHub Pages.

## Subscribe

Add this URL to your RSS reader:

```
https://nickrwann.github.io/tldr-rss/all.xml
```

In NetNewsWire: **File → New Feed** (Mac) or the **+** button (iOS), paste
the URL, and tap **Add**.

Want only some newsletters? Subscribe to a bundle or individual feeds below.
Individual newsletter feeds do not overlap with one another, but bundles can
overlap with each other and with individual feeds.

| Feed URL (append to `https://nickrwann.github.io/tldr-rss/`) | Covers |
| --- | --- |
| `all.xml` | Every newsletter |
| `engineering.xml` | Tech, AI, Web Dev, DevOps, Hardware, InfoSec, Data |
| `nick.xml` | Nick's selection: Tech, AI, Web Dev, DevOps, Hardware, Data |
| `tech.xml` | TLDR Tech |
| `ai.xml` | TLDR AI |
| `dev.xml` | TLDR Web Dev |
| `devops.xml` | TLDR DevOps |
| `hardware.xml` | TLDR Hardware |
| `infosec.xml` | TLDR InfoSec |
| `data.xml` | TLDR Data |
| `design.xml` | TLDR Design |
| `product.xml` | TLDR Product |
| `founders.xml` | TLDR Founders |
| `marketing.xml` | TLDR Marketing |
| `fintech.xml` | TLDR Fintech |
| `crypto.xml` | TLDR Crypto |

Every item links straight to the article, keeps TLDR's title and summary, and
ends with a link back to the issue it came from. `articles.json` at the same
base URL has the same articles as data.

## Change what gets generated

Edit [`feeds.toml`](feeds.toml): add or remove a newsletter, reorder them to
change which one "owns" a shared story, or define a bundle. Push to `main`
and the next run picks it up.

## How it works

Each run fetches the configured newsletters' issue lists, parses recent issue
pages into articles, removes sponsors and duplicate links, and writes static
RSS feeds. The default window is 14 calendar days, configured by `window_days`
in `feeds.toml`. Runs rebuild that window without storing history, so the
hosted feeds do not grow indefinitely. Weekends need no special handling:
recent weekday issues remain in the window until they age out.

The first source listed in `feeds.toml` wins when newsletters share an article.
Each item's RSS GUID is its canonical article URL, allowing readers to recognize
it across rebuilds. Readers may retain older items after they leave the feed,
depending on their retention settings.

GitHub Pages serves fixed files; URL query parameters cannot customize a feed.
Use configured bundles for subsets, or `articles.json` for custom integrations.
Generated files live in `public/` and are built and deployed by GitHub Actions,
not committed to the repository.

## Run locally

Requires Python 3.11 or newer.

```
pip install -e ".[dev]"
python -m pytest
python -m tldr_rss --out public/ --window-days 3 --verbose
```

## Host your own

1. Fork this repo and set `site_url` in `feeds.toml` to your Pages URL.
2. In the repo settings, set **Pages → Source** to **GitHub Actions**.
3. Run the **Publish feeds** workflow once from the Actions tab.
