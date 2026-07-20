#!/usr/bin/env python3
"""Focused behavior checks for Broker-Live Data View product knowledge."""

from __future__ import annotations

from ibkr_connector_adapter import position_row as ibkr_position_row
from longbridge_cli_adapter import position_row as longbridge_position_row
from portfolio_panel_adapter import build_portfolio_panel
from position_daily_report import Position, is_leveraged_product
from product_knowledge import effective_exposure, normalize_symbol, product_knowledge
from repair_portfolio_snapshot import repair_row


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_known_products() -> None:
    require(normalize_symbol(" tsmx.us ") == "TSMX", "market suffix normalization drifted")

    nvda = product_knowledge("NVDA")
    require(
        (
            nvda.known,
            nvda.product_type,
            nvda.underlying,
            nvda.underlying_kind,
            nvda.direction,
            nvda.leverage_multiple,
            nvda.theme,
        )
        == (True, "stock_common", "NVDA", "direct", "long", 1.0, "ai_hardware"),
        "ordinary equity knowledge drifted",
    )

    qqq = product_knowledge("QQQ.US")
    require(
        (qqq.product_type, qqq.underlying, qqq.direction, qqq.leverage_multiple, qqq.theme)
        == ("etf_common", "QQQ", "long", 1.0, "tech_beta"),
        "ordinary ETF knowledge drifted",
    )

    expected = {
        "KORU": ("EWY", "benchmark_proxy", "long", 3.0, "korea_equity_leverage"),
        "MVLL": ("MRVL", "single_name", "long", 2.0, "ai_hardware_leverage"),
        "TSMX": ("TSM", "single_name", "long", 2.0, "ai_hardware_leverage"),
        "SQQQ": ("QQQ", "benchmark_proxy", "inverse", 3.0, "tech_inverse_leverage"),
    }
    for symbol, facts in expected.items():
        product = product_knowledge(symbol)
        require(product.known, f"{symbol} should be known")
        require(product.product_type == "leveraged_etf", f"{symbol} product type drifted")
        require(
            (
                product.underlying,
                product.underlying_kind,
                product.direction,
                product.leverage_multiple,
                product.theme,
            )
            == facts,
            f"{symbol} product knowledge drifted",
        )

    require(effective_exposure("NVDA", 100.0) == 100.0, "ordinary equity exposure drifted")
    require(effective_exposure("SQQQ", 100.0) == -300.0, "inverse ETF exposure drifted")
    require(
        effective_exposure("TSMX", 100.0, position_direction="short") == -200.0,
        "short leveraged ETF direction drifted",
    )
    require(
        effective_exposure("SQQQ", 100.0, position_direction="short") == 300.0,
        "short inverse ETF direction drifted",
    )
    require(
        effective_exposure("NVDA", 100.0, 0.0) == 0.0,
        "explicit zero source exposure was replaced",
    )


def verify_unknown_fails_closed() -> None:
    unknown = product_knowledge(" mystery.us ")
    require(unknown.symbol == "MYSTERY", "unknown symbol was not normalized")
    require(not unknown.known, "unknown product must remain explicit")
    require(unknown.product_type == "unknown", "unknown product type was invented")
    require(unknown.underlying is None, "unknown look-through was invented")
    require(unknown.underlying_kind == "unknown", "unknown underlying kind was invented")
    require(unknown.direction == "unknown", "unknown product direction was invented")
    require(unknown.leverage_multiple is None, "unknown leverage was invented")
    require(unknown.theme == "unmapped", "unknown theme was invented")


def snapshot_row(symbol: str, **overrides: str) -> dict[str, str]:
    row = {
        "as_of": "2026-07-20T00:00:00Z",
        "broker": "fixture",
        "account_id": "fixture",
        "symbol": symbol,
        "underlying": symbol,
        "instrument_type": "stock_common",
        "direction": "long",
        "quantity": "1",
        "avg_cost": "100",
        "market_price": "100",
        "market_value": "100",
        "currency": "USD",
        "unrealized_pnl": "0",
        "realized_pnl": "0",
        "delta_exposure": "100",
        "notional_exposure": "100",
        "theme_id": "unmapped",
        "source_timestamp": "2026-07-20T00:00:00Z",
        "notes": "public fixture",
    }
    row.update(overrides)
    return row


def verify_adapter_consistency() -> None:
    longbridge = longbridge_position_row(
        {
            "symbol": "TSMX.US",
            "name": "Direxion Daily TSM Bull 2X Shares",
            "currency": "USD",
            "quantity": "2",
            "cost_price": "90",
            "market_price": "100",
            "market_value": "200",
        },
        as_of="2026-07-20T00:00:00Z",
        account_id="fixture",
    )
    require(
        (
            longbridge["symbol"],
            longbridge["instrument_type"],
            longbridge["underlying"],
            longbridge["theme_id"],
            longbridge["delta_exposure"],
        )
        == ("TSMX.US", "leveraged_etf", "TSM", "ai_hardware_leverage", "400"),
        "Longbridge adapter did not consume canonical product knowledge",
    )

    ibkr = ibkr_position_row(
        {
            "contract_description": "KORU",
            "asset_class": "STK",
            "currency": "USD",
            "position": "1",
            "average_price": "90",
            "market_price": "100",
            "market_value": "100",
            "unrealized_pnl": "10",
        },
        as_of="2026-07-20T00:00:00Z",
        account_id="fixture",
    )
    require(
        (
            ibkr["instrument_type"],
            ibkr["underlying"],
            ibkr["theme_id"],
            ibkr["delta_exposure"],
        )
        == ("leveraged_etf", "EWY", "korea_equity_leverage", "300"),
        "IBKR adapter did not consume canonical product knowledge",
    )

    short_longbridge = longbridge_position_row(
        {
            "symbol": "TSMX.US",
            "currency": "USD",
            "quantity": "-1",
            "market_price": "100",
            "market_value": "-100",
        },
        as_of="2026-07-20T00:00:00Z",
        account_id="fixture",
    )
    require(short_longbridge["delta_exposure"] == "-200", "short TSMX sign drifted")

    short_ibkr = ibkr_position_row(
        {
            "contract_description": "SQQQ",
            "asset_class": "STK",
            "currency": "USD",
            "position": "-1",
            "market_price": "100",
            "market_value": "-100",
        },
        as_of="2026-07-20T00:00:00Z",
        account_id="fixture",
    )
    require(short_ibkr["delta_exposure"] == "300", "short inverse ETF sign drifted")

    repaired = repair_row(snapshot_row("MVLL.US"))
    require(
        (
            repaired["symbol"],
            repaired["instrument_type"],
            repaired["underlying"],
            repaired["theme_id"],
        )
        == ("MVLL.US", "leveraged_etf", "MRVL", "ai_hardware_leverage"),
        "snapshot repair did not consume canonical product knowledge",
    )

    panel = build_portfolio_panel(
        [snapshot_row("TSMX.US")],
        as_of="2026-07-20T00:00:00Z",
        reconciliation="reconciled",
        privacy="public_fixture",
    )
    symbol_exposure = panel["payload"]["aggregations"]["by_symbol"][0]
    require(symbol_exposure["label"] == "TSM", "Portfolio Panel underlying drifted")
    require(symbol_exposure["delta_exposure"] == 200.0, "Portfolio Panel leverage drifted")


def verify_unknown_consumers_fail_closed() -> None:
    unknown = longbridge_position_row(
        {
            "symbol": "MYSTERY.US",
            "name": "Mystery Daily Bull 2X ETF",
            "currency": "USD",
            "quantity": "1",
            "market_price": "100",
            "market_value": "100",
        },
        as_of="2026-07-20T00:00:00Z",
        account_id="fixture",
    )
    require(unknown["instrument_type"] == "etf_common", "source ETF mapping was lost")
    require(unknown["underlying"] == "MYSTERY", "source direct symbol normalization was lost")
    require(unknown["theme_id"] == "unmapped", "unknown theme was invented")
    require(unknown["delta_exposure"] == "100", "unknown leverage was invented")

    repaired = repair_row(
        snapshot_row(
            "MYSTERY.US",
            underlying="MYSTERY",
            instrument_type="etf_common",
            notes="Mystery Daily Bull 2X ETF",
        )
    )
    require(repaired["instrument_type"] == "etf_common", "repair invented unknown leverage")
    require(repaired["underlying"] == "MYSTERY", "repair invented unknown look-through")
    require(repaired["theme_id"] == "unmapped", "repair invented unknown theme")

    position = Position(
        as_of="2026-07-20T00:00:00Z",
        broker="fixture",
        account_id="fixture",
        symbol="MYSTERY",
        underlying="MYSTERY",
        instrument_type="etf_common",
        direction="long",
        market_value=100.0,
        unrealized_pnl=0.0,
        delta_exposure=100.0,
        notional_exposure=100.0,
        theme_id="unmapped",
        source_timestamp="2026-07-20T00:00:00Z",
        notes="Mystery Daily Bull 2X ETF",
    )
    require(not is_leveraged_product(position), "daily report invented unknown leverage")

    zero_panel = build_portfolio_panel(
        [snapshot_row("NVDA", delta_exposure="0", notional_exposure="0")],
        as_of="2026-07-20T00:00:00Z",
        reconciliation="reconciled",
        privacy="public_fixture",
    )
    zero_totals = zero_panel["payload"]["totals"]
    require(zero_totals["net_delta_exposure"] == 0.0, "explicit zero delta was replaced")
    require(zero_totals["gross_notional_exposure"] == 0.0, "explicit zero notional was replaced")


def main() -> int:
    verify_known_products()
    verify_unknown_fails_closed()
    verify_adapter_consistency()
    verify_unknown_consumers_fail_closed()
    print("product knowledge selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
