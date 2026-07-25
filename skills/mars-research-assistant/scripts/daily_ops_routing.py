#!/usr/bin/env python3
"""Deterministic, no-I/O routing for unscoped Mars Daily Ops phases."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


CAPABILITY_STATES = frozenset({"pending", "checked"})
MACRO_STATES = frozenset({"pending", "delivered", "blocked"})
PORTFOLIO_REVIEW_STATES = frozenset({"undecided", "requested", "declined"})
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
    capability_state: str,
    macro_state: str,
    portfolio_review: str,
    broker_authorized: bool,
    portfolio_state: str,
) -> DailyOpsRoute:
    """Return one phase's required Board or data action without side effects.

    An unscoped workflow is intentionally stateful: source capability is checked
    before public acquisition, account data needs its own portfolio-review
    consent, and individual research, Price Action, and trade guidance remain
    user-selected. A directly named instrument remains focused.
    """

    if intent == "instrument_request":
        return DailyOpsRoute(("instrument_research_or_price_action",), ())
    if intent != "unscoped_daily_start":
        raise ValueError("daily_ops_intent_invalid")
    if capability_state not in CAPABILITY_STATES:
        raise ValueError("daily_ops_capability_state_invalid")
    if macro_state not in MACRO_STATES:
        raise ValueError("daily_ops_macro_state_invalid")
    if portfolio_review not in PORTFOLIO_REVIEW_STATES:
        raise ValueError("daily_ops_portfolio_review_state_invalid")
    if portfolio_state not in PORTFOLIO_STATES:
        raise ValueError("daily_ops_portfolio_state_invalid")
    if not broker_authorized and portfolio_state != "not_read":
        raise ValueError("portfolio_state_requires_broker_authorization")

    if capability_state == "pending":
        return DailyOpsRoute(
            ("check_broker_capability",),
            (
                "prose_only_macro_summary",
                "render_macro_research_result_or_blocker",
                "custom_html_board",
                "request_read_only_broker_authorization",
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if macro_state == "pending":
        return DailyOpsRoute(
            ("render_macro_research_result_or_blocker",),
            (
                "prose_only_macro_summary",
                "custom_html_board",
                "request_read_only_broker_authorization",
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if macro_state == "blocked":
        return DailyOpsRoute(
            ("macro_data_acquisition_blocker",),
            (
                "custom_html_board",
                "request_read_only_broker_authorization",
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if portfolio_review == "undecided":
        return DailyOpsRoute(
            ("ask_portfolio_review_consent",),
            (
                "request_read_only_broker_authorization",
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if portfolio_review == "declined":
        return DailyOpsRoute(
            ("ask_user_to_select_research_request",),
            (
                "request_read_only_broker_authorization",
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if not broker_authorized:
        return DailyOpsRoute(
            ("request_read_only_broker_authorization",),
            (
                "read_portfolio_baseline",
                "portfolio_risk_board",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if portfolio_state == "not_read":
        return DailyOpsRoute(
            ("read_portfolio_baseline",),
            (
                "individual_research",
                "price_action",
                "trade_guidance",
                "request_secondary_broker",
            ),
        )
    if portfolio_state == "ready":
        return DailyOpsRoute(
            (
                "render_portfolio_research_result",
                "ask_user_to_select_research_request",
            ),
            (
                "custom_html_board",
                "individual_research",
                "price_action",
                "trade_guidance",
                "request_secondary_broker",
            ),
        )
    if portfolio_state == "option_overlay_partial":
        return DailyOpsRoute(
            (
                "render_portfolio_research_result_partial",
                "ask_user_to_select_research_request",
            ),
            (
                "custom_html_board",
                "individual_research",
                "price_action",
                "trade_guidance",
                "request_secondary_broker",
            ),
        )
    return DailyOpsRoute(
        ("portfolio_data_gap", "ask_user_to_select_research_request"),
        (
            "individual_research",
            "price_action",
            "trade_guidance",
            "request_secondary_broker",
        ),
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
    parser.add_argument(
        "--capability-state", required=True, choices=sorted(CAPABILITY_STATES)
    )
    parser.add_argument("--macro-state", required=True, choices=sorted(MACRO_STATES))
    parser.add_argument(
        "--portfolio-review", required=True, choices=sorted(PORTFOLIO_REVIEW_STATES)
    )
    parser.add_argument("--broker-authorized", required=True, type=_parse_bool)
    parser.add_argument(
        "--portfolio-state",
        required=True,
        choices=sorted(PORTFOLIO_STATES),
    )
    args = parser.parse_args()
    route = resolve_daily_ops_route(
        intent=args.intent,
        capability_state=args.capability_state,
        macro_state=args.macro_state,
        portfolio_review=args.portfolio_review,
        broker_authorized=args.broker_authorized,
        portfolio_state=args.portfolio_state,
    )
    print(json.dumps(asdict(route), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
