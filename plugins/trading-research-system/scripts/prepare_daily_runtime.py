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

from bootstrap_runtime import update_note_template
from record_schemas import CSV_SCHEMAS, DAILY_TEMPLATE_TARGETS
from runtime_state import RuntimeWriter, default_runtime_dir, resolve_daily_dir
from runtime_state import template_dir_from_script as runtime_template_dir


EXTRA_DAILY_NOTES = {
    "research-notes.md": """# Research Notes

## Information Collection

-

## Information Processing

-

## Trade Ideas

-

## Verification

-
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare today's Daily Ops runtime package.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument(
        "--templates",
        default=None,
        help="Template directory; defaults to plugin assets/templates",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without creating files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing daily package files")
    return parser.parse_args()


def template_dir_from_script() -> Path:
    return runtime_template_dir(__file__)


def csv_header_text(schema_name: str) -> str:
    return ",".join(CSV_SCHEMAS[schema_name]) + "\n"


def template_schema_name(template_name: str) -> str | None:
    if not template_name.endswith(".csv"):
        return None
    if template_name not in CSV_SCHEMAS:
        raise SystemExit(f"missing schema for daily template: {template_name}")
    return template_name


def prepare_daily_runtime(
    runtime_dir: Path,
    trading_date: str,
    template_dir: Path,
    *,
    dry_run: bool,
    overwrite: bool,
) -> list[str]:
    writer = RuntimeWriter(dry_run=dry_run, overwrite=overwrite)
    daily_dir = resolve_daily_dir(runtime_dir, trading_date)
    messages: list[str] = [
        writer.ensure_dir(runtime_dir),
        writer.ensure_dir(runtime_dir / "updates"),
        writer.ensure_dir(runtime_dir / "daily"),
        writer.ensure_dir(daily_dir),
    ]

    messages.append(writer.copy_template(template_dir / "ops-state.md", runtime_dir / "ops-state.md"))
    messages.append(
        writer.write_text(
            runtime_dir / "updates" / f"{trading_date}.md",
            update_note_template(trading_date),
        )
    )

    for template_name, target_name in DAILY_TEMPLATE_TARGETS.items():
        schema_name = template_schema_name(template_name)
        if schema_name is not None:
            messages.append(writer.write_text(daily_dir / target_name, csv_header_text(schema_name)))
            continue
        messages.append(writer.copy_template(template_dir / template_name, daily_dir / target_name))

    for target_name, text in EXTRA_DAILY_NOTES.items():
        messages.append(writer.write_text(daily_dir / target_name, text))

    messages.append(prerequisite_status(runtime_dir / "market-plan.md", "Active Market Plan"))
    messages.append(prerequisite_status(runtime_dir / "trading-profile.md", "Trading Profile"))
    return messages


def prerequisite_status(path: Path, label: str) -> str:
    if path.exists():
        return f"{label}: available at {path}"
    return f"{label}: missing; run bootstrap or complete the plan before full Daily Ops analysis"


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
