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

Want only some newsletters? Subscribe to these instead. You can add more than
one; each story still appears only once across them.

| Feed URL (append to `https://nickrwann.github.io/tldr-rss/`) | Covers |
| --- | --- |
| `all.xml` | Every newsletter |
| `engineering.xml` | Tech, AI, Web Dev, DevOps, Hardware, InfoSec, Data |
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

## Run locally

```
pip install -e ".[dev]"
python -m pytest
python -m tldr_rss --out public/ --window-days 3 --verbose
```

## Host your own

1. Fork this repo and set `site_url` in `feeds.toml` to your Pages URL.
2. In the repo settings, set **Pages → Source** to **GitHub Actions**.
3. Run the **Publish feeds** workflow once from the Actions tab.

How it works and why it is built this way: see [`CLAUDE.md`](CLAUDE.md).
