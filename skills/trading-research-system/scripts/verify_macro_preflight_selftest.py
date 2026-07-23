#!/usr/bin/env python3
"""Focused black-box self-test for the Macro Blocker-or-Board seam."""

from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path

from artifact_packet_core import canonical_json_bytes, sha256_hex
from macro_preflight import load_field_registry, run_macro_board


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-23T12:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def refresh_snapshot_hash(snapshot: dict[str, object]) -> None:
    hashable = copy.deepcopy(snapshot)
    hashable.pop("content_hash", None)
    snapshot["content_hash"] = sha256_hex(canonical_json_bytes(hashable))


def research_result(observations: list[dict[str, object]]) -> dict[str, object]:
    values = {str(row["field_id"]): row["value"] for row in observations}
    values["credit.hyg_lqd_ratio"] = (
        float(values["credit.hyg_close"]) / float(values["credit.lqd_close"])
    )
    values["volatility.vix_vix3m_ratio"] = (
        float(values["volatility.vix_close"])
        / float(values["volatility.vix3m_close"])
    )
    values["equity.ndx_rut_ratio"] = (
        float(values["equity.ndx_close"]) / float(values["equity.rut_close"])
    )
    ndx_history = next(
        row["history"]
        for row in observations
        if row["field_id"] == "equity.ndx_close"
    )
    rut_history = next(
        row["history"]
        for row in observations
        if row["field_id"] == "equity.rut_close"
    )
    ratio_history = [
        float(ndx["value"]) / float(rut["value"])
        for ndx, rut in zip(ndx_history, rut_history)
    ]
    window = ratio_history[-20:]
    mean = sum(window) / len(window)
    variance = sum((value - mean) ** 2 for value in window) / len(window)
    values["equity.ndx_rut_normalized_20d"] = (
        (window[-1] - mean) / variance**0.5
    )
    snapshot = load("macro-regime-complete.json")
    payload = snapshot["payload"]
    snapshot["decision_cutoff"] = AS_OF
    snapshot["builder"]["generated_at"] = AS_OF
    for source in snapshot["source_registry"]:
        source["as_of"] = AS_OF
        source["freshness_status"] = "fresh"
    for module in payload["modules"]:
        module["as_of"] = AS_OF
        if module["id"] == "plan_context":
            module["data"]["applicable_session"] = "2026-07-23T00:00:00Z"
        elif module["id"] == "rates_liquidity":
            module["data"] = {
                "rule": "Core rates, credit, and volatility only.",
                "scope": "Synthetic core-only fields.",
            }
        elif module["id"] == "cross_asset":
            module["data"] = {
                "rule": "Core relative-strength and volatility confirmation.",
                "scope": "Synthetic core-only fields.",
            }
    for evidence in payload["evidence"]:
        evidence["as_of"] = AS_OF
        if evidence["category"] == "media":
            evidence["reading"] = "NDX/RUT and VIX/VIX3M are synthetic core-only values."
            evidence["transmission"] = "Relative strength and volatility are evaluated together."
        if evidence["category"] == "thesis":
            evidence["reading"] = "Rates, credit, VIX/VIX3M, and NDX/RUT require confirmation."
            evidence["transmission"] = "Verified core fields update the evidence gate."
    payload["liquidity_background"] = "Synthetic core-only financial-conditions coverage."
    payload["asset_preferences"] = [
        {
            "segment": "科技股",
            "bias": "neutral",
            "impact": "Synthetic core-only fixture.",
            "watch": "Rates, credit, and volatility confirmation.",
        }
    ]
    payload["event_watch"] = [
        {
            "event": "Synthetic policy event",
            "time": "2026-07-24T12:00:00Z",
            "importance": "high",
            "watch": "Core retained fields only.",
            "why_it_matters": "Synthetic event coverage.",
            "if_hot": "Tighter financial conditions.",
            "if_cool": "Easier financial conditions.",
        }
    ]
    payload["scenarios"] = [
        {
            "name": "Core field confirmation",
            "trigger": "Retained events update the verified fields.",
            "confirms": "Rates, credit, VIX/VIX3M, and NDX/RUT agree.",
            "cross_asset": "Synthetic core-only transmission.",
            "posture": "Reassess the evidence gate.",
            "impact_rank": 1,
            "affected_exposures": ["growth-theme"],
        }
    ]
    chart_fields = {
        "2Y": "rates.us_2y_yield",
        "10Y": "rates.us_10y_yield",
        "30Y": "rates.us_30y_yield",
        "HYG/LQD": "credit.hyg_lqd_ratio",
        "VIX/VIX3M": "volatility.vix_vix3m_ratio",
        "NDX/RUT": "equity.ndx_rut_ratio",
    }
    payload["chart_series"] = [
        {"label": label, "value": values[field_id]}
        for label, field_id in chart_fields.items()
    ]
    trend_fields = {
        "2Y": "rates.us_2y_yield",
        "10Y": "rates.us_10y_yield",
        "30Y": "rates.us_30y_yield",
        "NDX/RUT": "equity.ndx_rut_ratio",
    }
    payload["trend_series"] = [
        {
            "label": label,
            "unit": "percent" if label.endswith("Y") else "ratio",
            "implication": "Synthetic core-only binding coverage.",
            "points": [
                {"time": "2026-07-21T12:00:00Z", "value": float(values[field_id]) * 0.99},
                {"time": "2026-07-22T12:00:00Z", "value": values[field_id]},
            ],
        }
        for label, field_id in trend_fields.items()
    ]
    payload["preflight"] = {
        "field_contract_version": "macro-v1",
        "market_reference_date": "2026-07-22",
        "validated_field_ids": sorted(
            field["field_id"] for field in load_field_registry()["fields"]
        ),
        "chart_field_ids": chart_fields,
        "trend_field_ids": trend_fields,
    }
    refresh_snapshot_hash(snapshot)
    return {
        "schema_version": "1.0",
        "result_kind": "macro",
        "as_of": AS_OF,
        "decision": "Maintain the current evidence gate.",
        "key_evidence": [
            {
                "label": "Synthetic field coverage",
                "value": "Complete",
                "evidence_type": "fact",
                "status": "complete",
                "as_of": AS_OF,
                "source_refs": ["fixture"],
            }
        ],
        "risks": [],
        "scenarios": [],
        "next_checks": [],
        "data_gaps": [],
        "sources": [
            {
                "id": "fixture",
                "label": "Synthetic fixture",
                "priority": "S1",
                "as_of": AS_OF,
            }
        ],
        "privacy": "public_fixture",
        "locale": "zh-CN",
        "visual": {
            "adapter": "macro",
            "snapshot": snapshot,
            "default_view": "Overview",
        },
    }


def complete_observations() -> list[dict[str, object]]:
    registry = load_field_registry()
    require(
        set(registry["freshness_policies"])
        == {"completed_market", "official_release", "event", "policy"},
        "registry must declare every Macro freshness policy",
    )
    field_ids = {field["field_id"] for field in registry["fields"]}
    require(
        not {
            "fx.dxy_close",
            "commodities.brent_front_settlement",
            "commodities.brent_contract_code",
            "commodities.brent_roll_state",
            "commodities.xauusd_close",
            "valuation.spx_forward_12m_pe",
            "valuation.spx_forward_12m_pe_10y_average",
            "valuation.spx_forward_12m_pe_premium",
            "valuation.spx_forward_12m_pe_10y_percentile",
        }.intersection(field_ids),
        "deferred source-dependent fields must not remain in the 1.0 registry",
    )
    rows: list[dict[str, object]] = []
    for index, field in enumerate(registry["fields"], start=1):
        if field.get("derivation_inputs"):
            continue
        source_route = field["source_routes"][0]
        source_id = source_route["source_id"]
        if source_id == "configured_broker":
            source_id = "longbridge"
        row: dict[str, object] = {
            "field_id": field["field_id"],
            "value": float(index),
            "unit": field["unit"],
            "status": "available",
            "data_as_of": AS_OF,
            "source_id": source_id,
            "retrieval_method": source_route["method"],
            "raw_field_path": ["fixture", field["field_id"]],
        }
        timing = field["timing"]
        if timing == "completed_market":
            row["market_reference_date"] = "2026-07-22"
        else:
            row["reference_period"] = "2026-07"
        if field["field_id"] in {"equity.ndx_close", "equity.rut_close"}:
            end = date(2026, 7, 22)
            history = [
                {
                    "date": (end - timedelta(days=20 - offset)).isoformat(),
                    "value": (
                        1000.0 + 12.0 * offset
                        if field["field_id"] == "equity.ndx_close"
                        else 100.0 + float(offset)
                    ),
                }
                for offset in range(21)
            ]
            row["history"] = history
            row["value"] = history[-1]["value"]
        if field["field_id"] == "equity.rut_close":
            row["source_id"] = "cboe_daily_index_history"
            row["retrieval_method"] = "official_csv"
            row["source_url"] = (
                "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
                "RUT_History.csv"
            )
            row["source_columns"] = ["DATE", "RUT"]
            row["raw_field_path"] = ["records", "$last", "RUT"]
        if field["field_id"] == "volatility.vix3m_close":
            row["source_id"] = "cboe_daily_index_history"
            row["retrieval_method"] = "official_csv"
            row["source_url"] = (
                "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
                "VIX3M_History.csv"
            )
            row["source_columns"] = ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"]
            row["raw_field_path"] = ["records", "$last", "CLOSE"]
        rows.append(row)
    return rows


def main() -> int:
    config = {
        "default_broker": "longbridge",
        "broker_read_only_enabled": True,
        "skill_version": "1.0.0",
        "field_contract_version": "macro-v1",
    }
    observations = complete_observations()
    result = research_result(observations)

    missing = {
        "events.seven_day_allowlist",
        "liquidity.tga_balance",
        "rates.us_2y_yield",
    }
    partial = [row for row in observations if row["field_id"] not in missing]
    blocked = run_macro_board(config, partial, result)
    require(blocked.kind == "blocker", "missing required fields must block")
    require(blocked.delivery_packet is None, "blocked run must not create a Board packet")
    require(
        tuple(item.field_id for item in blocked.blockers) == tuple(sorted(missing)),
        "all missing fields must be returned in one deterministic blocker",
    )
    require(
        blocked.message.count("Data Acquisition Blocker") == 1,
        "missing fields must be batched into one user-facing blocker",
    )

    proxy_rows = copy.deepcopy(observations)
    rut = next(row for row in proxy_rows if row["field_id"] == "equity.rut_close")
    rut["source_symbol"] = "IWM"
    proxy = run_macro_board(config, proxy_rows, result)
    require(proxy.kind == "blocker", "a prohibited proxy must not satisfy RUT")
    require(
        any(item.field_id == "equity.rut_close" and item.reason == "proxy_not_allowed" for item in proxy.blockers),
        "proxy rejection must remain visible",
    )

    stale_rows = copy.deepcopy(observations)
    stale_ndx = next(row for row in stale_rows if row["field_id"] == "equity.ndx_close")
    stale_ndx["market_reference_date"] = "2026-06-01"
    stale_ndx["history"][-1]["date"] = "2026-06-01"
    stale = run_macro_board(config, stale_rows, result)
    require(stale.kind == "blocker", "stale completed-market input must block")
    require(
        any(
            item.field_id == "equity.ndx_close"
            and item.reason == "market_reference_date_stale"
            for item in stale.blockers
        ),
        "completed-market freshness must be enforced",
    )

    invalid_date_rows = copy.deepcopy(observations)
    invalid_date = next(
        row for row in invalid_date_rows if row["field_id"] == "equity.ndx_close"
    )
    invalid_date["market_reference_date"] = "not-a-date"
    invalid = run_macro_board(config, invalid_date_rows, result)
    require(invalid.kind == "blocker", "invalid market dates must block")
    require(
        any(
            item.field_id == "equity.ndx_close"
            and item.reason == "market_reference_date_invalid"
            for item in invalid.blockers
        ),
        "invalid market-date parsing must be visible",
    )

    generic_source_rows = copy.deepcopy(observations)
    ndx_generic = next(
        row for row in generic_source_rows if row["field_id"] == "equity.ndx_close"
    )
    ndx_generic["source_id"] = "qualified_index_source"
    generic = run_macro_board(config, generic_source_rows, result)
    require(generic.kind == "blocker", "generic source identifiers must not pass")
    require(
        any(
            item.field_id == "equity.ndx_close"
            and item.reason == "source_route_not_allowed"
            for item in generic.blockers
        ),
        "generic source rejection must be visible",
    )

    generic_registry = copy.deepcopy(load_field_registry())
    generic_ndx = next(
        field
        for field in generic_registry["fields"]
        if field["field_id"] == "equity.ndx_close"
    )
    generic_ndx["source_routes"] = [
        {"source_id": "qualified_index_source", "method": "daily_close"}
    ]
    generic_contract = run_macro_board(
        config,
        observations,
        result,
        registry=generic_registry,
    )
    require(
        generic_contract.kind == "blocker",
        "a generic source route must invalidate the field contract",
    )
    require(
        generic_contract.blockers[0].field_id == "preflight.contract",
        "invalid registry must be reported through the public blocker seam",
    )

    wrong_contract_rows = copy.deepcopy(observations)
    rut_contract = next(
        row for row in wrong_contract_rows if row["field_id"] == "equity.rut_close"
    )
    rut_contract["raw_field_path"] = ["fixture", "rut"]
    wrong_contract = run_macro_board(config, wrong_contract_rows, result)
    require(wrong_contract.kind == "blocker", "mapped Cboe fields need exact provenance")
    require(
        any(
            item.field_id == "equity.rut_close"
            and item.reason == "source_contract_provenance_invalid"
            for item in wrong_contract.blockers
        ),
        "Cboe source-contract provenance must be visible",
    )

    wrong_endpoint_rows = copy.deepcopy(observations)
    vix3m_contract = next(
        row
        for row in wrong_endpoint_rows
        if row["field_id"] == "volatility.vix3m_close"
    )
    vix3m_contract["source_url"] = "https://example.test/not-cboe.csv"
    wrong_endpoint = run_macro_board(config, wrong_endpoint_rows, result)
    require(
        wrong_endpoint.kind == "blocker",
        "mapped Cboe fields need the exact direct endpoint",
    )
    require(
        any(
            item.field_id == "volatility.vix3m_close"
            and item.reason == "source_contract_provenance_invalid"
            for item in wrong_endpoint.blockers
        ),
        "direct endpoint provenance must be visible",
    )

    derived_rows = copy.deepcopy(observations)
    derived_rows.append(
        {
            "field_id": "equity.ndx_rut_ratio",
            "value": 999.0,
            "unit": "ratio",
            "status": "available",
            "data_as_of": AS_OF,
            "market_reference_date": "2026-07-22",
            "source_id": "derived",
            "retrieval_method": "deterministic_formula",
            "raw_field_path": ["caller", "derived"],
            "lineage": {
                "inputs": ["equity.ndx_close", "equity.rut_close"],
                "formula": "equity.ndx_close / equity.rut_close",
            },
        }
    )
    caller_derived = run_macro_board(config, derived_rows, result)
    require(caller_derived.kind == "blocker", "caller-provided derived values must block")
    require(
        any(
            item.field_id == "equity.ndx_rut_ratio"
            and item.reason == "derived_field_must_not_be_supplied"
            for item in caller_derived.blockers
        ),
        "derived values must be calculated inside Preflight",
    )

    unbound_result = copy.deepcopy(result)
    unbound_result["visual"]["snapshot"]["payload"].pop("preflight")
    refresh_snapshot_hash(unbound_result["visual"]["snapshot"])
    unbound = run_macro_board(config, observations, unbound_result)
    require(unbound.kind == "blocker", "an unbound Board payload must block")
    require(
        any(
            item.reason == "research_result_preflight_binding_missing"
            for item in unbound.blockers
        ),
        "Board payloads must identify the validated field contract",
    )

    deferred_result = copy.deepcopy(result)
    deferred_result["visual"]["snapshot"]["payload"]["liquidity_background"] = (
        "DXY must not be displayed in the Mars 1.0 Board."
    )
    refresh_snapshot_hash(deferred_result["visual"]["snapshot"])
    deferred = run_macro_board(config, observations, deferred_result)
    require(deferred.kind == "blocker", "deferred fields must not leak into Board text")
    require(
        any(
            item.reason == "research_result_deferred_field_present"
            for item in deferred.blockers
        ),
        "deferred signal leakage must be visible at the Board seam",
    )

    top_level_proxy_result = copy.deepcopy(result)
    top_level_proxy_result["decision"] = "UUP must not appear in Mars 1.0 delivery."
    top_level_proxy = run_macro_board(config, observations, top_level_proxy_result)
    require(
        top_level_proxy.kind == "blocker",
        "deferred proxies must not leak through top-level ResearchResult text",
    )
    require(
        any(
            item.reason == "research_result_deferred_field_present"
            for item in top_level_proxy.blockers
        ),
        "top-level proxy leakage must be visible at the Board seam",
    )

    mixed_broker_rows = copy.deepcopy(observations)
    hyg = next(row for row in mixed_broker_rows if row["field_id"] == "credit.hyg_close")
    hyg["source_id"] = "ibkr"
    mixed = run_macro_board(config, mixed_broker_rows, result)
    require(mixed.kind == "blocker", "the unconfigured broker must not satisfy a field")
    require(
        any(item.field_id == "credit.hyg_close" and item.reason == "source_route_not_allowed" for item in mixed.blockers),
        "automatic broker switching must be rejected at the field seam",
    )

    valueless_rows = copy.deepcopy(observations)
    vix3m = next(
        row for row in valueless_rows if row["field_id"] == "volatility.vix3m_close"
    )
    vix3m.pop("value")
    valueless = run_macro_board(config, valueless_rows, result)
    require(valueless.kind == "blocker", "available status cannot replace the field value")
    require(
        any(
            item.field_id == "volatility.vix3m_close"
            and item.reason == "field_value_missing"
            for item in valueless.blockers
        ),
        "missing normalized value must remain visible",
    )

    mismatched_market_dates = copy.deepcopy(observations)
    ndx = next(
        row for row in mismatched_market_dates if row["field_id"] == "equity.ndx_close"
    )
    ndx["market_reference_date"] = "2026-07-21"
    for point in ndx["history"]:
        point["date"] = (
            date.fromisoformat(point["date"]) - timedelta(days=1)
        ).isoformat()
    common_date = run_macro_board(config, mismatched_market_dates, result)
    require(
        common_date.kind == "blocker",
        "mixed completed-session dates must block the Board",
    )
    require(
        any(
            item.reason == "market_reference_date_not_common"
            for item in common_date.blockers
        ),
        "common-date failure must be visible in the blocker",
    )

    allowed = run_macro_board(config, observations, result)
    require(allowed.kind == "board", "complete normalized input must reach Board delivery")
    require(allowed.delivery_packet is not None, "successful run must return delivery packet")
    require(
        allowed.delivery_packet.standalone_board is not None
        and allowed.delivery_packet.standalone_board.html.startswith(b"<!doctype html>"),
        "successful run must reuse the standalone Board artifact",
    )
    require(not allowed.blockers, "successful run must not retain blockers")
    require(
        round(allowed.resolved_values["equity.ndx_rut_ratio"], 6)
        == round(1240.0 / 120.0, 6),
        "Preflight must derive NDX/RUT rather than trust a caller value",
    )
    require(
        set(allowed.resolved_values).issuperset(
            {
                "credit.hyg_lqd_ratio",
                "volatility.vix_vix3m_ratio",
                "equity.ndx_rut_ratio",
                "equity.ndx_rut_normalized_20d",
                "equity.ndx_rut_ratio.change_1d",
                "equity.ndx_rut_ratio.change_5d",
                "equity.ndx_rut_ratio.change_20d",
            }
        ),
        "all retained derived core fields must be calculated before Board delivery",
    )
    ratio_history = [
        float(ndx["value"]) / float(rut["value"])
        for ndx, rut in zip(
            next(row["history"] for row in observations if row["field_id"] == "equity.ndx_close"),
            next(row["history"] for row in observations if row["field_id"] == "equity.rut_close"),
        )
    ]
    require(
        round(allowed.resolved_values["equity.ndx_rut_ratio.change_5d"], 9)
        == round((ratio_history[-1] / ratio_history[-6] - 1.0) * 100.0, 9),
        "NDX/RUT changes must be derived from aligned completed-session history",
    )

    ibkr_config = dict(config)
    ibkr_config["default_broker"] = "ibkr"
    ibkr_observations = copy.deepcopy(observations)
    for row in ibkr_observations:
        if row["source_id"] == "longbridge":
            row["source_id"] = "ibkr"
    ibkr_allowed = run_macro_board(ibkr_config, ibkr_observations, result)
    require(ibkr_allowed.kind == "board", "IBKR setup must use the same Preflight seam")
    require(
        ibkr_allowed.attempted_brokers == ("ibkr",),
        "Preflight must never auto-switch to the other broker",
    )

    bad_config = dict(config)
    bad_config["default_broker"] = ["longbridge", "ibkr"]
    invalid = run_macro_board(bad_config, observations, result)
    require(invalid.kind == "setup_required", "exactly one default broker is required")
    require(invalid.delivery_packet is None, "invalid setup must not create artifacts")
    print("macro preflight selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
