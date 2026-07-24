#!/usr/bin/env python3
"""broker snapshot ingest: normalize read-only broker CSV exports.

No live broker reads, no live market data calls, and no order actions are
performed here. This script only maps user-approved read-only broker export
files into the standard portfolio_snapshot.csv runtime view.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys

from record_schemas import CSV_SCHEMAS


PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])

ALIASES = {
    "account_id": ("account_id", "account", "accountid", "account number"),
    "symbol": ("symbol", "ticker", "local_symbol", "contract.symbol"),
    "underlying": ("underlying", "underlying_symbol"),
    "instrument_type": ("instrument_type", "asset_type", "sec_type", "sectype", "security_type", "product"),
    "direction": ("direction", "side"),
    "quantity": ("quantity", "qty", "position", "position_qty"),
    "avg_cost": ("avg_cost", "avgcost", "average_cost", "cost_price", "cost"),
    "market_price": ("market_price", "markprice", "mark_price", "last_price", "last_done", "price"),
    "market_value": ("market_value", "marketvalue", "value", "position_value"),
    "currency": ("currency", "ccy"),
    "unrealized_pnl": ("unrealized_pnl", "unrealizedpnl", "unrealized_pl", "unrealized"),
    "realized_pnl": ("realized_pnl", "realizedpnl", "realized_pl", "realized"),
    "delta_exposure": ("delta_exposure", "delta", "delta_value"),
    "notional_exposure": ("notional_exposure", "notional", "gross_exposure"),
    "theme_id": ("theme_id", "theme", "tag"),
    "source_timestamp": ("source_timestamp", "timestamp", "updated_at", "as_of", "time"),
    "notes": ("notes", "note", "description"),
}

INSTRUMENT_MAP = {
    "stk": "stock_common",
    "stock": "stock_common",
    "equity": "stock_common",
    "stock_common": "stock_common",
    "etf": "etf_common",
    "etf_common": "etf_common",
    "cash": "cash",
    "opt": "option",
    "option": "option",
    "fut": "future",
    "future": "future",
}


@dataclass(frozen=True)
class InputSpec:
    broker: str
    path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize read-only broker position CSV exports into portfolio_snapshot.csv."
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="BROKER:CSV",
        help="Read-only broker export, e.g. IBKR:/tmp/positions.csv or Longbridge:/tmp/positions.csv",
    )
    parser.add_argument("--output", required=True, help="Output standard portfolio_snapshot.csv path")
    parser.add_argument("--as-of", required=True, help="Snapshot timestamp, e.g. 2026-06-24T20:00:00Z")
    parser.add_argument("--default-account", default="unknown", help="Account id fallback")
    return parser.parse_args()


def parse_input_specs(raw_specs: list[str]) -> list[InputSpec]:
    if not raw_specs:
        raise SystemExit("at least one --input BROKER:CSV is required")

    specs: list[InputSpec] = []
    for raw in raw_specs:
        if ":" not in raw:
            raise SystemExit(f"invalid --input {raw!r}; expected BROKER:CSV")
        broker, path = raw.split(":", 1)
        broker = broker.strip()
        if not broker:
            raise SystemExit(f"invalid --input {raw!r}; missing broker")
        specs.append(InputSpec(broker=normalize_broker(broker), path=Path(path).expanduser()))
    return specs


def normalize_broker(value: str) -> str:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if lowered == "ibkr":
        return "IBKR"
    if lowered == "longbridge":
        return "Longbridge"
    return cleaned


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def row_value(row: dict[str, str], field: str) -> str:
    normalized = {normalize_key(key): value for key, value in row.items()}
    for alias in ALIASES[field]:
        value = normalized.get(normalize_key(alias))
        if value is not None and value.strip() != "":
            return value.strip()
    return ""


def decimal_or_zero(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "").replace("$", "")
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def decimal_text(value: Decimal | str) -> str:
    number = decimal_or_zero(value) if isinstance(value, str) else value
    if number == number.to_integral():
        return str(number.quantize(Decimal("1")))
    return format(number.normalize(), "f")


def signed_direction(row: dict[str, str]) -> str:
    explicit = row_value(row, "direction").lower()
    if explicit in {"short", "sell", "sold"}:
        return "short"
    if explicit in {"long", "buy", "bought"}:
        return "long"
    quantity = decimal_or_zero(row_value(row, "quantity"))
    return "short" if quantity < 0 else "long"


def normalize_instrument(raw: str, symbol: str) -> str:
    if symbol.upper() == "CASH":
        return "cash"
    cleaned = raw.strip().lower().replace(" ", "_").replace("-", "_")
    return INSTRUMENT_MAP.get(cleaned, cleaned or "unspecified")


def signed_abs_text(value: str) -> str:
    return decimal_text(abs(decimal_or_zero(value)))


def default_market_value(quantity: str, market_price: str) -> Decimal:
    return decimal_or_zero(quantity) * decimal_or_zero(market_price)


def normalize_row(row: dict[str, str], spec: InputSpec, as_of: str, default_account: str) -> dict[str, str]:
    symbol = row_value(row, "symbol").upper()
    if not symbol:
        return {}

    currency = row_value(row, "currency").upper() or "USD"
    instrument_type = normalize_instrument(row_value(row, "instrument_type"), symbol)
    quantity = row_value(row, "quantity") or "0"
    avg_cost = row_value(row, "avg_cost") or "0"
    market_price = row_value(row, "market_price") or avg_cost
    market_value_raw = row_value(row, "market_value")
    market_value = decimal_or_zero(market_value_raw) if market_value_raw else default_market_value(quantity, market_price)
    delta_raw = row_value(row, "delta_exposure")
    notional_raw = row_value(row, "notional_exposure")
    delta = decimal_or_zero(delta_raw) if delta_raw else (Decimal("0") if instrument_type == "cash" else market_value)
    notional = decimal_or_zero(notional_raw) if notional_raw else (Decimal("0") if instrument_type == "cash" else abs(market_value))
    underlying = row_value(row, "underlying").upper()
    if not underlying:
        underlying = currency if instrument_type == "cash" else symbol

    return {
        "as_of": as_of,
        "broker": spec.broker,
        "account_id": row_value(row, "account_id") or default_account,
        "symbol": symbol,
        "underlying": underlying,
        "instrument_type": instrument_type,
        "direction": signed_direction(row),
        "quantity": signed_abs_text(quantity),
        "avg_cost": decimal_text(avg_cost),
        "market_price": decimal_text(market_price),
        "market_value": decimal_text(abs(market_value)),
        "currency": currency,
        "unrealized_pnl": decimal_text(row_value(row, "unrealized_pnl") or "0"),
        "realized_pnl": decimal_text(row_value(row, "realized_pnl") or "0"),
        "delta_exposure": decimal_text(abs(delta)),
        "notional_exposure": decimal_text(abs(notional)),
        "theme_id": row_value(row, "theme_id") or "unmapped",
        "source_timestamp": row_value(row, "source_timestamp") or as_of,
        "notes": row_value(row, "notes"),
    }


def load_rows(spec: InputSpec, as_of: str, default_account: str) -> list[dict[str, str]]:
    if not spec.path.is_file():
        raise SystemExit(f"missing input CSV: {spec.path}")
    with spec.path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit(f"missing CSV header: {spec.path}")
        rows = [normalize_row(row, spec, as_of, default_account) for row in reader]
    return [row for row in rows if row]


def write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PORTFOLIO_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PORTFOLIO_HEADER})


def main() -> int:
    args = parse_args()
    specs = parse_input_specs(args.input)
    rows: list[dict[str, str]] = []
    for spec in specs:
        rows.extend(load_rows(spec, args.as_of, args.default_account))
    write_snapshot(Path(args.output).expanduser(), rows)
    print(f"Broker snapshot ingest wrote {len(rows)} row(s) to {args.output}")
    print("No live broker reads; consumed read-only broker export files only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
