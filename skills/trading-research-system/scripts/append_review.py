#!/usr/bin/env python3
"""Append a reviewed trade section to a daily reviews.md file."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from runtime_state import default_runtime_dir, resolve_daily_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a trade review to reviews.md")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Daily data root override. Defaults to <runtime-dir>/daily",
    )
    parser.add_argument("--trade-id", required=True, help="Trade identifier")
    parser.add_argument("--symbol", required=True, help="Trade symbol")
    parser.add_argument("--review-file", required=True, help="Markdown file containing the review section")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    daily_dir = resolve_daily_dir(args.runtime_dir, args.date, root=args.root)
    reviews_path = daily_dir / "reviews.md"
    review_source = Path(args.review_file)
    if not review_source.is_file():
        raise SystemExit(f"review file does not exist: {review_source}")
    daily_dir.mkdir(parents=True, exist_ok=True)
    section = review_source.read_text(encoding="utf-8").strip()
    if not section:
        raise SystemExit("review file is empty")
    if not reviews_path.exists():
        reviews_path.write_text("# Daily Review\n\n## Trade Reviews\n", encoding="utf-8")
    with reviews_path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n")
        if not section.startswith("### "):
            handle.write(f"### {args.trade_id} - {args.symbol}\n\n")
        handle.write(section)
        handle.write("\n")
    print(f"Appended review to {reviews_path}")


if __name__ == "__main__":
    main()
