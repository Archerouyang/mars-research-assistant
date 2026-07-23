#!/usr/bin/env python3
"""Focused black-box self-test for the Macro Blocker-or-Board seam."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from macro_preflight import load_field_registry, run_macro_board


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "assets" / "fixtures" / "input"
AS_OF = "2026-07-23T12:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def research_result() -> dict[str, object]:
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
            "snapshot": load("macro-regime-complete.json"),
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
        row: dict[str, object] = {
            "field_id": field["field_id"],
            "value": float(index),
            "unit": field["unit"],
            "status": "available",
            "data_as_of": AS_OF,
            "source_id": field["source_routes"][0]["source_id"],
            "retrieval_method": "synthetic_golden",
            "raw_field_path": ["fixture", field["field_id"]],
        }
        timing = field["timing"]
        if timing == "completed_market":
            row["market_reference_date"] = "2026-07-22"
        else:
            row["reference_period"] = "2026-07"
        if field.get("change_windows"):
            row.update({"change_1d": 0.1, "change_5d": 0.5, "change_20d": 2.0})
        if field.get("derivation_inputs"):
            row["lineage"] = {
                "inputs": list(field["derivation_inputs"]),
                "formula": field["formula"],
            }
        rows.append(row)
    return rows


def main() -> int:
    config = {
        "default_broker": "longbridge",
        "broker_read_only_enabled": True,
        "skill_version": "1.0.0",
        "field_contract_version": "macro-v1",
    }
    result = research_result()
    observations = complete_observations()

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

    ibkr_config = dict(config)
    ibkr_config["default_broker"] = "ibkr"
    ibkr_allowed = run_macro_board(ibkr_config, observations, result)
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
