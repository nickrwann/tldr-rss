# tldr-rss

Per-article RSS feeds for the [TLDR](https://tldr.tech) newsletters, with
stories that appear in several newsletters shown once and sponsor items
removed. Rebuilt every three hours by GitHub Actions and served from GitHub
Pages. No server, no database.

## Subscribe

Base URL: `https://nickrwann.github.io/tldr-rss/`

| Feed                | What's in it                                                     |
| ------------------- | ---------------------------------------------------------------- |
| `all.xml`           | Every newsletter, one item per article, deduped across all of them |
| `engineering.xml`   | Tech, AI, Web Dev, DevOps, Hardware, InfoSec, Data                |
| `tech.xml`          | TLDR Tech only                                                    |
| `ai.xml`, `dev.xml`, `devops.xml`, `hardware.xml`, `infosec.xml`, `data.xml`, `design.xml`, `product.xml`, `founders.xml`, `marketing.xml`, `fintech.xml`, `crypto.xml` | One newsletter each |
| `articles.json`     | The same articles as data, for anything that isn't an RSS reader  |

Dedupe is global: a story linked from Tech and DevOps appears in `all.xml`
once and in `tech.xml` only, because Tech is listed first in `feeds.toml`.
So subscribing to several per-source feeds still gives you each story once.

Each item links to the article itself (tracking parameters stripped), keeps
TLDR's title and blurb, and ends with a link back to the issue it came from.

## Configure

Everything lives in [`feeds.toml`](feeds.toml):

- **Sources**: one `[[sources]]` block per newsletter. Order is priority when
  the same story appears in several. Delete a block to stop fetching it.
- **Bundles**: named subsets under `[bundles]`. Each becomes `<name>.xml`.
- **`window_days`**: how many days of issues to include (default 14).

Push the change; the next scheduled run picks it up.

## Run locally

```
pip install -e ".[dev]"
python -m pytest
python -m tldr_rss --out public/ --window-days 3 --verbose
```

`public/` is git-ignored; the workflow builds and deploys it.

## How it works

See [`CLAUDE.md`](CLAUDE.md) for the architecture (functional core,
imperative shell) and the rules that keep it simple. In short: fetch each
newsletter's own RSS feed to find recent issue pages, parse every story out of
each page, drop sponsors, collapse duplicates by canonical URL, render RSS.

## Deploying your own copy

1. Fork, and change `site_url` in `feeds.toml` to your Pages URL.
2. In the repository settings, set **Pages → Source** to **GitHub Actions**.
3. Run the *Publish feeds* workflow once from the Actions tab.

## Filtering on the reader side

RSS readers fetch static files, so a query string like `?sources=tech,ai`
cannot change what GitHub Pages returns. If you ever want request-time
filtering, a small edge function (for example a Cloudflare Worker) can render
RSS from `articles.json` on demand without touching this generator.
