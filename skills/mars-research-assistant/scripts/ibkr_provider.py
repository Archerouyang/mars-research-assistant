#!/usr/bin/env python3
"""Single-provider boundary for Mars Research Assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


PROVIDER_ID = "ibkr"
BROKER_LABEL = "IBKR"
MARKET_SOURCE_ID = "ibkr_market_data"
TASK_TOOL_PREFIX = "mcp__codex_apps__interactive_brokers__"
MARKET_TOOL_REQUIREMENTS = (
    ("get_price_history",),
    ("search_contract",),
)
HOLDINGS_TOOL_REQUIREMENTS = (
    ("get_account_positions",),
    ("get_account_balances", "get_cash_balance"),
)
LEGACY_CONFIG_FILE = "mars-runtime-config.json"


def capability_statuses(task_tool_names: Iterable[str] = ()) -> dict[str, str]:
    """Report task-visible IBKR capability families without calling a tool."""

    names = tuple(
        name.casefold()
        for name in task_tool_names
        if isinstance(name, str) and name.startswith(TASK_TOOL_PREFIX)
    )
    market_data = _requirements_status(names, MARKET_TOOL_REQUIREMENTS)
    holdings = _requirements_status(names, HOLDINGS_TOOL_REQUIREMENTS)
    return {
        "read_only": (
            "available"
            if "available" in {market_data, holdings}
            else "unavailable"
        ),
        "market_data": market_data,
        "holdings": holdings,
    }


def _requirements_status(
    names: tuple[str, ...],
    requirements: tuple[tuple[str, ...], ...],
) -> str:
    return (
        "available"
        if all(
            any(marker in name for name in names for marker in alternatives)
            for alternatives in requirements
        )
        else "unavailable"
    )


def require_market_source(source_id: object) -> None:
    """Reject every broker-market source except the supported IBKR source."""

    if source_id != MARKET_SOURCE_ID:
        raise ValueError("broker_market_source_not_supported")


def require_holdings_broker(broker: object) -> None:
    """Reject holdings normalized from any broker other than IBKR."""

    if str(broker or "").strip().casefold() != BROKER_LABEL.casefold():
        raise ValueError("holdings_display_broker_not_supported")


def legacy_configuration_status(runtime_dir: str | Path) -> dict[str, str]:
    """Report a retired broker-choice config without reading its contents."""

    config = Path(runtime_dir).expanduser() / LEGACY_CONFIG_FILE
    if config.exists():
        return {
            "status": "version_incompatible",
            "reason": "legacy_broker_choice_config_retired",
        }
    return {"status": "absent", "reason": "no_broker_choice_config_required"}
