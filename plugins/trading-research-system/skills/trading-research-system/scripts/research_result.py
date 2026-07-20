#!/usr/bin/env python3
"""Validate one research result and build deterministic chat delivery bytes."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping

from artifact_packet import build_artifact_packet
from chart_artifact import build_chart_payload
from inline_visual import render_board_fragment, render_price_action_fragment
from portfolio_panel_adapter import validate_portfolio_panel


SCHEMA_VERSION = "1.0"
RESULT_KINDS = frozenset(
    {"operations", "macro", "instrument", "portfolio", "price_action", "report"}
)
EVIDENCE_STATES = frozenset({"complete", "partial", "stale", "source_error"})
EVIDENCE_TYPES = frozenset({"fact", "inference", "thesis", "counter_thesis"})
RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})
MAX_RESULT_BYTES = 500_000
MAX_MARKDOWN_BYTES = 50_000
MAX_INLINE_BYTES = 100_000
BOARD_BY_ADAPTER = {
    "macro": "macro_regime",
    "instrument": "instrument_research",
    "portfolio": "portfolio_risk",
}
PUBLIC_SENTINELS = (
    "/Users/",
    "account_id",
    "account_number",
    "api_key",
    "authorization",
    "bearer ",
    "broker_response",
    "credential",
    "password",
    "private_runtime",
    "secret",
    "token",
)
FORBIDDEN_ORDER_KEYS = frozenset(
    {
        "broker_action",
        "broker_write",
        "cancel_order",
        "modify_order",
        "order_id",
        "order_payload",
        "submit_order",
    }
)
FORBIDDEN_ORDER_PHRASES = (
    "cancel the order",
    "execute the order",
    "modify the order",
    "order approved",
    "place order",
    "place the order",
    "submit the order",
    "立即下单",
    "修改订单",
    "取消订单",
    "提交订单",
    "执行下单",
    "订单已批准",
)
FORBIDDEN_ORDER_PATTERNS = (
    re.compile(
        r"\b(?:buy|sell|short|cover)\s+(?:\d+(?:\.\d+)?\s+)?"
        r"(?:shares?|stocks?|etfs?|contracts?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:create|place|submit|send|execute|cancel|modify)\s+"
        r"(?:(?:an?|the)\s+)?(?:(?:market|limit|stop)\s+)?order\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:立即|马上|现在)?(?:下单|挂单|提交订单|执行交易|取消订单|修改订单)"),
    re.compile(r"(?:立即|马上|现在)?(?:买入|卖出|做空|平仓)\s*\d+(?:\.\d+)?\s*(?:股|份|张)"),
)


class ResearchResultError(ValueError):
    """Fail-closed result validation error with a stable public code."""


@dataclass(frozen=True)
class DeliveryPacket:
    """Canonical result, Markdown, and optional chat-inline HTML bytes."""

    canonical_result: bytes
    markdown: bytes
    inline_html: bytes | None
    diagnostics: tuple[str, ...]


def build_delivery_packet(result: Mapping[str, Any]) -> DeliveryPacket:
    """Validate and render one model-produced research result."""

    normalized = validate_research_result(result)
    canonical = canonical_json_bytes(normalized)
    markdown = render_markdown(normalized).encode("utf-8")
    inline_html = render_inline_html(normalized)
    if len(markdown) > MAX_MARKDOWN_BYTES:
        raise ResearchResultError("markdown_size_invalid")
    if inline_html is not None and len(inline_html) > MAX_INLINE_BYTES:
        raise ResearchResultError("inline_size_invalid")
    diagnostics = tuple(
        f"data_gap:{item['status']}:{item['label']}" for item in normalized["data_gaps"]
    )
    return DeliveryPacket(canonical, markdown, inline_html, diagnostics)


def validate_research_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a normalized result or raise a stable validation code."""

    if not isinstance(result, Mapping):
        raise ResearchResultError("result_invalid")
    allowed = {
        "schema_version",
        "result_kind",
        "as_of",
        "decision",
        "key_evidence",
        "risks",
        "scenarios",
        "next_checks",
        "data_gaps",
        "sources",
        "privacy",
        "locale",
        "visual",
    }
    if set(result) - allowed:
        raise ResearchResultError("result_fields_invalid")

    normalized = copy.deepcopy(dict(result))
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise ResearchResultError("schema_version_invalid")
    kind = _required_text(normalized, "result_kind")
    if kind not in RESULT_KINDS:
        raise ResearchResultError("result_kind_invalid")
    _iso_timestamp(_required_text(normalized, "as_of"), "as_of_invalid")
    _required_text(normalized, "decision")
    privacy = normalized.get("privacy", "private")
    if privacy not in {"private", "public_fixture"}:
        raise ResearchResultError("privacy_invalid")
    normalized["privacy"] = privacy
    normalized["locale"] = str(normalized.get("locale") or "zh-CN")

    normalized["key_evidence"] = _normalize_evidence(normalized.get("key_evidence"))
    normalized["risks"] = _normalize_risks(normalized.get("risks"))
    normalized["scenarios"] = _normalize_scenarios(normalized.get("scenarios"))
    normalized["next_checks"] = _text_list(normalized.get("next_checks"), "next_checks_invalid")
    normalized["data_gaps"] = _normalize_gaps(normalized.get("data_gaps"))
    normalized["sources"] = _normalize_sources(normalized.get("sources"))
    normalized["visual"] = _normalize_visual(normalized.get("visual"), kind)

    source_ids = {source["id"] for source in normalized["sources"]}
    for item in normalized["key_evidence"]:
        if not item["source_refs"]:
            raise ResearchResultError("source_refs_required")
        if any(source_ref not in source_ids for source_ref in item["source_refs"]):
            raise ResearchResultError("source_ref_invalid")
    if any(item["status"] != "complete" for item in normalized["key_evidence"]) and not normalized["data_gaps"]:
        raise ResearchResultError("data_gap_required")

    encoded = canonical_json_bytes(normalized)
    if len(encoded) > MAX_RESULT_BYTES:
        raise ResearchResultError("result_size_invalid")
    if _contains_forbidden_order_key(normalized):
        raise ResearchResultError("order_action_invalid")
    compact_text = encoded.decode("utf-8").lower()
    if _contains_forbidden_order_instruction(compact_text):
        raise ResearchResultError("order_action_invalid")

    if privacy == "public_fixture":
        if any(sentinel.lower() in compact_text for sentinel in PUBLIC_SENTINELS):
            raise ResearchResultError("public_privacy_invalid")
    return normalized


def render_markdown(result: Mapping[str, Any]) -> str:
    """Render stable concise Chinese Markdown from one validated result."""

    lines = ["## 结论", "", str(result["decision"]), "", "## 关键证据", ""]
    evidence = result["key_evidence"]
    if evidence:
        sources = {source["id"]: source for source in result["sources"]}
        for item in evidence:
            detail = f"：{item['detail']}" if item.get("detail") else ""
            provenance = "；".join(
                f"{sources[source_id]['label']} @ {sources[source_id]['as_of']}"
                for source_id in item["source_refs"]
            )
            lines.append(
                f"- **{item['label']}** `{item['evidence_type']}` `{item['status']}`："
                f"{item['value']}{detail} _(证据 {item['as_of']}；{provenance})_"
            )
    else:
        lines.append("- 暂无足以改变结论的新增证据。")

    lines.extend(["", "## 风险与失效", ""])
    if result["risks"]:
        for item in result["risks"]:
            suffix = f"；失效：{item['invalidation']}" if item.get("invalidation") else ""
            lines.append(f"- **{item['label']}** `{item['severity']}`：{item['detail']}{suffix}")
    else:
        lines.append("- 未识别到需要单独升级的风险。")

    lines.extend(["", "## 情景", ""])
    if result["scenarios"]:
        for item in result["scenarios"]:
            lines.append(f"- **{item['name']}**：若 {item['condition']}，则 {item['implication']}")
    else:
        lines.append("- 当前不需要额外情景分支。")

    lines.extend(["", "## 下一检查", ""])
    lines.extend(f"- {item}" for item in result["next_checks"])
    if not result["next_checks"]:
        lines.append("- 无待确认检查。")

    if result["data_gaps"]:
        lines.extend(["", "## 数据缺口", ""])
        lines.extend(
            f"- **{item['label']}** `{item['status']}`：{item['reason']}"
            for item in result["data_gaps"]
        )

    lines.extend(["", f"_as_of: {result['as_of']} · privacy: {result['privacy']}_", ""])
    return "\n".join(lines)


def render_inline_html(result: Mapping[str, Any]) -> bytes | None:
    """Dispatch the optional visual through one purpose-specific adapter."""

    visual = result["visual"]
    if visual is None:
        return None
    adapter = visual["adapter"]
    if adapter == "portfolio":
        panel = copy.deepcopy(visual["panel"])
        panel["privacy"] = result["privacy"]
        validate_portfolio_panel(panel)
        return render_board_fragment(adapter, panel)
    if adapter in BOARD_BY_ADAPTER:
        build_artifact_packet(
            visual["snapshot"],
            default_view=visual["default_view"],
            presentation_state="ready",
        )
        return render_board_fragment(adapter, visual["snapshot"])
    if adapter == "price_action":
        chart_payload = copy.deepcopy(visual["payload"])
        chart_payload["privacy"] = result["privacy"]
        return render_price_action_fragment(chart_payload)
    raise ResearchResultError("visual_adapter_invalid")


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _normalize_evidence(value: Any) -> list[dict[str, Any]]:
    rows = _mapping_list(value, "key_evidence_invalid")
    allowed = {"label", "value", "status", "evidence_type", "as_of", "source_refs", "detail"}
    for row in rows:
        _exact_fields(row, allowed, "key_evidence_fields_invalid")
        _required_text(row, "label")
        _required_text(row, "value")
        if row.get("evidence_type") not in EVIDENCE_TYPES:
            raise ResearchResultError("evidence_type_invalid")
        if row.get("status") not in EVIDENCE_STATES:
            raise ResearchResultError("evidence_status_invalid")
        _iso_timestamp(_required_text(row, "as_of"), "evidence_as_of_invalid")
        row["source_refs"] = _text_list(row.get("source_refs"), "source_refs_invalid")
        if "detail" in row:
            row["detail"] = str(row["detail"])
    return rows


def _normalize_risks(value: Any) -> list[dict[str, Any]]:
    rows = _mapping_list(value, "risks_invalid")
    allowed = {"label", "severity", "detail", "invalidation"}
    for row in rows:
        _exact_fields(row, allowed, "risk_fields_invalid")
        _required_text(row, "label")
        _required_text(row, "detail")
        if row.get("severity") not in RISK_LEVELS:
            raise ResearchResultError("risk_severity_invalid")
        if "invalidation" in row:
            row["invalidation"] = str(row["invalidation"])
    return rows


def _normalize_scenarios(value: Any) -> list[dict[str, Any]]:
    rows = _mapping_list(value, "scenarios_invalid")
    allowed = {"name", "condition", "implication"}
    for row in rows:
        _exact_fields(row, allowed, "scenario_fields_invalid")
        for key in allowed:
            _required_text(row, key)
    return rows


def _normalize_gaps(value: Any) -> list[dict[str, Any]]:
    rows = _mapping_list(value, "data_gaps_invalid")
    allowed = {"label", "reason", "status"}
    for row in rows:
        _exact_fields(row, allowed, "data_gap_fields_invalid")
        _required_text(row, "label")
        _required_text(row, "reason")
        if row.get("status") not in EVIDENCE_STATES - {"complete"}:
            raise ResearchResultError("data_gap_status_invalid")
    return rows


def _normalize_sources(value: Any) -> list[dict[str, Any]]:
    rows = _mapping_list(value, "sources_invalid")
    allowed = {"id", "label", "priority", "as_of"}
    seen: set[str] = set()
    for row in rows:
        _exact_fields(row, allowed, "source_fields_invalid")
        source_id = _required_text(row, "id")
        if source_id in seen:
            raise ResearchResultError("source_id_duplicate")
        seen.add(source_id)
        _required_text(row, "label")
        if row.get("priority") not in {"S0", "S1", "S2", "S3"}:
            raise ResearchResultError("source_priority_invalid")
        _iso_timestamp(_required_text(row, "as_of"), "source_as_of_invalid")
    return rows


def _normalize_visual(value: Any, result_kind: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ResearchResultError("visual_invalid")
    visual = copy.deepcopy(dict(value))
    adapter = _required_text(visual, "adapter")
    if adapter != result_kind or adapter not in {*BOARD_BY_ADAPTER, "price_action"}:
        raise ResearchResultError("visual_adapter_invalid")
    if adapter == "portfolio":
        _exact_fields(visual, {"adapter", "panel"}, "visual_fields_invalid")
        panel = visual.get("panel")
        if not isinstance(panel, Mapping):
            raise ResearchResultError("visual_panel_invalid")
        visual["panel"] = copy.deepcopy(dict(panel))
        validate_portfolio_panel(visual["panel"])
    elif adapter in BOARD_BY_ADAPTER:
        _exact_fields(visual, {"adapter", "snapshot", "default_view"}, "visual_fields_invalid")
        snapshot = visual.get("snapshot")
        if not isinstance(snapshot, Mapping) or snapshot.get("board") != BOARD_BY_ADAPTER[adapter]:
            raise ResearchResultError("visual_snapshot_invalid")
        visual["snapshot"] = copy.deepcopy(dict(snapshot))
        visual["default_view"] = str(visual.get("default_view") or "Overview")
    else:
        _exact_fields(visual, {"adapter", "payload", "title"}, "visual_fields_invalid")
        raw_payload = visual.get("payload")
        if not isinstance(raw_payload, Mapping):
            raise ResearchResultError("visual_payload_invalid")
        if "title" in visual:
            visual["title"] = str(visual["title"])
        payload = copy.deepcopy(dict(raw_payload))
        _validate_price_action_payload(payload)
        try:
            visual["payload"] = build_chart_payload(payload, visual.get("title"))
        except SystemExit as error:
            raise ResearchResultError("visual_payload_invalid") from error
    return visual


def _validate_price_action_payload(payload: Mapping[str, Any]) -> None:
    for key in (
        "ticker",
        "trade_horizon",
        "instrument",
        "primary_timeframe",
        "auxiliary_timeframes",
        "decision_summary",
        "structure_summary",
    ):
        _required_text(payload, key)

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, Mapping) or set(scenarios) != {"bull", "base", "bear"}:
        raise ResearchResultError("price_action_scenarios_invalid")
    for row in scenarios.values():
        if not isinstance(row, Mapping) or set(row) != {"target", "condition", "path", "action"}:
            raise ResearchResultError("price_action_scenarios_invalid")
        for key in ("condition", "path", "action"):
            _required_text(row, key)
        try:
            float(row["target"])
        except (TypeError, ValueError):
            raise ResearchResultError("price_action_scenarios_invalid") from None

    notes = payload.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(item, str) or not item.strip() for item in notes):
        raise ResearchResultError("visual_payload_invalid")

    daily = payload.get("daily_context", {})
    if not isinstance(daily, Mapping) or set(daily) - {"ema20", "ema50", "ema200"}:
        raise ResearchResultError("visual_payload_invalid")
    for value in daily.values():
        if value is not None:
            try:
                float(value)
            except (TypeError, ValueError):
                raise ResearchResultError("visual_payload_invalid") from None

    for key in ("atr14_primary", "atr14_4h"):
        if payload.get(key) is not None:
            try:
                float(payload[key])
            except (TypeError, ValueError):
                raise ResearchResultError("visual_payload_invalid") from None

    _validate_price_action_rows(
        payload.get("entry_plan", []),
        {"stage", "allocation", "condition", "invalidation"},
    )
    _validate_price_action_rows(
        payload.get("event_watch", []),
        {"time", "event", "importance", "transmission", "watch"},
    )
    if "event_note" in payload and not isinstance(payload["event_note"], str):
        raise ResearchResultError("visual_payload_invalid")


def _validate_price_action_rows(value: Any, fields: set[str]) -> None:
    if not isinstance(value, list):
        raise ResearchResultError("visual_payload_invalid")
    for row in value:
        if not isinstance(row, Mapping) or set(row) != fields:
            raise ResearchResultError("visual_payload_invalid")
        for key in fields:
            _required_text(row, key)


def _required_text(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ResearchResultError(f"{key}_invalid")
    return item


def _text_list(value: Any, code: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ResearchResultError(code)
    return list(value)


def _mapping_list(value: Any, code: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise ResearchResultError(code)
    return [copy.deepcopy(dict(item)) for item in value]


def _exact_fields(value: Mapping[str, Any], allowed: set[str], code: str) -> None:
    if set(value) - allowed:
        raise ResearchResultError(code)


def _contains_forbidden_order_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_ORDER_KEYS or _contains_forbidden_order_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_order_key(item) for item in value)
    return False


def _contains_forbidden_order_instruction(text: str) -> bool:
    if any(phrase in text for phrase in FORBIDDEN_ORDER_PHRASES):
        return True
    return any(pattern.search(text) for pattern in FORBIDDEN_ORDER_PATTERNS)


def _iso_timestamp(value: str, code: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ResearchResultError(code) from error


def _write_once(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != content:
        raise ResearchResultError("output_conflict")
    path.write_bytes(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        packet = build_delivery_packet(raw)
        _write_once(args.output_dir / "result.canonical.json", packet.canonical_result)
        _write_once(args.output_dir / "answer.md", packet.markdown)
        if packet.inline_html is not None:
            _write_once(args.output_dir / "inline.html", packet.inline_html)
    except (OSError, json.JSONDecodeError, ResearchResultError, ValueError) as error:
        print(f"research result failed: {error}")
        return 1
    print(f"delivery packet {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
