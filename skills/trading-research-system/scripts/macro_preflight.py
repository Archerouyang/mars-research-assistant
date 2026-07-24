#!/usr/bin/env python3
"""Fail-closed Macro Preflight at the Blocker-or-Board delivery seam."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field as dataclass_field
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from artifact_packet_core import ArtifactPacketError
from mars_macro_builder import build_mars_macro_research_result
from mars_web_capture import MarsWebCapture, MarsWebCaptureError, normalize_captured_mars_observations
from research_result import DeliveryPacket, ResearchResultError, build_delivery_packet


ALLOWED_STATUSES = frozenset(
    {
        "available",
        "stale",
        "missing",
        "unsupported",
        "source_error",
        "conflicted",
    }
)
FIELD_RECORD_KEYS = frozenset(
    {
        "field_id",
        "value",
        "unit",
        "status",
        "data_as_of",
        "market_reference_date",
        "reference_period",
        "source_id",
        "retrieval_method",
        "raw_field_path",
        "change_1d",
        "change_5d",
        "change_20d",
        "lineage",
        "diagnostic_ref",
        "source_symbol",
        "history",
        "source_url",
    "source_columns",
    "source_timing",
    }
)
COMPLETED_MARKET_MAX_AGE = timedelta(days=7)
OFFICIAL_RELEASE_MAX_AGE = timedelta(days=45)
EVENT_MAX_AGE = timedelta(days=1)
POLICY_MAX_AGE = timedelta(hours=24)

# Mars 1.0 deliberately keeps its macro core small. These terms name deferred
# fields or prohibited proxies, so none may appear anywhere in a delivered
# ResearchResult until an exact, stable source contract is admitted.
DEFERRED_SURFACE_TERMS = frozenset(
    {
        "dxy",
        "hyg",
        "lqd",
        "spx",
        "cpi",
        "ppi",
        "美元指数",
        "uup",
        "brent",
        "布伦特",
        "xau",
        "xau/usd",
        "xauusd",
        "黄金价格",
        "现货黄金",
        "gld",
        "iau",
        "uso",
        "bno",
        "油价etf",
        "oil etf",
        "forward 12m p/e",
        "forward twelve-month p/e",
        "forward p/e",
        "forward pe",
        "spx forward",
        "标普500市盈率",
        "标普 500 市盈率",
        "远期市盈率",
        "vxn",
    }
)
NUMERIC_UNITS = frozenset(
    {
        "percent",
        "usd",
        "usd_billions",
        "volatility_index_points",
        "index_points",
        "ratio",
        "z_score",
    }
)
SET_VALUE_SCHEMAS = {
    "event_set": frozenset({"id", "title", "time", "source_url"}),
    "policy_evidence_set": frozenset(
        {"id", "title", "published_at", "source_url"}
    ),
}


@dataclass(frozen=True)
class FieldBlocker:
    field_id: str
    decision_purpose: str
    attempted_routes: tuple[str, ...]
    status: str
    reason: str
    proxy_context: str = ""


@dataclass(frozen=True)
class MacroRunOutcome:
    kind: str
    message: str
    blockers: tuple[FieldBlocker, ...] = ()
    delivery_packet: DeliveryPacket | None = None
    resolved_values: Mapping[str, Any] = dataclass_field(default_factory=dict)


def load_field_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or (
        Path(__file__).resolve().parents[1]
        / "references"
        / "macro-field-registry-v1.json"
    )
    value = json.loads(registry_path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("contract_version") != "macro-v1"
        or not isinstance(value.get("fields"), list)
    ):
        raise ValueError("macro_field_registry_invalid")
    return value


def run_macro_board(
    web_capture: MarsWebCapture,
    as_of: str,
    *,
    registry: Mapping[str, Any] | None = None,
) -> MacroRunOutcome:
    """Return a direct-web blocker or canonical Board without broker state."""

    try:
        observations = normalize_captured_mars_observations(web_capture, as_of)
    except MarsWebCaptureError as error:
        return _observation_adapter_blocker(str(error), registry)
    return _run_normalized_macro_board(
        observations,
        as_of,
        registry=registry,
    )


def _run_normalized_macro_board(
    observations: Iterable[Mapping[str, Any]],
    as_of: str,
    *,
    registry: Mapping[str, Any] | None = None,
) -> MacroRunOutcome:
    """Private seam: validate adapter-normalized fields then create the only Board."""

    try:
        field_registry = copy.deepcopy(dict(registry or load_field_registry()))
        fields = _registry_fields(field_registry)
        source_maps = _load_closed_source_maps()
        cutoff = _parse_timestamp(as_of, "decision_cutoff")
        ordered_field_ids = sorted(
            fields,
            key=lambda item: (_derivation_depth(item, fields), item),
        )
    except (OSError, ValueError, TypeError) as error:
        blocker = FieldBlocker(
            field_id="preflight.contract",
            decision_purpose="验证 Macro Board 的字段合同、来源合同和决策截止时间。",
            attempted_routes=("macro_field_registry", "issue_75_source_contract"),
            status="source_error",
            reason=f"preflight_contract_invalid:{error}",
        )
        return MacroRunOutcome(
            kind="blocker",
            message=_render_blocker((blocker,)),
            blockers=(blocker,),
        )
    rows_by_id, duplicate_ids = _index_observations(observations)
    blockers: list[FieldBlocker] = []
    available_ids: set[str] = set()

    for field_id in ordered_field_ids:
        field = fields[field_id]
        if field.get("derivation_inputs"):
            if field_id in rows_by_id:
                blockers.append(
                    _blocker(
                        field,
                        "source_error",
                        "derived_field_must_not_be_supplied",
                    )
                )
            continue
        if field_id in duplicate_ids:
            blockers.append(_blocker(field, "conflicted", "duplicate_observation"))
            continue
        row = rows_by_id.get(field_id)
        if row is None:
            blockers.append(_blocker(field, "missing", "required_field_missing"))
            continue
        reason = _validate_observation(
            row,
            field,
            cutoff,
            source_maps,
        )
        if reason is not None:
            status, code, proxy = reason
            blockers.append(_blocker(field, status, code, proxy))
            continue
        available_ids.add(field_id)

    if not blockers:
        blockers.extend(
            _common_market_date_blockers(fields, rows_by_id, available_ids)
        )

    resolved_values: dict[str, Any] = {}
    if not blockers:
        resolved_values, derivation_blockers = _derive_values(fields, rows_by_id)
        blockers.extend(derivation_blockers)

    if not blockers:
        research_result = build_mars_macro_research_result(
            rows_by_id,
            resolved_values,
            as_of=as_of,
            field_ids=sorted(fields),
        )
        binding_error = _validate_board_binding(
            research_result,
            fields,
            rows_by_id,
            available_ids,
            resolved_values,
        )
        if binding_error is not None:
            blockers.append(
                FieldBlocker(
                    field_id="delivery.research_result",
                    decision_purpose="将 standalone Macro Board 绑定到本次已验证字段。",
                    attempted_routes=("research_result_preflight_binding",),
                    status="source_error",
                    reason=binding_error,
                )
            )

    if blockers:
        ordered = tuple(sorted(blockers, key=lambda item: item.field_id))
        return MacroRunOutcome(
            kind="blocker",
            message=_render_blocker(ordered),
            blockers=ordered,
        )

    try:
        packet = build_delivery_packet(research_result)
    except (ArtifactPacketError, ResearchResultError) as error:
        blocker = FieldBlocker(
            field_id="delivery.research_result",
            decision_purpose="生成通过现有合同验证的 standalone Macro Board。",
            attempted_routes=("existing_research_result_to_standalone_board",),
            status="source_error",
            reason=str(error),
        )
        return MacroRunOutcome(
            kind="blocker",
            message=_render_blocker((blocker,)),
            blockers=(blocker,),
        )
    if packet.standalone_board is None:
        blocker = FieldBlocker(
            field_id="delivery.standalone_board",
            decision_purpose="交付唯一受支持的 Macro 可视化。",
            attempted_routes=("existing_standalone_board",),
            status="source_error",
            reason="standalone_board_missing",
        )
        return MacroRunOutcome(
            kind="blocker",
            message=_render_blocker((blocker,)),
            blockers=(blocker,),
        )
    return MacroRunOutcome(
        kind="board",
        message="Macro Preflight 已通过；使用最近共同完成收盘数据生成 standalone Board。",
        delivery_packet=packet,
        resolved_values=resolved_values,
    )


def _observation_adapter_blocker(
    error: str,
    registry: Mapping[str, Any] | None,
) -> MacroRunOutcome:
    """Expose source-normalization failures as the public blocker, never a Board."""

    try:
        fields = _registry_fields(copy.deepcopy(dict(registry or load_field_registry())))
    except (OSError, ValueError, TypeError):
        fields = {}
    field_id = error.split(":", 1)[0]
    field = fields.get(field_id)
    if field is None:
        blocker = FieldBlocker(
            field_id="preflight.acquisition",
            decision_purpose="验证直接来源、共同完成收盘和最新官方观测。",
            attempted_routes=("mars_direct_observation_adapter",),
            status="source_error",
            reason=error,
        )
    else:
        blocker = _blocker(field, "source_error", error)
    return MacroRunOutcome(
        kind="blocker",
        message=_render_blocker((blocker,)),
        blockers=(blocker,),
    )


def _registry_fields(registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = registry.get("fields")
    freshness = registry.get("freshness_policies")
    if not isinstance(rows, list) or not isinstance(freshness, Mapping):
        raise ValueError("macro_field_registry_invalid")
    fields: dict[str, dict[str, Any]] = {}
    required = {"field_id", "decision_purpose", "unit", "timing", "source_routes"}
    for item in rows:
        if not isinstance(item, Mapping) or not required.issubset(item):
            raise ValueError("macro_field_registry_invalid")
        field = copy.deepcopy(dict(item))
        field_id = field["field_id"]
        if not isinstance(field_id, str) or not field_id or field_id in fields:
            raise ValueError("macro_field_registry_invalid")
        if not isinstance(field["source_routes"], list) or not field["source_routes"]:
            raise ValueError("macro_field_registry_invalid")
        if any(
            isinstance(route, Mapping)
            and isinstance(route.get("source_id"), str)
            and route["source_id"].startswith("qualified_")
            for route in field["source_routes"]
        ):
            raise ValueError("generic_source_route_forbidden")
        if field["timing"] not in freshness or not isinstance(
            freshness[field["timing"]], str
        ):
            raise ValueError("macro_field_registry_invalid")
        fields[field_id] = field
    return fields


def _load_closed_source_maps(path: Path | None = None) -> dict[str, dict[str, Any]]:
    contract_path = path or (
        Path(__file__).resolve().parents[1]
        / "references"
        / "mars-1-0-observation-source-contracts.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if (
        not isinstance(contract, Mapping)
        or contract.get("contract_version") != "mars-observation-adapter-v1"
    ):
        raise ValueError("source_contract_not_complete")
    rows = contract.get("fields")
    if not isinstance(rows, list):
        raise ValueError("source_contract_maps_invalid")
    maps: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("source_contract_map_invalid")
        field_id = item.get("field_id")
        path_value = item.get("raw_field_path")
        if (
            not isinstance(field_id, str)
            or not isinstance(item.get("source_id"), str)
            or not isinstance(item.get("source_url"), str)
            or item.get("source_timing") not in {
                "completed_market",
                "official_release",
                "policy",
            }
            or not _is_path(path_value)
        ):
            raise ValueError("source_contract_map_invalid")
        maps[field_id] = copy.deepcopy(dict(item))
    return maps


def _decision_cutoff(research_result: Mapping[str, Any]) -> datetime:
    if not isinstance(research_result, Mapping):
        raise ValueError("research_result_invalid")
    value = research_result.get("as_of")
    if not isinstance(value, str):
        raise ValueError("decision_cutoff_missing")
    return _parse_timestamp(value, "decision_cutoff")


def _derivation_depth(
    field_id: str,
    fields: Mapping[str, Mapping[str, Any]],
    trail: frozenset[str] = frozenset(),
) -> int:
    if field_id in trail:
        raise ValueError("macro_field_registry_cycle")
    inputs = tuple(fields[field_id].get("derivation_inputs") or ())
    if not inputs:
        return 0
    if any(item not in fields for item in inputs):
        raise ValueError("macro_field_registry_input_invalid")
    return 1 + max(
        _derivation_depth(item, fields, trail | {field_id}) for item in inputs
    )


def _index_observations(
    observations: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    rows: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for item in observations:
        if not isinstance(item, Mapping):
            continue
        row = copy.deepcopy(dict(item))
        field_id = row.get("field_id")
        if not isinstance(field_id, str):
            continue
        if field_id in rows:
            duplicates.add(field_id)
        else:
            rows[field_id] = row
    return rows, duplicates


def _common_market_date_blockers(
    fields: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, Mapping[str, Any]],
    available_ids: set[str],
) -> tuple[FieldBlocker, ...]:
    """Reject a Board when completed-market fields mix different close dates."""

    market_fields = [
        field_id
        for field_id in sorted(available_ids)
        if fields[field_id]["timing"] == "completed_market"
    ]
    dates = {str(rows_by_id[field_id]["market_reference_date"]) for field_id in market_fields}
    if len(dates) <= 1:
        return ()
    return tuple(
        _blocker(
            fields[field_id],
            "conflicted",
            "market_reference_date_not_common",
        )
        for field_id in market_fields
    )


def _validate_observation(
    row: Mapping[str, Any],
    field: Mapping[str, Any],
    cutoff: datetime,
    source_maps: Mapping[str, Mapping[str, Any]],
) -> tuple[str, str, str] | None:
    if set(row) - FIELD_RECORD_KEYS:
        return ("source_error", "normalized_field_shape_invalid", "")
    if row.get("field_id") != field["field_id"]:
        return ("source_error", "field_id_mismatch", "")
    status = row.get("status")
    if status not in ALLOWED_STATUSES:
        return ("source_error", "field_status_invalid", "")
    if status != "available":
        return (str(status), str(row.get("diagnostic_ref") or "field_unavailable"), "")
    if "value" not in row or row.get("value") is None:
        return ("missing", "field_value_missing", "")
    value_error = _validate_value_shape(row.get("value"), field)
    if value_error is not None:
        return ("source_error", value_error, "")
    if row.get("unit") != field["unit"]:
        return ("conflicted", "field_unit_mismatch", "")
    if row.get("source_timing") != field["timing"]:
        return ("conflicted", "field_timing_mismatch", "")
    for key in ("data_as_of", "source_id", "retrieval_method"):
        if not isinstance(row.get(key), str) or not str(row[key]).strip():
            return ("source_error", f"{key}_missing", "")
    try:
        data_as_of = _parse_timestamp(str(row["data_as_of"]), "data_as_of")
    except ValueError:
        return ("source_error", "data_as_of_invalid", "")
    if data_as_of > cutoff:
        return ("source_error", "data_as_of_after_decision_cutoff", "")
    path = row.get("raw_field_path")
    if not isinstance(path, list) or not path or any(not isinstance(item, str) or not item for item in path):
        return ("source_error", "raw_field_path_missing", "")
    route_ids = {
        item.get("source_id")
        for item in field["source_routes"]
        if isinstance(item, Mapping)
    }
    source_id = row.get("source_id")
    if source_id not in route_ids:
        return ("unsupported", "source_route_not_allowed", "")
    allowed_methods = {
        item.get("method")
        for item in field["source_routes"]
        if isinstance(item, Mapping)
        and (
            item.get("source_id") == source_id
        )
    }
    if row.get("retrieval_method") not in allowed_methods:
        return ("unsupported", "retrieval_method_not_allowed", "")
    source_map = source_maps.get(str(field["field_id"]))
    if source_map is not None and not _matches_source_map(row, source_map):
        return ("source_error", "source_contract_provenance_invalid", "")
    timing_key = (
        "market_reference_date"
        if field["timing"] == "completed_market"
        else "reference_period"
    )
    if not isinstance(row.get(timing_key), str) or not str(row[timing_key]).strip():
        return ("source_error", f"{timing_key}_missing", "")
    freshness_error = _validate_freshness(row, field, cutoff, data_as_of)
    if freshness_error is not None:
        return freshness_error
    symbol = row.get("source_symbol")
    forbidden = set(field.get("forbidden_substitutes") or ())
    if isinstance(symbol, str) and symbol.upper() in forbidden:
        return ("unsupported", "proxy_not_allowed", symbol.upper())
    if field.get("history_required"):
        history_error = _validate_history(row)
        if history_error is not None:
            return history_error
    return None


def _validate_value_shape(value: object, field: Mapping[str, Any]) -> str | None:
    """Accept only bounded normalized values, never provider payload objects."""

    unit = field.get("unit")
    if unit in NUMERIC_UNITS:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "field_value_shape_invalid"
        if not math.isfinite(float(value)):
            return "field_value_not_finite"
        return None
    allowed_item_keys = SET_VALUE_SCHEMAS.get(unit)
    if allowed_item_keys is None or not isinstance(value, list):
        return "field_value_shape_invalid"
    for item in value:
        if not isinstance(item, Mapping) or set(item) != allowed_item_keys:
            return "field_value_shape_invalid"
        if not all(isinstance(item[key], str) and item[key].strip() for key in allowed_item_keys):
            return "field_value_shape_invalid"
        time_key = "time" if unit == "event_set" else "published_at"
        try:
            _parse_timestamp(item[time_key], f"{unit}_{time_key}")
        except ValueError:
            return "field_value_shape_invalid"
        if not item["source_url"].startswith("https://"):
            return "field_value_shape_invalid"
    return None


def _matches_source_map(
    row: Mapping[str, Any], source_map: Mapping[str, Any]
) -> bool:
    return (
        row.get("source_id") == source_map.get("source_id")
        and row.get("retrieval_method") == "direct_web_capture"
        and row.get("raw_field_path") == source_map.get("raw_field_path")
        and row.get("source_url") == source_map.get("source_url")
    )


def _validate_freshness(
    row: Mapping[str, Any],
    field: Mapping[str, Any],
    cutoff: datetime,
    data_as_of: datetime,
) -> tuple[str, str, str] | None:
    timing = field["timing"]
    age = cutoff - data_as_of
    if timing == "completed_market":
        try:
            market_date = _parse_date(str(row["market_reference_date"]))
        except ValueError:
            return ("source_error", "market_reference_date_invalid", "")
        # The adapter already proves the session is complete. A close later on
        # the same UTC date is valid once that source fact is present.
        if market_date > cutoff.date():
            return ("unsupported", "completed_close_not_proven", "")
        if cutoff.date() - market_date > COMPLETED_MARKET_MAX_AGE:
            return ("stale", "market_reference_date_stale", "")
        return None
    if timing == "official_release" and age > OFFICIAL_RELEASE_MAX_AGE:
        return ("stale", "official_release_stale", "")
    if timing == "event" and age > EVENT_MAX_AGE:
        return ("stale", "event_metadata_stale", "")
    if timing == "policy" and age > POLICY_MAX_AGE:
        return ("stale", "policy_evidence_stale", "")
    return None


def _validate_history(
    row: Mapping[str, Any],
) -> tuple[str, str, str] | None:
    history = row.get("history")
    if not isinstance(history, list) or len(history) < 21:
        return ("source_error", "history_window_insufficient", "")
    parsed: list[tuple[date, float]] = []
    for item in history:
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("date"), str)
            or not isinstance(item.get("value"), (int, float))
        ):
            return ("source_error", "history_shape_invalid", "")
        try:
            history_date = _parse_date(item["date"])
        except ValueError:
            return ("source_error", "history_date_invalid", "")
        parsed.append((history_date, float(item["value"])))
    if any(left[0] >= right[0] for left, right in zip(parsed, parsed[1:])):
        return ("source_error", "history_dates_not_strictly_increasing", "")
    if parsed[-1][0].isoformat() != row.get("market_reference_date"):
        return ("source_error", "history_latest_date_mismatch", "")
    if not math.isclose(parsed[-1][1], float(row["value"]), rel_tol=0.0, abs_tol=1e-9):
        return ("source_error", "history_latest_value_mismatch", "")
    return None


def _derive_values(
    fields: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], tuple[FieldBlocker, ...]]:
    values = {
        field_id: float(row["value"])
        for field_id, row in rows_by_id.items()
        if (
            field_id in fields
            and not fields[field_id].get("derivation_inputs")
            and fields[field_id].get("unit") in NUMERIC_UNITS
        )
    }
    histories: dict[str, list[tuple[date, float]]] = {}
    for field_id in ("equity.ndx_close", "equity.rut_close"):
        row = rows_by_id[field_id]
        histories[field_id] = [
            (_parse_date(str(item["date"])), float(item["value"]))
            for item in row["history"]
        ]
    blockers: list[FieldBlocker] = []
    ratio_history: list[tuple[date, float]] = []
    for field_id in sorted(fields, key=lambda item: (_derivation_depth(item, fields), item)):
        field = fields[field_id]
        inputs = tuple(field.get("derivation_inputs") or ())
        if not inputs:
            continue
        if not set(inputs).issubset(values):
            blockers.append(_blocker(field, "source_error", "derived_input_unavailable"))
            continue
        if field.get("formula") not in {
            "volatility.vix_close / volatility.vix3m_close",
            "equity.ndx_close / equity.rut_close",
            "(ratio - mean_20d) / stddev_20d",
        }:
            blockers.append(_blocker(field, "source_error", "derived_formula_unsupported"))
            continue
        if field_id == "equity.ndx_rut_normalized_20d":
            if len(ratio_history) < 20:
                blockers.append(_blocker(field, "source_error", "derived_history_insufficient"))
                continue
            window = [item[1] for item in ratio_history[-20:]]
            mean = sum(window) / len(window)
            variance = sum((item - mean) ** 2 for item in window) / len(window)
            if variance <= 0:
                blockers.append(_blocker(field, "source_error", "derived_history_zero_variance"))
                continue
            values[field_id] = (window[-1] - mean) / math.sqrt(variance)
            continue
        if not all(isinstance(values[input_id], (int, float)) for input_id in inputs):
            blockers.append(_blocker(field, "source_error", "derived_input_not_numeric"))
            continue
        denominator = float(values[inputs[1]])
        if denominator == 0:
            blockers.append(_blocker(field, "source_error", "derived_denominator_zero"))
            continue
        values[field_id] = float(values[inputs[0]]) / denominator
        if field_id == "equity.ndx_rut_ratio":
            ndx_history = histories["equity.ndx_close"]
            rut_history = histories["equity.rut_close"]
            if [item[0] for item in ndx_history] != [item[0] for item in rut_history]:
                blockers.append(_blocker(field, "conflicted", "derived_history_dates_not_aligned"))
                continue
            if any(rut_value == 0 for _, rut_value in rut_history):
                blockers.append(_blocker(field, "source_error", "derived_history_denominator_zero"))
                continue
            ratio_history = [
                (ndx_date, ndx_value / rut_value)
                for (ndx_date, ndx_value), (_, rut_value) in zip(ndx_history, rut_history)
            ]
            for window in field.get("change_windows") or ():
                if not isinstance(window, int) or window <= 0:
                    blockers.append(
                        _blocker(field, "source_error", "derived_change_window_invalid")
                    )
                    continue
                if len(ratio_history) <= window:
                    blockers.append(
                        _blocker(field, "source_error", "derived_history_insufficient")
                    )
                    continue
                baseline = ratio_history[-(window + 1)][1]
                if baseline == 0:
                    blockers.append(
                        _blocker(field, "source_error", "derived_history_denominator_zero")
                    )
                    continue
                values[f"{field_id}.change_{window}d"] = (
                    (ratio_history[-1][1] / baseline - 1.0) * 100.0
                )
    return values, tuple(blockers)


def _validate_board_binding(
    research_result: Mapping[str, Any],
    fields: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, Mapping[str, Any]],
    available_ids: set[str],
    resolved_values: Mapping[str, Any],
) -> str | None:
    visual = research_result.get("visual") if isinstance(research_result, Mapping) else None
    snapshot = visual.get("snapshot") if isinstance(visual, Mapping) else None
    payload = snapshot.get("payload") if isinstance(snapshot, Mapping) else None
    binding = payload.get("preflight") if isinstance(payload, Mapping) else None
    if not isinstance(binding, Mapping):
        return "research_result_preflight_binding_missing"
    required = {
        "field_contract_version",
        "market_reference_date",
        "validated_field_ids",
        "chart_field_ids",
        "trend_field_ids",
    }
    if set(binding) != required or binding.get("field_contract_version") != "macro-v1":
        return "research_result_preflight_binding_invalid"
    result_text = json.dumps(research_result, ensure_ascii=False).casefold()
    if any(term in result_text for term in DEFERRED_SURFACE_TERMS):
        return "research_result_deferred_field_present"
    expected_ids = set(fields)
    bound_ids = binding.get("validated_field_ids")
    if (
        not isinstance(bound_ids, list)
        or len(bound_ids) != len(set(bound_ids))
        or set(bound_ids) != expected_ids
    ):
        return "research_result_preflight_field_set_mismatch"
    market_dates = {
        str(rows_by_id[field_id]["market_reference_date"])
        for field_id in available_ids
        if fields[field_id]["timing"] == "completed_market"
    }
    if len(market_dates) != 1 or binding.get("market_reference_date") != next(iter(market_dates)):
        return "research_result_preflight_market_date_mismatch"
    for key, series_key in (("chart_field_ids", "chart_series"), ("trend_field_ids", "trend_series")):
        labels = binding.get(key)
        series = payload.get(series_key) if isinstance(payload, Mapping) else None
        if not isinstance(labels, Mapping) or not isinstance(series, list):
            return "research_result_preflight_series_binding_invalid"
        by_label = {
            item.get("label"): item
            for item in series
            if isinstance(item, Mapping) and isinstance(item.get("label"), str)
        }
        if set(labels) != set(by_label):
            return "research_result_preflight_series_label_mismatch"
        for label, field_id in labels.items():
            value = resolved_values.get(field_id)
            if not isinstance(field_id, str) or not isinstance(value, (int, float)):
                return "research_result_preflight_series_field_invalid"
            item = by_label[label]
            actual = item.get("value") if series_key == "chart_series" else (
                item.get("points")[-1].get("value")
                if isinstance(item.get("points"), list) and item["points"]
                and isinstance(item["points"][-1], Mapping)
                else None
            )
            if not isinstance(actual, (int, float)) or not math.isclose(
                float(actual), float(value), rel_tol=0.0, abs_tol=1e-9
            ):
                return "research_result_preflight_series_value_mismatch"
    policy = rows_by_id.get("policy.us_executive_actions")
    expected_policy_watch = (
        [
            {
                "id": str(record["id"]),
                "title": str(record["title"]),
                "published_at": str(record["published_at"]),
                "source": "White House Presidential Actions",
            }
            for record in policy.get("value", [])
        ]
        if isinstance(policy, Mapping)
        else None
    )
    if payload.get("policy_watch") != expected_policy_watch:
        return "research_result_preflight_policy_binding_mismatch"
    return None


def _parse_timestamp(value: str, context: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{context}_invalid") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{context}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("date_invalid") from error


def _is_path(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
    )


def _blocker(
    field: Mapping[str, Any],
    status: str,
    reason: str,
    proxy: str = "",
) -> FieldBlocker:
    routes = tuple(
        f"{item['source_id']}:{item['method']}"
        for item in field["source_routes"]
        if isinstance(item, Mapping) and item.get("source_id") and item.get("method")
    )
    return FieldBlocker(
        field_id=str(field["field_id"]),
        decision_purpose=str(field["decision_purpose"]),
        attempted_routes=routes,
        status=status,
        reason=reason,
        proxy_context=proxy,
    )


def _render_blocker(blockers: tuple[FieldBlocker, ...]) -> str:
    lines = [
        "## Data Acquisition Blocker",
        "",
        "Macro Board 未生成。以下必填字段尚未满足：",
    ]
    for item in blockers:
        routes = "；".join(item.attempted_routes)
        proxy = f"；非等价代理仅作背景：{item.proxy_context}" if item.proxy_context else ""
        lines.append(
            f"- `{item.field_id}`：{item.decision_purpose}"
            f" 状态 `{item.status}`，原因 `{item.reason}`；已尝试 {routes}{proxy}"
        )
    lines.extend(
        [
            "",
            "请继续获取精确字段；保留核心字段在可用前不会生成 Macro Board。",
        ]
    )
    return "\n".join(lines)
