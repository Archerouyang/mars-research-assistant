#!/usr/bin/env python3
"""Public seam self-test for the Mars 1.0 source observation adapter."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from mars_observation_adapter import (
    ObservationAdapterError,
    load_mars_source_contract,
    normalize_mars_observation_run,
    normalize_mars_observations,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "mars-1-0-source-payloads.synthetic.json"
AS_OF = "2026-07-23T22:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_payloads() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def require_error(payloads: dict[str, object], expected: str) -> None:
    try:
        normalize_mars_observations(payloads, AS_OF)
    except ObservationAdapterError as error:
        require(str(error) == expected, f"expected {expected!r}, received {error!s}")
    else:
        raise AssertionError(f"expected ObservationAdapterError: {expected}")


def main() -> int:
    contract = load_mars_source_contract()
    treasury_urls = {
        field["source_url"]
        for field in contract["fields"]
        if field["field_id"] in {
            "rates.us_2y_yield",
            "rates.us_10y_yield",
            "rates.us_30y_yield",
        }
    }
    require(
        treasury_urls
        == {
            "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"
        },
        "Treasury yield fields must use the directly readable public TextView fallback, not the empty legacy XML route",
    )

    payloads = load_payloads()
    run = normalize_mars_observation_run(payloads, AS_OF)
    observations = normalize_mars_observations(payloads, AS_OF)
    by_id = {row["field_id"]: row for row in observations}
    expected_ids = {
        "rates.us_2y_yield",
        "rates.us_10y_yield",
        "rates.us_30y_yield",
        "volatility.vix_close",
        "volatility.vix3m_close",
        "equity.ndx_close",
        "equity.rut_close",
        "liquidity.reserve_balances",
        "liquidity.tga_balance",
        "liquidity.on_rrp_usage",
        "events.seven_day_allowlist",
        "policy.us_executive_actions",
    }
    require(set(by_id) == expected_ids, "adapter must emit only retained raw base fields")
    require(
        not {
            "credit.hyg_lqd_ratio",
            "equity.ndx_rut_ratio",
            "equity.ndx_rut_normalized_20d",
        }.intersection(by_id),
        "adapter must never emit caller-derived values",
    )

    ndx = by_id["equity.ndx_close"]
    require(ndx["value"] == 29000.0, "NDX must normalize from the direct FRED daily-close field")
    require(ndx["source_id"] == "fred_nasdaq100_history", "NDX direct source id must be retained")
    require(
        ndx["source_url"] == "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100",
        "NDX FRED direct CSV URL must be retained",
    )

    vix = by_id["volatility.vix_close"]
    require(vix["value"] == 18.0, "VIX close must normalize from the exact close column")
    require(vix["source_id"] == "cboe_vix_history", "VIX source id must be retained")
    require(vix["source_timing"] == "completed_market", "VIX timing must be retained")
    require(
        vix["source_url"] == "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
        "VIX direct source URL must be retained",
    )
    require(vix["raw_field_path"] == ["records", "$last", "CLOSE"], "VIX raw path must be retained")
    require(len(vix["history"]) == 21, "market history requires twenty-one aligned closes")

    market_rows = [row for row in observations if row["source_timing"] == "completed_market"]
    expected_dates = [point["date"] for point in vix["history"]]
    require(
        all(row["market_reference_date"] == "2026-07-22" for row in market_rows),
        "all completed-market rows must use one selected completed date",
    )
    require(
        all([point["date"] for point in row["history"]] == expected_dates for row in market_rows),
        "completed-market histories must be date-aligned",
    )
    require(
        run.completed_market_session["market_reference_date"] == "2026-07-22",
        "market histories must equal the declared latest completed session",
    )
    require(
        list(run.latest_official_observations)
        == [
            {"field_id": "liquidity.on_rrp_usage", "reference_period": "2026-07-23"},
            {"field_id": "liquidity.reserve_balances", "reference_period": "2026-07-15"},
            {"field_id": "liquidity.tga_balance", "reference_period": "2026-07-22"},
        ],
        "each official value must declare its actual latest published observation",
    )

    reserves = by_id["liquidity.reserve_balances"]
    require(reserves["value"] == 3280.5, "reserve balances must remain separate")
    require(reserves["reference_period"] == "2026-07-15", "official reference period must remain separate")
    require("market_reference_date" not in reserves, "official releases cannot pretend to be market closes")

    policy = by_id["policy.us_executive_actions"]
    require(policy["source_timing"] == "policy", "policy timing must be retained")
    require(
        policy["value"] == [
            {
                "id": "synthetic-direct-policy-action",
                "title": "Synthetic direct executive action",
                "published_at": "2026-07-23T20:00:00Z",
                "source_url": "https://www.whitehouse.gov/presidential-actions/",
                "policy_status": "confirmed",
                "posture_effect": "neutral",
            }
        ],
        "policy evidence must remain a bounded official summary",
    )
    require(
        "history" not in policy,
        "policy evidence must not pretend to be market history",
    )

    events = by_id["events.seven_day_allowlist"]
    require(events["source_timing"] == "event", "event timing must be retained")
    require(events["reference_period"] == "next_7_days", "event horizon must be explicit")
    require(
        {item["category"] for item in events["value"]}
        == {"fomc", "employment", "gdp", "pmi", "long_duration_treasury_auction", "major_central_bank"},
        "only approved direct event categories may enter the normalized event set",
    )
    require(
        all(item["actual"] is None and item["consensus"] for item in events["value"]),
        "pre-release events may omit actual but must preserve consensus",
    )

    missing = copy.deepcopy(payloads)
    missing.pop("cboe_vix_history")
    require_error(missing, "volatility.vix_close:source_payload_missing")

    misaligned = copy.deepcopy(payloads)
    misaligned["cboe_vix3m_history"]["records"].pop()
    require_error(misaligned, "completed_market_session_not_latest")

    stale_session = copy.deepcopy(payloads)
    stale_session["us_equities_session"]["latest_completed_market_session"] = "2026-07-21"
    require_error(stale_session, "completed_market_session_not_latest")

    stale_official = copy.deepcopy(payloads)
    stale_official["federal_reserve_h41"]["latest_official_observation"] = "2026-07-14"
    require_error(stale_official, "liquidity.reserve_balances:latest_official_observation_mismatch")

    stale_policy = copy.deepcopy(payloads)
    stale_policy["white_house_presidential_actions"]["retrieved_at"] = "2026-07-22T20:00:00Z"
    require_error(stale_policy, "policy.us_executive_actions:source_stale")

    raw_policy = copy.deepcopy(payloads)
    raw_policy["white_house_presidential_actions"]["records"][0]["body"] = "must not be retained"
    require_error(raw_policy, "policy.us_executive_actions:record_shape_invalid")

    unverified_policy = copy.deepcopy(payloads)
    unverified_policy["white_house_presidential_actions"]["records"][0]["policy_status"] = "unverified_lead"
    unverified_policy["white_house_presidential_actions"]["records"][0]["posture_effect"] = "pressures"
    require_error(
        unverified_policy,
        "policy.us_executive_actions:unverified_lead_must_be_neutral",
    )

    incomplete_event = copy.deepcopy(payloads)
    incomplete_event["bea_release_schedule"]["records"][0].pop("consensus")
    require_error(incomplete_event, "events.seven_day_allowlist:record_shape_invalid")

    stale_event = copy.deepcopy(payloads)
    stale_event["ecb_meeting_calendar"]["retrieved_at"] = "2026-07-22T20:00:00Z"
    require_error(stale_event, "events.seven_day_allowlist:source_stale")

    empty_events = copy.deepcopy(payloads)
    for source_id in (
        "federal_reserve_event_calendar",
        "bls_release_schedule",
        "bea_release_schedule",
        "sp_global_pmi_calendar",
        "us_treasury_auction_calendar",
        "ecb_meeting_calendar",
    ):
        empty_events[source_id]["records"] = []
    require_error(empty_events, "events.seven_day_allowlist:no_allowed_events_in_horizon")

    broker = copy.deepcopy(payloads)
    broker["configured_broker"] = {"source_url": "synthetic://broker"}
    require_error(broker, "source_payload_not_supported:configured_broker")

    print("mars observation adapter selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
