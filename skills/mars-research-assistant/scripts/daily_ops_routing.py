#!/usr/bin/env python3
"""Deterministic, no-I/O routing for guided Mars Daily Ops."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


CAPABILITY_STATES = frozenset({"pending", "checked"})
MACRO_STATES = frozenset({"pending", "delivered", "blocked"})
HOLDINGS_REVIEW_STATES = frozenset({"undecided", "requested", "declined"})
HOLDINGS_STATES = frozenset({"not_read", "displayed", "unavailable"})


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
    holdings_review: str,
    holdings_state: str,
) -> DailyOpsRoute:
    """Return one guided Daily Ops action without performing I/O.

    Capability checks establish eligible market/macro sources. Macro is the
    default artifact for an unscoped start. Holdings Display is optional and
    can only follow fresh user consent. A named instrument always bypasses the
    optional holdings step.
    """

    if intent == "instrument_request":
        return DailyOpsRoute(("run_named_instrument_research_bundle",), ())
    if intent != "unscoped_daily_start":
        raise ValueError("daily_ops_intent_invalid")
    if capability_state not in CAPABILITY_STATES:
        raise ValueError("daily_ops_capability_state_invalid")
    if macro_state not in MACRO_STATES:
        raise ValueError("daily_ops_macro_state_invalid")
    if holdings_review not in HOLDINGS_REVIEW_STATES:
        raise ValueError("daily_ops_holdings_review_state_invalid")
    if holdings_state not in HOLDINGS_STATES:
        raise ValueError("daily_ops_holdings_state_invalid")

    if capability_state == "pending":
        return DailyOpsRoute(
            ("check_broker_capability",),
            (
                "prose_only_macro_summary",
                "acquire_macro_fields_and_render_research_result_or_blocker",
                "read_ibkr_holdings",
                "render_holdings_display",
                "derived_holdings_risk_analysis",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if macro_state == "pending":
        return DailyOpsRoute(
            ("acquire_macro_fields_and_render_research_result_or_blocker",),
            (
                "prose_only_macro_summary",
                "read_ibkr_holdings",
                "render_holdings_display",
                "derived_holdings_risk_analysis",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if macro_state == "blocked":
        return DailyOpsRoute(
            ("macro_data_acquisition_blocker",),
            (
                "render_holdings_display",
                "derived_holdings_risk_analysis",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if holdings_review == "requested" and holdings_state == "not_read":
        return DailyOpsRoute(
            ("read_consented_ibkr_holdings_and_render_display",),
            (
                "derived_holdings_risk_analysis",
                "individual_research",
                "price_action",
                "trade_guidance",
            ),
        )
    if holdings_review == "requested" and holdings_state == "unavailable":
        return DailyOpsRoute(
            ("holdings_display_data_gap", "offer_next_research_action"),
            ("derived_holdings_risk_analysis", "individual_research", "price_action", "trade_guidance"),
        )
    return DailyOpsRoute(
        ("offer_next_research_action",),
        ("derived_holdings_risk_analysis", "individual_research", "price_action", "trade_guidance"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intent",
        required=True,
        choices=("unscoped_daily_start", "instrument_request"),
    )
    parser.add_argument("--capability-state", required=True, choices=sorted(CAPABILITY_STATES))
    parser.add_argument("--macro-state", required=True, choices=sorted(MACRO_STATES))
    parser.add_argument(
        "--holdings-review", required=True, choices=sorted(HOLDINGS_REVIEW_STATES)
    )
    parser.add_argument("--holdings-state", required=True, choices=sorted(HOLDINGS_STATES))
    args = parser.parse_args()
    route = resolve_daily_ops_route(
        intent=args.intent,
        capability_state=args.capability_state,
        macro_state=args.macro_state,
        holdings_review=args.holdings_review,
        holdings_state=args.holdings_state,
    )
    print(json.dumps(asdict(route), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
