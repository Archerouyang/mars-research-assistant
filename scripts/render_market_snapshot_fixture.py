#!/usr/bin/env python3
"""Render a deterministic Markdown market-snapshot fixture for offline checks."""

from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any


class SnapshotError(ValueError):
    """Report an invalid fixture as an actionable market-snapshot data gap."""


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{context} requires text")
    return value.strip()


def _source(source: object, context: str) -> tuple[str, str, str | None]:
    if not isinstance(source, dict):
        raise SnapshotError(f"{context} requires a source")
    name = _text(source.get("name"), f"{context} source")
    as_of = _text(source.get("as_of"), f"{context} source")
    url = source.get("url")
    if url is not None:
        url = _text(url, f"{context} source")
    return name, as_of, url


def _source_label(source: object, context: str) -> tuple[str, str]:
    name, as_of, url = _source(source, context)
    label = f"[{name}]({url})" if url else name
    return label, as_of


def _indicator_row(indicator: object, group_name: str) -> str:
    if not isinstance(indicator, dict):
        raise SnapshotError(f"{group_name} indicator must be an object")
    label = _text(indicator.get("label"), "indicator")
    if indicator.get("status") == "unavailable":
        reason_value = indicator.get("reason")
        if not isinstance(reason_value, str) or not reason_value.strip():
            raise SnapshotError("unavailable indicator requires a reason")
        reason = reason_value.strip()
        return f"| {label} | 数据不可用：{reason} | — | — |"
    value = _text(indicator.get("value"), f"{label} indicator")
    change = indicator.get("change")
    displayed = value if change is None else f"{value}；{_text(change, label + ' change')}"
    source, as_of = _source_label(indicator.get("source"), "indicator")
    return f"| {label} | {displayed} | {source} | {as_of} |"


def _indicator_groups(groups: object) -> list[str]:
    if not isinstance(groups, list) or not groups:
        raise SnapshotError("indicator groups require at least one group")
    rendered: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            raise SnapshotError("indicator group must be an object")
        title = _text(group.get("title"), "indicator group")
        indicators = group.get("indicators")
        if not isinstance(indicators, list) or not indicators:
            raise SnapshotError(f"{title} requires indicators")
        rendered.extend([f"### {title}", "| 指标 | 当前值 / 变化 | 来源 | as_of |", "| --- | --- | --- | --- |"])
        rendered.extend(_indicator_row(indicator, title) for indicator in indicators)
        rendered.append("")
    return rendered


def _optional_items(
    title: str, items: object, empty_reason: str, fields: tuple[str, ...]
) -> list[str]:
    if items is None:
        return [f"## {title}", f"数据不可用：{empty_reason}", ""]
    if not isinstance(items, list):
        raise SnapshotError(f"{title} must be a list")
    if not items:
        return [f"## {title}", f"数据不可用：{empty_reason}", ""]
    rendered = [f"## {title}"]
    for item in items:
        if not isinstance(item, dict):
            raise SnapshotError(f"{title} item must be an object")
        label = _text(item.get("label"), f"{title} item")
        details = "；".join(
            _text(item.get(field), f"{label} {field}").rstrip("。；") for field in fields
        ) + "。"
        source, as_of = _source_label(item.get("source"), f"{title} item")
        rendered.append(f"- **{label}**：{details}（来源：{source}；as_of：{as_of}）")
    rendered.append("")
    return rendered


def render_snapshot(fixture: dict[str, Any]) -> str:
    title = _text(fixture.get("title"), "snapshot")
    research_as_of = _text(fixture.get("research_as_of"), "snapshot")
    status = _text(fixture.get("status"), "snapshot")
    source, source_as_of = _source_label(fixture.get("status_source"), "status")
    lines = [
        f"# {title}",
        "",
        f"研究截至：{research_as_of}",
        "",
        "## 当前状态",
        f"{status}（来源：{source}；as_of：{source_as_of}）",
        "",
        "## 核心指标",
        "",
        *_indicator_groups(fixture.get("indicator_groups")),
        *_optional_items(
            "近期催化剂",
            fixture.get("event_context"),
            "未提供已核实的近期催化剂。",
            ("details", "market_implication"),
        ),
        *_optional_items(
            "情景与触发",
            fixture.get("scenarios"),
            "未提供满足证据要求的情景触发。",
            ("condition", "market_implication"),
        ),
        *_optional_items(
            "风险暴露",
            fixture.get("risks"),
            "未提供满足证据要求的风险暴露判断。",
            ("details", "watch"),
        ),
        "## 数据缺口",
    ]
    gaps = fixture.get("data_gaps", [])
    if not isinstance(gaps, list):
        raise SnapshotError("data gaps must be a list")
    unavailable = [
        indicator.get("reason")
        for group in fixture["indicator_groups"]
        if isinstance(group, dict)
        for indicator in group.get("indicators", [])
        if isinstance(indicator, dict) and indicator.get("status") == "unavailable"
    ]
    messages = [*unavailable, *(_text(gap, "data gap") for gap in gaps)]
    if messages:
        lines.extend(f"- {message}" for message in messages)
    else:
        lines.append("- 本次未记录额外数据缺口。")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise SnapshotError("fixture must be a JSON object")
        arguments.output.write_text(render_snapshot(fixture), encoding="utf-8")
    except (OSError, json.JSONDecodeError, SnapshotError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
