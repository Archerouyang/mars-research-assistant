#!/usr/bin/env python3
"""Behavior checks for the consented factual Holdings Display."""

from __future__ import annotations

import json
from pathlib import Path

from holdings_display import build_holdings_display, render_holdings_display_markdown
from ibkr_holdings_adapter import cash_rows as ibkr_cash_rows
from ibkr_holdings_adapter import position_rows as ibkr_position_rows


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-25T12:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def main() -> int:
    ibkr_rows = ibkr_position_rows(
        load("ibkr-connector-positions-2026-06-24.json"),
        retrieved_at=AS_OF,
    ) + ibkr_cash_rows(
        load("ibkr-connector-balances-2026-06-24.json"),
        retrieved_at=AS_OF,
    )
    display = build_holdings_display(ibkr_rows, consented_at=AS_OF)
    markdown = render_holdings_display_markdown(display)

    require(display["broker"] == "IBKR", "display must retain the only supported broker")
    require(len(display["positions"]) == 2, "cash rows must not be presented as positions")
    require(len(display["cash"]) == 1, "cash must remain per-currency without conversion")
    require(
        set(ibkr_rows[0])
        == {
            "row_type",
            "broker",
            "symbol",
            "quantity",
            "latest_price",
            "market_value",
            "cost",
            "unrealized_pnl",
            "currency",
            "retrieved_at",
        }
        and set(ibkr_rows[-1])
        == {"row_type", "broker", "currency", "cash", "retrieved_at"},
        "IBKR normalization must retain only approved holdings facts",
    )
    require(
        set(display["positions"][0])
        == {
            "broker",
            "symbol",
            "quantity",
            "latest_price",
            "market_value",
            "cost",
            "unrealized_pnl",
            "currency",
            "retrieved_at",
        },
        "position display must retain only the factual approved fields",
    )
    require(
        "account_id" not in markdown,
        "display must not expose account identifiers",
    )
    require(
        "| IBKR | CRDO | 12 | 48.25 | 579 | 42.5 | 69 | USD |" in markdown,
        "display must preserve broker, symbol, quantity, price, value, cost, and P&L",
    )
    require(
        "| IBKR | USD | 150.25 |" in markdown,
        "cash must be displayed without cross-currency aggregation",
    )
    require(
        not any(term in markdown.casefold() for term in ("concentration", "stress", "leverage", "risk score", "delta exposure")),
        "display must not reintroduce derived risk calculations",
    )

    incomplete = [dict(ibkr_rows[0])]
    incomplete[0]["latest_price"] = ""
    incomplete_display = build_holdings_display(incomplete, consented_at=AS_OF)
    require(
        incomplete_display["positions"][0]["latest_price"] == "不可用",
        "a missing factual field must remain visibly unavailable",
    )

    missing_broker = [dict(ibkr_rows[0])]
    missing_broker[0]["broker"] = ""
    try:
        build_holdings_display(missing_broker, consented_at=AS_OF)
    except ValueError as error:
        require(
            str(error) == "holdings_display_broker_not_supported",
            "missing source identity must be rejected",
        )
    else:
        raise AssertionError("missing holdings broker must be rejected")

    longbridge = dict(ibkr_rows[0])
    longbridge["broker"] = "Longbridge"
    try:
        build_holdings_display([longbridge], consented_at=AS_OF)
    except ValueError as error:
        require(str(error) == "holdings_display_broker_not_supported", "Longbridge must be rejected")
    else:
        raise AssertionError("Longbridge holdings must be rejected")

    print("holdings display selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
