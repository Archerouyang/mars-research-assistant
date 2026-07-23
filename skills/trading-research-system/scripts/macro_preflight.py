#!/usr/bin/env python3
"""Fail-closed Macro Preflight at the Blocker-or-Board delivery seam."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from research_result import DeliveryPacket, ResearchResultError, build_delivery_packet


ALLOWED_BROKERS = frozenset({"longbridge", "ibkr"})
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
    }
)


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
    attempted_brokers: tuple[str, ...] = ()


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
    config: Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    research_result: Mapping[str, Any],
    *,
    registry: Mapping[str, Any] | None = None,
) -> MacroRunOutcome:
    """Return exactly one setup prompt, blocker, or existing Board packet."""

    broker = _configured_broker(config)
    if broker is None:
        return MacroRunOutcome(
            kind="setup_required",
            message=(
                "需要先选择一个默认只读券商（Longbridge 或 IBKR）；"
                "本次未读取持仓，也未生成 Macro Board。"
            ),
        )

    field_registry = copy.deepcopy(dict(registry or load_field_registry()))
    fields = _registry_fields(field_registry)
    rows_by_id, duplicate_ids = _index_observations(observations)
    blockers: list[FieldBlocker] = []
    available_ids: set[str] = set()

    ordered_field_ids = sorted(
        fields,
        key=lambda item: (_derivation_depth(item, fields), item),
    )
    for field_id in ordered_field_ids:
        field = fields[field_id]
        if field_id in duplicate_ids:
            blockers.append(_blocker(field, "conflicted", "duplicate_observation"))
            continue
        row = rows_by_id.get(field_id)
        if row is None:
            blockers.append(_blocker(field, "missing", "required_field_missing"))
            continue
        reason = _validate_observation(row, field, available_ids, broker)
        if reason is not None:
            status, code, proxy = reason
            blockers.append(_blocker(field, status, code, proxy))
            continue
        available_ids.add(field_id)

    if not blockers:
        blockers.extend(
            _common_market_date_blockers(fields, rows_by_id, available_ids)
        )

    if blockers:
        ordered = tuple(sorted(blockers, key=lambda item: item.field_id))
        return MacroRunOutcome(
            kind="blocker",
            message=_render_blocker(ordered),
            blockers=ordered,
            attempted_brokers=(broker,),
        )

    try:
        packet = build_delivery_packet(research_result)
    except ResearchResultError as error:
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
            attempted_brokers=(broker,),
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
            attempted_brokers=(broker,),
        )
    return MacroRunOutcome(
        kind="board",
        message="Macro Preflight 已通过；使用最近共同完成收盘数据生成 standalone Board。",
        delivery_packet=packet,
        attempted_brokers=(broker,),
    )


def _configured_broker(config: Mapping[str, Any]) -> str | None:
    if not isinstance(config, Mapping):
        return None
    broker = config.get("default_broker")
    if not isinstance(broker, str) or broker not in ALLOWED_BROKERS:
        return None
    if config.get("broker_read_only_enabled") is not True:
        return None
    return str(broker)


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
        if field["timing"] not in freshness or not isinstance(
            freshness[field["timing"]], str
        ):
            raise ValueError("macro_field_registry_invalid")
        fields[field_id] = field
    return fields


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
    dates = {
        str(rows_by_id[field_id]["market_reference_date"])
        for field_id in market_fields
    }
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
    available_ids: set[str],
    configured_broker: str,
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
    if row.get("unit") != field["unit"]:
        return ("conflicted", "field_unit_mismatch", "")
    for key in ("data_as_of", "source_id", "retrieval_method"):
        if not isinstance(row.get(key), str) or not str(row[key]).strip():
            return ("source_error", f"{key}_missing", "")
    try:
        datetime.fromisoformat(str(row["data_as_of"]).replace("Z", "+00:00"))
    except ValueError:
        return ("source_error", "data_as_of_invalid", "")
    path = row.get("raw_field_path")
    if not isinstance(path, list) or not path or any(not isinstance(item, str) or not item for item in path):
        return ("source_error", "raw_field_path_missing", "")
    route_ids = {
        item.get("source_id")
        for item in field["source_routes"]
        if isinstance(item, Mapping)
    }
    source_id = row.get("source_id")
    source_allowed = source_id in route_ids
    if "configured_broker" in route_ids and source_id == configured_broker:
        source_allowed = True
    if source_id in ALLOWED_BROKERS and source_id != configured_broker:
        source_allowed = False
    if not source_allowed:
        return ("unsupported", "source_route_not_allowed", "")
    timing_key = (
        "market_reference_date"
        if field["timing"] == "completed_market"
        else "reference_period"
    )
    if not isinstance(row.get(timing_key), str) or not str(row[timing_key]).strip():
        return ("source_error", f"{timing_key}_missing", "")
    symbol = row.get("source_symbol")
    forbidden = set(field.get("forbidden_substitutes") or ())
    if isinstance(symbol, str) and symbol.upper() in forbidden:
        return ("unsupported", "proxy_not_allowed", symbol.upper())
    if field.get("change_windows"):
        for window in field["change_windows"]:
            if not isinstance(row.get(f"change_{window}d"), (int, float)):
                return ("source_error", f"change_{window}d_missing", "")
    inputs = tuple(field.get("derivation_inputs") or ())
    if inputs:
        lineage = row.get("lineage")
        if (
            not isinstance(lineage, Mapping)
            or tuple(lineage.get("inputs") or ()) != inputs
            or lineage.get("formula") != field.get("formula")
        ):
            return ("source_error", "derived_lineage_invalid", "")
        if not set(inputs).issubset(available_ids):
            return ("source_error", "derived_input_unavailable", "")
    return None


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
