#!/usr/bin/env python3
"""Portfolio Risk Board payload policy and renderer adapter."""

from __future__ import annotations

from datetime import timedelta
import math
from pathlib import Path
from typing import Any, Mapping

from portfolio_risk_board import render_portfolio_risk_board

from artifact_packet_core import (
    ArtifactPacketError,
    EVIDENCE_STATES,
    _is_nonempty_string,
    _parse_timestamp,
    _reject_unknown_fields,
    evaluate_freshness as evaluate_core_freshness,
)


BOARD_ID = "portfolio_risk"
PAYLOAD_VERSION = "1.0"
FRESHNESS_POLICIES: Mapping[str, timedelta | None] = {
    "official-current-v1": None,
    "event-calendar-v1": timedelta(hours=24),
    "intraday-market-v1": timedelta(minutes=15),
}
REQUIRED_PORTFOLIO_MODULES = (
    "plan_context",
    "position_detail",
    "reconciliation",
    "exposure_mapping",
    "product_risk",
    "stress_inputs",
)
PORTFOLIO_VIEWS = [
    "Overview",
    "By Symbol",
    "By Theme / Industry",
    "By Product",
    "By Broker",
    "Stress Tests",
]
PORTFOLIO_DIRECTIONS = frozenset({"long", "short"})
PORTFOLIO_PRODUCT_TYPES = frozenset(
    {"cash_equity", "etf", "leveraged_etf", "inverse_etf", "option"}
)
PORTFOLIO_LIQUIDITY_STATES = frozenset({"usable", "limited", "unavailable"})
PORTFOLIO_RESET_FREQUENCIES = frozenset({"none", "daily", "monthly", "expiry"})
PORTFOLIO_UNAVAILABLE_POSTURE = "Calculated exposure unavailable"
PORTFOLIO_UNAVAILABLE_DECISION = (
    "No portfolio risk calculation is available until confirmed position detail is restored."
)
ECHARTS_VERSION = "6.1.0"
ECHARTS_ASSET = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "vendor"
    / f"echarts-{ECHARTS_VERSION}"
    / "echarts.min.js"
)
PORTFOLIO_PAYLOAD_FIELDS = frozenset(
    {
        "aggregations",
        "board",
        "decision",
        "exclusions",
        "exposure_spine",
        "modules",
        "payload_version",
        "plan_context",
        "positions",
        "posture",
        "question",
        "risk_ledger",
        "source_coverage",
        "stress_scenarios",
        "totals",
        "views",
    }
)
def validate_payload(snapshot: Mapping[str, Any]) -> None:
    """Validate only Portfolio-owned payload fields and evidence semantics."""

    payload = snapshot["payload"]
    _reject_unknown_fields(payload, PORTFOLIO_PAYLOAD_FIELDS)
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision")):
        raise ArtifactPacketError("payload_invalid")
    if payload.get("views") != PORTFOLIO_VIEWS:
        raise ArtifactPacketError("views_invalid")
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ArtifactPacketError("modules_invalid")
    by_id = {item.get("id"): item for item in modules if isinstance(item, Mapping)}
    if len(modules) != len(REQUIRED_PORTFOLIO_MODULES) or set(by_id) != set(REQUIRED_PORTFOLIO_MODULES):
        raise ArtifactPacketError("modules_invalid")
    source_ids = {source["id"] for source in snapshot["source_registry"]}
    source_by_id = {source["id"]: source for source in snapshot["source_registry"]}
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    complete_count = 0
    for module_id in REQUIRED_PORTFOLIO_MODULES:
        module = by_id[module_id]
        if (
            module.get("requirement") != "required"
            or module.get("evidence_state") not in EVIDENCE_STATES
            or not _is_nonempty_string(module.get("summary"))
            or not isinstance(module.get("gap_reason"), str)
        ):
            raise ArtifactPacketError("modules_invalid")
        data = module.get("data")
        if not isinstance(data, Mapping) or set(data) != {"scope", "rule"} | ({"limit"} if module_id == "plan_context" else set()):
            raise ArtifactPacketError("module_data_invalid")
        if not all(_is_nonempty_string(value) for value in data.values()):
            raise ArtifactPacketError("module_data_invalid")
        refs = module.get("source_refs")
        if not isinstance(refs, list) or not refs or not set(refs).issubset(source_ids):
            raise ArtifactPacketError("modules_invalid")
        as_of = _parse_timestamp(module.get("as_of"), "modules_invalid")
        policy_id = module.get("freshness_policy_id")
        if as_of > cutoff or policy_id not in FRESHNESS_POLICIES:
            raise ArtifactPacketError("module_freshness_invalid")
        if evaluate_core_freshness(policy_id, as_of, cutoff, FRESHNESS_POLICIES) == "stale" and module["evidence_state"] != "stale":
            raise ArtifactPacketError("module_freshness_invalid")
        if module["evidence_state"] in {"complete", "partial"} and not any(
            source_by_id[source_id]["freshness_status"] == "fresh"
            for source_id in refs
        ):
            raise ArtifactPacketError("module_source_support_invalid")
        if module["evidence_state"] == "complete":
            complete_count += 1
    if snapshot.get("coverage") != {"required_complete": complete_count, "required_total": len(REQUIRED_PORTFOLIO_MODULES)}:
        raise ArtifactPacketError("coverage_mismatch")

    posture = payload.get("posture")
    if not isinstance(posture, Mapping) or set(posture) != {"label", "derived_from"} or not _is_nonempty_string(posture.get("label")):
        raise ArtifactPacketError("posture_derivation_invalid")
    derived_from = posture.get("derived_from")
    if not isinstance(derived_from, list) or not derived_from or not set(derived_from).issubset(REQUIRED_PORTFOLIO_MODULES):
        raise ArtifactPacketError("posture_derivation_invalid")

    plan = payload.get("plan_context")
    if not isinstance(plan, Mapping) or set(plan) != {"risk_budget", "constraints", "decision_rules"} or not all(
        _is_nonempty_string(value) for value in plan.values()
    ):
        raise ArtifactPacketError("plan_context_invalid")
    coverage = payload.get("source_coverage")
    if not isinstance(coverage, list) or not coverage:
        raise ArtifactPacketError("source_coverage_invalid")
    coverage_by_ref: dict[str, Mapping[str, Any]] = {}
    for row in coverage:
        required = {"source_ref", "source_alias", "account_alias", "detail_status", "evidence_state", "as_of", "currency", "reconciliation_status", "nav_context", "gap_reason"}
        if not isinstance(row, Mapping) or set(row) != required or row["source_ref"] not in source_ids:
            raise ArtifactPacketError("source_coverage_invalid")
        if row["source_ref"] in coverage_by_ref:
            raise ArtifactPacketError("source_coverage_invalid")
        coverage_by_ref[row["source_ref"]] = row
        if (
            row["detail_status"] not in {"position_detail", "nav_only", "unavailable"}
            or row["evidence_state"] not in EVIDENCE_STATES
            or row["reconciliation_status"] not in {"reconciled", "unreconciled", "not_applicable", "source_error"}
            or not all(_is_nonempty_string(row[key]) for key in ("source_alias", "account_alias", "as_of", "currency"))
            or row["source_alias"] != source_by_id[row["source_ref"]]["alias"]
            or _parse_timestamp(row["as_of"], "source_coverage_invalid") > cutoff
            or not isinstance(row["gap_reason"], str)
            or (
                row["nav_context"] is not None
                and not _is_portfolio_number(row["nav_context"], minimum=0.0)
            )
        ):
            raise ArtifactPacketError("source_coverage_invalid")
        if row["detail_status"] == "position_detail" and row["evidence_state"] == "complete" and row["reconciliation_status"] not in {"reconciled", "unreconciled"}:
            raise ArtifactPacketError("source_coverage_invalid")
        if row["detail_status"] == "nav_only" and row["reconciliation_status"] != "not_applicable":
            raise ArtifactPacketError("source_coverage_invalid")
        if row["detail_status"] == "unavailable" and (
            row["evidence_state"] != "source_error" or row["reconciliation_status"] != "source_error"
        ):
            raise ArtifactPacketError("source_coverage_invalid")
        if row["evidence_state"] != "complete" and not _is_nonempty_string(row["gap_reason"]):
            raise ArtifactPacketError("source_coverage_invalid")

    confirmed_refs = {
        row["source_ref"]
        for row in coverage
        if row["detail_status"] == "position_detail"
        and row["evidence_state"] == "complete"
        and row["reconciliation_status"] == "reconciled"
    }

    totals = payload.get("totals")
    total_fields = {"scope_label", "confirmed_source_refs", "gross_market_value", "net_market_value", "gross_delta_exposure", "net_delta_exposure", "cash_context", "currency", "options_delta_included"}
    if not isinstance(totals, Mapping) or set(totals) != total_fields or not _is_nonempty_string(totals.get("scope_label")):
        raise ArtifactPacketError("portfolio_totals_invalid")
    if (
        not isinstance(totals["confirmed_source_refs"], list)
        or len(totals["confirmed_source_refs"]) != len(set(totals["confirmed_source_refs"]))
        or set(totals["confirmed_source_refs"]) != confirmed_refs
        or not isinstance(totals["options_delta_included"], bool)
        or not _is_nonempty_string(totals.get("currency"))
    ):
        raise ArtifactPacketError("portfolio_totals_invalid")
    if any(coverage_by_ref[source_ref]["currency"] != totals["currency"] for source_ref in confirmed_refs):
        raise ArtifactPacketError("position_currency_invalid")
    calculated_total_fields = ("gross_market_value", "net_market_value", "gross_delta_exposure", "net_delta_exposure", "cash_context")
    if confirmed_refs:
        if not any(token in totals["scope_label"].casefold() for token in ("confirmed", "reconciled")) or not all(
            _is_portfolio_number(totals[key]) for key in calculated_total_fields
        ):
            raise ArtifactPacketError("portfolio_totals_invalid")
        if not _is_portfolio_number(totals["gross_market_value"], minimum=0.0) or not _is_portfolio_number(
            totals["gross_delta_exposure"], minimum=0.0
        ):
            raise ArtifactPacketError("portfolio_totals_invalid")
    elif any(totals[key] is not None for key in calculated_total_fields) or totals["options_delta_included"]:
        raise ArtifactPacketError("portfolio_totals_invalid")

    positions = payload.get("positions")
    if not isinstance(positions, list):
        raise ArtifactPacketError("position_detail_required")
    if confirmed_refs and not positions:
        raise ArtifactPacketError("position_detail_required")
    if not confirmed_refs and positions:
        raise ArtifactPacketError("position_detail_required")
    position_ids: set[str] = set()
    for position in positions:
        required = {"id", "symbol", "underlying", "source_ref", "account_alias", "product_type", "direction", "quantity", "market_value", "currency", "direct_exposure", "delta_exposure", "notional_exposure", "theme", "industry", "event_cluster", "liquidity_status", "leverage_multiple", "reset_frequency", "path_dependency", "option_greeks", "excluded"}
        if not isinstance(position, Mapping) or set(position) != required or position["id"] in position_ids or position["source_ref"] not in totals["confirmed_source_refs"]:
            raise ArtifactPacketError("positions_invalid")
        position_ids.add(position["id"])
        if not all(_is_nonempty_string(position[key]) for key in ("id", "symbol", "underlying", "account_alias", "product_type", "direction", "currency", "theme", "industry", "event_cluster", "liquidity_status", "reset_frequency", "path_dependency")):
            raise ArtifactPacketError("positions_invalid")
        if position["account_alias"] != coverage_by_ref[position["source_ref"]]["account_alias"]:
            raise ArtifactPacketError("positions_invalid")
        if position["currency"] != totals["currency"]:
            raise ArtifactPacketError("position_currency_invalid")
        numeric_fields = ("quantity", "market_value", "direct_exposure", "notional_exposure", "leverage_multiple")
        if (
            not all(_is_portfolio_number(position[key]) for key in numeric_fields)
            or (position["delta_exposure"] is not None and not _is_portfolio_number(position["delta_exposure"]))
            or position["quantity"] == 0
            or position["leverage_multiple"] <= 0
            or position["direction"] not in PORTFOLIO_DIRECTIONS
            or position["product_type"] not in PORTFOLIO_PRODUCT_TYPES
            or position["liquidity_status"] not in PORTFOLIO_LIQUIDITY_STATES
            or position["reset_frequency"] not in PORTFOLIO_RESET_FREQUENCIES
            or not isinstance(position["excluded"], bool)
        ):
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] in {"cash_equity", "etf"} and position["reset_frequency"] != "none":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] in {"leveraged_etf", "inverse_etf"} and position["reset_frequency"] == "none":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] == "option" and position["reset_frequency"] != "expiry":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] == "option":
            greeks = position["option_greeks"]
            if greeks is not None and (
                not isinstance(greeks, Mapping)
                or set(greeks) != {"delta", "gamma", "vega", "theta"}
                or not all(_is_portfolio_number(value) for value in greeks.values())
            ):
                raise ArtifactPacketError("option_greeks_required")
            if (greeks is None) != (position["delta_exposure"] is None):
                raise ArtifactPacketError("option_greeks_required")
        elif position["delta_exposure"] is None or position["option_greeks"] is not None:
            raise ArtifactPacketError("positions_invalid")

    included_positions = [position for position in positions if not position["excluded"]]
    if confirmed_refs:
        reconciled_totals = {
            "gross_market_value": sum(abs(position["market_value"]) for position in included_positions),
            "net_market_value": sum(position["market_value"] for position in included_positions),
            "gross_delta_exposure": sum(
                abs(position["delta_exposure"])
                for position in included_positions
                if position["delta_exposure"] is not None
            ),
            "net_delta_exposure": sum(
                position["delta_exposure"]
                for position in included_positions
                if position["delta_exposure"] is not None
            ),
        }
        if any(not _portfolio_number_matches(totals[key], expected) for key, expected in reconciled_totals.items()):
            raise ArtifactPacketError("portfolio_totals_invalid")
        if totals["options_delta_included"] != any(
            position["product_type"] == "option" and position["delta_exposure"] is not None
            for position in included_positions
        ):
            raise ArtifactPacketError("portfolio_totals_invalid")

    aggregations = payload.get("aggregations")
    if not isinstance(aggregations, Mapping) or set(aggregations) != {
        "by_symbol",
        "by_theme",
        "by_industry",
        "by_product",
        "by_broker",
    }:
        raise ArtifactPacketError("aggregations_invalid")
    excluded_symbols = {position["symbol"] for position in positions if position["excluded"]}
    for dimension, rows in aggregations.items():
        if not isinstance(rows, list) or (confirmed_refs and not rows) or (not confirmed_refs and rows):
            raise ArtifactPacketError("aggregations_invalid")
        for row in rows:
            required = {
                "label",
                "direct_market_value",
                "delta_exposure",
                "notional_exposure",
                "weight_pct",
                "affected_position_ids",
                "affected_holdings",
                "plan_limit",
            }
            if not isinstance(row, Mapping) or set(row) != required or not _is_nonempty_string(row.get("label")) or not _is_nonempty_string(row.get("plan_limit")):
                raise ArtifactPacketError("aggregations_invalid")
            if (
                not all(
                    _is_portfolio_number(row[key])
                    for key in ("direct_market_value", "delta_exposure", "notional_exposure")
                )
                or not _is_portfolio_number(row["weight_pct"], minimum=0.0, maximum=100.0)
                or not isinstance(row["affected_position_ids"], list)
                or not all(_is_nonempty_string(item) for item in row["affected_position_ids"])
                or not isinstance(row["affected_holdings"], list)
                or not all(_is_nonempty_string(item) for item in row["affected_holdings"])
                or excluded_symbols.intersection(row["affected_holdings"])
            ):
                raise ArtifactPacketError("aggregations_invalid")
        if confirmed_refs:
            _validate_portfolio_aggregation(
                dimension,
                rows,
                included_positions,
                totals,
                coverage_by_ref,
            )

    spine = payload.get("exposure_spine")
    if not isinstance(spine, list) or (confirmed_refs and not spine) or (not confirmed_refs and spine):
        raise ArtifactPacketError("exposure_spine_invalid")
    included_symbols = {position["symbol"] for position in included_positions}
    for item in spine:
        required = {"risk_id", "exposure", "risk_issue", "affected_holdings", "decompositions", "plan_constraint"}
        if (
            not isinstance(item, Mapping)
            or set(item) != required
            or not all(_is_nonempty_string(item.get(key)) for key in ("risk_id", "exposure", "risk_issue", "plan_constraint"))
            or not isinstance(item.get("affected_holdings"), list)
            or not item["affected_holdings"]
            or not all(_is_nonempty_string(symbol) for symbol in item["affected_holdings"])
            or not set(item["affected_holdings"]).issubset(included_symbols)
            or not isinstance(item.get("decompositions"), list)
            or item["decompositions"] != ["symbol", "theme", "industry", "product", "broker"]
        ):
            raise ArtifactPacketError("exposure_spine_invalid")
    ledger = payload.get("risk_ledger")
    if not isinstance(ledger, list) or not ledger:
        raise ArtifactPacketError("risk_ledger_invalid")
    for item in ledger:
        required = {"exposure", "risk_issue", "affected_holdings", "plan_constraint", "severity", "status"}
        holdings = item.get("affected_holdings") if isinstance(item, Mapping) else None
        if (
            not isinstance(item, Mapping)
            or set(item) != required
            or not all(_is_nonempty_string(item.get(key)) for key in ("exposure", "risk_issue", "plan_constraint"))
            or item.get("severity") not in {"low", "medium", "high"}
            or item.get("status") not in {"active", "watch", "blocked"}
            or not isinstance(holdings, list)
            or not all(_is_nonempty_string(symbol) for symbol in holdings)
            or not set(holdings).issubset(included_symbols)
            or (confirmed_refs and not holdings)
            or (not confirmed_refs and holdings)
        ):
            raise ArtifactPacketError("risk_ledger_invalid")
    exclusions = payload.get("exclusions")
    if not isinstance(exclusions, list):
        raise ArtifactPacketError("exclusions_invalid")
    exclusion_ids: set[str] = set()
    positions_by_id = {position["id"]: position for position in positions}
    for exclusion in exclusions:
        required = {
            "position_id",
            "symbol",
            "source_ref",
            "source_alias",
            "account_alias",
            "as_of",
            "reported_exposure",
            "authorized_scope",
            "exclusion_policy",
            "reason",
            "affected_totals",
            "affected_scenarios",
        }
        if (
            not isinstance(exclusion, Mapping)
            or set(exclusion) != required
            or exclusion.get("position_id") in exclusion_ids
            or exclusion.get("position_id") not in positions_by_id
            or exclusion.get("source_ref") not in confirmed_refs
            or not all(
                _is_nonempty_string(exclusion.get(key))
                for key in (
                    "position_id",
                    "symbol",
                    "source_ref",
                    "source_alias",
                    "account_alias",
                    "as_of",
                    "authorized_scope",
                    "exclusion_policy",
                    "reason",
                )
            )
            or not _is_portfolio_number(exclusion.get("reported_exposure"), minimum=0.0)
            or not all(isinstance(exclusion.get(key), list) and exclusion[key] for key in ("affected_totals", "affected_scenarios"))
            or not all(
                _is_nonempty_string(value)
                for key in ("affected_totals", "affected_scenarios")
                for value in exclusion[key]
            )
        ):
            raise ArtifactPacketError("exclusions_invalid")
        position = positions_by_id[exclusion["position_id"]]
        if (
            not position["excluded"]
            or exclusion["symbol"] != position["symbol"]
            or exclusion["source_ref"] != position["source_ref"]
            or exclusion["account_alias"] != position["account_alias"]
            or exclusion["source_alias"] != coverage_by_ref[exclusion["source_ref"]]["source_alias"]
            or _parse_timestamp(exclusion["as_of"], "exclusions_invalid") > cutoff
            or exclusion["as_of"] != coverage_by_ref[exclusion["source_ref"]]["as_of"]
            or not _portfolio_number_matches(exclusion["reported_exposure"], abs(position["direct_exposure"]))
        ):
            raise ArtifactPacketError("exclusions_invalid")
        exclusion_ids.add(exclusion["position_id"])
    if {position["id"] for position in positions if position["excluded"]} != exclusion_ids:
        raise ArtifactPacketError("exclusions_invalid")
    expected_exclusion_totals = {
        "gross_market_value",
        "net_market_value",
        "gross_delta_exposure",
        "net_delta_exposure",
        "by_symbol",
        "by_theme",
        "by_industry",
        "by_product",
        "by_broker",
    }
    expected_exclusion_scenarios = {
        scenario.get("name")
        for scenario in payload.get("stress_scenarios", [])
        if isinstance(scenario, Mapping) and _is_nonempty_string(scenario.get("name"))
    }
    if any(
        set(exclusion["affected_totals"]) != expected_exclusion_totals
        or set(exclusion["affected_scenarios"]) != expected_exclusion_scenarios
        for exclusion in exclusions
    ):
        raise ArtifactPacketError("exclusions_invalid")
    expected_position_detail_state = (
        "source_error"
        if not confirmed_refs
        else "partial"
        if exclusions or any(row["source_ref"] not in confirmed_refs for row in coverage)
        else "complete"
    )
    if by_id["position_detail"]["evidence_state"] != expected_position_detail_state:
        raise ArtifactPacketError("position_detail_state_invalid")
    scenarios = payload.get("stress_scenarios")
    expected_families = {"rates_up", "rates_down", "usd_up", "risk_off", "theme_shock", "event_gap"}
    if not isinstance(scenarios, list) or (confirmed_refs and len(scenarios) != 6) or (not confirmed_refs and scenarios):
        raise ArtifactPacketError("stress_scenarios_invalid")
    families: set[str] = set()
    excluded_exposure = sum(abs(position["direct_exposure"]) for position in positions if position["excluded"])
    unconfirmed_nav_context = sum(
        row["nav_context"] or 0.0
        for row in coverage
        if row["source_ref"] not in confirmed_refs
    )
    scenario_scope = (totals["gross_market_value"] or 0.0) + excluded_exposure + unconfirmed_nav_context
    missing_greeks_ids = {
        position["id"]
        for position in included_positions
        if position["product_type"] == "option" and position["option_greeks"] is None
    }
    for scenario in scenarios:
        required = {
            "name",
            "family",
            "assumptions",
            "covered_exposure",
            "missing_exposure",
            "estimated_impact",
            "impact_contributions",
            "confidence",
            "affected_position_ids",
            "affected_holdings",
            "plan_constraint",
            "status",
            "additive",
        }
        if (
            not isinstance(scenario, Mapping)
            or set(scenario) != required
            or scenario.get("family") not in expected_families
            or scenario["family"] in families
            or scenario.get("status") not in EVIDENCE_STATES
            or not all(_is_nonempty_string(scenario.get(key)) for key in ("name", "family", "confidence", "plan_constraint"))
            or not all(
                _is_portfolio_number(scenario.get(key))
                for key in ("covered_exposure", "missing_exposure", "estimated_impact")
            )
            or scenario["covered_exposure"] < 0
            or scenario["missing_exposure"] < 0
            or abs(scenario["estimated_impact"]) > scenario["covered_exposure"]
            or scenario.get("confidence") not in {"low", "medium", "high"}
            or not isinstance(scenario.get("assumptions"), list)
            or not scenario["assumptions"]
            or not all(_is_nonempty_string(item) for item in scenario["assumptions"])
            or not isinstance(scenario.get("affected_holdings"), list)
            or not scenario["affected_holdings"]
            or not all(_is_nonempty_string(item) for item in scenario["affected_holdings"])
            or not set(scenario["affected_holdings"]).issubset(included_symbols)
            or not isinstance(scenario.get("affected_position_ids"), list)
            or not scenario["affected_position_ids"]
            or not all(_is_nonempty_string(item) for item in scenario["affected_position_ids"])
            or len(scenario["affected_position_ids"]) != len(set(scenario["affected_position_ids"]))
            or not set(scenario["affected_position_ids"]).issubset({position["id"] for position in included_positions})
            or not isinstance(scenario.get("impact_contributions"), list)
            or not scenario["impact_contributions"]
            or not isinstance(scenario.get("additive"), bool)
            or not scenario["additive"]
            or excluded_symbols.intersection(scenario["affected_holdings"])
        ):
            raise ArtifactPacketError("stress_scenarios_invalid")
        affected_positions = [
            position
            for position in included_positions
            if position["id"] in scenario["affected_position_ids"]
        ]
        if set(scenario["affected_holdings"]) != {position["symbol"] for position in affected_positions}:
            raise ArtifactPacketError("stress_scenarios_invalid")
        contribution_ids: set[str] = set()
        contribution_total = 0.0
        for contribution in scenario["impact_contributions"]:
            if (
                not isinstance(contribution, Mapping)
                or set(contribution) != {"position_id", "estimated_impact"}
                or not _is_nonempty_string(contribution.get("position_id"))
                or contribution["position_id"] in contribution_ids
                or not _is_portfolio_number(contribution.get("estimated_impact"))
            ):
                raise ArtifactPacketError("stress_scenarios_invalid")
            contribution_ids.add(contribution["position_id"])
            contribution_total += contribution["estimated_impact"]
        if contribution_ids != set(scenario["affected_position_ids"]) or not _portfolio_number_matches(
            contribution_total, scenario["estimated_impact"]
        ):
            raise ArtifactPacketError("stress_scenarios_invalid")
        expected_covered = sum(abs(position["direct_exposure"]) for position in affected_positions)
        expected_missing = scenario_scope - expected_covered
        if (
            not _portfolio_number_matches(scenario["covered_exposure"], expected_covered)
            or not _portfolio_number_matches(scenario["missing_exposure"], expected_missing)
            or missing_greeks_ids.intersection(scenario["affected_position_ids"])
            or (missing_greeks_ids and scenario["status"] == "complete")
        ):
            raise ArtifactPacketError("stress_scenarios_invalid")
        families.add(scenario["family"])
    if confirmed_refs and families != expected_families:
        raise ArtifactPacketError("stress_scenarios_invalid")
    if missing_greeks_ids and (
        by_id["product_risk"]["evidence_state"] == "complete"
        or by_id["stress_inputs"]["evidence_state"] == "complete"
    ):
        raise ArtifactPacketError("option_greeks_required")
    derived_state = _derive_portfolio_evidence_state(by_id, coverage, confirmed_refs)
    if snapshot["evidence_state"] != derived_state:
        raise ArtifactPacketError("evidence_state_mismatch")
    if derived_state == "source_error" and (
        posture["label"] != PORTFOLIO_UNAVAILABLE_POSTURE
        or payload["decision"] != PORTFOLIO_UNAVAILABLE_DECISION
    ):
        raise ArtifactPacketError("posture_derivation_invalid")


def _derive_portfolio_evidence_state(
    modules: Mapping[str, Mapping[str, Any]], coverage: list[Mapping[str, Any]], confirmed_refs: set[str]
) -> str:
    states = {module_id: modules[module_id]["evidence_state"] for module_id in REQUIRED_PORTFOLIO_MODULES}
    if not confirmed_refs:
        return "source_error"
    if any(state == "source_error" for state in states.values()):
        return "partial"
    if any(state == "stale" for state in states.values()) or any(
        row["evidence_state"] == "stale" for row in coverage
    ):
        return "stale"
    fully_reconciled = all(
        row["detail_status"] == "position_detail"
        and row["evidence_state"] == "complete"
        and row["reconciliation_status"] == "reconciled"
        for row in coverage
    )
    if fully_reconciled and all(state == "complete" for state in states.values()):
        return "complete"
    return "partial"


def _portfolio_number_matches(actual: int | float, expected: int | float) -> bool:
    if not _is_portfolio_number(actual) or not _is_portfolio_number(expected):
        return False
    tolerance = max(1e-6, abs(float(expected)) * 1e-9)
    return abs(float(actual) - float(expected)) <= tolerance


def _is_portfolio_number(value: Any, *, minimum: float | None = None, maximum: float | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return False
    if minimum is not None and float(value) < minimum:
        return False
    if maximum is not None and float(value) > maximum:
        return False
    return True


def _validate_portfolio_aggregation(
    dimension: str,
    rows: list[Mapping[str, Any]],
    positions: list[Mapping[str, Any]],
    totals: Mapping[str, Any],
    coverage_by_ref: Mapping[str, Mapping[str, Any]],
) -> None:
    positions_by_id = {position["id"]: position for position in positions}
    expected_position_ids = set(positions_by_id)
    seen_position_ids: set[str] = set()
    group_fields = {
        "by_symbol": ("underlying",),
        "by_theme": ("theme",),
        "by_industry": ("industry",),
        "by_product": ("product_type",),
        "by_broker": ("source_ref", "account_alias"),
    }
    for row in rows:
        position_ids = set(row["affected_position_ids"])
        if (
            not position_ids
            or len(position_ids) != len(row["affected_position_ids"])
            or not position_ids.issubset(expected_position_ids)
            or position_ids.intersection(seen_position_ids)
        ):
            raise ArtifactPacketError("aggregations_invalid")
        row_positions = [positions_by_id[position_id] for position_id in row["affected_position_ids"]]
        expected_holdings = {position["symbol"] for position in row_positions}
        if set(row["affected_holdings"]) != expected_holdings:
            raise ArtifactPacketError("aggregations_invalid")
        grouping = {tuple(position[field] for field in group_fields[dimension]) for position in row_positions}
        if len(grouping) != 1:
            raise ArtifactPacketError("aggregations_invalid")
        group = next(iter(grouping))
        expected_label = _portfolio_aggregation_label(dimension, group, row_positions, coverage_by_ref)
        if row["label"] != expected_label:
            raise ArtifactPacketError("aggregations_invalid")
        expected_values = {
            "direct_market_value": sum(position["direct_exposure"] for position in row_positions),
            "delta_exposure": sum(
                position["delta_exposure"]
                for position in row_positions
                if position["delta_exposure"] is not None
            ),
            "notional_exposure": sum(position["notional_exposure"] for position in row_positions),
        }
        gross_delta = totals["gross_delta_exposure"]
        expected_weight = (
            100.0
            * sum(
                abs(position["delta_exposure"])
                for position in row_positions
                if position["delta_exposure"] is not None
            )
            / gross_delta
            if gross_delta
            else 0.0
        )
        if any(not _portfolio_number_matches(row[key], expected) for key, expected in expected_values.items()) or not _portfolio_number_matches(
            row["weight_pct"], round(expected_weight, 1)
        ):
            raise ArtifactPacketError("aggregations_invalid")
        seen_position_ids.update(position_ids)
    if seen_position_ids != expected_position_ids:
        raise ArtifactPacketError("aggregations_invalid")


def _portfolio_aggregation_label(
    dimension: str,
    group: tuple[Any, ...],
    positions: list[Mapping[str, Any]],
    coverage_by_ref: Mapping[str, Mapping[str, Any]],
) -> str:
    if dimension == "by_symbol":
        return f"{group[0]} look-through" if len(positions) > 1 else str(group[0])
    if dimension in {"by_theme", "by_industry"}:
        return str(group[0])
    if dimension == "by_product":
        return {
            "cash_equity": "Cash equities",
            "etf": "ETFs",
            "leveraged_etf": "Daily leveraged ETF",
            "inverse_etf": "Inverse ETF",
            "option": "Listed option",
        }[str(group[0])]
    source_ref, account_alias = group
    return f"{coverage_by_ref[str(source_ref)]['source_alias']} / {account_alias}"


def render_board(
    snapshot: Mapping[str, Any],
    default_view: str,
    presentation_state: str,
) -> bytes:
    return render_portfolio_risk_board(
        snapshot,
        default_view,
        presentation_state,
        echarts_source=ECHARTS_ASSET.read_text(encoding="utf-8").replace(
            "</script", "<\\/script"
        ),
    )
