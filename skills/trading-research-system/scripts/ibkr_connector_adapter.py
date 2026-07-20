#!/usr/bin/env python3
"""Normalize saved IBKR connector JSON into portfolio_snapshot.csv.

This adapter consumes JSON already returned by read-only IBKR connector tools,
such as get_account_positions and get_account_balances. It does not call IBKR,
read live broker data by itself, call market data, or perform order actions.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any

from product_knowledge import effective_exposure, product_knowledge
from record_schemas import CSV_SCHEMAS


PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])
ASSET_CLASS_MAP = {
    "CASH": "cash",
    "FUT": "future",
    "OPT": "option",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize saved IBKR connector JSON into standard portfolio_snapshot.csv."
    )
    parser.add_argument(
        "--positions-json",
        required=True,
        help="Saved JSON returned by the read-only IBKR get_account_positions tool; use '-' for stdin",
    )
    parser.add_argument(
        "--balances-json",
        help="Optional saved JSON returned by the read-only IBKR get_account_balances tool",
    )
    parser.add_argument("--output", required=True, help="Output standard portfolio_snapshot.csv path")
    parser.add_argument("--as-of", required=True, help="Snapshot timestamp, e.g. 2026-06-24T20:00:00Z")
    parser.add_argument("--account-id", default="IBKR", help="Account id label for the standard view")
    parser.add_argument(
        "--no-cash",
        action="store_true",
        help="Do not include IBKR balances as cash rows",
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
            raise SystemExit("IBKR connector adapter expected a JSON object")
        payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, dict):
        raise SystemExit("IBKR connector adapter expected a JSON object")
    return payload


def position_symbol(position: dict[str, Any]) -> str:
    return str(position.get("contract_description") or position.get("symbol") or "").strip().upper()


def infer_instrument_type(symbol: str, asset_class: str) -> str:
    product = product_knowledge(symbol)
    if product.known:
        return product.product_type
    upper_asset = asset_class.strip().upper()
    if upper_asset == "STK":
        return "stock_common"
    return ASSET_CLASS_MAP.get(upper_asset, upper_asset.lower() or "unspecified")


def direction(quantity: Decimal) -> str:
    return "short" if quantity < 0 else "long"


def position_row(position: dict[str, Any], *, as_of: str, account_id: str) -> dict[str, str]:
    symbol = position_symbol(position)
    if not symbol:
        return {}

    currency = str(position.get("currency") or "USD").strip().upper()
    quantity = decimal_or_zero(position.get("position"))
    avg_cost = decimal_or_zero(position.get("average_price"))
    market_price = decimal_or_zero(position.get("market_price"))
    market_value = decimal_or_zero(position.get("market_value"))
    if market_value == 0 and market_price != 0:
        market_value = quantity * market_price
    unrealized = decimal_or_zero(position.get("unrealized_pnl"))
    asset_class = str(position.get("asset_class") or "").strip().upper()
    instrument_type = infer_instrument_type(symbol, asset_class)
    product = product_knowledge(symbol)
    underlying = product.underlying if product.known and product.underlying else symbol
    row_direction = direction(quantity)
    delta_exposure = (
        effective_exposure(
            symbol,
            float(abs(market_value)),
            position_direction=row_direction,
        )
        if instrument_type != "cash"
        else 0.0
    )

    return {
        "as_of": as_of,
        "broker": "IBKR",
        "account_id": account_id,
        "symbol": symbol,
        "underlying": currency if instrument_type == "cash" else underlying,
        "instrument_type": instrument_type,
        "direction": row_direction,
        "quantity": decimal_text(abs(quantity)),
        "avg_cost": decimal_text(avg_cost),
        "market_price": decimal_text(market_price),
        "market_value": decimal_text(abs(market_value)),
        "currency": currency,
        "unrealized_pnl": decimal_text(unrealized),
        "realized_pnl": "0",
        "delta_exposure": decimal_text(delta_exposure),
        "notional_exposure": decimal_text(delta_exposure),
        "theme_id": "cash" if instrument_type == "cash" else product.theme,
        "source_timestamp": as_of,
        "notes": f"IBKR connector positions JSON; asset_class={asset_class or 'unknown'}",
    }


def position_rows(payload: dict[str, Any], *, as_of: str, account_id: str) -> list[dict[str, str]]:
    positions = payload.get("positions")
    if not isinstance(positions, list):
        raise SystemExit("IBKR connector adapter expected a positions list")
    return [
        row
        for row in (position_row(position, as_of=as_of, account_id=account_id) for position in positions if isinstance(position, dict))
        if row
    ]


def cash_rows(payload: dict[str, Any], *, as_of: str, account_id: str) -> list[dict[str, str]]:
    balances = payload.get("balances")
    if not isinstance(balances, list):
        return []

    explicit_currencies = {
        str(balance.get("currency") or "").strip().upper()
        for balance in balances
        if isinstance(balance, dict)
    }
    skip_base = "USD" in explicit_currencies
    rows: list[dict[str, str]] = []
    for balance in balances:
        if not isinstance(balance, dict):
            continue
        currency = str(balance.get("currency") or "").strip().upper()
        if not currency:
            continue
        if currency == "BASE" and skip_base:
            continue
        if currency == "BASE":
            currency = "USD"
        amount = decimal_or_zero(balance.get("cash_balance") or balance.get("settled_cash"))
        if amount == 0:
            continue
        rows.append(
            {
                "as_of": as_of,
                "broker": "IBKR",
                "account_id": account_id,
                "symbol": "CASH",
                "underlying": currency,
                "instrument_type": "cash",
                "direction": direction(amount),
                "quantity": "1",
                "avg_cost": decimal_text(abs(amount)),
                "market_price": decimal_text(abs(amount)),
                "market_value": decimal_text(abs(amount)),
                "currency": currency,
                "unrealized_pnl": "0",
                "realized_pnl": decimal_text(balance.get("realized_pnl") or "0"),
                "delta_exposure": "0",
                "notional_exposure": "0",
                "theme_id": "cash",
                "source_timestamp": as_of,
                "notes": "IBKR connector balances JSON cash balance",
            }
        )
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
    rows = position_rows(read_json(args.positions_json), as_of=args.as_of, account_id=args.account_id)
    if args.balances_json and not args.no_cash:
        rows.extend(cash_rows(read_json(args.balances_json), as_of=args.as_of, account_id=args.account_id))

    write_snapshot(Path(args.output).expanduser(), rows)
    print(f"IBKR connector adapter wrote {len(rows)} row(s) to {args.output}")
    print("No live broker reads; consumed saved IBKR connector JSON only.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
