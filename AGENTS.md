# Agent instructions

See [README.md](README.md) for the project overview and subscription links.

## Architecture: Functional Core, Imperative Shell

The functional core transforms data through pure functions: the same inputs
produce the same outputs, without network or filesystem access. Parsing,
deduplication, and RSS rendering belong here.

The imperative shell handles configuration, HTTP requests, file writes, and
CLI execution. `pipeline.py` composes the stages and accepts an `http` callable
so tests can supply fixtures without making network requests.

Keep TLDR-specific URLs and HTML selectors in `src/tldr_rss/tldr.py`. Pass
fetched content into parsers; do not fetch from within core functions.

## Working rules

- Preserve deterministic output and source priority from `feeds.toml`.
  Canonical article URLs are RSS GUIDs; changing them can reset reader state.
- Keep runs stateless: rebuild from the configured window without persistent
  history or a database.
- Use type hints and frozen dataclasses for data. Prefer the standard library;
  justify new dependencies.
- Use `uv sync --locked` to install dependencies. Add dependencies with `uv add`
  (or `uv add --dev`) and commit `uv.lock` alongside `pyproject.toml`.
- Run `uv run --locked python -m pytest` for code changes. Parser tests use saved HTML in
  `tests/fixtures/`; fake the HTTP callable, not BeautifulSoup.
- For changes to fetching, parsing, or publishing, also run
  `uv run --locked python -m tldr_rss --out public/ --verbose` against the live site and check
  for skipped sources or empty output.
- Never commit generated `public/` files.
