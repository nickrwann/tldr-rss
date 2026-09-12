# tldr-rss

Turns the TLDR newsletters (tldr.tech) into per-article RSS feeds with
cross-newsletter duplicates and sponsor items removed, published as static
files on GitHub Pages.

## Why this exists

- TLDR's own RSS feeds contain one item per *issue* (a whole newsletter) with
  no body. We want one item per *article*.
- The same article is often linked from several newsletters (tech, ai,
  devops, ...) under different titles and tracking tags. We want it once.
- Sponsor and ad items are noise. We drop them.

## Architecture: Functional Core, Imperative Shell

The pattern is *Functional Core, Imperative Shell*, the lightweight form of
Hexagonal (Ports and Adapters). The core is organised as a pipeline. Judge
every change against it.

```
feeds.toml ─▶ fetch issues ─▶ parse articles ─▶ dedupe ─▶ render ─▶ write
              (shell)         (core)             (core)    (core)    (shell)
```

| Role              | Module          | Job                                                    |
| ----------------- | --------------- | ------------------------------------------------------ |
| Core (pure)       | `tldr.py`       | Everything TLDR-specific: feed URL, feed XML parsing, issue HTML parsing |
| Core (pure)       | `dedupe.py`     | `canonical_url()`, `dedupe()`                          |
| Core (pure)       | `rss.py`        | Render a list of `Article`s to an RSS 2.0 document     |
| Data              | `models.py`     | `Source`, `Issue`, `Article` frozen dataclasses         |
| Port              | `http`          | A plain `Callable[[str], str]` the pipeline is given    |
| Adapter (shell)   | `fetch.py`      | `urllib` fetcher with User-Agent, timeout, one retry    |
| Adapter (shell)   | `config.py`     | Load `feeds.toml` into a `Config`                       |
| Composition root  | `pipeline.py`   | `run(config, http) -> list[Article]`, `write_outputs()` |
| Entry point       | `__main__.py`   | CLI: `python -m tldr_rss --out public/`                 |

`tldr.py` is also the anti-corruption layer: it is the only module that knows
TLDR's HTML selectors, URL conventions, and sponsor markers. When TLDR changes
their site, that is the only file that changes.

Rules that keep it simple:

- **Stateless.** Every run rebuilds all outputs from the last `window_days` of
  every source. No database, no cache, no "seen" list. Re-running is harmless.
- **Deterministic.** Sources are processed in the order listed in `feeds.toml`;
  the first occurrence of a canonical URL wins. Same inputs, identical outputs.
- **Pure functions take data, not URLs.** Parsers take strings. The pipeline
  takes an `http` callable so tests inject fixtures and never hit the network.
- **Stable guids.** An item's guid is its canonical URL, so readers keep
  read/unread state across regenerations.
- **No parameterised feeds.** GitHub Pages is static; a query string is
  ignored. `articles.json` is published so a request-time renderer (e.g. a
  Cloudflare Worker) could be added later without touching this generator.

## Conventions

- Python 3.11+, standard library first. Runtime deps: `beautifulsoup4` only.
  Config is TOML (stdlib `tomllib`). No new dependency without the reason in
  the commit message.
- Tests: `pytest`, run as `python -m pytest`. Parser tests run against real saved pages in
  `tests/fixtures/`. Never mock BeautifulSoup; only ever fake the `http` port.
- Type hints everywhere. Frozen dataclasses for data. No classes for behaviour
  unless state genuinely has to be carried.
- Readability beats cleverness. A short docstring on every public function
  saying what it returns, not how.

## Workflow

- **One feature per commit.** Each commit adds one working, tested capability
  (e.g. "Parse articles out of a TLDR issue page"). No "wip" or "fix" commits;
  amend into the feature commit if it hasn't been pushed yet.
- Commit message: imperative subject under 72 chars, blank line, then a short
  paragraph on *why* when the subject isn't self-evident.
- `python -m pytest` must pass before every commit. Run
  `python -m tldr_rss --out public/` against the live site before touching
  `tldr.py`, the workflow, or the README.
- Generated output (`public/`) is never committed; the workflow builds and
  deploys it.

## Commands

```
pip install -e ".[dev]"            # install package + pytest
python -m pytest                   # run tests
python -m tldr_rss --out public/   # generate feeds locally
```
