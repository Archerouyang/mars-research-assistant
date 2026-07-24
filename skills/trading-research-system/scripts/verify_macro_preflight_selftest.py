#!/usr/bin/env python3
"""Focused black-box self-test for the Mars direct-source Blocker-or-Board seam."""

from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

from macro_preflight import run_macro_board
from mars_observation_adapter import load_mars_source_contract
from mars_web_capture import MarsWebCaptureError, capture_mars_direct_web_observations


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "mars-1-0-source-payloads.synthetic.json"
AS_OF = "2026-07-23T22:00:00Z"
BANNED_SURFACE_TERMS = (
    "hyg", "lqd", "spx", "dxy", "uup", "brent", "xau", "gld", "uso", "bno", "vxn", "cpi", "ppi",
    "inflation & growth", "event scenarios", "event watch", "partial", "source_error",
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


def capture(source_payloads: dict[str, object]):
    """Simulate only the host's direct-search then direct-open handoff."""

    contract = load_mars_source_contract()
    sources = {
        str(field["source_id"]): str(field["source_url"])
        for field in contract["fields"]
    }
    market_session = contract["market_session"]
    sources[str(market_session["source_id"])] = str(market_session["source_url"])
    receipts = {
        source_id: {
            "source_url": source_url,
            "opened_at": (
                source_payloads.get(source_id, {}).get("retrieved_at")
                if isinstance(source_payloads.get(source_id), dict)
                else "2026-07-22T22:00:00Z"
            ),
            "method": "web_search_then_direct_open",
        }
        for source_id, source_url in sources.items()
    }
    return capture_mars_direct_web_observations(
        source_payloads, receipts, acquired_at=AS_OF
    )


def main() -> int:
    parameters = tuple(inspect.signature(run_macro_board).parameters)
    require(
        parameters[:2] == ("web_capture", "as_of"),
        "the public seam must accept a direct-web capture, never a raw source map or broker config",
    )

    raw_map = run_macro_board(payloads(), AS_OF)  # type: ignore[arg-type]
    require(raw_map.kind == "blocker", "raw source maps must be rejected at the public seam")
    require(
        raw_map.blockers[0].reason == "direct_web_capture_required",
        "the user-visible blocker must explain the missing direct-web capture",
    )

    allowed = run_macro_board(capture(payloads()), AS_OF)
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

    current_day = run_macro_board(capture(current_day_completed_payloads()), AS_OF)
    require(
        current_day.kind == "board",
        "a source-declared completed close on the decision date must be accepted",
    )

    missing_vix = payloads()
    missing_vix.pop("cboe_vix_history")
    blocked_missing = run_macro_board(capture(missing_vix), AS_OF)
    require(blocked_missing.kind == "blocker", "missing direct source payload must block")
    require(blocked_missing.delivery_packet is None, "blocked run must not create a Board")
    require(
        blocked_missing.blockers[0].field_id == "volatility.vix_close",
        "the blocker must identify the unavailable requested field",
    )

    missing_policy = payloads()
    missing_policy.pop("white_house_presidential_actions")
    blocked_policy = run_macro_board(capture(missing_policy), AS_OF)
    require(blocked_policy.kind == "blocker", "missing policy source must block")
    require(
        blocked_policy.blockers[0].field_id == "policy.us_executive_actions",
        "the blocker must identify missing White House policy coverage",
    )

    stale_session = payloads()
    stale_session["us_equities_session"]["latest_completed_market_session"] = "2026-07-21"
    blocked_stale = run_macro_board(capture(stale_session), AS_OF)
    require(blocked_stale.kind == "blocker", "not-latest session must block")
    require(
        blocked_stale.blockers[0].reason == "completed_market_session_not_latest",
        "the blocker must explain the common-close failure",
    )

    bad_receipt = payloads()
    contract = load_mars_source_contract()
    source_id = str(contract["fields"][0]["source_id"])
    source_url = str(contract["fields"][0]["source_url"])
    receipts = {
        item_source_id: {
            "source_url": item_source_url,
            "opened_at": "2026-07-22T22:00:00Z",
            "method": "web_search_then_direct_open",
        }
        for item_source_id, item_source_url in {
            **{
                str(field["source_id"]): str(field["source_url"])
                for field in contract["fields"]
            },
            str(contract["market_session"]["source_id"]): str(contract["market_session"]["source_url"]),
        }.items()
    }
    receipts[source_id]["method"] = "broker_proxy"
    try:
        capture_mars_direct_web_observations(bad_receipt, receipts, acquired_at=AS_OF)
    except MarsWebCaptureError as error:
        require(
            str(error) == f"{source_id}:direct_web_method_invalid",
            "a broker/proxy receipt must be rejected before preflight",
        )
    else:
        raise AssertionError("a broker/proxy receipt must be rejected")

    future_receipt = payloads()
    receipts[source_id]["method"] = "web_search_then_direct_open"
    receipts[source_id]["opened_at"] = "2026-07-23T22:00:01Z"
    try:
        capture_mars_direct_web_observations(future_receipt, receipts, acquired_at=AS_OF)
    except MarsWebCaptureError as error:
        require(
            str(error) == f"{source_id}:direct_web_opened_after_capture",
            "a receipt after the capture cutoff must be rejected",
        )
    else:
        raise AssertionError("a receipt after the capture cutoff must be rejected")

    print("macro preflight selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
