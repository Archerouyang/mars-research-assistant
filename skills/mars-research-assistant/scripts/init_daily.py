#!/usr/bin/env python3
"""Create a local daily trading research folder from bundled templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from private_runtime import PreparationScope, prepare_private_runtime
from runtime_state import default_runtime_dir, resolve_daily_dir
from runtime_state import template_dir_from_script as runtime_template_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize runtime daily trading research files.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/mars-research-assistant-runtime",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Daily data root override. Defaults to <runtime-dir>/daily",
    )
    parser.add_argument(
        "--templates",
        default=None,
        help="Template directory; defaults to Skill assets/templates",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def template_dir_from_script() -> Path:
    return runtime_template_dir(__file__)


def main() -> None:
    args = parse_args()
    target_dir = resolve_daily_dir(args.runtime_dir, args.date, root=args.root)
    template_dir = Path(args.templates) if args.templates else template_dir_from_script()
    messages = prepare_private_runtime(
        args.runtime_dir,
        args.date,
        template_dir,
        scope=PreparationScope.DAILY_ONLY,
        overwrite=args.overwrite,
        daily_root=args.root,
    )

    print(f"Daily research folder: {target_dir}")
    for message in messages:
        print(f"- {message}")


if __name__ == "__main__":
    main()
