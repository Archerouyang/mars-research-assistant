#!/usr/bin/env python3
"""Prepare a Daily Ops runtime package for one trading date.

This script creates safe local containers for the daily workflow, including
`trade-plans.csv` and `intraday-watchlist.csv`. It does not read broker data,
market data, private plan contents, or perform order actions.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from private_runtime import PreparationScope, prepare_private_runtime
from runtime_state import default_runtime_dir, resolve_daily_dir
from runtime_state import template_dir_from_script as runtime_template_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare today's Daily Ops runtime package.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/mars-research-assistant-runtime",
    )
    parser.add_argument(
        "--templates",
        default=None,
        help="Template directory; defaults to Skill assets/templates",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without creating files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing daily package files")
    return parser.parse_args()


def template_dir_from_script() -> Path:
    return runtime_template_dir(__file__)


def prepare_daily_runtime(
    runtime_dir: Path,
    trading_date: str,
    template_dir: Path,
    *,
    dry_run: bool,
    overwrite: bool,
) -> list[str]:
    return prepare_private_runtime(
        runtime_dir,
        trading_date,
        template_dir,
        scope=PreparationScope.DAILY,
        dry_run=dry_run,
        overwrite=overwrite,
    )


def main() -> int:
    args = parse_args()
    runtime_dir = Path(args.runtime_dir).expanduser()
    template_dir = Path(args.templates).expanduser() if args.templates else template_dir_from_script()
    messages = prepare_daily_runtime(
        runtime_dir=runtime_dir,
        trading_date=args.date,
        template_dir=template_dir,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )

    mode = "DRY RUN " if args.dry_run else ""
    print(f"{mode}Daily runtime package: {resolve_daily_dir(runtime_dir, args.date)}")
    print("No live broker reads; no live market data; no order actions.")
    print("Creates header-only CSV containers; prepared setups must come from the Active Market Plan or user input.")
    for message in messages:
        print(f"- {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
