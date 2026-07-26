#!/usr/bin/env python3
"""Render a deterministic market-catalysts Markdown fixture for offline checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class BriefError(ValueError):
    """Report a fixture field that would make a catalyst brief misleading."""


def _text(row: dict[str, Any], field: str, context: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BriefError(f"{context} requires {field.replace('_', ' ')}")
    return value


def _render_event(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        raise BriefError("market catalyst event requires a source")
    return "\n".join(
        (
            f"### {_text(event, 'title', 'market catalyst event')}",
            f"- 类别：{_text(event, 'category', 'market catalyst event')}",
            f"- 时间/状态：{_text(event, 'time_or_status', 'market catalyst event')}",
            f"- 市场传导：{_text(event, 'market_transmission', 'market catalyst event')}",
            f"- 证据状态：{_text(event, 'evidence_status', 'market catalyst event')}",
            "- 来源：{}（{}）{}".format(
                _text(source, "name", "source"),
                _text(source, "kind", "source"),
                _text(source, "url", "source"),
            ),
            f"- 来源时间：{_text(event, 'as_of', 'market catalyst event')}",
        )
    )


def render_brief(fixture: dict[str, Any]) -> str:
    scheduled = fixture.get("scheduled_events")
    risks = fixture.get("developing_risks")
    if not isinstance(scheduled, list) or not scheduled:
        raise BriefError("market catalysts fixture requires scheduled events")
    if not isinstance(risks, list) or not risks:
        raise BriefError("market catalysts fixture requires developing risks")
    if not all(isinstance(event, dict) for event in [*scheduled, *risks]):
        raise BriefError("market catalysts fixture events must be objects")
    return "\n\n".join(
        (
            "# 市场催化剂简报",
            "- 目标市场：{}\n- 研究时间：{}".format(
                _text(fixture, "target_market", "fixture"),
                _text(fixture, "research_as_of", "fixture"),
            ),
            "## 已定事件\n\n" + "\n\n".join(_render_event(event) for event in scheduled),
            "## 发展中风险\n\n" + "\n\n".join(_render_event(event) for event in risks),
            f"## 数据缺口\n\n{_text(fixture, 'data_gap', 'fixture')}",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise BriefError("fixture must be an object")
        output = render_brief(fixture)
    except (BriefError, OSError, json.JSONDecodeError) as error:
        parser.error(f"Market catalysts fixture error: {error}")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
