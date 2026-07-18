#!/usr/bin/env python3
"""Portfolio Risk Board payload policy and renderer adapter."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from pathlib import Path
import re
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
PORTFOLIO_RISK_HORIZONS = frozenset(
    {"intraday", "swing", "medium_term", "long_term", "expiry_bounded"}
)
PORTFOLIO_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
ACTIONABLE_LANGUAGE_PATTERN = re.compile(
    r"\b(?:acquire|add|ask|buy|cancel|close|cover|decrease|enter|execute|exit|"
    r"increase|instruct|liquidate|modify|open|place|purchase|rebalance|reduce|sell|"
    r"short|submit|tell|trade|use)\b",
    re.IGNORECASE,
)
BROKER_REFERENCE_PATTERN = re.compile(r"^[a-z0-9_-]*broker[a-z0-9_-]*$")
BROKER_ALIAS_PATTERN = re.compile(
    r"^(?:Synthetic Broker (?:Alpha|Beta)|"
    r"(?:[A-Z][A-Za-z0-9.&'-]*\s+){0,3}Brokers?)$"
)
DIRECT_ORDER_INTENT_PATTERN = re.compile(
    r"\b(?:acquire|buy|decrease|execute|increase|liquidate|place\s+an?\s+order|"
    r"order|purchase|sell|submit|trade)\b",
    re.IGNORECASE,
)
IMMEDIATE_POSITION_ACTION_PATTERN = re.compile(
    r"(?:\b(?:add|boost|close|cover|enter|exit|open|rebalance|reduce|rotate|short|"
    r"long|unload)\b.{0,80}\b(?:immediately|now|today)\b|"
    r"\b(?:immediately|now|today)\b.{0,80}\b(?:add|boost|close|cover|enter|exit|"
    r"long|open|rebalance|reduce|rotate|short|unload)\b)",
    re.IGNORECASE,
)
ORDER_INSTRUCTION_PATTERN = re.compile(
    r"(?:\b(?:cancel|modify)\b.{0,40}\border\b|\bplace\b.{0,40}\border\b)",
    re.IGNORECASE,
)
ORDER_APPROVAL_PATTERN = re.compile(
    r"\b(?:approval|approved|authorization|authorized)\b",
    re.IGNORECASE,
)
COMMAND_START_PATTERN = re.compile(
    r"^\s*(?:acquire|add|buy|cancel|close|cover|cut|decrease|dispose(?:\s+of)?|"
    r"dump|enter|execute|exit|flatten|halve|increase|liquidate|modify|offload|"
    r"open|pare|place|purchase|rebalance|reduce|rotate|scale\s+(?:down|out)|"
    r"sell|short|submit|take\s+profits?|trade|trim|unload)\b",
    re.IGNORECASE,
)
POSITION_INSTRUCTION_PATTERN = re.compile(
    r"(?:(?i:\b(?:add|close|cut|dump|enter|exit|flatten|halve|long|open|pare|"
    r"reduce|scale\s+(?:down|out(?:\s+of)?)|short|take\s+profit(?:\s+on)?|"
    r"trim|unload)\b)"
    r"(?:.{0,80}\b(?:contracts?|holdings?|lots?|positions?|shares?)\b|"
    r".{0,40}\b[A-Z][A-Z0-9.]{0,9}\b)|"
    r"(?i:\b(?:close|reduce)\b).{0,20}\bhalf\b.{0,20}\bexposure\b|"
    r"(?i:\breduce\b).{0,20}\bexposure\b.{0,20}\bhalf\b|"
    r"(?i:\bcover\b).{0,20}\b\d+(?:\.\d+)?\b.{0,20}"
    r"\b(?:contracts?|lots?|shares?)\b)"
)
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
        "cash_collateral",
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


def allow_snapshot_action_term(path: tuple[str, ...], text: str, term: str) -> bool:
    """Allow broker taxonomy only in structured Portfolio identity fields."""

    if term != "broker" or ACTIONABLE_LANGUAGE_PATTERN.search(text):
        return False
    is_source_ref = (
        len(path) == 3
        and path[0] in {
            "positions",
            "source_coverage",
            "cash_collateral",
            "exclusions",
        }
        and path[1].isdigit()
        and path[2] == "source_ref"
    ) or (
        len(path) == 4
        and path[0] == "modules"
        and path[1].isdigit()
        and path[2] == "source_refs"
        and path[3].isdigit()
    ) or (
        len(path) == 3
        and path[:2] == ("totals", "confirmed_source_refs")
        and path[2].isdigit()
    )
    if is_source_ref:
        return bool(BROKER_REFERENCE_PATTERN.fullmatch(text))
    is_source_alias = (
        len(path) == 3
        and path[0] in {"source_coverage", "cash_collateral", "exclusions"}
        and path[1].isdigit()
        and path[2] == "source_alias"
    )
    if is_source_alias:
        return bool(BROKER_ALIAS_PATTERN.fullmatch(text))
    is_broker_label = (
        len(path) == 4
        and path[:2] == ("aggregations", "by_broker")
        and path[2].isdigit()
        and path[3] == "label"
    )
    if is_broker_label:
        alias, separator, account = text.partition(" / ")
        return bool(separator and account and BROKER_ALIAS_PATTERN.fullmatch(alias))
    fixed_path_values = {
        ("aggregations", "by_broker"): "by_broker",
    }
    if path in fixed_path_values:
        return fixed_path_values[path] == text
    if (
        len(path) == 4
        and path[0] == "exclusions"
        and path[1].isdigit()
        and path[2] == "affected_totals"
        and path[3].isdigit()
    ):
        return text == "by_broker"
    if (
        len(path) == 3
        and path[0] == "exclusions"
        and path[1].isdigit()
        and path[2] == "authorized_scope"
    ):
        return text == "Analytical Board calculations only; broker position remains reported."
    if (
        len(path) == 4
        and path[0] == "exposure_spine"
        and path[1].isdigit()
        and path[2] == "decompositions"
        and path[3].isdigit()
    ):
        return text == "broker"
    if (
        len(path) == 4
        and path[0] == "modules"
        and path[1].isdigit()
        and path[2:] == ("data", "scope")
    ):
        return text == "symbol, theme, product, broker"
    if len(path) == 2 and path[0] == "views" and path[1].isdigit():
        return text == "By Broker"
    return False


def validate_snapshot_text(path: tuple[str, ...], text: str) -> None:
    """Reject order-like imperative text independently of broker taxonomy."""

    if (
        DIRECT_ORDER_INTENT_PATTERN.search(text)
        or IMMEDIATE_POSITION_ACTION_PATTERN.search(text)
        or ORDER_INSTRUCTION_PATTERN.search(text)
        or ORDER_APPROVAL_PATTERN.search(text)
        or (path[-1:] != ("direction",) and COMMAND_START_PATTERN.search(text))
        or POSITION_INSTRUCTION_PATTERN.search(text)
    ):
        raise ArtifactPacketError("html_safety_violation")


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
            or (
                module.get("evidence_state") == "complete"
                and module.get("gap_reason") != ""
            )
            or (
                module.get("evidence_state") != "complete"
                and not _is_nonempty_string(module.get("gap_reason"))
            )
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
        if any(
            as_of
            > _parse_timestamp(
                source_by_id[source_id]["as_of"], "module_freshness_invalid"
            )
            for source_id in refs
        ):
            raise ArtifactPacketError("module_freshness_invalid")
        referenced_freshness = {
            source_by_id[source_id]["freshness_status"] for source_id in refs
        }
        if (
            module["evidence_state"] == "complete"
            and referenced_freshness != {"fresh"}
        ) or (
            module["evidence_state"] == "partial"
            and "fresh" not in referenced_freshness
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
        required = {
            "source_ref",
            "source_alias",
            "account_alias",
            "detail_status",
            "evidence_state",
            "as_of",
            "source_currency",
            "source_nav_context",
            "currency",
            "nav_context",
            "fx_rate_to_base",
            "fx_as_of",
            "fx_source_ref",
            "reconciliation_status",
            "gap_reason",
        }
        if not isinstance(row, Mapping) or set(row) != required or row["source_ref"] not in source_ids:
            raise ArtifactPacketError("source_coverage_invalid")
        if row["source_ref"] in coverage_by_ref:
            raise ArtifactPacketError("source_coverage_invalid")
        coverage_by_ref[row["source_ref"]] = row
        row_as_of = _parse_timestamp(row["as_of"], "source_coverage_invalid")
        row_freshness = evaluate_core_freshness(
            source_by_id[row["source_ref"]]["freshness_policy_id"],
            row_as_of,
            cutoff,
            FRESHNESS_POLICIES,
        )
        if (
            row["detail_status"] not in {"position_detail", "nav_only", "unavailable"}
            or row["evidence_state"] not in EVIDENCE_STATES
            or row["reconciliation_status"] not in {"reconciled", "unreconciled", "not_applicable", "source_error"}
            or not all(
                _is_nonempty_string(row[key])
                for key in (
                    "source_alias",
                    "account_alias",
                    "as_of",
                    "source_currency",
                    "currency",
                    "fx_as_of",
                )
            )
            or row["source_alias"] != source_by_id[row["source_ref"]]["alias"]
            or source_by_id[row["source_ref"]]["freshness_policy_id"]
            != "intraday-market-v1"
            or row["as_of"] != source_by_id[row["source_ref"]]["as_of"]
            or not PORTFOLIO_CURRENCY_PATTERN.fullmatch(row["source_currency"])
            or not PORTFOLIO_CURRENCY_PATTERN.fullmatch(row["currency"])
            or row_as_of > cutoff
            or (
                source_by_id[row["source_ref"]]["freshness_status"] == "stale"
                and row["evidence_state"] != "stale"
            )
            or (row_freshness == "stale" and row["evidence_state"] != "stale")
            or not isinstance(row["gap_reason"], str)
            or (
                row["evidence_state"] == "complete" and row["gap_reason"] != ""
            )
            or (
                row["nav_context"] is not None
                and not _is_portfolio_number(row["nav_context"], minimum=0.0)
            )
        ):
            raise ArtifactPacketError("source_coverage_invalid")
        _validate_fx_metadata(
            row,
            source_by_id,
            cutoff,
            error_code="source_coverage_invalid",
        )
        if row["source_currency"] == row["currency"] and row["fx_as_of"] != row["as_of"]:
            raise ArtifactPacketError("source_coverage_invalid")
        if (row["source_nav_context"] is None) != (row["nav_context"] is None):
            raise ArtifactPacketError("source_coverage_invalid")
        if row["nav_context"] is not None and (
            not _is_portfolio_number(row["source_nav_context"], minimum=0.0)
            or not _portfolio_number_matches(
                row["nav_context"],
                row["source_nav_context"] * row["fx_rate_to_base"],
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
        and row["evidence_state"] in {"complete", "partial", "stale"}
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
    if any(row["currency"] != totals["currency"] for row in coverage):
        raise ArtifactPacketError("position_currency_invalid")
    calculated_total_fields = ("gross_market_value", "net_market_value", "gross_delta_exposure", "net_delta_exposure", "cash_context")
    if confirmed_refs:
        if not all(_is_portfolio_number(totals[key]) for key in calculated_total_fields):
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
        required = {
            "id",
            "symbol",
            "underlying",
            "source_ref",
            "account_alias",
            "product_type",
            "direction",
            "quantity",
            "source_currency",
            "source_market_value",
            "source_direct_exposure",
            "source_delta_exposure",
            "source_notional_exposure",
            "currency",
            "market_value",
            "direct_exposure",
            "delta_exposure",
            "notional_exposure",
            "fx_rate_to_base",
            "fx_as_of",
            "fx_source_ref",
            "theme",
            "industry",
            "event_cluster",
            "liquidity_status",
            "risk_horizon",
            "expiry_at",
            "leverage_multiple",
            "reset_frequency",
            "path_dependency",
            "option_greeks",
            "excluded",
        }
        if not isinstance(position, Mapping) or set(position) != required or position["id"] in position_ids or position["source_ref"] not in totals["confirmed_source_refs"]:
            raise ArtifactPacketError("positions_invalid")
        position_ids.add(position["id"])
        if not all(
            _is_nonempty_string(position[key])
            for key in (
                "id",
                "symbol",
                "underlying",
                "account_alias",
                "product_type",
                "direction",
                "source_currency",
                "currency",
                "fx_as_of",
                "theme",
                "industry",
                "event_cluster",
                "liquidity_status",
                "risk_horizon",
                "reset_frequency",
                "path_dependency",
            )
        ):
            raise ArtifactPacketError("positions_invalid")
        coverage_row = coverage_by_ref[position["source_ref"]]
        if position["account_alias"] != coverage_row["account_alias"]:
            raise ArtifactPacketError("positions_invalid")
        if position["currency"] != totals["currency"]:
            raise ArtifactPacketError("position_currency_invalid")
        numeric_fields = (
            "quantity",
            "source_market_value",
            "source_direct_exposure",
            "source_notional_exposure",
            "market_value",
            "direct_exposure",
            "notional_exposure",
            "leverage_multiple",
        )
        if (
            not all(_is_portfolio_number(position[key]) for key in numeric_fields)
            or (position["delta_exposure"] is not None and not _is_portfolio_number(position["delta_exposure"]))
            or position["quantity"] == 0
            or position["leverage_multiple"] <= 0
            or position["direction"] not in PORTFOLIO_DIRECTIONS
            or position["product_type"] not in PORTFOLIO_PRODUCT_TYPES
            or position["liquidity_status"] not in PORTFOLIO_LIQUIDITY_STATES
            or position["risk_horizon"] not in PORTFOLIO_RISK_HORIZONS
            or position["reset_frequency"] not in PORTFOLIO_RESET_FREQUENCIES
            or (
                position["expiry_at"] is not None
                and not _is_nonempty_string(position["expiry_at"])
            )
            or not isinstance(position["excluded"], bool)
            or not _portfolio_number_matches(
                position["direct_exposure"], position["market_value"]
            )
        ):
            raise ArtifactPacketError("positions_invalid")
        if (
            (position["source_delta_exposure"] is None)
            != (position["delta_exposure"] is None)
            or (
                position["source_delta_exposure"] is not None
                and not _is_portfolio_number(position["source_delta_exposure"])
            )
        ):
            raise ArtifactPacketError("position_currency_invalid")
        _validate_fx_metadata(
            position,
            source_by_id,
            cutoff,
            error_code="position_currency_invalid",
        )
        if (
            position["source_currency"] != coverage_row["source_currency"]
            or position["currency"] != coverage_row["currency"]
            or not _portfolio_number_matches(
                position["fx_rate_to_base"], coverage_row["fx_rate_to_base"]
            )
            or position["fx_as_of"] != coverage_row["fx_as_of"]
            or position["fx_source_ref"] != coverage_row["fx_source_ref"]
        ):
            raise ArtifactPacketError("position_currency_invalid")
        converted_fields = (
            ("source_market_value", "market_value"),
            ("source_direct_exposure", "direct_exposure"),
            ("source_notional_exposure", "notional_exposure"),
        )
        if any(
            not _portfolio_number_matches(
                position[base_field],
                position[source_field] * position["fx_rate_to_base"],
            )
            for source_field, base_field in converted_fields
        ) or (
            position["source_delta_exposure"] is not None
            and not _portfolio_number_matches(
                position["delta_exposure"],
                position["source_delta_exposure"] * position["fx_rate_to_base"],
            )
        ):
            raise ArtifactPacketError("position_currency_invalid")
        if position["product_type"] in {"cash_equity", "etf"} and position["reset_frequency"] != "none":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] in {"leveraged_etf", "inverse_etf"} and position["reset_frequency"] == "none":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] == "option" and position["reset_frequency"] != "expiry":
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] == "option":
            if position["expiry_at"] is None or _parse_timestamp(
                position["expiry_at"], "positions_invalid"
            ) <= cutoff:
                raise ArtifactPacketError("positions_invalid")
        elif position["expiry_at"] is not None:
            raise ArtifactPacketError("positions_invalid")
        if position["product_type"] == "option":
            greeks = position["option_greeks"]
            if greeks is not None and (
                not isinstance(greeks, Mapping)
                or set(greeks) != {"delta", "gamma", "vega", "theta"}
                or not all(_is_portfolio_number(value) for value in greeks.values())
                or not _is_portfolio_number(greeks["delta"], minimum=-1.0, maximum=1.0)
            ):
                raise ArtifactPacketError("option_greeks_required")
            if (greeks is None) != (position["delta_exposure"] is None):
                raise ArtifactPacketError("option_greeks_required")
        elif position["delta_exposure"] is None or position["option_greeks"] is not None:
            raise ArtifactPacketError("positions_invalid")
        direction_sign = 1.0 if position["direction"] == "long" else -1.0
        if position["quantity"] <= 0 or (
            position["market_value"] != 0
            and math.copysign(1.0, position["market_value"]) != direction_sign
        ):
            raise ArtifactPacketError("positions_invalid")
        product_type = position["product_type"]
        if product_type in {"cash_equity", "etf"}:
            if (
                not _portfolio_number_matches(position["leverage_multiple"], 1.0)
                or not _portfolio_number_matches(
                    position["notional_exposure"], position["market_value"]
                )
                or not _portfolio_number_matches(
                    position["delta_exposure"], position["market_value"]
                )
            ):
                raise ArtifactPacketError("positions_invalid")
        elif product_type in {"leveraged_etf", "inverse_etf"}:
            expected_notional = (
                position["market_value"] * position["leverage_multiple"]
            )
            if product_type == "inverse_etf":
                expected_notional *= -1.0
            if (
                (
                    product_type == "leveraged_etf"
                    and position["leverage_multiple"] <= 1.0
                )
                or (
                    product_type == "inverse_etf"
                    and position["leverage_multiple"] < 1.0
                )
                or not _portfolio_number_matches(
                    position["notional_exposure"], expected_notional
                )
                or not _portfolio_number_matches(
                    position["delta_exposure"], expected_notional
                )
            ):
                raise ArtifactPacketError("positions_invalid")
        else:
            if position["notional_exposure"] != 0 and math.copysign(
                1.0, position["notional_exposure"]
            ) != direction_sign:
                raise ArtifactPacketError("positions_invalid")
            if greeks is not None and not _portfolio_number_matches(
                position["delta_exposure"],
                position["notional_exposure"] * greeks["delta"],
            ):
                raise ArtifactPacketError("positions_invalid")

    _validate_cash_collateral(
        payload.get("cash_collateral"),
        confirmed_refs,
        coverage_by_ref,
        positions,
        totals,
        source_by_id,
        cutoff,
    )

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
            or not isinstance(exclusion.get("affected_totals"), list)
            or not exclusion["affected_totals"]
            or not isinstance(exclusion.get("affected_scenarios"), list)
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
    _validate_portfolio_scope_label(
        totals["scope_label"], coverage, confirmed_refs, exclusions
    )
    confirmed_coverage_states = {
        row["evidence_state"]
        for row in coverage
        if row["source_ref"] in confirmed_refs
    }
    expected_position_detail_state = (
        "source_error"
        if not confirmed_refs
        else "stale"
        if "stale" in confirmed_coverage_states
        else "partial"
        if exclusions
        or any(row["source_ref"] not in confirmed_refs for row in coverage)
        or any(
            row["source_ref"] in confirmed_refs and row["evidence_state"] != "complete"
            for row in coverage
        )
        else "complete"
    )
    if by_id["position_detail"]["evidence_state"] != expected_position_detail_state:
        raise ArtifactPacketError("position_detail_state_invalid")
    scenarios = payload.get("stress_scenarios")
    expected_families = {"rates_up", "rates_down", "usd_up", "risk_off", "theme_shock", "event_gap"}
    stress_inputs_state = by_id["stress_inputs"]["evidence_state"]
    if (
        not isinstance(scenarios, list)
        or (confirmed_refs and stress_inputs_state == "source_error" and scenarios)
        or (confirmed_refs and stress_inputs_state != "source_error" and len(scenarios) != 6)
        or (not confirmed_refs and scenarios)
    ):
        raise ArtifactPacketError("stress_scenarios_invalid")
    families: set[str] = set()
    excluded_exposure = sum(
        abs(position["delta_exposure"] or 0.0)
        for position in positions
        if position["excluded"]
    )
    unconfirmed_nav_context = sum(
        row["nav_context"] or 0.0
        for row in coverage
        if row["source_ref"] not in confirmed_refs
    )
    scenario_scope = (totals["gross_delta_exposure"] or 0.0) + excluded_exposure
    missing_greeks_ids = {
        position["id"]
        for position in included_positions
        if position["product_type"] == "option" and position["option_greeks"] is None
    }
    unscoped_derivative_notional = sum(
        abs(position["notional_exposure"])
        for position in positions
        if position["product_type"] == "option"
        and position["delta_exposure"] is None
    )
    for scenario in scenarios:
        required = {
            "name",
            "family",
            "assumptions",
            "covered_exposure",
            "missing_exposure",
            "coverage_basis",
            "impact_model",
            "unscoped_nav_context",
            "unscoped_derivative_notional",
            "estimated_impact",
            "impact_contributions",
            "confidence",
            "gap_reason",
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
            or not isinstance(scenario.get("gap_reason"), str)
            or (
                scenario.get("status") == "complete"
                and scenario.get("gap_reason") != ""
            )
            or (
                scenario.get("status") != "complete"
                and not _is_nonempty_string(scenario.get("gap_reason"))
            )
            or scenario.get("coverage_basis") != "gross_delta_exposure"
            or scenario.get("impact_model") != "position_delta_times_shock_v1"
            or not all(
                _is_portfolio_number(scenario.get(key))
                for key in (
                    "covered_exposure",
                    "missing_exposure",
                    "unscoped_nav_context",
                    "unscoped_derivative_notional",
                    "estimated_impact",
                )
            )
            or scenario["covered_exposure"] < 0
            or scenario["missing_exposure"] < 0
            or scenario["unscoped_nav_context"] < 0
            or scenario["unscoped_derivative_notional"] < 0
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
        affected_positions_by_id = {
            position["id"]: position for position in affected_positions
        }
        for contribution in scenario["impact_contributions"]:
            if (
                not isinstance(contribution, Mapping)
                or set(contribution) != {
                    "position_id",
                    "shock_pct",
                    "estimated_impact",
                }
                or not _is_nonempty_string(contribution.get("position_id"))
                or contribution["position_id"] in contribution_ids
                or contribution["position_id"] not in affected_positions_by_id
                or not _is_portfolio_number(
                    contribution.get("shock_pct"), minimum=-1.0, maximum=1.0
                )
                or not _is_portfolio_number(contribution.get("estimated_impact"))
            ):
                raise ArtifactPacketError("stress_scenarios_invalid")
            contribution_ids.add(contribution["position_id"])
            contribution_position = affected_positions_by_id[contribution["position_id"]]
            if not _portfolio_number_matches(
                contribution["estimated_impact"],
                contribution_position["delta_exposure"]
                * contribution["shock_pct"],
            ):
                raise ArtifactPacketError("stress_scenarios_invalid")
            contribution_total += contribution["estimated_impact"]
        if contribution_ids != set(scenario["affected_position_ids"]) or not _portfolio_number_matches(
            contribution_total, scenario["estimated_impact"]
        ):
            raise ArtifactPacketError("stress_scenarios_invalid")
        expected_covered = sum(
            abs(position["delta_exposure"] or 0.0) for position in affected_positions
        )
        expected_missing = scenario_scope - expected_covered
        if (
            not _portfolio_number_matches(scenario["covered_exposure"], expected_covered)
            or not _portfolio_number_matches(scenario["missing_exposure"], expected_missing)
            or not _portfolio_number_matches(
                scenario["unscoped_nav_context"], unconfirmed_nav_context
            )
            or not _portfolio_number_matches(
                scenario["unscoped_derivative_notional"],
                unscoped_derivative_notional,
            )
            or missing_greeks_ids.intersection(scenario["affected_position_ids"])
            or (missing_greeks_ids and scenario["status"] == "complete")
        ):
            raise ArtifactPacketError("stress_scenarios_invalid")
        families.add(scenario["family"])
    if confirmed_refs and stress_inputs_state != "source_error" and families != expected_families:
        raise ArtifactPacketError("stress_scenarios_invalid")
    if stress_inputs_state != "complete" and any(
        scenario["status"] == "complete" for scenario in scenarios
    ):
        raise ArtifactPacketError("stress_scenarios_invalid")
    if missing_greeks_ids and (
        by_id["product_risk"]["evidence_state"] == "complete"
        or by_id["stress_inputs"]["evidence_state"] == "complete"
    ):
        raise ArtifactPacketError("option_greeks_required")
    derived_state = _derive_portfolio_evidence_state(
        by_id, coverage, confirmed_refs, scenarios
    )
    if snapshot["evidence_state"] != derived_state:
        raise ArtifactPacketError("evidence_state_mismatch")
    if derived_state == "source_error" and (
        posture["label"] != PORTFOLIO_UNAVAILABLE_POSTURE
        or payload["decision"] != PORTFOLIO_UNAVAILABLE_DECISION
    ):
        raise ArtifactPacketError("posture_derivation_invalid")


def _validate_cash_collateral(
    rows: Any,
    confirmed_refs: set[str],
    coverage_by_ref: Mapping[str, Mapping[str, Any]],
    positions: list[Mapping[str, Any]],
    totals: Mapping[str, Any],
    source_by_id: Mapping[str, Mapping[str, Any]],
    cutoff: datetime,
) -> None:
    if not isinstance(rows, list):
        raise ArtifactPacketError("cash_collateral_invalid")
    required = {
        "source_ref",
        "source_alias",
        "account_alias",
        "as_of",
        "source_currency",
        "source_cash_balance",
        "source_collateral_value",
        "currency",
        "cash_balance",
        "collateral_value",
        "fx_rate_to_base",
        "fx_as_of",
        "fx_source_ref",
    }
    if len(rows) != len(confirmed_refs):
        raise ArtifactPacketError("cash_collateral_invalid")
    if not confirmed_refs:
        if rows or totals["cash_context"] is not None:
            raise ArtifactPacketError("cash_collateral_invalid")
        return
    seen_refs: set[str] = set()
    total_cash_collateral = 0.0
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or set(row) != required
            or row.get("source_ref") not in confirmed_refs
            or row["source_ref"] in seen_refs
        ):
            raise ArtifactPacketError("cash_collateral_invalid")
        seen_refs.add(row["source_ref"])
        coverage = coverage_by_ref[row["source_ref"]]
        if (
            row["source_alias"] != coverage["source_alias"]
            or row["account_alias"] != coverage["account_alias"]
            or row["as_of"] != coverage["as_of"]
            or row["source_currency"] != coverage["source_currency"]
            or row["currency"] != coverage["currency"]
            or not _portfolio_number_matches(
                row["fx_rate_to_base"], coverage["fx_rate_to_base"]
            )
            or row["fx_as_of"] != coverage["fx_as_of"]
            or row["fx_source_ref"] != coverage["fx_source_ref"]
            or not _is_portfolio_number(row["source_cash_balance"])
            or not _is_portfolio_number(
                row["source_collateral_value"], minimum=0.0
            )
            or not _is_portfolio_number(row["cash_balance"])
            or not _is_portfolio_number(row["collateral_value"], minimum=0.0)
        ):
            raise ArtifactPacketError("cash_collateral_invalid")
        _validate_fx_metadata(
            row,
            source_by_id,
            cutoff,
            error_code="cash_collateral_invalid",
        )
        if (
            not _portfolio_number_matches(
                row["cash_balance"],
                row["source_cash_balance"] * row["fx_rate_to_base"],
            )
            or not _portfolio_number_matches(
                row["collateral_value"],
                row["source_collateral_value"] * row["fx_rate_to_base"],
            )
        ):
            raise ArtifactPacketError("cash_collateral_invalid")
        source_market_value = sum(
            position["market_value"]
            for position in positions
            if position["source_ref"] == row["source_ref"]
        )
        if not _is_portfolio_number(coverage["nav_context"]) or not _portfolio_number_matches(
            coverage["nav_context"],
            source_market_value + row["cash_balance"] + row["collateral_value"],
        ):
            raise ArtifactPacketError("cash_collateral_invalid")
        total_cash_collateral += row["cash_balance"] + row["collateral_value"]
    if seen_refs != confirmed_refs:
        raise ArtifactPacketError("cash_collateral_invalid")
    if not _portfolio_number_matches(totals["cash_context"], total_cash_collateral):
        raise ArtifactPacketError("portfolio_totals_invalid")


def _derive_portfolio_evidence_state(
    modules: Mapping[str, Mapping[str, Any]],
    coverage: list[Mapping[str, Any]],
    confirmed_refs: set[str],
    scenarios: list[Mapping[str, Any]],
) -> str:
    states = {module_id: modules[module_id]["evidence_state"] for module_id in REQUIRED_PORTFOLIO_MODULES}
    if not confirmed_refs:
        return "source_error"
    if any(state == "source_error" for state in states.values()):
        return "partial"
    scenario_states = {scenario["status"] for scenario in scenarios}
    if any(state == "stale" for state in states.values()) or any(
        row["evidence_state"] == "stale" for row in coverage
    ) or "stale" in scenario_states:
        return "stale"
    fully_reconciled = all(
        row["detail_status"] == "position_detail"
        and row["evidence_state"] == "complete"
        and row["reconciliation_status"] == "reconciled"
        for row in coverage
    )
    if (
        fully_reconciled
        and all(state == "complete" for state in states.values())
        and scenario_states == {"complete"}
    ):
        return "complete"
    return "partial"


def _validate_portfolio_scope_label(
    scope_label: str,
    coverage: list[Mapping[str, Any]],
    confirmed_refs: set[str],
    exclusions: list[Mapping[str, Any]],
) -> None:
    if not confirmed_refs:
        if scope_label != "No confirmed position-detail source":
            raise ArtifactPacketError("portfolio_totals_invalid")
        return
    omissions: list[str] = []
    if any(row["detail_status"] == "nav_only" for row in coverage):
        omissions.append("NAV-only context")
    if any(row["detail_status"] == "unavailable" for row in coverage):
        omissions.append("unavailable source")
    if any(
        row["detail_status"] == "position_detail"
        and row["source_ref"] not in confirmed_refs
        for row in coverage
    ):
        omissions.append("unreconciled position-detail source")
    if exclusions:
        omissions.append("excluded holding")
    expected = (
        "All reconciled position-detail sources"
        if not omissions
        else f"Confirmed position-detail sources only; {' and '.join(omissions)} omitted"
    )
    if scope_label != expected:
        raise ArtifactPacketError("portfolio_totals_invalid")


def _portfolio_number_matches(actual: int | float, expected: int | float) -> bool:
    if not _is_portfolio_number(actual) or not _is_portfolio_number(expected):
        return False
    tolerance = max(1e-6, abs(float(expected)) * 1e-9)
    return abs(float(actual) - float(expected)) <= tolerance


def _validate_fx_metadata(
    item: Mapping[str, Any],
    source_by_id: Mapping[str, Mapping[str, Any]],
    cutoff: Any,
    *,
    error_code: str,
) -> None:
    rate = item.get("fx_rate_to_base")
    fx_as_of_raw = item.get("fx_as_of")
    source_currency = item.get("source_currency")
    base_currency = item.get("currency")
    fx_source_ref = item.get("fx_source_ref")
    if (
        not _is_portfolio_number(rate, minimum=0.0)
        or rate == 0
        or not _is_nonempty_string(source_currency)
        or not _is_nonempty_string(base_currency)
        or not _is_nonempty_string(fx_as_of_raw)
        or (fx_source_ref is not None and not _is_nonempty_string(fx_source_ref))
    ):
        raise ArtifactPacketError(error_code)
    fx_as_of = _parse_timestamp(fx_as_of_raw, error_code)
    if fx_as_of > cutoff:
        raise ArtifactPacketError(error_code)
    if source_currency == base_currency:
        if not _portfolio_number_matches(rate, 1.0) or fx_source_ref is not None:
            raise ArtifactPacketError(error_code)
        return
    if fx_source_ref not in source_by_id:
        raise ArtifactPacketError(error_code)
    fx_source = source_by_id[fx_source_ref]
    if (
        fx_source["priority"] != "S1"
        or fx_source["freshness_policy_id"] != "intraday-market-v1"
        or fx_source["freshness_status"] != "fresh"
        or fx_source["as_of"] != fx_as_of_raw
        or evaluate_core_freshness(
            fx_source["freshness_policy_id"],
            fx_as_of,
            cutoff,
            FRESHNESS_POLICIES,
        )
        != "fresh"
    ):
        raise ArtifactPacketError(error_code)


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
