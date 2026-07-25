#!/usr/bin/env python3
"""Focused black-box self-test for the Mars direct-source Blocker-or-Board seam."""

from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

from ibkr_macro_adapter import normalize_ibkr_yield_history
from macro_preflight import run_macro_board
from mars_observation_adapter import load_mars_source_contract
from mars_web_capture import (
    MarsBrokerMarketCaptureError,
    MarsWebCaptureError,
    REGISTERED_DIRECT_OPEN_METHOD,
    WEB_SEARCH_DIRECT_OPEN_METHOD,
    capture_mars_broker_market_observations,
    capture_mars_direct_web_observations,
    normalize_captured_mars_observations,
)


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


def capture(
    source_payloads: dict[str, object],
    *,
    web_search_sources: frozenset[str] = frozenset(),
):
    """Simulate registered direct opens and explicit Web Search fallback."""

    contract = load_mars_source_contract()
    sources = {
        str(field["source_id"]): str(field["source_url"])
        for field in contract["fields"]
    }
    market_session = contract["market_session"]
    sources[str(market_session["source_id"])] = str(market_session["source_url"])
    sources.update(
        {
            str(source["source_id"]): str(source["source_url"])
            for source in contract["event_sources"]
        }
    )
    receipts = {
        source_id: {
            "source_url": source_url,
            "opened_at": (
                source_payloads.get(source_id, {}).get("retrieved_at")
                if isinstance(source_payloads.get(source_id), dict)
                else "2026-07-22T22:00:00Z"
            ),
            "method": (
                WEB_SEARCH_DIRECT_OPEN_METHOD
                if source_id in web_search_sources
                or source_id not in source_payloads
                else REGISTERED_DIRECT_OPEN_METHOD
            ),
        }
        for source_id, source_url in sources.items()
    }
    return capture_mars_direct_web_observations(
        source_payloads, receipts, acquired_at=AS_OF
    )


def broker_market_capture(source_payloads: dict[str, object]):
    """Provide exact verified IBKR TNX/TYX fields only."""

    public_rows = {
        row["field_id"]: row
        for row in normalize_captured_mars_observations(capture(source_payloads), AS_OF)
    }
    contracts = {
        "rates.us_10y_yield": {
            "contract_id": "416921",
            "symbol": "TNX",
            "exchange": "CBOE",
            "security_type": "IND",
            "description": "Interest Rate Option On 10-Year Note",
            "scale": 10.0,
        },
        "rates.us_30y_yield": {
            "contract_id": "416933",
            "symbol": "TYX",
            "exchange": "CBOE",
            "security_type": "IND",
            "description": "Interest Rate Option On 30-Year Bond",
            "scale": 10.0,
        },
    }
    selected = []
    for field_id, contract in contracts.items():
        public = public_rows[field_id]
        selected.append(
            normalize_ibkr_yield_history(
                {
                    "contract": {
                        key: value
                        for key, value in contract.items()
                        if key != "scale"
                    },
                    "history": {
                        "chart_step": 86400,
                        "chart_start": public["history"][0]["date"] + "T00:00:00Z",
                        "chart_end": "2026-07-23T00:00:00Z",
                        "source": "Last",
                        "time": [
                            point["date"] + "T20:00:00Z"
                            for point in public["history"]
                        ],
                        "open": [
                            float(point["value"]) * contract["scale"]
                            for point in public["history"]
                        ],
                        "high": [
                            float(point["value"]) * contract["scale"]
                            for point in public["history"]
                        ],
                        "low": [
                            float(point["value"]) * contract["scale"]
                            for point in public["history"]
                        ],
                        "close": [
                            float(point["value"]) * contract["scale"]
                            for point in public["history"]
                        ],
                    },
                },
                field_id=field_id,
                acquired_at=AS_OF,
            )
        )
    return capture_mars_broker_market_observations(selected, acquired_at=AS_OF)


def missing_broker_covered_public_payloads() -> dict[str, object]:
    """Remove public 10Y/30Y columns while preserving the official 2Y route."""

    current = payloads()
    for record in current["us_treasury_daily_rates"]["records"]:
        record.pop("10 Yr")
        record.pop("30 Yr")
    return current


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
        "fomc statement" in html
        and "employment situation" in html
        and "future seven-day" not in html
        and "未来七日事件" in html,
        "validated future-event fields must render from the direct allowlist rather than an old scenario shape",
    )
    require(
        "最近共同完成收盘" in html
        and "盘中数据：排除" in html
        and "hold_current_risk" in html,
        "the Board must disclose its close-only timing and qualitative posture",
    )
    require(
        not allowed.fallback_disclosures,
        "registered official direct opens must not be mislabeled as Web Search fallback",
    )
    searched = run_macro_board(
        capture(
            payloads(),
            web_search_sources=frozenset({"us_treasury_daily_rates"}),
        ),
        AS_OF,
    )
    require(searched.kind == "board", "verified Web Search authority opens must remain eligible")
    require(
        any(
            item["field_id"] == "rates.us_2y_yield"
            and item["source_id"] == "us_treasury_daily_rates"
            and item["authority_url"].startswith("https://home.treasury.gov/")
            and item["reference_date"] == "2026-07-22"
            for item in searched.fallback_disclosures
        ),
        "Web Search fallback must disclose field, authority URL, and reference date",
    )

    broker_preferred = run_macro_board(
        capture(payloads()),
        AS_OF,
        broker_market_capture=broker_market_capture(payloads()),
    )
    require(
        broker_preferred.kind == "board" and broker_preferred.delivery_packet is not None,
        "complete broker market observations must be admitted over the public fallback",
    )
    broker_snapshot = json.loads(broker_preferred.delivery_packet.canonical_result)
    source_ids = {item["id"] for item in broker_snapshot["sources"]}
    require(
        "ibkr_market_data" in source_ids,
        "a broker-provided market field must retain its actual source identity",
    )
    require(
        "us_treasury_daily_rates" in source_ids,
        "unsupported IBKR 2Y coverage must retain the official Treasury fallback",
    )
    require(
        not any(
            item["field_id"] in {"rates.us_10y_yield", "rates.us_30y_yield"}
            for item in broker_preferred.fallback_disclosures
        ),
        "exact IBKR fields must not be mislabeled as public fallback",
    )
    rejected = copy.deepcopy(
        broker_market_capture(payloads()).observations[0]
    )
    rejected["source_id"] = "longbridge_market_data"
    try:
        capture_mars_broker_market_observations([rejected], acquired_at=AS_OF)
    except MarsWebCaptureError:
        raise AssertionError("broker source rejection must use the broker capture error")
    except MarsBrokerMarketCaptureError as error:
        require(
            str(error) == "broker_market_source_not_supported",
            "Longbridge market captures must be rejected by the provider boundary",
        )
    else:
        raise AssertionError("Longbridge market captures must be rejected")

    broker_priority = run_macro_board(
        capture(missing_broker_covered_public_payloads()),
        AS_OF,
        broker_market_capture=broker_market_capture(payloads()),
    )
    require(
        broker_priority.kind == "board" and broker_priority.delivery_packet is not None,
        "broker market fields must not require their public fallback payloads",
    )
    no_broker_priority = run_macro_board(
        capture(missing_broker_covered_public_payloads()),
        AS_OF,
    )
    require(
        no_broker_priority.kind == "web_search_required",
        "an invalid registered public source must require Web Search before blocking",
    )
    no_broker_priority = run_macro_board(
        capture(
            missing_broker_covered_public_payloads(),
            web_search_sources=frozenset({"us_treasury_daily_rates"}),
        ),
        AS_OF,
    )
    require(
        no_broker_priority.kind == "blocker",
        "the same missing source must block when no eligible broker field is supplied",
    )
    require(
        no_broker_priority.blockers[0].field_id == "rates.us_10y_yield",
        "the public fallback gap must identify the exact missing market field",
    )
    require(
        "https://www.whitehouse.gov/presidential-actions/" not in canonical_result
        and "https://www.federalreserve.gov/newsevents/calendar.htm" not in canonical_result
        and "must not be retained" not in canonical_result,
        "delivery artifacts must not persist raw policy or event URLs or page content",
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
    require(
        blocked_missing.blockers[0].attempted_routes[-1]
        == "web_search_discovery:direct_authority_open",
        "a public-source blocker must disclose the mandatory Web Search fallback attempt",
    )

    missing_policy = payloads()
    missing_policy.pop("white_house_presidential_actions")
    blocked_policy = run_macro_board(capture(missing_policy), AS_OF)
    require(blocked_policy.kind == "blocker", "missing policy source must block")
    require(
        blocked_policy.blockers[0].field_id == "policy.us_executive_actions",
        "the blocker must identify missing White House policy coverage",
    )

    missing_events = payloads()
    missing_events.pop("ecb_meeting_calendar")
    blocked_events = run_macro_board(capture(missing_events), AS_OF)
    require(blocked_events.kind == "blocker", "missing direct event source must block")
    require(
        blocked_events.blockers[0].field_id == "events.seven_day_allowlist",
        "the blocker must identify missing seven-day event coverage",
    )

    stale_session = payloads()
    stale_session["us_equities_session"]["latest_completed_market_session"] = "2026-07-21"
    retry_stale = run_macro_board(capture(stale_session), AS_OF)
    require(
        retry_stale.kind == "web_search_required",
        "an invalid registered source must require Web Search before final blocking",
    )
    blocked_stale = run_macro_board(
        capture(
            stale_session,
            web_search_sources=frozenset({"us_equities_session"}),
        ),
        AS_OF,
    )
    require(blocked_stale.kind == "blocker", "not-latest session must block")
    require(
        blocked_stale.blockers[0].reason == "completed_market_session_not_latest",
        "the blocker must explain the common-close failure",
    )
    require(
        blocked_stale.blockers[0].attempted_routes[-1]
        == "web_search_discovery:direct_authority_open",
        "the final source blocker must prove Web Search was attempted",
    )

    invalid_vix = payloads()
    invalid_vix["cboe_vix_history"]["records"][-1]["CLOSE"] = "invalid"
    retry_vix = run_macro_board(capture(invalid_vix), AS_OF)
    require(
        retry_vix.kind == "web_search_required",
        "schema-invalid registered payloads must not become final blockers",
    )
    final_vix = run_macro_board(
        capture(
            invalid_vix,
            web_search_sources=frozenset({"cboe_vix_history"}),
        ),
        AS_OF,
    )
    require(
        final_vix.kind == "blocker"
        and final_vix.blockers[0].attempted_routes[-1]
        == "web_search_discovery:direct_authority_open",
        "only a failed Web Search authority open may produce the final field blocker",
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
            **{
                str(source["source_id"]): str(source["source_url"])
                for source in contract["event_sources"]
            },
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
