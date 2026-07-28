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
RESEARCH_CENTER_NAME = "交易研究中心"
INDEX_NAME = "总索引"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
DOCUMENT_MIME_TYPE = "application/vnd.google-apps.document"
RESEARCH_DIRECTORIES = (
    "收件箱",
    "每日市场思考",
    "交易计划",
    "专题研究",
    "周度复盘",
    "案例复盘",
)


class DriveWritebackError(ValueError):
    """Report an artifact that cannot be proposed for archival."""


@dataclass(frozen=True)
class ArchivePlan:
    label: str
    destination: str
    operation: str
    updates_index: bool
    simulated_result: str


@dataclass(frozen=True)
class DriveItem:
    item_id: str
    name: str
    mime_type: str
    parent_id: str


def _drive_items(value: object) -> list[DriveItem]:
    if not isinstance(value, list):
        raise DriveWritebackError("Drive snapshot items require a list")
    items: list[DriveItem] = []
    for raw_item in value:
        if not isinstance(raw_item, dict):
            raise DriveWritebackError("Drive snapshot item requires an object")
        items.append(
            DriveItem(
                item_id=_text(raw_item.get("id"), "Drive item ID"),
                name=_text(raw_item.get("name"), "Drive item name"),
                mime_type=_text(raw_item.get("mime_type"), "Drive item MIME type"),
                parent_id=_text(raw_item.get("parent_id"), "Drive item parent ID"),
            )
        )
    return items


def _matching_items(
    items: list[DriveItem], *, name: str, mime_type: str, parent_id: str
) -> list[DriveItem]:
    return [
        item
        for item in items
        if item.name == name
        and item.mime_type == mime_type
        and item.parent_id == parent_id
    ]


def _render_initialization_execution(
    *,
    fixture: dict[str, Any],
    proposal_id: str,
    my_drive_id: str,
    root_id: str | None,
    existing: list[str],
    missing_names: list[str],
    directory_ids: dict[str, str],
) -> str:
    execution = fixture.get("execution")
    if not isinstance(execution, dict):
        raise DriveWritebackError("confirmed initialization requires execution results")
    create_results = execution.get("create_results")
    if not isinstance(create_results, dict):
        raise DriveWritebackError("initialization create results require an object")

    created: list[str] = []
    failed: list[str] = []
    pending: list[str] = []
    unresolved_directories = False
    resolved_root_id = root_id
    if RESEARCH_CENTER_NAME in missing_names:
        root_result = create_results.get(RESEARCH_CENTER_NAME)
        if isinstance(root_result, dict) and root_result.get("status") == "created":
            candidate_id = _text(root_result.get("id"), "research center created ID")
            if root_result.get("readback_verified") is True:
                resolved_root_id = candidate_id
                created.append(f"{RESEARCH_CENTER_NAME}（{candidate_id}）")
            else:
                pending.append(f"{RESEARCH_CENTER_NAME}（读回未验证）")
        elif isinstance(root_result, dict) and root_result.get("status") == "failed":
            failed.append(
                f"{RESEARCH_CENTER_NAME}（"
                f"{_text(root_result.get('reason'), 'research center failure reason')}）"
            )
        else:
            pending.append(f"{RESEARCH_CENTER_NAME}（未执行）")

    if resolved_root_id is None:
        unresolved_directories = True
        pending.extend(
            f"{name}（等待根目录创建）"
            for name in RESEARCH_DIRECTORIES
            if name in missing_names
        )
    else:
        for name in RESEARCH_DIRECTORIES:
            if name not in missing_names:
                continue
            result = create_results.get(name)
            if not isinstance(result, dict):
                pending.append(f"{name}（未执行）")
                unresolved_directories = True
                continue
            status = result.get("status")
            if status == "created":
                item_id = _text(result.get("id"), f"{name} created ID")
                if result.get("readback_verified") is not True:
                    pending.append(f"{name}（读回未验证）")
                    unresolved_directories = True
                else:
                    created.append(f"{name}（{item_id}）")
                    directory_ids[name] = item_id
            elif status == "failed":
                failed.append(
                    f"{name}（{_text(result.get('reason'), f'{name} failure reason')}）"
                )
                unresolved_directories = True
            else:
                pending.append(f"{name}（未执行）")
                unresolved_directories = True

    index_created = False
    if INDEX_NAME in missing_names:
        if unresolved_directories:
            pending.insert(0, f"{INDEX_NAME}（等待六个目录完整后创建）")
        else:
            result = create_results.get(INDEX_NAME)
            if isinstance(result, dict) and result.get("status") == "created":
                item_id = _text(result.get("id"), "index created ID")
                if result.get("readback_verified") is True:
                    created.append(f"{INDEX_NAME}（{item_id}）")
                    index_created = True
                else:
                    pending.append(f"{INDEX_NAME}（读回未验证）")
            elif isinstance(result, dict) and result.get("status") == "failed":
                failed.append(
                    f"{INDEX_NAME}（{_text(result.get('reason'), 'index failure reason')}）"
                )
            else:
                pending.append(f"{INDEX_NAME}（未执行）")

    partial = bool(failed or pending)
    lines = [
        "# 交易研究中心初始化结果",
        "",
        "## 锁定目标",
        f"- 初始化提议标识：{proposal_id}",
        f"- My Drive ID：{my_drive_id}",
        f"- 交易研究中心 Drive ID：{resolved_root_id or '不可用'}",
        (
            f"- 目标 parent ID：根目录→{my_drive_id}；子项→"
            f"{resolved_root_id or '等待根目录'}"
            if root_id is None
            else f"- 目标 parent ID：{resolved_root_id}"
        ),
        "",
        "## 逐项状态",
        f"- created：{'、'.join(created) if created else '无'}",
        f"- existing：{'、'.join(existing) if existing else '无'}",
        f"- failed：{'、'.join(failed) if failed else '无'}",
        f"- pending：{'、'.join(pending) if pending else '无'}",
        "- 确认状态：已明确确认",
        (
            "- 读回验证：created 项均已验证"
            if created
            else "- 读回验证：没有新建项需要验证"
        ),
        (
            "- 初始化结果：部分失败；再次运行只补缺失项"
            if partial
            else "- 初始化结果：已完整初始化"
        ),
    ]
    if index_created:
        as_of = _text(execution.get("as_of"), "index as_of")
        data_gaps = _text(execution.get("data_gaps"), "index data gaps")
        lines.extend(["", *_render_index_template(directory_ids, as_of, data_gaps)])
    return "\n".join(lines) + "\n"


def _render_index_template(
    directory_ids: dict[str, str], as_of: str, data_gaps: str
) -> list[str]:
    missing_links = [
        directory for directory in RESEARCH_DIRECTORIES if directory not in directory_ids
    ]
    if missing_links:
        raise DriveWritebackError(
            f"index requires all directory IDs: {', '.join(missing_links)}"
        )
    lines = [
        "## 总索引模板",
        "",
        "### 交易研究中心说明",
        "交易研究中心用于归档已完成的交易研究；初始化不扫描或回填历史文档。",
        "",
        "### 分类目录",
    ]
    lines.extend(
        f"- [{directory}](https://drive.google.com/drive/folders/{directory_ids[directory]})"
        for directory in RESEARCH_DIRECTORIES
    )
    for section in ("交易计划", "专题研究", "周度复盘", "案例复盘"):
        lines.extend(["", f"### {section}索引", "- 暂无初始化后归档的条目。"])
    lines.extend(
        [
            "",
            f"- 最近更新时间：{as_of}",
            f"- 数据缺口：{data_gaps}",
        ]
    )
    return lines


def _render_archive_after_initialization(fixture: dict[str, Any]) -> str:
    initialization_fixture = {
        "operation": "initialize",
        "drive_snapshot": fixture.get("drive_snapshot"),
        "confirmation": fixture.get("initialization_confirmation"),
        "execution": fixture.get("execution"),
    }
    initialization = _render_initialization_proposal(initialization_fixture)
    if "- 初始化结果：已完整初始化" not in initialization:
        return initialization

    execution = fixture.get("execution")
    if not isinstance(execution, dict):
        raise DriveWritebackError("initialization execution requires an object")
    create_results = execution.get("create_results")
    if not isinstance(create_results, dict):
        raise DriveWritebackError("initialization create results require an object")
    root_result = create_results.get(RESEARCH_CENTER_NAME)
    if not isinstance(root_result, dict) or root_result.get("status") != "created":
        raise DriveWritebackError("initialized research center ID is unavailable")
    root_id = _text(root_result.get("id"), "initialized research center ID")

    research = fixture.get("research")
    if not isinstance(research, dict):
        raise DriveWritebackError("research requires an object")
    if research.get("status") != "completed":
        raise DriveWritebackError("only completed research can be archived")
    research_type = _text(research.get("type"), "research type")
    title = _text(research.get("title"), "research title")
    _text(research.get("content"), "research content")
    plan = _archive_plan(research, research_type, title)
    archive_proposal_id = (
        f"archive:{research_type}:{root_id}:{plan.destination}"
    )
    archive_confirmation = fixture.get("archive_confirmation")
    reused_initialization_confirmation = (
        isinstance(archive_confirmation, dict)
        and str(archive_confirmation.get("proposal_id", "")).startswith("initialize:")
    )
    confirmation_status = (
        "初始化确认不能授权研究归档"
        if reused_initialization_confirmation
        else "等待用户对新的归档提议明确确认"
    )
    archive_proposal = "\n".join(
        [
            "# Drive 写入提议",
            "",
            "## 已完成研究",
            f"- 标题：{title}",
            f"- 类型：{plan.label}",
            "",
            "## 归档提议",
            f"- 归档提议标识：{archive_proposal_id}",
            f"- 归档目标 Drive ID：{root_id}",
            f"- 目标位置：{plan.destination}",
            f"- 计划操作：{plan.operation}",
            f"- 总索引：{'更新' if plan.updates_index else '不更新'}",
            "",
            "## 确认状态",
            f"- 确认状态：{confirmation_status}",
            "- 写入结果：未执行",
        ]
    )
    return initialization + "\n" + archive_proposal + "\n"


def _render_initialization_proposal(fixture: dict[str, Any]) -> str:
    drive_error = fixture.get("drive_error")
    if isinstance(drive_error, dict):
        return (
            "\n".join(
                [
                    "# 交易研究中心初始化失败",
                    "",
                    f"- 失败代码：{_text(drive_error.get('code'), 'Drive error code')}",
                    f"- 失败原因：{_text(drive_error.get('reason'), 'Drive error reason')}",
                    "- 初始化结果：未执行",
                ]
            )
            + "\n"
        )
    snapshot = fixture.get("drive_snapshot")
    if not isinstance(snapshot, dict):
        raise DriveWritebackError("Drive snapshot requires an object")
    my_drive_id = _text(snapshot.get("my_drive_id"), "My Drive ID")
    items = _drive_items(snapshot.get("items"))
    roots = _matching_items(
        items,
        name=RESEARCH_CENTER_NAME,
        mime_type=FOLDER_MIME_TYPE,
        parent_id=my_drive_id,
    )
    if len(roots) > 1:
        return (
            "\n".join(
                [
                    "# 交易研究中心根目录选择",
                    "",
                    f"- My Drive ID：{my_drive_id}",
                    "- 解析状态：发现多个 My Drive 同名根目录，不能猜测目标",
                    f"- 候选 Drive ID：{'、'.join(root.item_id for root in roots)}",
                    "- 选择状态：等待用户明确选择",
                    "- 初始化结果：未执行",
                ]
            )
            + "\n"
        )
    root = roots[0] if roots else None
    root_id = root.item_id if root else None
    target_id = root_id or my_drive_id
    proposal_id = (
        f"initialize:root:{root_id}"
        if root_id
        else f"initialize:parent:{my_drive_id}:{RESEARCH_CENTER_NAME}"
    )
    tree = [
        f"{RESEARCH_CENTER_NAME}/",
        f"├── {INDEX_NAME}（Google Doc）",
        *(f"├── {directory}/" for directory in RESEARCH_DIRECTORIES[:-1]),
        f"└── {RESEARCH_DIRECTORIES[-1]}/",
    ]
    existing = [f"{RESEARCH_CENTER_NAME}（{root_id}）"] if root_id else []
    proposed = [] if root_id else [f"{RESEARCH_CENTER_NAME}（文件夹）"]
    missing_names = [] if root_id else [RESEARCH_CENTER_NAME]
    directory_ids: dict[str, str] = {}
    if root_id:
        index_items = _matching_items(
            items,
            name=INDEX_NAME,
            mime_type=DOCUMENT_MIME_TYPE,
            parent_id=root_id,
        )
        if index_items:
            existing.append(f"{INDEX_NAME}（{index_items[0].item_id}）")
        else:
            proposed.append(f"{INDEX_NAME}（Google Doc）")
            missing_names.append(INDEX_NAME)
        for directory in RESEARCH_DIRECTORIES:
            directory_items = _matching_items(
                items,
                name=directory,
                mime_type=FOLDER_MIME_TYPE,
                parent_id=root_id,
            )
            if directory_items:
                existing.append(f"{directory}（{directory_items[0].item_id}）")
                directory_ids[directory] = directory_items[0].item_id
            else:
                proposed.append(f"{directory}（文件夹）")
                missing_names.append(directory)
    else:
        proposed.extend(
            [
                f"{INDEX_NAME}（Google Doc）",
                *(f"{directory}（文件夹）" for directory in RESEARCH_DIRECTORIES),
            ]
        )
        missing_names.extend((INDEX_NAME, *RESEARCH_DIRECTORIES))
    no_changes = not proposed
    confirmation = fixture.get("confirmation")
    confirmation_matches = (
        isinstance(confirmation, dict)
        and confirmation.get("explicit") is True
        and confirmation.get("proposal_id") == proposal_id
        and confirmation.get("target_id") == target_id
    )
    confirmation_mismatched = confirmation is not None and not confirmation_matches
    if confirmation_matches and fixture.get("execution") is not None:
        return _render_initialization_execution(
            fixture=fixture,
            proposal_id=proposal_id,
            my_drive_id=my_drive_id,
            root_id=root_id,
            existing=existing,
            missing_names=missing_names,
            directory_ids=directory_ids,
        )
    return (
        "\n".join(
            [
                (
                    "# 交易研究中心初始化结果"
                    if no_changes
                    else "# 交易研究中心初始化提议"
                ),
                "",
                "## 锁定目标",
                f"- 初始化提议标识：{proposal_id}",
                f"- My Drive ID：{my_drive_id}",
                f"- 交易研究中心 Drive ID：{root_id or '尚未创建'}",
                f"- 目标 Drive ID：{target_id}",
                "",
                "## 完整目录树",
                "```text",
                *tree,
                "```",
                "",
                "## 初始化状态",
                f"- 已存在项：{'、'.join(existing) if existing else '无'}",
                f"- 拟创建项：{'、'.join(proposed) if proposed else '无'}",
                (
                    "- 确认状态：无需确认（无写入）"
                    if no_changes
                    else (
                        "- 确认状态：确认与当前初始化提议或目标不匹配"
                        if confirmation_mismatched
                        else (
                            "- 确认状态：已明确确认，等待执行"
                            if confirmation_matches
                            else "- 确认状态：等待用户明确确认"
                        )
                    )
                ),
                (
                    "- 初始化结果：无变更，目录结构已完整"
                    if no_changes
                    else "- 初始化结果：未执行"
                ),
            ]
        )
        + "\n"
    )


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
    if fixture.get("operation") == "initialize":
        return _render_initialization_proposal(fixture)
    if fixture.get("operation") == "archive" and "drive_snapshot" in fixture:
        return _render_archive_after_initialization(fixture)
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
