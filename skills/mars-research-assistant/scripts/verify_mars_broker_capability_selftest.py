#!/usr/bin/env python3
"""Regression coverage for IBKR-only capability discovery."""

from __future__ import annotations

from broker_capability import (
    CAPABILITY_PROBE_VERSION,
    probe_broker_capabilities,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    active = probe_broker_capabilities(
        task_tool_names=(
            "mcp__codex_apps__interactive_brokers__ibkr__get_account_positions",
            "mcp__codex_apps__interactive_brokers__ibkr__get_account_balances",
            "mcp__codex_apps__interactive_brokers__ibkr__get_price_history",
            "mcp__codex_apps__interactive_brokers__ibkr__search_contracts",
        ),
    )
    require(active["capability_state"] == "checked", "capability probe must retain its checked state")
    probes = active["capability_probes"]
    require(isinstance(probes, dict), "confirmed probe must return a normalized capability mapping")
    require(
        probes == {
            "ibkr": {
                "read_only": "available",
                "market_data": "available",
                "holdings": "available",
                "probe_version": CAPABILITY_PROBE_VERSION,
            },
        },
        "the capability boundary must expose only IBKR",
    )

    unavailable = probe_broker_capabilities()
    require(
        unavailable["capability_probes"] == {
            "ibkr": {
                "read_only": "unavailable",
                "market_data": "unavailable",
                "holdings": "unavailable",
                "probe_version": CAPABILITY_PROBE_VERSION,
            },
        },
        "a task-invisible IBKR capability must remain unavailable",
    )

    unrelated = probe_broker_capabilities(
        task_tool_names=("mcp__codex_apps__github_list_repositories",),
    )
    require(
        unrelated["capability_probes"]["ibkr"]["read_only"] == "unavailable",
        "an unrelated task tool must not make IBKR available",
    )

    market_only = probe_broker_capabilities(
        task_tool_names=(
            "mcp__codex_apps__interactive_brokers__ibkr__get_price_history",
            "mcp__codex_apps__interactive_brokers__ibkr__search_contracts",
        ),
    )
    require(
        market_only["capability_probes"]["ibkr"]["market_data"] == "available"
        and market_only["capability_probes"]["ibkr"]["holdings"] == "unavailable",
        "market and holdings capabilities must remain distinct",
    )
    partial_market = probe_broker_capabilities(
        task_tool_names=(
            "mcp__codex_apps__interactive_brokers__ibkr__search_contracts",
        ),
    )
    require(
        partial_market["capability_probes"]["ibkr"]["market_data"] == "unavailable",
        "contract search alone must not claim usable market data",
    )
    partial_holdings = probe_broker_capabilities(
        task_tool_names=(
            "mcp__codex_apps__interactive_brokers__ibkr__get_account_balances",
        ),
    )
    require(
        partial_holdings["capability_probes"]["ibkr"]["holdings"] == "unavailable",
        "balances alone must not claim a complete holdings display capability",
    )

    print("mars broker capability selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
