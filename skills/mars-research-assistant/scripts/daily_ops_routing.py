#!/usr/bin/env python3
"""Deterministic routing guard for unscoped Mars Daily Ops starts."""

from __future__ import annotations


def resolve_daily_ops_route(
    *,
    intent: str,
    broker_authorized: bool,
    portfolio_data_ready: bool,
) -> tuple[str, ...]:
    """Return the minimum next actions without reading data or mutating state.

    An unscoped Daily Ops start must establish the public macro regime first and,
    once authorized holdings are usable, render the Portfolio Risk Board before
    proposing an instrument-specific workflow. A user who directly requests a
    named instrument keeps the focused route.
    """

    if intent == "instrument_request":
        return ("instrument_research_or_price_action",)
    if intent != "unscoped_daily_start":
        raise ValueError("daily_ops_intent_invalid")
    if portfolio_data_ready and not broker_authorized:
        raise ValueError("portfolio_data_requires_broker_authorization")

    actions = ["macro_board_or_blocker"]
    if not broker_authorized:
        actions.append("request_read_only_broker_authorization")
    elif not portfolio_data_ready:
        actions.append("portfolio_data_gap")
    else:
        actions.extend(("portfolio_risk_board", "ask_user_to_select_instrument"))
    return tuple(actions)
