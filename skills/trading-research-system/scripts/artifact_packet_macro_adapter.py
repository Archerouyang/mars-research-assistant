#!/usr/bin/env python3
"""Macro Regime Board payload policy and renderer adapter."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from macro_regime_board import render_macro_regime_board

from artifact_packet_core import (
    ArtifactPacketError,
    EVIDENCE_STATES,
    _is_nonempty_string,
    _parse_timestamp,
    _reject_unknown_fields,
    evaluate_freshness as evaluate_core_freshness,
)


BOARD_ID = "macro_regime"
PAYLOAD_VERSION = "1.0"
FRESHNESS_POLICIES: Mapping[str, timedelta | None] = {
    "official-current-v1": None,
    "event-calendar-v1": timedelta(hours=24),
    "intraday-market-v1": timedelta(minutes=15),
}
REQUIRED_MACRO_MODULES = (
    "plan_context", "holdings_context", "rates_liquidity", "inflation_growth",
    "cross_asset", "event_scenarios",
)
MACRO_DECISION_FAMILIES = ("rates_liquidity", "inflation_growth", "cross_asset", "event_scenarios")
MACRO_VIEWS = [
    "Overview", "Rates & Liquidity", "Inflation & Growth",
    "Cross-Asset Impact", "Event Scenarios",
]
MARS_DIRECT_PROFILE = "mars_direct_v1"
MARS_DIRECT_MODULES = (
    "plan_context", "rates_liquidity", "cross_asset", "policy_watch",
)
MARS_DIRECT_VIEWS = [
    "Overview", "Rates & Liquidity", "Cross-Asset Impact", "Policy Watch",
]
MARS_DIRECT_EVIDENCE_FAMILIES = frozenset(
    {"rates_liquidity", "cross_asset", "policy_watch"}
)
MACRO_PLAN_CONTEXT_FIELDS = frozenset(
    {
        "active_plan_id", "applicable_horizon", "applicable_session",
        "assumptions", "constraints", "current_posture", "decision_rules",
    }
)
MACRO_PLAN_UNAVAILABLE_POSTURE = "Plan context unavailable"
MACRO_PLAN_UNAVAILABLE_DECISION = (
    "No plan-linked Macro decision is available until plan context is complete."
)
MACRO_DERIVED_BINDING_IDS = frozenset(
    {
        "equity.ndx_rut_ratio.change_1d",
        "equity.ndx_rut_ratio.change_5d",
        "equity.ndx_rut_ratio.change_20d",
    }
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
        "board", "chart_series", "decision", "evidence", "exposure_lens",
        "holdings_context", "modules", "payload_version", "posture", "question",
        "scenarios", "views", "trend_series", "event_watch",
        "policy_watch", "asset_preferences", "liquidity_background", "preflight",
        "macro_profile",
    }
)


def validate_payload(snapshot: Mapping[str, Any]) -> None:
    """Validate only Macro-owned payload fields and evidence semantics."""

    payload = snapshot.get("payload")
    _reject_unknown_fields(payload, MACRO_PAYLOAD_FIELDS)
    _validate_macro_payload(snapshot)


def _validate_macro_payload(snapshot: Mapping[str, Any]) -> None:
    payload = snapshot["payload"]
    if payload.get("macro_profile") == MARS_DIRECT_PROFILE:
        _validate_mars_direct_macro_payload(snapshot)
        return
    if "macro_profile" in payload:
        raise ArtifactPacketError("macro_profile_invalid")
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision")):
        raise ArtifactPacketError("payload_invalid")
    if payload.get("views") != MACRO_VIEWS:
        raise ArtifactPacketError("views_invalid")
    _validate_preflight_binding_metadata(payload.get("preflight"))
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
        if (
            evaluate_core_freshness(
                policy_id,
                as_of,
                cutoff,
                FRESHNESS_POLICIES,
            )
            == "stale"
            and module["evidence_state"] != "stale"
        ):
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
    _validate_trend_series(payload.get("trend_series"), cutoff)
    _validate_event_watch(payload.get("event_watch"), cutoff)
    _validate_policy_watch(payload.get("policy_watch"), cutoff)
    _validate_asset_preferences(
        payload.get("asset_preferences"), payload.get("liquidity_background")
    )
    derived_state = _derive_macro_evidence_state(by_id)
    if snapshot.get("evidence_state") != derived_state:
        raise ArtifactPacketError("evidence_state_mismatch")
    if derived_state == "source_error" and "regime" in posture["label"].casefold():
        raise ArtifactPacketError("posture_derivation_invalid")


def _validate_mars_direct_macro_payload(snapshot: Mapping[str, Any]) -> None:
    """Validate the fail-closed, direct-web-only Mars Macro profile."""

    payload = snapshot["payload"]
    if not all(_is_nonempty_string(payload.get(key)) for key in ("question", "decision")):
        raise ArtifactPacketError("payload_invalid")
    if payload.get("views") != MARS_DIRECT_VIEWS:
        raise ArtifactPacketError("views_invalid")
    _validate_preflight_binding_metadata(payload.get("preflight"))
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ArtifactPacketError("modules_invalid")
    by_id = {item.get("id"): item for item in modules if isinstance(item, Mapping)}
    if len(modules) != len(MARS_DIRECT_MODULES) or set(by_id) != set(MARS_DIRECT_MODULES):
        raise ArtifactPacketError("modules_invalid")
    source_by_id = {source["id"]: source for source in snapshot["source_registry"]}
    cutoff = _parse_timestamp(snapshot["decision_cutoff"], "decision_cutoff_invalid")
    for module_id in MARS_DIRECT_MODULES:
        module = by_id[module_id]
        if (
            module.get("requirement") != "required"
            or module.get("evidence_state") != "complete"
            or not _is_nonempty_string(module.get("summary"))
            or module.get("gap_reason") != ""
        ):
            raise ArtifactPacketError("modules_invalid")
        _validate_macro_module_data(module_id, module.get("data"), "complete", cutoff)
        refs = module.get("source_refs")
        if not isinstance(refs, list) or len(refs) != 1 or refs[0] not in source_by_id:
            raise ArtifactPacketError("modules_invalid")
        if source_by_id[refs[0]]["freshness_status"] != "fresh":
            raise ArtifactPacketError("module_source_support_invalid")
        as_of = _parse_timestamp(module.get("as_of"), "modules_invalid")
        if as_of > cutoff or module.get("freshness_policy_id") not in FRESHNESS_POLICIES:
            raise ArtifactPacketError("module_freshness_invalid")
    if snapshot.get("coverage") != {"required_complete": 4, "required_total": 4}:
        raise ArtifactPacketError("coverage_mismatch")
    if snapshot.get("evidence_state") != "complete":
        raise ArtifactPacketError("evidence_state_mismatch")

    holdings = payload.get("holdings_context")
    if (
        not isinstance(holdings, Mapping)
        or set(holdings) != {"conditional", "status", "summary"}
        or holdings.get("conditional") is not True
        or not all(_is_nonempty_string(holdings.get(key)) for key in ("status", "summary"))
    ):
        raise ArtifactPacketError("holdings_invalid")

    exposures = payload.get("exposure_lens")
    if not isinstance(exposures, list) or not exposures:
        raise ArtifactPacketError("exposure_invalid")
    exposure_ids: set[str] = set()
    for item in exposures:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"id", "impact", "kind", "label", "plan_rule", "sensitivity"}
            or not all(_is_nonempty_string(item.get(key)) for key in item)
            or item["id"] in exposure_ids
            or "conditional" not in item["impact"].casefold()
        ):
            raise ArtifactPacketError("exposure_invalid")
        exposure_ids.add(item["id"])

    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or len(evidence) != 3:
        raise ArtifactPacketError("evidence_invalid")
    evidence_ids: set[str] = set()
    allowed = {
        "as_of", "category", "exposure_id", "family", "id", "label",
        "plan_effect", "reading", "source_ref", "status", "transmission",
    }
    for item in evidence:
        if (
            not isinstance(item, Mapping)
            or set(item) != allowed
            or not all(_is_nonempty_string(item.get(key)) for key in allowed)
            or item["id"] in evidence_ids
            or item["family"] not in MARS_DIRECT_EVIDENCE_FAMILIES
            or item["exposure_id"] not in exposure_ids
            or item["category"] != "actual"
            or item["status"] != "verified"
            or item["source_ref"] not in source_by_id
            or source_by_id[item["source_ref"]]["priority"] != "S0"
            or _parse_timestamp(item["as_of"], "evidence_invalid") > cutoff
        ):
            raise ArtifactPacketError("evidence_invalid")
        evidence_ids.add(item["id"])
    if {item["family"] for item in evidence} != MARS_DIRECT_EVIDENCE_FAMILIES:
        raise ArtifactPacketError("evidence_invalid")

    posture = payload.get("posture")
    if (
        not isinstance(posture, Mapping)
        or set(posture) != {"consequence", "derived_from", "label"}
        or not all(_is_nonempty_string(posture.get(key)) for key in ("consequence", "label"))
        or not isinstance(posture.get("derived_from"), list)
        or set(posture["derived_from"]) != evidence_ids
    ):
        raise ArtifactPacketError("posture_derivation_invalid")

    scenarios = payload.get("scenarios")
    if scenarios != []:
        raise ArtifactPacketError("scenarios_invalid")

    chart_series = payload.get("chart_series")
    if not isinstance(chart_series, list) or not chart_series or not all(
        isinstance(item, Mapping)
        and set(item) == {"label", "value"}
        and _is_nonempty_string(item.get("label"))
        and isinstance(item.get("value"), (int, float))
        for item in chart_series
    ):
        raise ArtifactPacketError("chart_series_invalid")
    _validate_trend_series(payload.get("trend_series"), cutoff)
    _validate_policy_watch(payload.get("policy_watch"), cutoff)
    if payload.get("event_watch") is not None or payload.get("asset_preferences") is not None or payload.get("liquidity_background") is not None:
        raise ArtifactPacketError("mars_direct_unsupported_payload")


def _validate_preflight_binding_metadata(value: Any) -> None:
    """Validate the optional Macro Preflight marker without owning its policy."""

    if value is None:
        return
    required = {
        "field_contract_version",
        "market_reference_date",
        "validated_field_ids",
        "chart_field_ids",
        "trend_field_ids",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ArtifactPacketError("preflight_binding_invalid")
    if not _is_nonempty_string(value.get("field_contract_version")):
        raise ArtifactPacketError("preflight_binding_invalid")
    try:
        datetime.fromisoformat(str(value["market_reference_date"]))
    except ValueError as error:
        raise ArtifactPacketError("preflight_binding_invalid") from error
    field_ids = value.get("validated_field_ids")
    if (
        not isinstance(field_ids, list)
        or not field_ids
        or not all(_is_nonempty_string(field_id) for field_id in field_ids)
        or len(field_ids) != len(set(field_ids))
    ):
        raise ArtifactPacketError("preflight_binding_invalid")
    for key in ("chart_field_ids", "trend_field_ids"):
        labels = value.get(key)
        if (
            not isinstance(labels, Mapping)
            or not labels
            or not all(
                _is_nonempty_string(label)
                and _is_nonempty_string(field_id)
                and (field_id in field_ids or field_id in MACRO_DERIVED_BINDING_IDS)
                for label, field_id in labels.items()
            )
        ):
            raise ArtifactPacketError("preflight_binding_invalid")


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


def _validate_trend_series(value: Any, cutoff: datetime) -> None:
    if value is None:
        return
    if not isinstance(value, list) or not value:
        raise ArtifactPacketError("trend_series_invalid")
    labels: set[str] = set()
    for series in value:
        if not isinstance(series, Mapping) or set(series) != {"label", "unit", "points", "implication"}:
            raise ArtifactPacketError("trend_series_invalid")
        label = series.get("label")
        if (
            not _is_nonempty_string(label)
            or label in labels
            or not _is_nonempty_string(series.get("unit"))
            or not _is_nonempty_string(series.get("implication"))
        ):
            raise ArtifactPacketError("trend_series_invalid")
        points = series.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise ArtifactPacketError("trend_series_invalid")
        previous: datetime | None = None
        for point in points:
            if (
                not isinstance(point, Mapping)
                or set(point) != {"time", "value"}
                or not isinstance(point.get("value"), (int, float))
            ):
                raise ArtifactPacketError("trend_series_invalid")
            observed = _parse_timestamp(point.get("time"), "trend_series_invalid")
            if observed > cutoff or (previous is not None and observed <= previous):
                raise ArtifactPacketError("trend_series_invalid")
            previous = observed
        labels.add(label)


def _validate_event_watch(value: Any, cutoff: datetime) -> None:
    if value is None:
        return
    if not isinstance(value, list) or not value:
        raise ArtifactPacketError("event_watch_invalid")
    previous: datetime | None = None
    required = {"time", "event", "why_it_matters", "watch", "if_hot", "if_cool"}
    allowed = required | {"importance"}
    for item in value:
        if not isinstance(item, Mapping) or not required.issubset(item) or set(item) - allowed or not all(
            _is_nonempty_string(item.get(key)) for key in required
        ):
            raise ArtifactPacketError("event_watch_invalid")
        if item.get("importance", "normal") not in {"normal", "high"}:
            raise ArtifactPacketError("event_watch_invalid")
        scheduled = _parse_timestamp(item["time"], "event_watch_invalid")
        if scheduled <= cutoff or (previous is not None and scheduled <= previous):
            raise ArtifactPacketError("event_watch_invalid")
        previous = scheduled


def _validate_policy_watch(value: Any, cutoff: datetime) -> None:
    """Allow only bounded, already-normalized official policy records."""

    if value is None:
        return
    if not isinstance(value, list):
        raise ArtifactPacketError("policy_watch_invalid")
    previous: datetime | None = None
    required = {"id", "title", "published_at", "source"}
    for item in value:
        if (
            not isinstance(item, Mapping)
            or set(item) != required
            or not all(_is_nonempty_string(item.get(key)) for key in required)
        ):
            raise ArtifactPacketError("policy_watch_invalid")
        published = _parse_timestamp(item["published_at"], "policy_watch_invalid")
        if published > cutoff or (previous is not None and published < previous):
            raise ArtifactPacketError("policy_watch_invalid")
        previous = published


def _validate_asset_preferences(value: Any, background: Any) -> None:
    if value is None and background is None:
        return
    if not _is_nonempty_string(background) or not isinstance(value, list) or not value:
        raise ArtifactPacketError("asset_preferences_invalid")
    allowed = {"segment", "bias", "impact", "watch"}
    segments: set[str] = set()
    for item in value:
        if (
            not isinstance(item, Mapping)
            or set(item) != allowed
            or not all(_is_nonempty_string(item.get(key)) for key in allowed)
            or item["bias"] not in {"overweight", "neutral", "underweight"}
            or item["segment"] in segments
        ):
            raise ArtifactPacketError("asset_preferences_invalid")
        segments.add(item["segment"])


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



def render_board(
    snapshot: Mapping[str, Any],
    default_view: str,
    presentation_state: str,
) -> bytes:
    return render_macro_regime_board(
        snapshot,
        default_view,
        presentation_state,
        echarts_source=ECHARTS_ASSET.read_text(encoding="utf-8").replace(
            "</script", "<\\/script"
        ),
    )
