#!/usr/bin/env python3
"""Instrument Research Board payload policy and renderer adapter."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping

from instrument_research_board import render_instrument_research_board

from artifact_packet_core import (
    ArtifactPacketError,
    EVIDENCE_STATES,
    _is_nonempty_string,
    _parse_timestamp,
    _reject_unknown_fields,
    evaluate_freshness as evaluate_core_freshness,
)


BOARD_ID = "instrument_research"
PAYLOAD_VERSION = "1.0"
FRESHNESS_POLICIES: Mapping[str, timedelta | None] = {
    "official-current-v1": None,
    "event-calendar-v1": timedelta(hours=24),
    "intraday-market-v1": timedelta(minutes=15),
}
REQUIRED_INSTRUMENT_MODULES = ("industry", "fundamentals", "catalysts", "market_instrument")
PAYLOAD_V1_FIELDS = frozenset(
    {
        "board", "claims", "decision", "event_transmission", "modules",
        "payload_version", "peers", "posture", "price_setup", "question",
        "subject", "verification_queue", "views",
    }
)
SUBJECT_V1_FIELDS = frozenset(
    {
        "analysis_horizon", "currency", "identity_status", "instrument",
        "market", "path_dependent", "product_name", "product_type", "underlying",
    }
)
SUPPORTING_INSTRUMENT_MODULES = ("flows",)
ALL_INSTRUMENT_MODULES = REQUIRED_INSTRUMENT_MODULES + SUPPORTING_INSTRUMENT_MODULES
CLAIM_KINDS = frozenset(
    {
        "industry_fact", "fundamental_hypothesis", "event_fact", "market_fact",
        "market_reaction", "counter_thesis",
    }
)
CLAIM_STATUSES = frozenset({"verified", "needs_check", "blocked", "insufficient_alone"})
CLAIM_IMPACTS = frozenset({"supports", "pressures", "blocks", "watch", "none"})
QUEUE_STATUSES = frozenset({"open", "blocked", "complete"})
PEER_STATUSES = frozenset({"complete", "partial", "stale", "source_error"})
EVENT_STATUSES = frozenset({"scheduled", "confirmed", "invalidated", "source_error"})
SETUP_STATES = frozenset({"watch", "candidate", "invalidated", "needs_review"})
LIQUIDITY_STATUSES = frozenset({"usable", "limited", "unavailable"})
VOLATILITY_STATUSES = frozenset({"normal", "elevated", "extreme", "unavailable"})


def validate_payload(snapshot: Mapping[str, Any]) -> None:
    """Validate only Instrument-owned payload fields and evidence semantics."""

    payload = snapshot.get("payload")
    _reject_unknown_fields(payload, PAYLOAD_V1_FIELDS)
    if not isinstance(payload, Mapping):
        return
    _reject_unknown_fields(payload.get("subject"), SUBJECT_V1_FIELDS)
    _validate_payload(snapshot)

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
        module_freshness = evaluate_core_freshness(
            policy_id,
            module_as_of,
            cutoff,
            FRESHNESS_POLICIES,
        )
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





def render_board(
    snapshot: Mapping[str, Any],
    default_view: str,
    presentation_state: str,
) -> bytes:
    return render_instrument_research_board(snapshot, default_view, presentation_state)
