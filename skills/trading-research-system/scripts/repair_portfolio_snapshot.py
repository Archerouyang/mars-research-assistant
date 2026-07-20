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

from product_knowledge import normalize_symbol, product_knowledge
from record_schemas import CSV_SCHEMAS


PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])


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


def clean(value: str | None) -> str:
    return (value or "").strip()


def inferred_instrument_type(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    current = clean(row.get("instrument_type")) or "unspecified"
    product = product_knowledge(symbol)

    if normalize_symbol(symbol) == "CASH":
        return "cash"
    if "option" in current.lower() or current.lower() == "opt":
        return "option"
    if "future" in current.lower() or current.lower() == "fut":
        return "future"
    if product.known:
        return product.product_type
    normalized_source_types = {"STK": "stock_common", "stk": "stock_common", "stock": "stock_common"}
    return normalized_source_types.get(current, current)


def inferred_theme_id(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    current = clean(row.get("theme_id"))
    product = product_knowledge(symbol)
    if normalize_symbol(symbol) == "CASH":
        return "cash"
    return product.theme if product.known else current or "unmapped"


def inferred_underlying(row: Mapping[str, str]) -> str:
    symbol = clean(row.get("symbol")).upper()
    current = clean(row.get("underlying")).upper()
    product = product_knowledge(symbol)
    if normalize_symbol(symbol) == "CASH":
        return current or clean(row.get("currency")).upper() or "CASH"
    if product.known:
        return product.underlying or ""
    return normalize_symbol(current) if current else ""


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
