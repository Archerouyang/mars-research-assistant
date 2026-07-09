#!/usr/bin/env python3
"""prepare_macro_panel.py: prepare the standard macro-panel.json runtime view.

This script wraps the saved-JSON Longbridge macrodata adapter with runtime path,
dry-run, and overwrite behavior. It does not call Longbridge, read broker
accounts, call market data, or perform order actions.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from longbridge_macrodata_adapter import normalize_panel, read_json, write_panel
from runtime_state import default_runtime_dir, resolve_daily_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare macro-panel.json in the private Daily Ops runtime.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument(
        "--macrodata-json",
        default=None,
        help="Saved Longbridge macrodata JSON; use '-' for stdin after an authorized macrodata read",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Snapshot timestamp, e.g. 2026-06-24T20:00:00Z; defaults to dateT00:00:00Z",
    )
    parser.add_argument("--data-status", default="live", help="live / delayed / prior close / partial / fixture")
    parser.add_argument(
        "--source-status",
        default="available",
        help="available / unauthorized / not_installed / missing / stale",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned action without creating files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing macro-panel.json")
    return parser.parse_args()


def target_path(runtime_dir: Path, trading_date: str) -> Path:
    return resolve_daily_dir(runtime_dir, trading_date) / "macro-panel.json"


def safety_lines() -> list[str]:
    return [
        "No live macrodata reads; this script consumes saved Longbridge macrodata JSON only.",
        "Longbridge macrodata is not a broker account source.",
        "No order actions; this script never creates, modifies, cancels, or submits orders.",
    ]


def missing_input_message(target: Path, dry_run: bool) -> list[str]:
    prefix = "DRY RUN " if dry_run else ""
    return [
        f"{prefix}Macro panel target: {target}",
        "macrodata JSON was not supplied; macro-panel.json was not generated.",
        "Next step: run an authorized Longbridge macrodata read or official fallback collection, save the JSON privately, then rerun with --macrodata-json.",
    ] + safety_lines()


def prepare_macro_panel(
    *,
    runtime_dir: Path,
    trading_date: str,
    macrodata_json: str | None,
    as_of: str,
    data_status: str,
    source_status: str,
    dry_run: bool,
    overwrite: bool,
) -> list[str]:
    output = target_path(runtime_dir, trading_date)
    if not macrodata_json:
        return missing_input_message(output, dry_run)

    if output.exists() and not overwrite:
        return [
            f"Macro panel target: {output}",
            f"kept existing {output}",
            "Use --overwrite to refresh the runtime macro panel after confirming the new macrodata snapshot.",
        ] + safety_lines()

    payload = read_json(macrodata_json)
    panel = normalize_panel(
        payload,
        as_of=as_of,
        data_status=data_status,
        source_status=source_status,
    )

    if dry_run:
        return [
            f"DRY RUN Macro panel target: {output}",
            f"would write {output}",
            f"source_capability: {panel['source_capability']}",
            f"strategy_posture: {panel['strategy_posture']}",
            f"indicators: {len(panel['indicators'])}",
            f"missing_indicators: {', '.join(panel['missing_indicators']) or 'none'}",
        ] + safety_lines()

    write_panel(output, panel)
    return [
        f"Macro panel target: {output}",
        f"wrote {output}",
        f"source_capability: {panel['source_capability']}",
        f"strategy_posture: {panel['strategy_posture']}",
        f"indicators: {len(panel['indicators'])}",
        f"missing_indicators: {', '.join(panel['missing_indicators']) or 'none'}",
    ] + safety_lines()


def main() -> int:
    args = parse_args()
    runtime_dir = Path(args.runtime_dir).expanduser()
    as_of = args.as_of or f"{args.date}T00:00:00Z"
    messages = prepare_macro_panel(
        runtime_dir=runtime_dir,
        trading_date=args.date,
        macrodata_json=args.macrodata_json,
        as_of=as_of,
        data_status=args.data_status,
        source_status=args.source_status,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
