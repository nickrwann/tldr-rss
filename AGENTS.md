# Agent instructions

See [README.md](README.md) for the project overview and subscription links.

- Keep parsing, deduplication, and RSS rendering pure. Inject network access
  through the pipeline's `http` callable; keep TLDR-specific URLs and HTML
  selectors in `src/tldr_rss/tldr.py`.
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
