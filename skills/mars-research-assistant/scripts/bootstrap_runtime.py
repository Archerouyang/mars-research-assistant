#!/usr/bin/env python3
"""bootstrap private runtime files from bundled blank templates.

No live broker reads, no live market data, and no real automation actions are
performed by this script. It only creates local files from Skill templates.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from private_runtime import PreparationScope, prepare_private_runtime
from runtime_state import default_runtime_dir, template_dir_from_script as runtime_template_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap private Trading Research runtime.")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/mars-research-assistant-runtime",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--templates",
        default=None,
        help="Template directory; defaults to Skill assets/templates",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without creating files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing runtime files")
    parser.add_argument("--no-daily", action="store_true", help="Do not create the dated daily folder")
    return parser.parse_args()


def template_dir_from_script() -> Path:
    return runtime_template_dir(__file__)


def bootstrap_runtime(
    runtime_dir: Path,
    trading_date: str,
    template_dir: Path,
    overwrite: bool,
    dry_run: bool,
    include_daily: bool,
) -> list[str]:
    return prepare_private_runtime(
        runtime_dir,
        trading_date,
        template_dir,
        scope=PreparationScope.BOOTSTRAP,
        dry_run=dry_run,
        overwrite=overwrite,
        include_daily=include_daily,
    )


def main() -> None:
    args = parse_args()
    runtime_dir = Path(args.runtime_dir).expanduser()
    template_dir = Path(args.templates).expanduser() if args.templates else template_dir_from_script()
    messages = bootstrap_runtime(
        runtime_dir=runtime_dir,
        trading_date=args.date,
        template_dir=template_dir,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        include_daily=not args.no_daily,
    )

    mode = "DRY RUN " if args.dry_run else ""
    print(f"{mode}Runtime bootstrap: {runtime_dir}")
    print("No live broker reads; no live market data; no real Codex automations.")
    for message in messages:
        print(f"- {message}")


if __name__ == "__main__":
    main()
