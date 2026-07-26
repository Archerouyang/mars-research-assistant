#!/usr/bin/env python3
"""Render deterministic Drive writeback fixtures without contacting Drive."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "skills" / "drive-writeback" / "capability.json"


class DriveWritebackError(ValueError):
    """Report an artifact that cannot be proposed for archival."""


@dataclass(frozen=True)
class ArchivePlan:
    label: str
    destination: str
    operation: str
    updates_index: bool
    simulated_result: str


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DriveWritebackError(f"{context} requires text")
    return value.strip()


def _route(research_type: str) -> dict[str, object]:
    try:
        contract = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DriveWritebackError("Drive writeback routes are unavailable") from error
    routes = contract.get("archive_routes")
    if not isinstance(routes, dict) or not isinstance(routes.get(research_type), dict):
        raise DriveWritebackError("research type is not supported for Drive writeback")
    return routes[research_type]


def _archive_plan(research: dict[str, Any], research_type: str, title: str) -> ArchivePlan:
    route = _route(research_type)
    template = _text(route.get("destination_template"), "archive route destination")
    values = {"title": title}
    if "{date}" in template:
        values["date"] = _text(research.get("date"), "research date")
    if "{period}" in template:
        values["period"] = _text(research.get("period"), "research period")
    try:
        destination = template.format(**values)
    except (KeyError, ValueError) as error:
        raise DriveWritebackError("archive route destination template is invalid") from error
    updates_index = route.get("index_update")
    if not isinstance(updates_index, bool):
        raise DriveWritebackError("archive route index update must be boolean")
    return ArchivePlan(
        label=_text(route.get("label"), "archive route label"),
        destination=destination,
        operation=_text(route.get("operation"), "archive route operation"),
        updates_index=updates_index,
        simulated_result=_text(route.get("simulated_result"), "archive route result"),
    )


def _proposal_id(research_type: str, plan: ArchivePlan) -> str:
    return f"{research_type}:{plan.destination}"


def _render_report(
    heading: str,
    operation_heading: str,
    title: str,
    plan: ArchivePlan,
    proposal_id: str,
    confirmation_status: str,
    write_result: str,
    simulated_index: bool,
) -> str:
    index_status = "更新（模拟）" if simulated_index and plan.updates_index else "更新"
    if not plan.updates_index:
        index_status = "不更新"
    lines = [
        heading,
        "",
        "## 已完成研究",
        f"- 标题：{title}",
        f"- 类型：{plan.label}",
        "",
        operation_heading,
        f"- 提议标识：{proposal_id}",
        f"- 目标位置：{plan.destination}",
        f"- 计划操作：{plan.operation}",
        f"- 总索引：{index_status}",
        "",
        "## 确认状态",
        f"- 确认状态：{confirmation_status}",
        f"- 写入结果：{write_result}",
    ]
    return "\n".join(lines) + "\n"


def render_writeback(fixture: dict[str, Any]) -> str:
    research = fixture.get("research")
    if not isinstance(research, dict):
        raise DriveWritebackError("research requires an object")
    if research.get("status") != "completed":
        raise DriveWritebackError("only completed research can be archived")
    research_type = _text(research.get("type"), "research type")
    title = _text(research.get("title"), "research title")
    _text(research.get("content"), "research content")
    plan = _archive_plan(research, research_type, title)
    proposal_id = _proposal_id(research_type, plan)
    confirmation = fixture.get("confirmation")
    if confirmation is None:
        return _render_report(
            "# Drive 写入提议",
            "## 归档提议",
            title,
            plan,
            proposal_id,
            "等待用户明确确认",
            "未执行",
            False,
        )
    if not isinstance(confirmation, dict) or confirmation.get("explicit") is not True:
        raise DriveWritebackError("confirmation requires an explicit proposal reference")
    if _text(confirmation.get("proposal_id"), "confirmation proposal") != proposal_id:
        return _render_report(
            "# Drive 写入提议",
            "## 归档提议",
            title,
            plan,
            proposal_id,
            "确认与当前提议不匹配",
            "未执行",
            False,
        )
    return _render_report(
        "# Drive 写入结果",
        "## 已确认操作",
        title,
        plan,
        proposal_id,
        "已明确确认",
        plan.simulated_result,
        True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise DriveWritebackError("fixture must be a JSON object")
        arguments.output.write_text(render_writeback(fixture), encoding="utf-8")
    except (OSError, json.JSONDecodeError, DriveWritebackError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
