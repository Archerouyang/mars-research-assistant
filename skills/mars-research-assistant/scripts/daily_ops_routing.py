#!/usr/bin/env python3
"""Deterministic, no-I/O routing for unscoped Mars Daily Ops phases."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


MACRO_STATES = frozenset({"pending", "delivered", "blocked"})
PORTFOLIO_STATES = frozenset(
    {"not_read", "ready", "option_overlay_partial", "core_gap"}
)


@dataclass(frozen=True)
class DailyOpsRoute:
    """Required and forbidden actions for exactly one Daily Ops phase."""

    required_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]


def resolve_daily_ops_route(
    *,
    intent: str,
    macro_state: str,
    broker_authorized: bool,
    portfolio_state: str,
) -> DailyOpsRoute:
    """Return one phase's required Board or data action without side effects.

    An unscoped workflow is intentionally stateful: it cannot use a prose market
    summary in place of the Macro Board or use incomplete option overlays to
    skip the Portfolio Risk Board. A directly named instrument remains focused.
    """

    if intent == "instrument_request":
        return DailyOpsRoute(("instrument_research_or_price_action",), ())
    if intent != "unscoped_daily_start":
        raise ValueError("daily_ops_intent_invalid")
    if macro_state not in MACRO_STATES:
        raise ValueError("daily_ops_macro_state_invalid")
    if portfolio_state not in PORTFOLIO_STATES:
        raise ValueError("daily_ops_portfolio_state_invalid")
    if not broker_authorized and portfolio_state != "not_read":
        raise ValueError("portfolio_state_requires_broker_authorization")

    if macro_state == "pending":
        return DailyOpsRoute(
            ("render_macro_research_result_or_blocker",),
            (
                "prose_only_macro_summary",
                "custom_html_board",
                "request_read_only_broker_authorization",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
            ),
        )
    if macro_state == "blocked":
        return DailyOpsRoute(
            ("macro_data_acquisition_blocker",),
            (
                "custom_html_board",
                "request_read_only_broker_authorization",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
            ),
        )
    if not broker_authorized:
        return DailyOpsRoute(
            ("request_read_only_broker_authorization",),
            ("portfolio_risk_board", "individual_research", "price_action"),
        )
    if portfolio_state == "not_read":
        return DailyOpsRoute(
            ("read_portfolio_baseline",),
            ("individual_research", "price_action", "request_secondary_broker"),
        )
    if portfolio_state == "ready":
        return DailyOpsRoute(
            ("render_portfolio_research_result", "ask_user_to_select_instrument"),
            (
                "custom_html_board",
                "individual_research",
                "price_action",
                "request_secondary_broker",
            ),
        )
    if portfolio_state == "option_overlay_partial":
        return DailyOpsRoute(
            (
                "render_portfolio_research_result_partial",
                "ask_user_to_select_instrument",
            ),
            (
                "custom_html_board",
                "individual_research",
                "price_action",
                "request_secondary_broker",
            ),
        )
    return DailyOpsRoute(
        ("portfolio_data_gap",),
        ("individual_research", "price_action", "request_secondary_broker"),
    )


def _parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intent",
        required=True,
        choices=("unscoped_daily_start", "instrument_request"),
    )
    parser.add_argument("--macro-state", required=True, choices=sorted(MACRO_STATES))
    parser.add_argument("--broker-authorized", required=True, type=_parse_bool)
    parser.add_argument(
        "--portfolio-state",
        required=True,
        choices=sorted(PORTFOLIO_STATES),
    )
    args = parser.parse_args()
    route = resolve_daily_ops_route(
        intent=args.intent,
        macro_state=args.macro_state,
        broker_authorized=args.broker_authorized,
        portfolio_state=args.portfolio_state,
    )
    print(json.dumps(asdict(route), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
