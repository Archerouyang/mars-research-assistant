#!/usr/bin/env python3
"""Render a deterministic Markdown instrument-research fixture for offline checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class InstrumentResearchError(ValueError):
    """Report fixture evidence gaps without inventing company facts."""


PRIMARY_KINDS = {
    "sec_filing": "SEC 披露",
    "regulatory_filing": "监管披露",
    "issuer_ir": "发行人 IR",
}


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InstrumentResearchError(f"{context} requires text")
    return value.strip()


def _source(source: object, context: str) -> str:
    if not isinstance(source, dict):
        raise InstrumentResearchError(f"{context} requires a source")
    name = _text(source.get("name"), f"{context} source")
    kind = _text(source.get("kind"), f"{context} source")
    if kind not in PRIMARY_KINDS:
        raise InstrumentResearchError(f"{context} requires primary filing or issuer IR evidence")
    as_of = _text(source.get("as_of"), f"{context} source")
    url = _text(source.get("url"), f"{context} source")
    return f"[{PRIMARY_KINDS[kind]}：{name}]({url})（as_of：{as_of}）"


def _evidence_items(title: str, items: object) -> tuple[list[str], str | None]:
    if items is None or items == []:
        reason = f"未提供{title}的一手证据。"
        return [f"## {title}", f"数据不可用：{reason}", ""], reason
    if not isinstance(items, list):
        raise InstrumentResearchError(f"{title} must be a list")
    rendered = [f"## {title}"]
    for item in items:
        if not isinstance(item, dict):
            raise InstrumentResearchError(f"{title} item must be an object")
        label = _text(item.get("label"), f"{title} item")
        statement = _text(item.get("statement"), f"{label} statement")
        rendered.append(
            f"- **{label}**：{statement}（来源：{_source(item.get('source'), label)}）"
        )
    rendered.append("")
    return rendered, None


def _inferences(items: object) -> tuple[list[str], str | None]:
    if items is None or items == []:
        reason = "未提供可验证的公司推断。"
        return ["## 推断", f"数据不可用：{reason}", ""], reason
    if not isinstance(items, list):
        raise InstrumentResearchError("inferences must be a list")
    rendered = ["## 推断"]
    for item in items:
        if not isinstance(item, dict):
            raise InstrumentResearchError("inference must be an object")
        label = _text(item.get("label"), "inference")
        statement = _text(item.get("statement"), f"{label} inference")
        validation_condition = _text(
            item.get("validation_condition"), f"{label} validation condition"
        )
        rendered.append(
            f"- **推断｜{label}**：{statement}（依据：{_source(item.get('source'), label)}；"
            f"验证条件：{validation_condition}）"
        )
    rendered.append("")
    return rendered, None


def render_research(fixture: dict[str, Any]) -> str:
    instrument = _text(fixture.get("instrument"), "fixture")
    research_as_of = _text(fixture.get("research_as_of"), "fixture")
    identity = fixture.get("identity")
    if not isinstance(identity, dict):
        raise InstrumentResearchError("identity requires an object")
    gaps = fixture.get("data_gaps", [])
    if not isinstance(gaps, list):
        raise InstrumentResearchError("data gaps must be a list")
    if identity.get("status") == "unavailable":
        reason = _text(identity.get("reason"), "unavailable identity")
        lines = [
            f"# 标的研究：{instrument}",
            "",
            f"研究截至：{research_as_of}",
            "",
            "## 事实与证据",
            f"数据不可用：{reason}",
            f"- 来源：未提供可验证资料（as_of：{research_as_of}）",
            "",
            "## 数据缺口",
        ]
        lines.extend(f"- {_text(gap, 'data gap')}" for gap in gaps)
        return "\n".join(lines).rstrip() + "\n"
    issuer = _text(identity.get("issuer"), "identity")
    fundamentals, fundamentals_gap = _evidence_items("基本面", fixture.get("fundamentals"))
    industry_context, industry_context_gap = _evidence_items(
        "行业背景", fixture.get("industry_context")
    )
    company_events, company_events_gap = _evidence_items(
        "公司事件", fixture.get("company_events")
    )
    inferences, inferences_gap = _inferences(fixture.get("inferences"))
    lines = [
        f"# 标的研究：{instrument}",
        "",
        f"研究截至：{research_as_of}",
        "",
        "## 事实与证据",
        f"- 发行人：{issuer}（来源：{_source(identity.get('source'), 'identity')}）",
        "",
        *fundamentals,
        *industry_context,
        *company_events,
        *inferences,
        "## 数据缺口",
    ]
    messages = [
        *(gap for gap in (fundamentals_gap, industry_context_gap, company_events_gap, inferences_gap) if gap),
        *(_text(gap, "data gap") for gap in gaps),
    ]
    if messages:
        lines.extend(f"- {gap}" for gap in messages)
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
            raise InstrumentResearchError("fixture must be a JSON object")
        arguments.output.write_text(render_research(fixture), encoding="utf-8")
    except (OSError, json.JSONDecodeError, InstrumentResearchError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
