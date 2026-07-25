#!/usr/bin/env python3
"""Focused behavior checks for broker normalization product knowledge."""

from __future__ import annotations

from ibkr_connector_adapter import position_row as ibkr_position_row
from longbridge_cli_adapter import position_row as longbridge_position_row
from product_knowledge import effective_exposure, normalize_symbol, product_knowledge


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(normalize_symbol(" tsmx.us ") == "TSMX", "market suffix normalization drifted")
    require(product_knowledge("NVDA").underlying == "NVDA", "equity knowledge drifted")
    require(product_knowledge("TSMX").leverage_multiple == 2.0, "known product metadata drifted")
    require(not product_knowledge("mystery.us").known, "unknown product must remain explicit")
    require(effective_exposure("SQQQ", 100.0) == -300.0, "inverse product direction drifted")

    longbridge = longbridge_position_row({"symbol": "TSMX.US", "currency": "USD", "quantity": "2", "cost_price": "90", "market_price": "100", "market_value": "200"}, as_of="2026-07-20T00:00:00Z", account_id="fixture")
    require((longbridge["instrument_type"], longbridge["underlying"], longbridge["theme_id"]) == ("leveraged_etf", "TSM", "ai_hardware_leverage"), "Longbridge normalization drifted")

    ibkr = ibkr_position_row({"contract_description": "KORU", "asset_class": "STK", "currency": "USD", "position": "1", "average_price": "90", "market_price": "100", "market_value": "100", "unrealized_pnl": "10"}, as_of="2026-07-20T00:00:00Z", account_id="fixture")
    require((ibkr["instrument_type"], ibkr["underlying"], ibkr["theme_id"]) == ("leveraged_etf", "EWY", "korea_equity_leverage"), "IBKR normalization drifted")
    print("product knowledge selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
