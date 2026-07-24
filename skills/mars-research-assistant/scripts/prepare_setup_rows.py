#!/usr/bin/env python3
"""Populate daily setup CSV rows from a user-confirmed setup JSON file.

This script bridges plan preparation and formal intraday scanning. It consumes
structured setup rows that were already confirmed by the user or Active Market
Plan workflow. It does not parse free-form trade ideas, read broker accounts,
call market data, or perform order actions.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any

from record_schemas import CSV_SCHEMAS
from runtime_state import default_runtime_dir, resolve_daily_dir


REQUIRED_SETUP_FIELDS = (
    "setup_id",
    "ticker",
    "underlying",
    "direction",
    "trade_horizon",
    "instrument_type",
    "analysis_timeframe",
    "trigger_timeframe",
    "setup_type",
    "trigger_zone",
    "invalidation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare daily trade-plans.csv and intraday-watchlist.csv rows from confirmed setup JSON."
    )
    parser.add_argument("--setup-json", required=True, help="User-confirmed setup JSON; use '-' for stdin")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/mars-research-assistant-runtime",
    )
    parser.add_argument("--daily-dir", default=None, help="Explicit daily/YYYY-MM-DD directory override")
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without creating files")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing CSVs even when they already contain setup rows",
    )
    return parser.parse_args()


def read_payload(path_text: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path_text == "-" else Path(path_text).expanduser().read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"setup JSON is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise SystemExit("setup JSON must be an object with a setups array")
    return payload


def payload_setups(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("setups")
    if not isinstance(value, list):
        raise SystemExit("setup JSON must contain a setups array")
    setups = [item for item in value if isinstance(item, dict)]
    if len(setups) != len(value):
        raise SystemExit("every setup in setups must be an object")
    if not setups:
        raise SystemExit("setup JSON contains no setup rows")
    return setups


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ";".join(text(item) for item in value if text(item))
    return str(value).strip()


def setup_value(setup: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = text(setup.get(key))
        if value:
            return value
    return ""


def validate_setups(setups: list[dict[str, Any]]) -> None:
    errors: list[str] = []
    seen: set[str] = set()
    for index, setup in enumerate(setups, start=1):
        missing = [field for field in REQUIRED_SETUP_FIELDS if not setup_value(setup, field)]
        setup_id = setup_value(setup, "setup_id") or f"row {index}"
        if missing:
            errors.append(f"{setup_id}: missing {', '.join(missing)}")
        if setup_id in seen:
            errors.append(f"{setup_id}: duplicate setup_id")
        seen.add(setup_id)
    if errors:
        raise SystemExit("invalid setup JSON:\n- " + "\n- ".join(errors))


def trade_id(setup: dict[str, Any], trading_date: str, index: int) -> str:
    explicit = setup_value(setup, "trade_id")
    if explicit:
        return explicit
    ticker = setup_value(setup, "underlying", "ticker").replace(" ", "")
    return f"{trading_date.replace('-', '')}-{ticker}-{index:03d}"


def key_levels(setup: dict[str, Any]) -> str:
    explicit = setup_value(setup, "key_levels")
    if explicit:
        return explicit
    parts = [
        f"trigger {setup_value(setup, 'trigger_zone')}",
        f"invalidation {setup_value(setup, 'invalidation')}",
        f"target1 {setup_value(setup, 'target_1')}",
        f"target2 {setup_value(setup, 'target_2')}",
    ]
    return "; ".join(part for part in parts if not part.endswith(" "))


def trade_plan_row(setup: dict[str, Any], trading_date: str, index: int) -> dict[str, str]:
    row = {field: "" for field in CSV_SCHEMAS["trade-plans.csv"]}
    row.update(
        {
            "date": setup_value(setup, "date") or trading_date,
            "trade_id": trade_id(setup, trading_date, index),
            "setup_id": setup_value(setup, "setup_id"),
            "theme_id": setup_value(setup, "theme_id"),
            "status": setup_value(setup, "status", "current_status") or "active",
            "ticker": setup_value(setup, "ticker"),
            "underlying": setup_value(setup, "underlying"),
            "direction": setup_value(setup, "direction"),
            "trade_horizon": setup_value(setup, "trade_horizon"),
            "instrument_type": setup_value(setup, "instrument_type"),
            "strategy_type": setup_value(setup, "strategy_type"),
            "analysis_timeframe": setup_value(setup, "analysis_timeframe"),
            "trigger_timeframe": setup_value(setup, "trigger_timeframe"),
            "setup_type": setup_value(setup, "setup_type"),
            "entry_trigger": setup_value(setup, "entry_trigger"),
            "trigger_zone": setup_value(setup, "trigger_zone"),
            "invalidation": setup_value(setup, "invalidation"),
            "stop_price": setup_value(setup, "stop_price"),
            "target_1": setup_value(setup, "target_1"),
            "target_2": setup_value(setup, "target_2"),
            "ema_context": setup_value(setup, "ema_context"),
            "price_action_context": setup_value(setup, "price_action_context"),
            "options_context": setup_value(setup, "options_context"),
            "macro_context": setup_value(setup, "macro_context"),
            "risk_per_trade": setup_value(setup, "risk_per_trade"),
            "max_position_size": setup_value(setup, "max_position_size"),
            "time_stop": setup_value(setup, "time_stop"),
            "notes": setup_value(setup, "notes"),
        }
    )
    return row


def watchlist_row(setup: dict[str, Any], trading_date: str, index: int) -> dict[str, str]:
    status = setup_value(setup, "current_status", "status") or "active"
    row = {field: "" for field in CSV_SCHEMAS["intraday-watchlist.csv"]}
    row.update(
        {
            "date": setup_value(setup, "date") or trading_date,
            "setup_id": setup_value(setup, "setup_id"),
            "trade_id": trade_id(setup, trading_date, index),
            "theme_id": setup_value(setup, "theme_id"),
            "ticker": setup_value(setup, "ticker"),
            "underlying": setup_value(setup, "underlying"),
            "direction": setup_value(setup, "direction"),
            "trade_horizon": setup_value(setup, "trade_horizon"),
            "instrument_type": setup_value(setup, "instrument_type"),
            "analysis_timeframe": setup_value(setup, "analysis_timeframe"),
            "trigger_timeframe": setup_value(setup, "trigger_timeframe"),
            "setup_type": setup_value(setup, "setup_type"),
            "key_levels": key_levels(setup),
            "trigger_zone": setup_value(setup, "trigger_zone"),
            "invalidation": setup_value(setup, "invalidation"),
            "current_status": status,
            "last_checked": setup_value(setup, "last_checked"),
            "attention_reason": setup_value(setup, "attention_reason"),
            "execution_check_required": setup_value(setup, "execution_check_required") or "no",
            "notes": setup_value(setup, "notes"),
        }
    )
    return row


def csv_text(schema_name: str, rows: list[dict[str, str]]) -> str:
    output = []
    header = CSV_SCHEMAS[schema_name]
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    output.append(buffer.getvalue())
    return "".join(output)


def has_data_rows(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return any(row for row in csv.DictReader(handle))


def write_or_keep(path: Path, content: str, *, dry_run: bool, overwrite: bool) -> str:
    populated = has_data_rows(path)
    if populated and not overwrite:
        return f"kept existing populated {path}; use --overwrite after confirming replacement"
    if dry_run:
        action = "would overwrite" if path.exists() else "would write"
        if path.exists() and not populated:
            action = "would fill header-only"
        return f"{action} {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if path.exists() and populated:
        return f"overwrote populated {path}"
    return f"wrote {path}"


def prepare_setup_rows(
    *,
    payload: dict[str, Any],
    runtime_dir: Path,
    trading_date: str,
    daily_dir: Path | None,
    dry_run: bool,
    overwrite: bool,
) -> list[str]:
    setups = payload_setups(payload)
    validate_setups(setups)
    resolved_daily_dir = daily_dir or resolve_daily_dir(runtime_dir, trading_date)
    trade_rows = [trade_plan_row(setup, trading_date, index) for index, setup in enumerate(setups, start=1)]
    watch_rows = [watchlist_row(setup, trading_date, index) for index, setup in enumerate(setups, start=1)]
    trade_path = resolved_daily_dir / "trade-plans.csv"
    watch_path = resolved_daily_dir / "intraday-watchlist.csv"
    return [
        f"Daily setup rows target: {resolved_daily_dir}",
        f"confirmed setups: {len(setups)}",
        write_or_keep(
            trade_path,
            csv_text("trade-plans.csv", trade_rows),
            dry_run=dry_run,
            overwrite=overwrite,
        ),
        write_or_keep(
            watch_path,
            csv_text("intraday-watchlist.csv", watch_rows),
            dry_run=dry_run,
            overwrite=overwrite,
        ),
        "No live broker reads; no live market data; no order actions.",
        "Consumes user-confirmed setup JSON only; it does not parse free-form trade ideas.",
    ]


def main() -> int:
    args = parse_args()
    payload = read_payload(args.setup_json)
    messages = prepare_setup_rows(
        payload=payload,
        runtime_dir=Path(args.runtime_dir).expanduser(),
        trading_date=args.date,
        daily_dir=Path(args.daily_dir).expanduser() if args.daily_dir else None,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )
    prefix = "DRY RUN " if args.dry_run else ""
    for index, message in enumerate(messages):
        if index == 0:
            print(prefix + message)
        else:
            print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
