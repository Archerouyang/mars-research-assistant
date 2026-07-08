#!/usr/bin/env python3
"""Normalize saved Longbridge CLI JSON into portfolio_snapshot.csv.

This adapter consumes JSON that was already produced by a read-only Longbridge
CLI command such as `longbridge portfolio --format json`. It does not run the
Longbridge CLI, read live broker data, call market data, or perform order
actions.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any

from record_schemas import CSV_SCHEMAS


PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])
COMMON_MARKET_SUFFIXES = {".US", ".HK", ".SG", ".SH", ".SZ"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize saved Longbridge CLI portfolio JSON into standard portfolio_snapshot.csv."
    )
    parser.add_argument(
        "--portfolio-json",
        required=True,
        help="Saved output from `longbridge portfolio --format json`; use '-' for stdin",
    )
    parser.add_argument("--output", required=True, help="Output standard portfolio_snapshot.csv path")
    parser.add_argument("--as-of", required=True, help="Snapshot timestamp, e.g. 2026-06-24T20:00:00Z")
    parser.add_argument("--account-id", default="Longbridge", help="Account id label for the standard view")
    parser.add_argument(
        "--no-cash",
        action="store_true",
        help="Do not include Longbridge cash_balances as cash rows",
    )
    return parser.parse_args()


def decimal_or_zero(value: Any) -> Decimal:
    cleaned = str(value or "").strip().replace(",", "").replace("$", "")
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def decimal_text(value: Decimal | Any) -> str:
    number = value if isinstance(value, Decimal) else decimal_or_zero(value)
    if number == number.to_integral():
        return str(number.quantize(Decimal("1")))
    return format(number.normalize(), "f")


def read_json(path_text: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path_text == "-" else Path(path_text).expanduser().read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise SystemExit("Longbridge CLI adapter expected a JSON object")
        payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, dict):
        raise SystemExit("Longbridge CLI adapter expected a portfolio JSON object")
    return payload


def underlying_from_symbol(symbol: str, currency: str) -> str:
    upper = symbol.upper()
    for suffix in COMMON_MARKET_SUFFIXES:
        if upper.endswith(suffix):
            return upper[: -len(suffix)]
    return upper or currency.upper()


def position_direction(quantity: Decimal) -> str:
    return "short" if quantity < 0 else "long"


def position_row(holding: dict[str, Any], *, as_of: str, account_id: str) -> dict[str, str]:
    symbol = str(holding.get("symbol") or "").strip().upper()
    if not symbol:
        return {}

    currency = str(holding.get("currency") or "USD").strip().upper()
    quantity = decimal_or_zero(holding.get("quantity"))
    avg_cost = decimal_or_zero(holding.get("cost_price"))
    market_price = decimal_or_zero(holding.get("market_price"))
    market_value = decimal_or_zero(holding.get("market_value") or holding.get("market_value_usd"))
    if market_value == 0 and market_price != 0:
        market_value = quantity * market_price
    unrealized = market_value - (quantity * avg_cost)
    name = str(holding.get("name") or "").strip()
    note = "Longbridge CLI portfolio JSON"
    if name:
        note = f"{note}; {name}"

    return {
        "as_of": as_of,
        "broker": "Longbridge",
        "account_id": account_id,
        "symbol": symbol,
        "underlying": underlying_from_symbol(symbol, currency),
        "instrument_type": "stock_common",
        "direction": position_direction(quantity),
        "quantity": decimal_text(abs(quantity)),
        "avg_cost": decimal_text(avg_cost),
        "market_price": decimal_text(market_price),
        "market_value": decimal_text(abs(market_value)),
        "currency": currency,
        "unrealized_pnl": decimal_text(unrealized),
        "realized_pnl": "0",
        "delta_exposure": decimal_text(abs(market_value)),
        "notional_exposure": decimal_text(abs(market_value)),
        "theme_id": "unmapped",
        "source_timestamp": as_of,
        "notes": note,
    }


def cash_rows(payload: dict[str, Any], *, as_of: str, account_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    balances = payload.get("cash_balances")
    if not isinstance(balances, list):
        return rows

    for balance in balances:
        if not isinstance(balance, dict):
            continue
        currency = str(balance.get("currency") or "").strip().upper()
        amount = decimal_or_zero(balance.get("total_amount") or balance.get("balance"))
        if not currency or amount == 0:
            continue
        rows.append(
            {
                "as_of": as_of,
                "broker": "Longbridge",
                "account_id": account_id,
                "symbol": "CASH",
                "underlying": currency,
                "instrument_type": "cash",
                "direction": "long",
                "quantity": "1",
                "avg_cost": decimal_text(amount),
                "market_price": decimal_text(amount),
                "market_value": decimal_text(abs(amount)),
                "currency": currency,
                "unrealized_pnl": "0",
                "realized_pnl": "0",
                "delta_exposure": "0",
                "notional_exposure": "0",
                "theme_id": "cash",
                "source_timestamp": as_of,
                "notes": "Longbridge CLI portfolio JSON cash balance",
            }
        )
    return rows


def portfolio_rows(payload: dict[str, Any], *, as_of: str, account_id: str, include_cash: bool) -> list[dict[str, str]]:
    holdings = payload.get("holdings")
    if not isinstance(holdings, list):
        raise SystemExit("Longbridge CLI adapter expected a holdings list")

    rows = [
        row
        for row in (position_row(holding, as_of=as_of, account_id=account_id) for holding in holdings if isinstance(holding, dict))
        if row
    ]
    if include_cash:
        rows.extend(cash_rows(payload, as_of=as_of, account_id=account_id))
    return rows


def write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PORTFOLIO_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PORTFOLIO_HEADER})


def main() -> int:
    args = parse_args()
    payload = read_json(args.portfolio_json)
    rows = portfolio_rows(
        payload,
        as_of=args.as_of,
        account_id=args.account_id,
        include_cash=not args.no_cash,
    )
    write_snapshot(Path(args.output).expanduser(), rows)
    print(f"Longbridge CLI adapter wrote {len(rows)} row(s) to {args.output}")
    print("No live broker reads; consumed saved Longbridge CLI JSON only.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
