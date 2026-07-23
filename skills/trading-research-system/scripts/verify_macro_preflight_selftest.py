#!/usr/bin/env python3
"""Focused black-box self-test for the Mars direct-source Blocker-or-Board seam."""

from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

from macro_preflight import run_macro_board


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "mars-1-0-source-payloads.synthetic.json"
AS_OF = "2026-07-23T22:00:00Z"
BANNED_SURFACE_TERMS = (
    "hyg", "lqd", "spx", "dxy", "uup", "brent", "xau", "gld", "uso", "bno", "vxn", "cpi", "ppi",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def payloads() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def current_day_completed_payloads() -> dict[str, object]:
    """Move every direct market series to a source-declared completed session."""

    current = payloads()
    current["us_equities_session"]["latest_completed_market_session"] = "2026-07-23"
    current["us_treasury_daily_rates"]["records"][-1]["date"] = "2026-07-23"
    for source_id in (
        "cboe_vix_history",
        "cboe_vix3m_history",
        "cboe_rut_history",
        "fred_nasdaq100_history",
    ):
        current[source_id]["records"][-1]["DATE"] = "2026-07-23"
    return current


def main() -> int:
    config = {
        "default_broker": "longbridge",
        "broker_read_only_enabled": True,
        "skill_version": "1.0.0",
        "field_contract_version": "macro-v1",
    }
    parameters = tuple(inspect.signature(run_macro_board).parameters)
    require(
        parameters[:3] == ("config", "source_payloads", "as_of"),
        "the public seam must accept raw direct source payloads, not a caller-built ResearchResult",
    )

    allowed = run_macro_board(config, payloads(), AS_OF)
    require(allowed.kind == "board", "complete direct observations must reach the canonical Board")
    require(allowed.delivery_packet is not None, "successful run must return a delivery packet")
    require(allowed.delivery_packet.standalone_board is not None, "only a standalone Board may be delivered")
    html = allowed.delivery_packet.standalone_board.html.decode("utf-8").casefold()
    canonical_result = allowed.delivery_packet.canonical_result.decode("utf-8")
    require(
        not any(term in html for term in BANNED_SURFACE_TERMS),
        "no removed field or proxy may leak into any generated Board surface",
    )
    require(
        set(allowed.resolved_values).issuperset(
            {
                "volatility.vix_vix3m_ratio",
                "equity.ndx_rut_ratio",
                "equity.ndx_rut_normalized_20d",
                "equity.ndx_rut_ratio.change_1d",
                "equity.ndx_rut_ratio.change_5d",
                "equity.ndx_rut_ratio.change_20d",
            }
        ),
        "all retained ratios and NDX/RUT changes must be derived internally",
    )
    require(
        "synthetic direct executive action" in html
        and "white house presidential actions" in html,
        "validated White House policy evidence must appear as a bounded Board summary",
    )
    require(
        "下周事件" not in html,
        "a field without a direct event contract must be omitted rather than rendered empty",
    )
    require(
        "https://www.whitehouse.gov/presidential-actions/" not in canonical_result
        and "must not be retained" not in canonical_result,
        "delivery artifacts must not persist raw policy URLs or page content",
    )

    current_day = run_macro_board(config, current_day_completed_payloads(), AS_OF)
    require(
        current_day.kind == "board",
        "a source-declared completed close on the decision date must be accepted",
    )

    missing_vix = payloads()
    missing_vix.pop("cboe_vix_history")
    blocked_missing = run_macro_board(config, missing_vix, AS_OF)
    require(blocked_missing.kind == "blocker", "missing direct source payload must block")
    require(blocked_missing.delivery_packet is None, "blocked run must not create a Board")
    require(
        blocked_missing.blockers[0].field_id == "volatility.vix_close",
        "the blocker must identify the unavailable requested field",
    )

    missing_policy = payloads()
    missing_policy.pop("white_house_presidential_actions")
    blocked_policy = run_macro_board(config, missing_policy, AS_OF)
    require(blocked_policy.kind == "blocker", "missing policy source must block")
    require(
        blocked_policy.blockers[0].field_id == "policy.us_executive_actions",
        "the blocker must identify missing White House policy coverage",
    )

    stale_session = payloads()
    stale_session["us_equities_session"]["latest_completed_market_session"] = "2026-07-21"
    blocked_stale = run_macro_board(config, stale_session, AS_OF)
    require(blocked_stale.kind == "blocker", "not-latest session must block")
    require(
        blocked_stale.blockers[0].reason == "completed_market_session_not_latest",
        "the blocker must explain the common-close failure",
    )

    proxy_payload = payloads()
    proxy_payload["configured_broker"] = {"source_url": "synthetic://broker"}
    blocked_proxy = run_macro_board(config, proxy_payload, AS_OF)
    require(blocked_proxy.kind == "blocker", "broker or proxy data must not enter direct macro core")
    require(
        blocked_proxy.blockers[0].reason == "source_payload_not_supported:configured_broker",
        "unsupported provider payload must remain visible",
    )

    invalid_config = dict(config)
    invalid_config["default_broker"] = ["longbridge", "ibkr"]
    setup = run_macro_board(invalid_config, payloads(), AS_OF)
    require(setup.kind == "setup_required", "exactly one installation-selected broker is required")
    require(setup.delivery_packet is None, "setup required must not create a Board")

    print("macro preflight selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
