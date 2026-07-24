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


SOURCE_LABELS = {
    "longbridge_macrodata": "Longbridge macrodata",
    "official_source_fallback": "official source fallback",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare macro-panel.json in the private Daily Ops runtime.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/mars-research-assistant-runtime",
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
    parser.add_argument(
        "--source-capability",
        choices=tuple(SOURCE_LABELS),
        default="longbridge_macrodata",
        help="Macro value source used for this panel; default longbridge_macrodata",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned action without creating files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing macro-panel.json")
    return parser.parse_args()


def target_path(runtime_dir: Path, trading_date: str) -> Path:
    return resolve_daily_dir(runtime_dir, trading_date) / "macro-panel.json"


def source_label(source_capability: str) -> str:
    return SOURCE_LABELS[source_capability]


def safety_lines(source_capability: str) -> list[str]:
    label = source_label(source_capability)
    return [
        f"No live macrodata reads; this script consumes saved {label} JSON only.",
        f"{label} is not a broker account source.",
        "No order actions; this script never creates, modifies, cancels, or submits orders.",
    ]


def missing_input_message(target: Path, dry_run: bool, source_capability: str) -> list[str]:
    prefix = "DRY RUN " if dry_run else ""
    label = source_label(source_capability)
    return [
        f"{prefix}Macro panel target: {target}",
        "macrodata JSON was not supplied; macro-panel.json was not generated.",
        f"Next step: run an authorized {label} read or collection, save the JSON privately, then rerun with --macrodata-json.",
    ] + safety_lines(source_capability)


def prepare_macro_panel(
    *,
    runtime_dir: Path,
    trading_date: str,
    macrodata_json: str | None,
    as_of: str,
    data_status: str,
    source_status: str,
    source_capability: str,
    dry_run: bool,
    overwrite: bool,
) -> list[str]:
    output = target_path(runtime_dir, trading_date)
    if not macrodata_json:
        return missing_input_message(output, dry_run, source_capability)

    if output.exists() and not overwrite:
        return [
            f"Macro panel target: {output}",
            f"kept existing {output}",
            "Use --overwrite to refresh the runtime macro panel after confirming the new macrodata snapshot.",
        ] + safety_lines(source_capability)

    payload = read_json(macrodata_json)
    panel = normalize_panel(
        payload,
        as_of=as_of,
        data_status=data_status,
        source_status=source_status,
        source_capability=source_capability,
        source_label=source_label(source_capability),
    )

    if dry_run:
        return [
            f"DRY RUN Macro panel target: {output}",
            f"would write {output}",
            f"source_capability: {panel['source_capability']}",
            f"strategy_posture: {panel['strategy_posture']}",
            f"indicators: {len(panel['indicators'])}",
            f"missing_indicators: {', '.join(panel['missing_indicators']) or 'none'}",
        ] + safety_lines(source_capability)

    write_panel(output, panel)
    return [
        f"Macro panel target: {output}",
        f"wrote {output}",
        f"source_capability: {panel['source_capability']}",
        f"strategy_posture: {panel['strategy_posture']}",
        f"indicators: {len(panel['indicators'])}",
        f"missing_indicators: {', '.join(panel['missing_indicators']) or 'none'}",
    ] + safety_lines(source_capability)


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
        source_capability=args.source_capability,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
