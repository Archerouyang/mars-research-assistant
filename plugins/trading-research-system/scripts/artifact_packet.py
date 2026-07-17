#!/usr/bin/env python3
"""Build immutable, offline research artifact packets from one Board snapshot.

This module owns the public artifact-packet seam only. It never reads a live
source, private runtime state, or a host environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from instrument_research_board import render_instrument_research_board
from macro_regime_board import render_macro_regime_board
from portfolio_risk_board import render_portfolio_risk_board


SCHEMA_VERSION = "1.0"
INSTRUMENT_BOARD = "instrument_research"
MACRO_BOARD = "macro_regime"
PORTFOLIO_BOARD = "portfolio_risk"
PAYLOAD_VERSION = "1.0"
MACRO_PAYLOAD_VERSION = "1.0"
PORTFOLIO_PAYLOAD_VERSION = "1.0"
RENDERER_VERSION = "1.0"
MANIFEST_VERSION = "1.0"
SNAPSHOT_HARD_LIMIT_BYTES = 1536 * 1024
HTML_HARD_LIMIT_BYTES = 4 * 1024 * 1024
MANIFEST_HARD_LIMIT_BYTES = 64 * 1024
PRESENTATION_STATES = frozenset(
    {"ready", "static_fallback", "missing_artifact", "invalid_artifact", "capture_mismatch"}
)
EVIDENCE_STATES = frozenset({"complete", "partial", "stale", "source_error"})
PORTFOLIO_DIRECTIONS = frozenset({"long", "short"})
PORTFOLIO_PRODUCT_TYPES = frozenset({"cash_equity", "etf", "leveraged_etf", "inverse_etf", "option"})
PORTFOLIO_LIQUIDITY_STATES = frozenset({"usable", "limited", "unavailable"})
PORTFOLIO_RESET_FREQUENCIES = frozenset({"none", "daily", "monthly", "expiry"})
FRESHNESS_POLICIES: Mapping[str, timedelta | None] = {
    "official-current-v1": None,
    "event-calendar-v1": timedelta(hours=24),
    "intraday-market-v1": timedelta(minutes=15),
}
PRIVACY_SENTINELS = (
    "/Users/",
    "BEGIN PRIVATE KEY",
    "api_key",
    "password",
    "account_id",
    "broker_response",
    "private_runtime",
    ".codex",
)
PUBLIC_PRIVACY_COMPACT_SENTINELS = frozenset(
    {
        "accountid",
        "accountnumber",
        "credential",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "rawbrokerresponse",
        "brokerresponse",
        "privateplan",
        "privateposition",
        "userchart",
        "usergeneratedchart",
    }
)
PUBLIC_PRIVATE_PATH_PATTERN = re.compile(r"(?:^|/)(?:users|home|\.ssh|\.codex)(?:/|$)", re.IGNORECASE)
BROKER_ACCOUNT_ID_PATTERN = re.compile(r"\b(?:DU|U)\d{5,}\b", re.IGNORECASE)
UNSAFE_DIAGNOSTIC_TERMS = ("traceback", "stack trace", "/Users/", "api_key", "password", "token")
REQUIRED_INSTRUMENT_MODULES = ("industry", "fundamentals", "catalysts", "market_instrument")
REQUIRED_MACRO_MODULES = (
    "plan_context",
    "holdings_context",
    "rates_liquidity",
    "inflation_growth",
    "cross_asset",
    "event_scenarios",
)
REQUIRED_PORTFOLIO_MODULES = (
    "plan_context",
    "position_detail",
    "reconciliation",
    "exposure_mapping",
    "product_risk",
    "stress_inputs",
)
MACRO_DECISION_FAMILIES = ("rates_liquidity", "inflation_growth", "cross_asset", "event_scenarios")
MACRO_VIEWS = ["Overview", "Rates & Liquidity", "Inflation & Growth", "Cross-Asset Impact", "Event Scenarios"]
PORTFOLIO_VIEWS = [
    "Overview",
    "By Symbol",
    "By Theme / Industry",
    "By Product",
    "By Broker",
    "Stress Tests",
]
MACRO_PLAN_CONTEXT_FIELDS = frozenset(
    {
        "active_plan_id",
        "applicable_horizon",
        "applicable_session",
        "assumptions",
        "constraints",
        "current_posture",
        "decision_rules",
    }
)
MACRO_PLAN_UNAVAILABLE_POSTURE = "Plan context unavailable"
MACRO_PLAN_UNAVAILABLE_DECISION = (
    "No plan-linked Macro decision is available until plan context is complete."
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
MACRO_PAYLOAD_FIELDS = frozenset(
    {
        "board",
        "chart_series",
        "decision",
        "evidence",
        "exposure_lens",
        "holdings_context",
        "modules",
        "payload_version",
        "posture",
        "question",
        "scenarios",
        "views",
    }
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
DIAGNOSTIC_SEVERITIES = frozenset({"info", "warning", "error"})
DIAGNOSTIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SAFE_TEXT_FORBIDDEN_TERMS = UNSAFE_DIAGNOSTIC_TERMS + (
    "raw response",
    "credential",
    "authorization",
    "bearer ",
    "full account",
)
ACCOUNT_ID_PATTERN = re.compile(r"\b(?:\d[ -]?){7,}\d\b")
FORBIDDEN_SNAPSHOT_TERMS = (
    "fetch(",
    "xmlhttprequest",
    "websocket",
    "http://",
    "https://",
    "cdn",
    "telemetry",
    "broker",
    "runtime",
    "order action",
)
FORBIDDEN_HTML_TERMS = (
    'src="http',
    "src='http",
    'src="//',
    "src='//",
    'href="http',
    "href='http",
    "fetch(",
    "xmlhttprequest",
    "websocket",
    "telemetry",
    "order action",
)
SNAPSHOT_V1_FIELDS = frozenset(
    {
        "artifact_lifecycle",
        "board",
        "builder",
        "content_hash",
        "coverage",
        "decision_cutoff",
        "diagnostics",
        "evidence_state",
        "locale",
        "payload",
        "payload_version",
        "privacy",
        "renderer_version",
        "schema_version",
        "snapshot_id",
        "source_registry",
        "state_reasons",
        "timezone",
    }
)
BUILDER_V1_FIELDS = frozenset({"generated_at", "id"})
COVERAGE_V1_FIELDS = frozenset({"required_complete", "required_total"})
PAYLOAD_V1_FIELDS = frozenset(
    {
        "board",
        "claims",
        "decision",
        "event_transmission",
        "modules",
        "payload_version",
        "peers",
        "posture",
        "price_setup",
        "question",
        "subject",
        "verification_queue",
        "views",
    }
)
SUBJECT_V1_FIELDS = frozenset(
    {
        "analysis_horizon",
        "currency",
        "identity_status",
        "instrument",
        "market",
        "path_dependent",
        "product_name",
        "product_type",
        "underlying",
    }
)
MODULE_V1_FIELDS = frozenset(
    {
        "as_of",
        "data",
        "evidence_state",
        "freshness_policy_id",
        "gap_reason",
        "id",
        "requirement",
        "source_refs",
        "summary",
    }
)
SOURCE_V1_FIELDS = frozenset({"alias", "as_of", "freshness_policy_id", "freshness_status", "id", "priority"})
SUPPORTING_INSTRUMENT_MODULES = ("flows",)
ALL_INSTRUMENT_MODULES = REQUIRED_INSTRUMENT_MODULES + SUPPORTING_INSTRUMENT_MODULES
CLAIM_KINDS = frozenset({"industry_fact", "fundamental_hypothesis", "event_fact", "market_fact", "market_reaction", "counter_thesis"})
CLAIM_STATUSES = frozenset({"verified", "needs_check", "blocked", "insufficient_alone"})
CLAIM_IMPACTS = frozenset({"supports", "pressures", "blocks", "watch", "none"})
QUEUE_STATUSES = frozenset({"open", "blocked", "complete"})
PEER_STATUSES = frozenset({"complete", "partial", "stale", "source_error"})
EVENT_STATUSES = frozenset({"scheduled", "confirmed", "invalidated", "source_error"})
SETUP_STATES = frozenset({"watch", "candidate", "invalidated", "needs_review"})
LIQUIDITY_STATUSES = frozenset({"usable", "limited", "unavailable"})
VOLATILITY_STATUSES = frozenset({"normal", "elevated", "extreme", "unavailable"})


class ArtifactPacketError(ValueError):
    """A fail-closed public error code without sensitive input details."""


@dataclass(frozen=True)
class ArtifactPacket:
    """Exact bytes returned by the artifact-packet public interface."""

    canonical_json: bytes
    html: bytes
    manifest: bytes


def build_artifact_packet(
    snapshot: Mapping[str, Any],
    *,
    default_view: str = "Overview",
    presentation_state: str = "ready",
) -> ArtifactPacket:
    """Validate one Board snapshot and return its canonical artifact packet."""

    normalized = validate_board_snapshot(snapshot)
    views = normalized["payload"]["views"]
    if default_view not in views:
        raise ArtifactPacketError("default_view_invalid")
    if presentation_state not in PRESENTATION_STATES:
        raise ArtifactPacketError("presentation_state_invalid")

    canonical_json = canonical_json_bytes(normalized)
    _require_size(canonical_json, SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    html = render_research_brief(normalized, default_view, presentation_state)
    _validate_html_safety(html)
    _require_size(html, HTML_HARD_LIMIT_BYTES, "html_size_exceeded")
    html_sha256 = sha256_hex(html)
    manifest = canonical_json_bytes(
        {
            "artifact_identity": f"{normalized['snapshot_id']}:{normalized['board']}",
            "artifact_lifecycle": normalized["artifact_lifecycle"],
            "board": normalized["board"],
            "canonical_html": "research-brief.html",
            "canonical_json": "snapshot.canonical.json",
            "canonical_json_sha256": sha256_hex(canonical_json),
            "content_hash": normalized["content_hash"],
            "decision_cutoff": normalized["decision_cutoff"],
            "default_view": default_view,
            "html_sha256": html_sha256,
            "manifest_version": MANIFEST_VERSION,
            "payload_version": normalized["payload_version"],
            "presentation_state": presentation_state,
            "privacy": normalized["privacy"],
            "renderer_version": normalized["renderer_version"],
            "snapshot_id": normalized["snapshot_id"],
            "snapshot_contract_version": normalized["schema_version"],
            "views": views,
        }
    )
    _require_size(manifest, MANIFEST_HARD_LIMIT_BYTES, "manifest_size_exceeded")
    return ArtifactPacket(canonical_json=canonical_json, html=html, manifest=manifest)


def write_artifact_packet(packet: ArtifactPacket, output_dir: Path) -> dict[str, Path]:
    """Write a packet once; pre-existing bytes must exactly match the packet."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_dir / "snapshot.canonical.json",
        "html": output_dir / "research-brief.html",
        "manifest": output_dir / "artifact.manifest.json",
    }
    existing_names = {path.name for path in output_dir.iterdir()}
    expected_names = {path.name for path in paths.values()}
    if existing_names and existing_names != expected_names:
        raise ArtifactPacketError("immutable_output_conflict")
    if existing_names and any(path.is_symlink() or not path.is_file() for path in paths.values()):
        raise ArtifactPacketError("immutable_output_conflict")
    for key, path in paths.items():
        data = getattr(packet, "canonical_json" if key == "json" else key)
        if path.exists() and path.read_bytes() != data:
            raise ArtifactPacketError("immutable_output_conflict")
    for key, path in paths.items():
        if not path.exists():
            data = getattr(packet, "canonical_json" if key == "json" else key)
            path.write_bytes(data)
    return paths


def validate_instrument_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep-copied valid Instrument snapshot or a safe error code."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    normalized = copy.deepcopy(dict(snapshot))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    if normalized.get("board") != INSTRUMENT_BOARD:
        raise ArtifactPacketError("board_invalid")
    if normalized.get("payload_version") != PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_invalid")
    if normalized.get("renderer_version") != RENDERER_VERSION:
        raise ArtifactPacketError("renderer_version_invalid")
    if normalized.get("privacy") not in {"public_fixture", "private_runtime"}:
        raise ArtifactPacketError("privacy_invalid")
    if normalized.get("artifact_lifecycle") not in {"transient", "durable"}:
        raise ArtifactPacketError("artifact_lifecycle_invalid")
    _validate_public_privacy(normalized)
    _validate_snapshot_action_safety(normalized)
    _validate_v1_field_sets(normalized)
    if not isinstance(normalized.get("payload"), dict):
        raise ArtifactPacketError("payload_invalid")
    payload = normalized["payload"]
    if payload.get("board") != normalized["board"]:
        raise ArtifactPacketError("board_mismatch")
    if payload.get("payload_version") != normalized["payload_version"]:
        raise ArtifactPacketError("payload_version_mismatch")
    if not _is_nonempty_string(normalized.get("snapshot_id")):
        raise ArtifactPacketError("snapshot_id_invalid")
    _parse_timestamp(normalized.get("decision_cutoff"), "decision_cutoff_invalid")
    _validate_envelope_fields(normalized)
    _require_size(canonical_json_bytes(normalized), SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    _validate_sources(normalized)
    _validate_diagnostics(normalized)
    _validate_payload(normalized)
    _validate_content_hash(normalized)
    return normalized


def validate_board_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Dispatch a versioned Board snapshot without weakening Instrument validation."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    validator = {
        MACRO_BOARD: validate_macro_snapshot,
        PORTFOLIO_BOARD: validate_portfolio_snapshot,
    }.get(snapshot.get("board"), validate_instrument_snapshot)
    return validator(snapshot)


def validate_portfolio_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the independently versioned Portfolio Risk Board payload."""

    normalized = copy.deepcopy(dict(snapshot))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    if normalized.get("board") != PORTFOLIO_BOARD:
        raise ArtifactPacketError("board_invalid")
    if normalized.get("payload_version") != PORTFOLIO_PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_invalid")
    if normalized.get("renderer_version") != RENDERER_VERSION:
        raise ArtifactPacketError("renderer_version_invalid")
    if normalized.get("privacy") not in {"public_fixture", "private_runtime"}:
        raise ArtifactPacketError("privacy_invalid")
    if normalized.get("artifact_lifecycle") not in {"transient", "durable"}:
        raise ArtifactPacketError("artifact_lifecycle_invalid")
    _validate_public_privacy(normalized)
    _validate_snapshot_action_safety(normalized)
    _validate_portfolio_field_sets(normalized)
    payload = normalized.get("payload")
    if not isinstance(payload, dict) or payload.get("board") != PORTFOLIO_BOARD:
        raise ArtifactPacketError("board_mismatch")
    if payload.get("payload_version") != PORTFOLIO_PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_mismatch")
    if not _is_nonempty_string(normalized.get("snapshot_id")):
        raise ArtifactPacketError("snapshot_id_invalid")
    _parse_timestamp(normalized.get("decision_cutoff"), "decision_cutoff_invalid")
    _validate_envelope_fields(normalized)
    _validate_sources(normalized)
    _validate_diagnostics(normalized)
    _validate_portfolio_payload(normalized)
    _validate_content_hash(normalized)
    return normalized


def _validate_portfolio_field_sets(snapshot: Mapping[str, Any]) -> None:
    _reject_unknown_fields(snapshot, SNAPSHOT_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("builder"), BUILDER_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("coverage"), COVERAGE_V1_FIELDS)
    payload = snapshot.get("payload")
    _reject_unknown_fields(payload, PORTFOLIO_PAYLOAD_FIELDS)
    if isinstance(payload, Mapping):
        modules = payload.get("modules")
        if isinstance(modules, list):
            for module in modules:
                _reject_unknown_fields(module, MODULE_V1_FIELDS)
    sources = snapshot.get("source_registry")
    if isinstance(sources, list):
        for source in sources:
            _reject_unknown_fields(source, SOURCE_V1_FIELDS)


def _validate_portfolio_payload(snapshot: Mapping[str, Any]) -> None:
    payload = snapshot["payload"]
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
        if evaluate_freshness(policy_id, as_of, cutoff) == "stale" and module["evidence_state"] != "stale":
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


def validate_macro_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the independently versioned, plan-linked Macro Board payload."""

    normalized = copy.deepcopy(dict(snapshot))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    if normalized.get("board") != MACRO_BOARD:
        raise ArtifactPacketError("board_invalid")
    if normalized.get("payload_version") != MACRO_PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_invalid")
    if normalized.get("renderer_version") != RENDERER_VERSION:
        raise ArtifactPacketError("renderer_version_invalid")
    if normalized.get("privacy") not in {"public_fixture", "private_runtime"}:
        raise ArtifactPacketError("privacy_invalid")
    if normalized.get("artifact_lifecycle") not in {"transient", "durable"}:
        raise ArtifactPacketError("artifact_lifecycle_invalid")
    _validate_public_privacy(normalized)
    _validate_snapshot_action_safety(normalized)
    _validate_macro_field_sets(normalized)
    payload = normalized.get("payload")
    if not isinstance(payload, dict) or payload.get("board") != MACRO_BOARD:
        raise ArtifactPacketError("board_mismatch")
    if payload.get("payload_version") != MACRO_PAYLOAD_VERSION:
        raise ArtifactPacketError("payload_version_mismatch")
    if not _is_nonempty_string(normalized.get("snapshot_id")):
        raise ArtifactPacketError("snapshot_id_invalid")
    _parse_timestamp(normalized.get("decision_cutoff"), "decision_cutoff_invalid")
    _validate_envelope_fields(normalized)
    _validate_sources(normalized)
    _validate_diagnostics(normalized)
    _validate_macro_payload(normalized)
    _validate_content_hash(normalized)
    return normalized


def _validate_macro_field_sets(snapshot: Mapping[str, Any]) -> None:
    _reject_unknown_fields(snapshot, SNAPSHOT_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("builder"), BUILDER_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("coverage"), COVERAGE_V1_FIELDS)
    payload = snapshot.get("payload")
    _reject_unknown_fields(payload, MACRO_PAYLOAD_FIELDS)
    if isinstance(payload, Mapping):
        modules = payload.get("modules")
        if isinstance(modules, list):
            for module in modules:
                _reject_unknown_fields(module, MODULE_V1_FIELDS)
    sources = snapshot.get("source_registry")
    if isinstance(sources, list):
        for source in sources:
            _reject_unknown_fields(source, SOURCE_V1_FIELDS)


def _validate_macro_payload(snapshot: Mapping[str, Any]) -> None:
    payload = snapshot["payload"]
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision")):
        raise ArtifactPacketError("payload_invalid")
    if payload.get("views") != MACRO_VIEWS:
        raise ArtifactPacketError("views_invalid")
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ArtifactPacketError("modules_invalid")
    by_id = {item.get("id"): item for item in modules if isinstance(item, Mapping)}
    if len(modules) != len(REQUIRED_MACRO_MODULES) or set(by_id) != set(REQUIRED_MACRO_MODULES):
        raise ArtifactPacketError("modules_invalid")
    source_ids = {source["id"] for source in snapshot["source_registry"]}
    source_by_id = {source["id"]: source for source in snapshot["source_registry"]}
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    complete_count = 0
    for module_id in REQUIRED_MACRO_MODULES:
        module = by_id[module_id]
        if (
            module.get("requirement") != "required"
            or module.get("evidence_state") not in EVIDENCE_STATES
            or not _is_nonempty_string(module.get("summary"))
            or not isinstance(module.get("gap_reason"), str)
        ):
            raise ArtifactPacketError("modules_invalid")
        _validate_macro_module_data(module_id, module.get("data"), module["evidence_state"], cutoff)
        refs = module.get("source_refs")
        if not isinstance(refs, list) or not refs or not set(refs).issubset(source_ids):
            raise ArtifactPacketError("modules_invalid")
        as_of = _parse_timestamp(module.get("as_of"), "modules_invalid")
        policy_id = module.get("freshness_policy_id")
        if as_of > cutoff or policy_id not in FRESHNESS_POLICIES:
            raise ArtifactPacketError("module_freshness_invalid")
        if evaluate_freshness(policy_id, as_of, cutoff) == "stale" and module["evidence_state"] != "stale":
            raise ArtifactPacketError("module_freshness_invalid")
        if module["evidence_state"] in {"complete", "partial"} and not any(
            source_by_id[source_id]["freshness_status"] == "fresh"
            and source_by_id[source_id]["priority"] != "S4"
            for source_id in refs
        ):
            raise ArtifactPacketError("module_source_support_invalid")
        if module["evidence_state"] == "complete":
            complete_count += 1
    if snapshot.get("coverage") != {"required_complete": complete_count, "required_total": len(REQUIRED_MACRO_MODULES)}:
        raise ArtifactPacketError("coverage_mismatch")

    holdings = payload.get("holdings_context")
    if not isinstance(holdings, Mapping) or set(holdings) != {"conditional", "status", "summary"} or not isinstance(
        holdings.get("conditional"), bool
    ) or not all(_is_nonempty_string(holdings.get(key)) for key in ("status", "summary")):
        raise ArtifactPacketError("holdings_invalid")
    if by_id["holdings_context"]["evidence_state"] != "complete" and not holdings["conditional"]:
        raise ArtifactPacketError("holdings_conditional_required")

    exposures = payload.get("exposure_lens")
    if not isinstance(exposures, list) or not exposures:
        raise ArtifactPacketError("exposure_invalid")
    exposure_ids: set[str] = set()
    for item in exposures:
        if not isinstance(item, Mapping) or set(item) != {"id", "impact", "kind", "label", "plan_rule", "sensitivity"} or not all(
            _is_nonempty_string(item.get(key)) for key in item
        ) or item["id"] in exposure_ids:
            raise ArtifactPacketError("exposure_invalid")
        if by_id["holdings_context"]["evidence_state"] != "complete" and "conditional" not in item["impact"].casefold():
            raise ArtifactPacketError("holdings_conditional_required")
        exposure_ids.add(item["id"])

    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ArtifactPacketError("evidence_invalid")
    evidence_ids: set[str] = set()
    seen_categories: set[str] = set()
    category_priorities = {
        "actual": {"S0", "S1"},
        "forecast": {"S1", "S3"},
        "media": {"S2"},
        "thesis": {"S3"},
    }
    for item in evidence:
        allowed = {"as_of", "category", "exposure_id", "family", "id", "label", "plan_effect", "reading", "source_ref", "status", "transmission"}
        if not isinstance(item, Mapping) or set(item) != allowed or not all(_is_nonempty_string(item.get(key)) for key in allowed):
            raise ArtifactPacketError("evidence_invalid")
        if item["id"] in evidence_ids or item["family"] not in MACRO_DECISION_FAMILIES or item["exposure_id"] not in exposure_ids:
            raise ArtifactPacketError("evidence_invalid")
        if item["source_ref"] not in source_by_id or item["category"] not in category_priorities:
            raise ArtifactPacketError("evidence_invalid")
        if source_by_id[item["source_ref"]]["priority"] not in category_priorities[item["category"]]:
            raise ArtifactPacketError("evidence_invalid")
        if _parse_timestamp(item["as_of"], "evidence_invalid") > cutoff:
            raise ArtifactPacketError("evidence_cutoff_invalid")
        evidence_ids.add(item["id"])
        seen_categories.add(item["category"])
    if seen_categories != set(category_priorities):
        raise ArtifactPacketError("evidence_invalid")

    posture = payload.get("posture")
    if not isinstance(posture, Mapping) or set(posture) != {"consequence", "derived_from", "label"} or not all(
        _is_nonempty_string(posture.get(key)) for key in ("consequence", "label")
    ) or not isinstance(posture.get("derived_from"), list) or not posture["derived_from"] or not set(posture["derived_from"]).issubset(evidence_ids):
        raise ArtifactPacketError("posture_derivation_invalid")
    evidence_by_id = {item["id"]: item for item in evidence}
    if not any(
        evidence_by_id[item_id]["category"] == "thesis"
        and evidence_by_id[item_id]["source_ref"] in by_id["plan_context"]["source_refs"]
        for item_id in posture["derived_from"]
    ):
        raise ArtifactPacketError("posture_derivation_invalid")

    if by_id["plan_context"]["evidence_state"] != "complete":
        if posture["label"] != MACRO_PLAN_UNAVAILABLE_POSTURE:
            raise ArtifactPacketError("plan_context_invalid")
        if payload["decision"] != MACRO_PLAN_UNAVAILABLE_DECISION:
            raise ArtifactPacketError("plan_context_invalid")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ArtifactPacketError("scenarios_invalid")
    previous_rank = 0
    for item in scenarios:
        allowed = {"affected_exposures", "confirms", "cross_asset", "impact_rank", "name", "posture", "trigger"}
        if not isinstance(item, Mapping) or set(item) != allowed or not isinstance(item.get("impact_rank"), int) or item["impact_rank"] <= previous_rank or not isinstance(item.get("affected_exposures"), list) or not item["affected_exposures"] or not set(item["affected_exposures"]).issubset(exposure_ids) or not all(_is_nonempty_string(item.get(key)) for key in allowed - {"affected_exposures", "impact_rank"}):
            raise ArtifactPacketError("scenarios_invalid")
        if any(term in " ".join(str(value) for value in item.values()).casefold() for term in ("buy ", "sell ", "order", "enter ", "exit ")):
            raise ArtifactPacketError("scenario_prescriptive")
        previous_rank = item["impact_rank"]

    chart_series = payload.get("chart_series")
    if not isinstance(chart_series, list) or not chart_series or not all(
        isinstance(item, Mapping) and set(item) == {"label", "value"} and _is_nonempty_string(item.get("label")) and isinstance(item.get("value"), (int, float))
        for item in chart_series
    ):
        raise ArtifactPacketError("chart_series_invalid")
    derived_state = _derive_macro_evidence_state(by_id)
    if snapshot.get("evidence_state") != derived_state:
        raise ArtifactPacketError("evidence_state_mismatch")
    if derived_state == "source_error" and "regime" in posture["label"].casefold():
        raise ArtifactPacketError("posture_derivation_invalid")


def _derive_macro_evidence_state(modules: Mapping[str, Mapping[str, Any]]) -> str:
    states = {module_id: modules[module_id]["evidence_state"] for module_id in REQUIRED_MACRO_MODULES}
    if states["plan_context"] != "complete":
        return "source_error"
    if states["cross_asset"] not in {"complete", "partial"}:
        return "source_error"
    usable_families = sum(states[module_id] in {"complete", "partial"} for module_id in MACRO_DECISION_FAMILIES)
    if usable_families < 3:
        return "source_error"
    if all(state == "complete" for state in states.values()):
        return "complete"
    if any(state == "stale" for state in states.values()):
        return "stale"
    return "partial"


def _validate_macro_module_data(
    module_id: str, data: Any, evidence_state: str, cutoff: datetime
) -> None:
    if module_id != "plan_context":
        if not isinstance(data, Mapping) or set(data) != {"rule", "scope"} or not all(
            isinstance(value, str) for value in data.values()
        ):
            raise ArtifactPacketError("module_data_invalid")
        if evidence_state in {"complete", "partial", "stale"} and not all(
            _is_nonempty_string(value) for value in data.values()
        ):
            raise ArtifactPacketError("module_data_invalid")
        if evidence_state == "source_error" and any(data.values()):
            raise ArtifactPacketError("module_data_invalid")
        return

    if not isinstance(data, Mapping) or set(data) != MACRO_PLAN_CONTEXT_FIELDS or not all(
        isinstance(value, str) for value in data.values()
    ):
        raise ArtifactPacketError("plan_context_invalid")
    if evidence_state == "source_error":
        if any(data.values()):
            raise ArtifactPacketError("plan_context_invalid")
        return
    if not all(_is_nonempty_string(value) for value in data.values()):
        raise ArtifactPacketError("plan_context_invalid")
    if _parse_timestamp(data["applicable_session"], "plan_context_invalid").date() != cutoff.date():
        raise ArtifactPacketError("plan_context_invalid")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON with stable key order and no presentation whitespace."""

    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ArtifactPacketError("schema_invalid") from exc


def sha256_hex(data: bytes) -> str:
    """Return the stable SHA-256 identity for an exact byte sequence."""

    return hashlib.sha256(data).hexdigest()


def render_research_brief(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str
) -> bytes:
    """Render one Board through its purpose-specific renderer."""

    if snapshot["board"] == MACRO_BOARD:
        return render_macro_regime_board(
            snapshot,
            default_view,
            presentation_state,
            echarts_source=_load_echarts_source(),
        )
    if snapshot["board"] == PORTFOLIO_BOARD:
        return render_portfolio_risk_board(
            snapshot,
            default_view,
            presentation_state,
            echarts_source=_load_echarts_source(),
        )
    return render_instrument_research_board(snapshot, default_view, presentation_state)


def render_instrument_research_brief(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str
) -> bytes:
    """Backward-compatible Instrument-only render entrypoint."""

    return render_research_brief(snapshot, default_view, presentation_state)


def _load_echarts_source() -> str:
    """Load the bundled offline chart library in the packet-builder layer."""

    return ECHARTS_ASSET.read_text(encoding="utf-8").replace("</script", "<\\/script")


def _validate_sources(snapshot: Mapping[str, Any]) -> None:
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    sources = snapshot.get("source_registry")
    if not isinstance(sources, list) or not sources:
        raise ArtifactPacketError("source_registry_invalid")
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ArtifactPacketError("source_registry_invalid")
        source_id = source.get("id")
        policy = source.get("freshness_policy_id")
        alias = source.get("alias")
        if (
            not _is_nonempty_string(source_id)
            or not _is_nonempty_string(alias)
            or _contains_unsafe_text(alias)
            or source_id in source_ids
            or policy not in FRESHNESS_POLICIES
        ):
            raise ArtifactPacketError("source_registry_invalid")
        source_ids.add(source_id)
        if source.get("priority") not in {"S0", "S1", "S2", "S3", "S4"}:
            raise ArtifactPacketError("source_registry_invalid")
        observed = _parse_timestamp(source.get("as_of"), "source_freshness_invalid")
        if observed > cutoff:
            raise ArtifactPacketError("source_freshness_invalid")
        expected_status = evaluate_freshness(policy, observed, cutoff)
        if source.get("freshness_status") != expected_status:
            raise ArtifactPacketError("source_freshness_invalid")


def _validate_envelope_fields(snapshot: Mapping[str, Any]) -> None:
    builder = snapshot.get("builder")
    if not isinstance(builder, dict) or not _is_nonempty_string(builder.get("id")):
        raise ArtifactPacketError("schema_invalid")
    _parse_timestamp(builder.get("generated_at"), "schema_invalid")
    if not _is_nonempty_string(snapshot.get("timezone")) or not _is_nonempty_string(snapshot.get("locale")):
        raise ArtifactPacketError("schema_invalid")
    if snapshot.get("evidence_state") not in EVIDENCE_STATES:
        raise ArtifactPacketError("evidence_state_invalid")
    reasons = snapshot.get("state_reasons")
    if not isinstance(reasons, list) or not all(isinstance(reason, str) for reason in reasons):
        raise ArtifactPacketError("schema_invalid")


def _validate_v1_field_sets(snapshot: Mapping[str, Any]) -> None:
    """Reject extension fields until a newer snapshot contract explicitly defines them."""

    _reject_unknown_fields(snapshot, SNAPSHOT_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("builder"), BUILDER_V1_FIELDS)
    _reject_unknown_fields(snapshot.get("coverage"), COVERAGE_V1_FIELDS)

    payload = snapshot.get("payload")
    _reject_unknown_fields(payload, PAYLOAD_V1_FIELDS)
    if not isinstance(payload, Mapping):
        return
    _reject_unknown_fields(payload.get("subject"), SUBJECT_V1_FIELDS)
    modules = payload.get("modules")
    if isinstance(modules, list):
        for module in modules:
            _reject_unknown_fields(module, MODULE_V1_FIELDS)

    sources = snapshot.get("source_registry")
    if isinstance(sources, list):
        for source in sources:
            _reject_unknown_fields(source, SOURCE_V1_FIELDS)


def _reject_unknown_fields(value: Any, allowed_fields: frozenset[str]) -> None:
    if isinstance(value, Mapping) and set(value) - allowed_fields:
        raise ArtifactPacketError("schema_invalid")


def evaluate_freshness(policy_id: str, observed_at: datetime, decision_cutoff: datetime) -> str:
    """Evaluate a versioned source freshness policy at a fixed decision cutoff."""

    limit = FRESHNESS_POLICIES.get(policy_id)
    if limit is None:
        return "fresh"
    return "fresh" if decision_cutoff - observed_at <= limit else "stale"


def _validate_payload(snapshot: Mapping[str, Any]) -> None:
    payload = snapshot["payload"]
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision", "posture")):
        raise ArtifactPacketError("payload_invalid")
    subject = payload.get("subject")
    if not isinstance(subject, dict) or not all(
        _is_nonempty_string(subject.get(key))
        for key in (
            "product_type",
            "market",
            "currency",
            "analysis_horizon",
        )
    ):
        raise ArtifactPacketError("subject_invalid")
    identity_status = subject.get("identity_status")
    identity_fields = ("instrument", "underlying", "product_name")
    if identity_status not in {"complete", "source_error"} or not all(
        isinstance(subject.get(key), str) for key in identity_fields
    ):
        raise ArtifactPacketError("subject_invalid")
    if identity_status == "complete" and not all(_is_nonempty_string(subject[key]) for key in identity_fields):
        raise ArtifactPacketError("subject_invalid")
    if identity_status == "source_error" and any(subject[key] for key in identity_fields):
        raise ArtifactPacketError("subject_invalid")
    if not isinstance(subject.get("path_dependent"), bool):
        raise ArtifactPacketError("subject_invalid")
    views = payload.get("views")
    if not isinstance(views, list) or views != ["Overview", "Price & Setup", "Industry & Peers", "Catalysts & Flows"]:
        raise ArtifactPacketError("views_invalid")
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ArtifactPacketError("modules_invalid")
    by_id = {module.get("id"): module for module in modules if isinstance(module, dict)}
    if (
        len(modules) != len(ALL_INSTRUMENT_MODULES)
        or len(by_id) != len(modules)
        or set(by_id) != set(ALL_INSTRUMENT_MODULES)
    ):
        raise ArtifactPacketError("modules_invalid")
    source_ids = {source["id"] for source in snapshot["source_registry"]}
    sources_by_id = {source["id"]: source for source in snapshot["source_registry"]}
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    required_complete = 0
    for module_id in ALL_INSTRUMENT_MODULES:
        module = by_id[module_id]
        expected_requirement = "required" if module_id in REQUIRED_INSTRUMENT_MODULES else "supporting"
        if module.get("requirement") != expected_requirement or module.get("evidence_state") not in EVIDENCE_STATES:
            raise ArtifactPacketError("modules_invalid")
        if not _is_nonempty_string(module.get("summary")) or not isinstance(module.get("gap_reason"), str):
            raise ArtifactPacketError("modules_invalid")
        _validate_module_data(module_id, module.get("data"), module["evidence_state"])
        module_as_of = _parse_timestamp(module.get("as_of"), "modules_invalid")
        refs = module.get("source_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(_is_nonempty_string(reference) for reference in refs)
            or not set(refs).issubset(source_ids)
        ):
            raise ArtifactPacketError("modules_invalid")
        policy_id = module.get("freshness_policy_id")
        if policy_id not in FRESHNESS_POLICIES:
            raise ArtifactPacketError("modules_invalid")
        module_freshness = evaluate_freshness(policy_id, module_as_of, cutoff)
        if module_as_of > cutoff:
            raise ArtifactPacketError("module_freshness_invalid")
        if module_freshness == "stale" and module["evidence_state"] != "stale":
            raise ArtifactPacketError("module_freshness_invalid")
        if module["evidence_state"] in {"complete", "partial"} and not any(
            sources_by_id[reference]["freshness_status"] == "fresh"
            and sources_by_id[reference]["priority"] != "S4"
            for reference in refs
        ):
            raise ArtifactPacketError("module_source_support_invalid")
        if module_id in REQUIRED_INSTRUMENT_MODULES and module["evidence_state"] == "complete":
            required_complete += 1
    coverage = snapshot.get("coverage")
    if coverage != {"required_complete": required_complete, "required_total": 4}:
        raise ArtifactPacketError("coverage_mismatch")
    derived_state = _derive_instrument_evidence_state(by_id, identity_status)
    if snapshot.get("evidence_state") != derived_state:
        raise ArtifactPacketError("evidence_state_mismatch")
    _validate_instrument_details(payload, source_ids, derived_state, cutoff, by_id)


def _validate_module_data(module_id: str, data: Any, evidence_state: str) -> None:
    required_keys = {
        "industry": {"demand", "supply_capacity", "inventory_pricing", "cycle_position", "competitive_structure"},
        "fundamentals": {"business_quality", "earnings_cash_flow", "valuation_context", "operating_risks"},
        "catalysts": {"next_event", "event_time", "expected_transmission"},
        "market_instrument": {"price_structure", "relative_strength", "liquidity", "volatility"},
        "flows": {"participation", "positioning", "methodology"},
    }[module_id]
    if not isinstance(data, Mapping) or set(data) != required_keys:
        raise ArtifactPacketError("module_data_invalid")
    if not all(isinstance(data[key], str) for key in required_keys):
        raise ArtifactPacketError("module_data_invalid")
    if evidence_state in {"complete", "partial", "stale"} and not all(
        _is_nonempty_string(data[key]) for key in required_keys
    ):
        raise ArtifactPacketError("module_data_invalid")
    if evidence_state == "source_error" and any(data[key] for key in required_keys):
        raise ArtifactPacketError("module_data_invalid")


def _validate_instrument_details(
    payload: Mapping[str, Any],
    source_ids: set[str],
    evidence_state: str,
    cutoff: datetime,
    modules: Mapping[str, Mapping[str, Any]],
) -> None:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ArtifactPacketError("claims_invalid")
    claim_ids: set[str] = set()
    for claim in claims:
        allowed = {"id", "kind", "claim", "evidence_gate", "evidence_refs", "status", "impact"}
        if not isinstance(claim, Mapping) or set(claim) != allowed:
            raise ArtifactPacketError("claims_invalid")
        claim_id = claim.get("id")
        refs = claim.get("evidence_refs")
        if (
            not _is_nonempty_string(claim_id)
            or claim_id in claim_ids
            or claim.get("kind") not in CLAIM_KINDS
            or claim.get("status") not in CLAIM_STATUSES
            or claim.get("impact") not in CLAIM_IMPACTS
            or not _is_nonempty_string(claim.get("claim"))
            or claim.get("evidence_gate") not in ALL_INSTRUMENT_MODULES
            or not isinstance(refs, list)
            or not refs
            or not set(refs).issubset(source_ids)
        ):
            raise ArtifactPacketError("claims_invalid")
        gate = claim["evidence_gate"]
        if not set(refs).issubset(set(modules[gate]["source_refs"])):
            raise ArtifactPacketError("claim_source_mismatch")
        if gate == "flows" and claim["kind"] != "market_reaction":
            raise ArtifactPacketError("claim_source_mismatch")
        if gate != "flows" and claim["kind"] == "market_reaction":
            raise ArtifactPacketError("claim_source_mismatch")
        if modules[gate]["evidence_state"] == "source_error" and claim["status"] == "verified":
            raise ArtifactPacketError("claim_source_mismatch")
        claim_ids.add(claim_id)

    queue = payload.get("verification_queue")
    if not isinstance(queue, list):
        raise ArtifactPacketError("verification_queue_invalid")
    for item in queue:
        allowed = {"claim_id", "check", "due_event", "status"}
        if (
            not isinstance(item, Mapping)
            or set(item) != allowed
            or item.get("claim_id") not in claim_ids
            or not all(_is_nonempty_string(item.get(key)) for key in allowed - {"status"})
            or item.get("status") not in QUEUE_STATUSES
        ):
            raise ArtifactPacketError("verification_queue_invalid")

    peers = payload.get("peers")
    if not isinstance(peers, list) or not peers:
        raise ArtifactPacketError("peers_invalid")
    for peer in peers:
        allowed = {
            "symbol", "role", "revenue_growth_pct", "gross_margin_pct", "valuation_multiple",
            "status", "source_refs", "as_of", "comparability_gap",
        }
        refs = peer.get("source_refs") if isinstance(peer, Mapping) else None
        metrics = ("revenue_growth_pct", "gross_margin_pct", "valuation_multiple")
        if (
            not isinstance(peer, Mapping)
            or set(peer) != allowed
            or not all(_is_nonempty_string(peer.get(key)) for key in ("symbol", "role", "as_of"))
            or peer.get("status") not in PEER_STATUSES
            or not isinstance(peer.get("comparability_gap"), str)
            or not isinstance(refs, list)
            or not refs
            or not set(refs).issubset(source_ids)
        ):
            raise ArtifactPacketError("peers_invalid")
        if peer["status"] == "source_error":
            if any(peer.get(key) is not None for key in metrics) or not _is_nonempty_string(peer["comparability_gap"]):
                raise ArtifactPacketError("peers_invalid")
        elif not all(isinstance(peer.get(key), (int, float)) for key in metrics):
            raise ArtifactPacketError("peers_invalid")
        if _parse_timestamp(peer["as_of"], "peers_invalid") > cutoff:
            raise ArtifactPacketError("evidence_cutoff_invalid")

    transmissions = payload.get("event_transmission")
    if not isinstance(transmissions, list) or not transmissions:
        raise ArtifactPacketError("event_transmission_invalid")
    for item in transmissions:
        allowed = {
            "event_id", "event_time", "catalyst", "claim_ids", "expected_evidence", "confirmation",
            "invalidation", "decision_consequence", "source_refs", "status",
        }
        refs = item.get("source_refs") if isinstance(item, Mapping) else None
        linked_claims = item.get("claim_ids") if isinstance(item, Mapping) else None
        if (
            not isinstance(item, Mapping)
            or set(item) != allowed
            or not all(_is_nonempty_string(item.get(key)) for key in allowed - {"claim_ids", "source_refs", "status"})
            or item.get("status") not in EVENT_STATUSES
            or not isinstance(linked_claims, list)
            or not linked_claims
            or not set(linked_claims).issubset(claim_ids)
            or not isinstance(refs, list)
            or not refs
            or not set(refs).issubset(source_ids)
        ):
            raise ArtifactPacketError("event_transmission_invalid")
        if not set(refs).issubset(set(modules["catalysts"]["source_refs"])):
            raise ArtifactPacketError("event_transmission_source_mismatch")
        _parse_timestamp(item["event_time"], "event_transmission_invalid")

    _validate_price_setup(payload.get("price_setup"), evidence_state, cutoff)


def _validate_price_setup(price_setup: Any, evidence_state: str, cutoff: datetime) -> None:
    allowed = {
        "main_timeframe", "auxiliary_timeframe", "setup_state", "research_gate_status", "invalidation",
        "liquidity", "volatility", "product_path", "candles", "overlays", "levels", "zones", "scenarios",
    }
    if not isinstance(price_setup, Mapping) or set(price_setup) != allowed:
        raise ArtifactPacketError("price_setup_invalid")
    if (
        not all(_is_nonempty_string(price_setup.get(key)) for key in ("main_timeframe", "auxiliary_timeframe"))
        or price_setup.get("setup_state") not in SETUP_STATES
        or price_setup.get("research_gate_status") not in {"ready", "blocked"}
    ):
        raise ArtifactPacketError("price_setup_invalid")
    expected_gate = "ready" if evidence_state == "complete" else "blocked"
    if price_setup["research_gate_status"] != expected_gate:
        raise ArtifactPacketError("research_gate_mismatch")

    invalidation = price_setup.get("invalidation")
    if (
        not isinstance(invalidation, Mapping)
        or set(invalidation) != {"price", "condition"}
        or not isinstance(invalidation.get("price"), (int, float))
        or not _is_nonempty_string(invalidation.get("condition"))
    ):
        raise ArtifactPacketError("price_setup_invalid")
    liquidity = price_setup.get("liquidity")
    if (
        not isinstance(liquidity, Mapping)
        or set(liquidity) != {"average_daily_volume", "bid_ask_bps", "status"}
        or not isinstance(liquidity.get("average_daily_volume"), (int, float))
        or not isinstance(liquidity.get("bid_ask_bps"), (int, float))
        or liquidity.get("status") not in LIQUIDITY_STATUSES
    ):
        raise ArtifactPacketError("price_setup_invalid")
    volatility = price_setup.get("volatility")
    if (
        not isinstance(volatility, Mapping)
        or set(volatility) != {"atr_percent", "realized_20d_percent", "status"}
        or not isinstance(volatility.get("atr_percent"), (int, float))
        or not isinstance(volatility.get("realized_20d_percent"), (int, float))
        or volatility.get("status") not in VOLATILITY_STATUSES
    ):
        raise ArtifactPacketError("price_setup_invalid")
    product = price_setup.get("product_path")
    if (
        not isinstance(product, Mapping)
        or set(product) != {"underlying_identity", "leverage_multiple", "reset_frequency", "path_dependency", "risk_note"}
        or not isinstance(product.get("leverage_multiple"), (int, float))
        or not all(_is_nonempty_string(product.get(key)) for key in ("underlying_identity", "reset_frequency", "path_dependency", "risk_note"))
    ):
        raise ArtifactPacketError("price_setup_invalid")
    candles = price_setup.get("candles")
    if not isinstance(candles, list) or len(candles) < 10:
        raise ArtifactPacketError("price_setup_invalid")
    previous_time: int | float | None = None
    for candle in candles:
        if not isinstance(candle, Mapping) or set(candle) != {"time", "open", "high", "low", "close", "volume"}:
            raise ArtifactPacketError("price_setup_invalid")
        if not all(isinstance(candle.get(key), (int, float)) for key in candle):
            raise ArtifactPacketError("price_setup_invalid")
        if candle["low"] > min(candle["open"], candle["close"]) or candle["high"] < max(candle["open"], candle["close"]):
            raise ArtifactPacketError("price_setup_invalid")
        if previous_time is not None and candle["time"] <= previous_time:
            raise ArtifactPacketError("price_setup_invalid")
        if candle["time"] > cutoff.timestamp():
            raise ArtifactPacketError("evidence_cutoff_invalid")
        previous_time = candle["time"]
    _validate_price_collections(price_setup, cutoff)


def _validate_price_collections(price_setup: Mapping[str, Any], cutoff: datetime) -> None:
    overlays = price_setup.get("overlays")
    if not isinstance(overlays, list):
        raise ArtifactPacketError("price_setup_invalid")
    for overlay in overlays:
        if not isinstance(overlay, Mapping) or set(overlay) != {"id", "label", "points"}:
            raise ArtifactPacketError("price_setup_invalid")
        points = overlay.get("points")
        if not _is_nonempty_string(overlay.get("id")) or not _is_nonempty_string(overlay.get("label")) or not isinstance(points, list):
            raise ArtifactPacketError("price_setup_invalid")
        if not all(isinstance(point, Mapping) and set(point) == {"time", "value"} and all(isinstance(point[key], (int, float)) for key in point) for point in points):
            raise ArtifactPacketError("price_setup_invalid")
        if any(point["time"] > cutoff.timestamp() for point in points):
            raise ArtifactPacketError("evidence_cutoff_invalid")
    levels = price_setup.get("levels")
    if not isinstance(levels, list) or not all(
        isinstance(item, Mapping)
        and set(item) == {"price", "label", "kind"}
        and isinstance(item["price"], (int, float))
        and _is_nonempty_string(item["label"])
        and _is_nonempty_string(item["kind"])
        for item in levels
    ):
        raise ArtifactPacketError("price_setup_invalid")
    zones = price_setup.get("zones")
    if not isinstance(zones, list) or not all(
        isinstance(item, Mapping)
        and set(item) == {"low", "high", "label", "kind"}
        and isinstance(item["low"], (int, float))
        and isinstance(item["high"], (int, float))
        and item["low"] <= item["high"]
        and _is_nonempty_string(item["label"])
        and _is_nonempty_string(item["kind"])
        for item in zones
    ):
        raise ArtifactPacketError("price_setup_invalid")
    scenarios = price_setup.get("scenarios")
    scenario_keys = {"name", "bias", "trigger", "evidence_required", "invalidation", "response"}
    if not isinstance(scenarios, list) or not scenarios:
        raise ArtifactPacketError("price_setup_invalid")
    if not all(isinstance(item, Mapping) and set(item) == scenario_keys and all(_is_nonempty_string(item[key]) for key in scenario_keys) for item in scenarios):
        raise ArtifactPacketError("price_setup_invalid")


def _derive_instrument_evidence_state(
    modules: Mapping[str, Mapping[str, Any]], identity_status: str
) -> str:
    states = {module_id: modules[module_id]["evidence_state"] for module_id in REQUIRED_INSTRUMENT_MODULES}
    if identity_status == "source_error":
        return "source_error"
    usable = {module_id for module_id, state in states.items() if state in {"complete", "partial"}}
    if states["industry"] != "complete" or states["fundamentals"] != "complete":
        return "source_error"
    if len(usable) < 3:
        return "source_error"
    if any(state == "stale" for state in states.values()):
        return "stale"
    if all(state == "complete" for state in states.values()):
        return "complete"
    return "partial"


def _validate_content_hash(snapshot: Mapping[str, Any]) -> None:
    content = copy.deepcopy(dict(snapshot))
    expected = content.pop("content_hash", None)
    if not isinstance(expected, str) or len(expected) != 64:
        raise ArtifactPacketError("content_hash_invalid")
    if sha256_hex(canonical_json_bytes(content)) != expected:
        raise ArtifactPacketError("content_hash_mismatch")


def _validate_public_privacy(value: Any) -> None:
    if value.get("privacy") != "public_fixture":
        return
    for text in _iter_snapshot_text(value):
        if _contains_public_privacy_sentinel(text):
            raise ArtifactPacketError("privacy_violation")


def _validate_diagnostics(snapshot: Mapping[str, Any]) -> None:
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise ArtifactPacketError("diagnostics_invalid")
    known_aliases = {source["alias"] for source in snapshot["source_registry"]}
    known_modules = {
        INSTRUMENT_BOARD: set(ALL_INSTRUMENT_MODULES),
        MACRO_BOARD: set(REQUIRED_MACRO_MODULES),
        PORTFOLIO_BOARD: set(REQUIRED_PORTFOLIO_MODULES),
    }.get(snapshot.get("board"), set())
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            raise ArtifactPacketError("diagnostics_invalid")
        allowed = {"code", "severity", "module", "source_alias", "message", "retryable"}
        if set(diagnostic) - allowed:
            raise ArtifactPacketError("diagnostics_invalid")
        code = diagnostic.get("code")
        severity = diagnostic.get("severity")
        message = diagnostic.get("message")
        retryable = diagnostic.get("retryable")
        if (
            not _is_nonempty_string(code)
            or not isinstance(severity, str)
            or severity not in DIAGNOSTIC_SEVERITIES
            or not isinstance(message, str)
            or len(message) > 200
            or not isinstance(retryable, bool)
        ):
            raise ArtifactPacketError("diagnostics_invalid")
        module = diagnostic.get("module")
        source_alias = diagnostic.get("source_alias")
        if (module is not None and not isinstance(module, str)) or (
            source_alias is not None and not isinstance(source_alias, str)
        ):
            raise ArtifactPacketError("diagnostics_invalid")
        for field in (code, message, module, source_alias):
            if field is not None and _contains_unsafe_text(field):
                raise ArtifactPacketError("diagnostic_unsafe")
        if not DIAGNOSTIC_CODE_PATTERN.fullmatch(code):
            raise ArtifactPacketError("diagnostics_invalid")
        if module is not None and (not _is_nonempty_string(module) or module not in known_modules):
            raise ArtifactPacketError("diagnostic_reference_invalid")
        if source_alias is not None and (
            not _is_nonempty_string(source_alias) or source_alias not in known_aliases
        ):
            raise ArtifactPacketError("diagnostic_reference_invalid")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(term.lower() in lowered for term in SAFE_TEXT_FORBIDDEN_TERMS) or bool(
        ACCOUNT_ID_PATTERN.search(value) or BROKER_ACCOUNT_ID_PATTERN.search(value)
    )


def _iter_snapshot_text(value: Any, *, top_level: bool = True):
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            yield str(key)
            if top_level and key == "content_hash":
                continue
            yield from _iter_snapshot_text(nested_value, top_level=False)
    elif isinstance(value, list):
        for nested_value in value:
            yield from _iter_snapshot_text(nested_value, top_level=False)
    elif isinstance(value, str):
        yield value


def _contains_public_privacy_sentinel(value: str) -> bool:
    normalized_path = value.replace("\\", "/")
    compact = re.sub(r"[^a-z0-9]+", "", value.casefold())
    bare_account_id = ACCOUNT_ID_PATTERN.fullmatch(value.strip())
    return (
        any(sentinel.casefold() in value.casefold() for sentinel in PRIVACY_SENTINELS)
        or bool(PUBLIC_PRIVATE_PATH_PATTERN.search(normalized_path))
        or any(sentinel in compact for sentinel in PUBLIC_PRIVACY_COMPACT_SENTINELS)
        or bool(bare_account_id)
        or bool(BROKER_ACCOUNT_ID_PATTERN.search(value))
    )


def _validate_html_safety(html: bytes) -> None:
    lowered = html.decode("utf-8").lower()
    if any(term in lowered for term in FORBIDDEN_HTML_TERMS):
        raise ArtifactPacketError("html_safety_violation")


def _validate_snapshot_action_safety(snapshot: Mapping[str, Any]) -> None:
    forbidden_terms = FORBIDDEN_SNAPSHOT_TERMS
    if snapshot.get("board") == PORTFOLIO_BOARD:
        # Portfolio evidence must name safe broker-source coverage. Continue to
        # reject broker responses through the privacy sentinel and diagnostics
        # gates, while retaining every network, runtime, telemetry, and order
        # action prohibition.
        forbidden_terms = tuple(term for term in FORBIDDEN_SNAPSHOT_TERMS if term != "broker")
    for text in _iter_snapshot_text(snapshot.get("payload", {})):
        if any(term in text.casefold() for term in forbidden_terms):
            raise ArtifactPacketError("html_safety_violation")


def _parse_timestamp(value: Any, error_code: str) -> datetime:
    if not _is_nonempty_string(value):
        raise ArtifactPacketError(error_code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArtifactPacketError(error_code) from exc
    if parsed.tzinfo is None:
        raise ArtifactPacketError(error_code)
    return parsed.astimezone(timezone.utc)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_size(data: bytes, limit: int, error_code: str) -> None:
    if len(data) > limit:
        raise ArtifactPacketError(error_code)
