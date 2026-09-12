"""CLI entry point: python -m tldr_rss --out public/"""

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from .config import load_config
from .fetch import http
from .pipeline import run, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate per-article, de-duplicated TLDR RSS feeds.")
    parser.add_argument("--out", type=Path, default=Path("public"), help="output directory (default: public/)")
    parser.add_argument("--config", type=Path, default=Path("feeds.toml"), help="config file (default: feeds.toml)")
    parser.add_argument("--window-days", type=int, help="override window_days from the config")
    parser.add_argument("-v", "--verbose", action="store_true", help="show per-source progress")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    config = load_config(args.config)
    if args.window_days is not None:
        config = replace(config, window_days=args.window_days)

    articles = run(config, http)
    written = write_outputs(articles, config, args.out)
    print(f"{len(articles)} articles → {len(written)} files in {args.out}/")


if __name__ == "__main__":
    main()
