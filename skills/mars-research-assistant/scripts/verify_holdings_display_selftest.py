#!/usr/bin/env python3
"""Behavior checks for the consented factual Holdings Display."""

from __future__ import annotations

import json
from pathlib import Path

from holdings_display import build_holdings_display, render_holdings_display_markdown
from ibkr_connector_adapter import cash_rows as ibkr_cash_rows
from ibkr_connector_adapter import position_rows as ibkr_position_rows
from longbridge_cli_adapter import portfolio_rows as longbridge_portfolio_rows


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-25T12:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def main() -> int:
    longbridge_rows = longbridge_portfolio_rows(
        load("longbridge-portfolio-cli-2026-06-24.json"),
        as_of=AS_OF,
        account_id="private-longbridge-account",
        include_cash=True,
    )
    display = build_holdings_display(longbridge_rows, consented_at=AS_OF)
    markdown = render_holdings_display_markdown(display)

    require(display["broker"] == "Longbridge", "display must retain its single broker identity")
    require(len(display["positions"]) == 4, "cash rows must not be presented as positions")
    require(len(display["cash"]) == 2, "cash must remain per-currency without conversion")
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
        "private-longbridge-account" not in markdown,
        "display must not expose account identifiers",
    )
    require(
        "| Longbridge | CRDO.US | 100 | 121 | 12100 | 118 | 300 | USD |" in markdown,
        "display must preserve broker, symbol, quantity, price, value, cost, and P&L",
    )
    require(
        "| USD | 15000 |" in markdown and "| HKD | 1000 |" in markdown,
        "cash must be displayed without cross-currency aggregation",
    )
    require(
        not any(term in markdown.casefold() for term in ("concentration", "stress", "leverage", "risk score", "delta exposure")),
        "display must not reintroduce derived risk calculations",
    )

    ibkr_rows = ibkr_position_rows(
        load("ibkr-connector-positions-2026-06-24.json"),
        as_of=AS_OF,
        account_id="private-ibkr-account",
    ) + ibkr_cash_rows(
        load("ibkr-connector-balances-2026-06-24.json"),
        as_of=AS_OF,
        account_id="private-ibkr-account",
    )
    ibkr_display = build_holdings_display(ibkr_rows, consented_at=AS_OF)
    require(ibkr_display["broker"] == "IBKR", "IBKR snapshots must use the same factual display contract")

    incomplete = [dict(longbridge_rows[0])]
    incomplete[0]["market_price"] = ""
    incomplete_display = build_holdings_display(incomplete, consented_at=AS_OF)
    require(
        incomplete_display["positions"][0]["latest_price"] == "不可用",
        "a missing factual field must remain visibly unavailable",
    )

    mixed = [dict(longbridge_rows[0]), dict(ibkr_rows[0])]
    try:
        build_holdings_display(mixed, consented_at=AS_OF)
    except ValueError as error:
        require(str(error) == "holdings_display_single_broker_required", "mixed brokers must not be silently combined")
    else:
        raise AssertionError("mixed-broker holdings display must be rejected")

    print("holdings display selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
