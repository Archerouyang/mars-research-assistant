#!/usr/bin/env python3
"""Regression coverage for unscoped Daily Ops Board-first routing."""

from __future__ import annotations

from pathlib import Path

from daily_ops_routing import resolve_daily_ops_route


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    pending = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        broker_authorized=False,
        portfolio_data_ready=False,
    )
    require(
        pending == ("macro_board_or_blocker", "request_read_only_broker_authorization"),
        "unscoped start must show Macro before requesting broker authorization",
    )

    ready = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        broker_authorized=True,
        portfolio_data_ready=True,
    )
    require(
        ready == (
            "macro_board_or_blocker",
            "portfolio_risk_board",
            "ask_user_to_select_instrument",
        ),
        "authorized complete holdings must produce both baseline Boards before PA",
    )

    portfolio_gap = resolve_daily_ops_route(
        intent="unscoped_daily_start",
        broker_authorized=True,
        portfolio_data_ready=False,
    )
    require(
        portfolio_gap == ("macro_board_or_blocker", "portfolio_data_gap"),
        "missing portfolio fields must not be replaced by individual-instrument analysis",
    )

    explicit_instrument = resolve_daily_ops_route(
        intent="instrument_request",
        broker_authorized=False,
        portfolio_data_ready=False,
    )
    require(
        explicit_instrument == ("instrument_research_or_price_action",),
        "an explicitly named instrument may take the focused path",
    )

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    operations = (ROOT / "references" / "operations.md").read_text(encoding="utf-8")
    template = (
        ROOT / "assets" / "templates" / "daily-ops-orchestrator.md"
    ).read_text(encoding="utf-8")
    require("## Unscoped Daily Ops Baseline" in skill, "Skill must expose the Board-first baseline")
    require(
        "The\nunscoped Daily Ops baseline below is a required exception." in skill,
        "the shorter-path rule must not override the unscoped Board baseline",
    )
    require("## Unscoped Daily Ops Baseline" in operations, "operations must own the Board-first baseline")
    require("## 无标的 Daily Ops 启动基线" in template, "Daily Ops template must retain the Board-first baseline")

    print("daily ops routing selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
