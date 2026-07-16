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
from pathlib import Path
import re
from typing import Any, Mapping

from instrument_research_board import render_instrument_research_board


SCHEMA_VERSION = "1.0"
INSTRUMENT_BOARD = "instrument_research"
PAYLOAD_VERSION = "1.0"
RENDERER_VERSION = "1.0"
MANIFEST_VERSION = "1.0"
SNAPSHOT_HARD_LIMIT_BYTES = 1536 * 1024
HTML_HARD_LIMIT_BYTES = 4 * 1024 * 1024
MANIFEST_HARD_LIMIT_BYTES = 64 * 1024
PRESENTATION_STATES = frozenset(
    {"ready", "static_fallback", "missing_artifact", "invalid_artifact", "capture_mismatch"}
)
EVIDENCE_STATES = frozenset({"complete", "partial", "stale", "source_error"})
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
    """Validate one Instrument snapshot and return its canonical artifact packet."""

    normalized = validate_instrument_snapshot(snapshot)
    views = normalized["payload"]["views"]
    if default_view not in views:
        raise ArtifactPacketError("default_view_invalid")
    if presentation_state not in PRESENTATION_STATES:
        raise ArtifactPacketError("presentation_state_invalid")

    canonical_json = canonical_json_bytes(normalized)
    _require_size(canonical_json, SNAPSHOT_HARD_LIMIT_BYTES, "snapshot_size_exceeded")
    html = render_instrument_research_brief(normalized, default_view, presentation_state)
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


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON with stable key order and no presentation whitespace."""

    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ArtifactPacketError("schema_invalid") from exc


def sha256_hex(data: bytes) -> str:
    """Return the stable SHA-256 identity for an exact byte sequence."""

    return hashlib.sha256(data).hexdigest()


def render_instrument_research_brief(
    snapshot: Mapping[str, Any], default_view: str, presentation_state: str
) -> bytes:
    """Render the board through its purpose-specific renderer."""

    return render_instrument_research_board(snapshot, default_view, presentation_state)


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
        if module is not None and (not _is_nonempty_string(module) or module not in ALL_INSTRUMENT_MODULES):
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
    for text in _iter_snapshot_text(snapshot.get("payload", {})):
        if any(term in text.casefold() for term in FORBIDDEN_SNAPSHOT_TERMS):
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
