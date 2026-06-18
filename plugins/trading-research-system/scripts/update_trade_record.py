#!/usr/bin/env python3
"""Create or update a local actual-trade record after interactive review."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

from trade_records import TradeRecordUpdate, apply_trade_update


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update trades.csv and append a reviews.md section.")
    parser.add_argument("--stage", required=True, choices=("post-order", "post-exit", "post_order", "post_exit"))
    parser.add_argument("--trade-id", required=True)
    parser.add_argument("--fields-json", required=True, help="JSON object containing trades.csv field values")
    parser.add_argument("--review-file", default=None, help="Markdown/text review section to append")
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
    parser.add_argument(
        "--daily-dir",
        default=None,
        help="Daily directory override. Defaults to <root>/<date>",
    )
    parser.add_argument("--trades-csv", default=None, help="trades.csv override")
    parser.add_argument("--reviews-md", default=None, help="reviews.md override")
    return parser.parse_args()


def load_fields(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"fields JSON must contain an object: {path}")
    return {str(key): "" if value is None else str(value) for key, value in raw.items()}


def load_review_text(path: str | None) -> str:
    if not path:
        return ""
    review_path = Path(path)
    if not review_path.is_file():
        raise ValueError(f"review file does not exist: {review_path}")
    return review_path.read_text(encoding="utf-8")


def resolve_daily_dir(args: argparse.Namespace) -> Path:
    if args.daily_dir:
        return Path(args.daily_dir).expanduser()
    root = Path(args.root).expanduser() if args.root else Path(args.runtime_dir).expanduser() / "daily"
    return root / args.date


def main() -> int:
    args = parse_args()
    daily_dir = resolve_daily_dir(args)
    trades_path = Path(args.trades_csv).expanduser() if args.trades_csv else daily_dir / "trades.csv"
    reviews_path = Path(args.reviews_md).expanduser() if args.reviews_md else daily_dir / "reviews.md"

    try:
        message = apply_trade_update(
            trades_path,
            reviews_path,
            TradeRecordUpdate(
                stage=args.stage,
                trade_id=args.trade_id,
                fields=load_fields(Path(args.fields_json)),
                review_text=load_review_text(args.review_file),
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"update trade record failed: {error}", file=sys.stderr)
        return 1

    print(message)
    print(f"review appended to {reviews_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
