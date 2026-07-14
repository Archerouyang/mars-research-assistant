#!/usr/bin/env python3
"""Repair stale product/theme mappings in a standard portfolio_snapshot.csv.

This script is a local transformation for already-normalized runtime snapshots.
No live broker reads, no live market data, and no order actions are performed.
It rewrites only the output CSV path provided by the user.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Mapping

from record_schemas import CSV_SCHEMAS


PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])
MARKET_SUFFIXES = (".US", ".HK", ".SG", ".SH", ".SZ")

BROAD_ETFS = {"DIA", "IWM", "QQQ", "SPY", "VOO"}
RATES_CREDIT_ETFS = {"HYG", "IEF", "LQD", "SHY", "TLT"}
COMMODITY_ETFS = {"GLD", "SLV"}
SECTOR_ETFS = {
    "DRAM": "memory_storage",
    "SMH": "semiconductor",
    "SOXX": "semiconductor",
    "XLK": "tech_beta",
    "XLV": "defensive_healthcare",
    "XLY": "consumer_discretionary",
}
LEVERAGED_ETFS = {
    "KORU": "leveraged_etf",
    "MVLL": "leveraged_etf",
    "MUU": "leveraged_etf",
    "NVDL": "leveraged_etf",
    "SOXL": "leveraged_etf",
    "SQQQ": "leveraged_etf",
    "TQQQ": "leveraged_etf",
    "TSLL": "leveraged_etf",
    "TSMX": "leveraged_etf",
}
STOCK_THEMES = {
    "AMD": "ai_hardware",
    "ARM": "ai_hardware",
    "BE": "ai_power",
    "CRDO": "ai_infra_momentum",
    "GLW": "ai_networking",
    "GOOGL": "mag7",
    "LITE": "ai_networking",
    "META": "mag7",
    "MRVL": "ai_hardware",
    "MU": "memory_storage",
    "NVDA": "ai_hardware",
    "SNDK": "memory_storage",
    "TSM": "ai_hardware",
}
THEME_OVERRIDES = {
    **{symbol: "tech_beta" for symbol in BROAD_ETFS},
    **{symbol: "rates_credit" for symbol in RATES_CREDIT_ETFS},
    **{symbol: "gold_precious_metals" for symbol in COMMODITY_ETFS},
    **SECTOR_ETFS,
    **{symbol: "ai_hardware_leverage" for symbol in LEVERAGED_ETFS},
    **STOCK_THEMES,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair standard portfolio_snapshot.csv product/theme fields from symbol and notes."
    )
    parser.add_argument("--input", required=True, help="Input standard portfolio_snapshot.csv path")
    parser.add_argument("--output", required=True, help="Output repaired portfolio_snapshot.csv path")
    parser.add_argument(
        "--allow-same-path",
        action="store_true",
        help="Allow --input and --output to point to the same file",
    )
    return parser.parse_args()


def root_symbol(symbol: str) -> str:
    upper = symbol.strip().upper()
    for suffix in MARKET_SUFFIXES:
        if upper.endswith(suffix):
            return upper[: -len(suffix)]
    return upper


def clean(value: str | None) -> str:
    return (value or "").strip()


def inferred_instrument_type(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    root = root_symbol(symbol)
    current = clean(row.get("instrument_type")) or "unspecified"
    notes = clean(row.get("notes")).upper()

    if symbol == "CASH" or root == "CASH":
        return "cash"
    if "option" in current.lower() or current.lower() == "opt":
        return "option"
    if "future" in current.lower() or current.lower() == "fut":
        return "future"
    if root in LEVERAGED_ETFS or any(marker in notes for marker in (" 2X", " 3X", "LEVERAGED", "BULL", "BEAR")):
        return "leveraged_etf"
    if root in SECTOR_ETFS:
        return "sector_etf"
    if root in BROAD_ETFS or root in RATES_CREDIT_ETFS or root in COMMODITY_ETFS:
        return "etf_common"
    return "stock_common" if current in {"", "unspecified", "STK", "stk", "stock", "stock_common"} else current


def inferred_theme_id(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    root = root_symbol(symbol)
    current = clean(row.get("theme_id"))
    if symbol == "CASH" or root == "CASH":
        return "cash"
    return THEME_OVERRIDES.get(root, current or "unmapped")


def inferred_underlying(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    current = clean(row.get("underlying")).upper()
    if symbol == "CASH":
        return current or clean(row.get("currency")).upper() or "CASH"
    root = root_symbol(symbol)
    if not current or current == symbol:
        return root
    return current


def repair_row(row: Mapping[str, str]) -> dict[str, str]:
    repaired = {field: clean(row.get(field)) for field in PORTFOLIO_HEADER}
    changes: list[str] = []

    for field, value in (
        ("underlying", inferred_underlying(repaired)),
        ("instrument_type", inferred_instrument_type(repaired)),
        ("theme_id", inferred_theme_id(repaired)),
    ):
        old = repaired.get(field, "")
        if old != value:
            repaired[field] = value
            changes.append(f"{field} {old or '-'}->{value}")

    if changes:
        note = repaired.get("notes", "")
        repair_note = "Snapshot repair: " + "; ".join(changes)
        repaired["notes"] = f"{note}; {repair_note}" if note else repair_note

    return repaired


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit(f"missing CSV header: {path}")
        missing = [field for field in PORTFOLIO_HEADER if field not in reader.fieldnames]
        if missing:
            raise SystemExit(f"portfolio_snapshot.csv missing field(s): {', '.join(missing)}")
        return [repair_row(row) for row in reader if clean(row.get("symbol"))]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PORTFOLIO_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PORTFOLIO_HEADER})


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()
    if input_path.resolve() == output_path.resolve() and not args.allow_same_path:
        raise SystemExit("refusing in-place repair without --allow-same-path")

    rows = load_rows(input_path)
    write_rows(output_path, rows)
    changed = sum(1 for row in rows if "Snapshot repair:" in row.get("notes", ""))
    print(f"Repaired {changed} of {len(rows)} portfolio snapshot row(s) to {output_path}")
    print("No live broker reads; consumed existing portfolio_snapshot.csv only.")
    print("No order actions; this script never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
