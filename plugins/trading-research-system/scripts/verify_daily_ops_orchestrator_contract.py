#!/usr/bin/env python3
"""Verify Daily Ops Orchestrator contract and fixtures."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references
TEMPLATES = PATHS.templates
FIXTURES = PATHS.fixtures
ROUTER_INTENTS = FIXTURES / "input" / "router-intents.json"
EMPTY_RUNTIME_WEEKEND_EXPECTED = (
    FIXTURES / "expected" / "daily-ops-weekend-empty-runtime-first-start.md"
)
RUNTIME_HEALTH_SCRIPT = ROOT / "scripts" / "runtime_health.py"

FILES = {
    "context": REPO / "CONTEXT.md",
    "router_skill": ROOT / "skills" / "trading-research-system" / "SKILL.md",
    "orchestrator_reference": REFERENCES / "daily-ops-orchestrator.md",
    "active_plan": REFERENCES / "active-market-plan.md",
    "orchestrator_template": TEMPLATES / "daily-ops-orchestrator.md",
    "daily_tracking_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-daily-market-tracking.md",
    "ops_state_template": TEMPLATES / "ops-state.md",
    "fixture_input": FIXTURES / "input" / "daily-ops-orchestrator-start-today.md",
    "fixture_expected": FIXTURES / "expected" / "daily-ops-orchestrator-start-today.md",
    "weekend_fixture_input": FIXTURES / "input" / "daily-ops-weekend-first-start.md",
    "weekend_fixture_expected": FIXTURES / "expected" / "daily-ops-weekend-first-start.md",
    "weekly_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-weekly-trading-plan.md",
    "macro_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-macro-equity-research.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
    "plugin_design": REPO / "docs" / "PLUGIN_DESIGN.md",
}

REQUIRED = {
    "context": [
        "Daily Ops Orchestrator",
        "主动日程引导",
        "券商只读来源设置",
        "ops-state.md",
        "交易周期确认",
        "ticker + trade_horizon + instrument",
    ],
    "router_skill": [
        "Daily Ops Orchestrator",
        "daily-ops-orchestrator.md",
        "start today",
        "begin daily ops",
        "formal runtime",
        "runtime_dir",
        "trade_horizon",
        "ticker + trade_horizon + instrument",
        "If trade horizon is missing",
        "before deep research",
        "weekend first start",
        "reduced-scope research summary",
        "partial_data",
        "upstream_error",
        "empty_positions_unverified",
        "needs_review",
        "every Daily Ops first start",
    ],
    "orchestrator_reference": [
        "Daily Ops Orchestrator",
        "Purpose",
        "Stage Detection",
        "Required Reads",
        "Output Contract",
        "Startup Health Block",
        "运行状态检查",
        "券商来源健康",
        "当前模式",
        "formal runtime",
        "runtime_dir",
        "repo fixture",
        "券商只读来源设置",
        "下一步指引",
        "Ticker Trade Horizon Confirmation",
        "trade_horizon",
        "instrument",
        "ticker + trade_horizon + instrument",
        "long-term holding",
        "medium-term swing",
        "intraday",
        "0DTE",
        "LEAP",
        "watch only",
        "If trade horizon is missing",
        "ops-state.md",
        "建议下一步",
        "默认建议",
        "你只需要回复",
        "Longbridge read-only",
        "IBKR read-only",
        "暂不启用",
        "Do not create buy/sell instructions",
        "Weekend First Start",
        "before deep research",
        "reduced-scope research summary",
        "do not write runtime",
        "partial_data",
        "upstream_error",
        "empty_positions_unverified",
        "needs_review",
        "是否启用只读 broker 数据？",
    ],
    "active_plan": [
        "trade_horizon",
        "Ticker Trade Horizon Confirmation",
        "ticker + trade_horizon + instrument",
        "If trade horizon is missing",
    ],
    "orchestrator_template": [
        "交易研究日程引导输出",
        "当前日程阶段",
        "读取状态",
        "运行状态检查",
        "券商来源健康",
        "当前模式",
        "formal runtime",
        "runtime_dir",
        "缺失确认",
        "券商只读来源设置",
        "标的与交易想法周期确认",
        "建议下一步",
        "下一步指引",
        "默认建议",
        "你只需要回复",
        "确认后我会执行",
        "ticker + trade_horizon + instrument",
        "Do not create buy/sell instructions",
        "周末首次启动",
        "startup_status=partial / uninitialized",
        "可用研究摘要",
        "partial_data",
        "upstream_error",
        "empty_positions_unverified",
        "needs_review",
        "是否启用只读 broker 数据？",
    ],
    "daily_tracking_skill": [
        "Daily Market Tracking",
    ],
    "ops_state_template": [
        "Daily Ops State",
        "current_stage",
        "last_deep_update",
        "last_quick_update",
        "last_intraday_scan",
        "pending_confirmations",
        "next_recommended_action",
        "active_setups",
        "ticker",
        "trade_horizon",
        "instrument",
    ],
    "fixture_input": [
        "开始今天的交易研究",
        "QQQ",
        "MU",
        "TSM",
        "GLW",
        "交易周期未知",
        "runtime health",
    ],
    "fixture_expected": [
        "当前日程阶段",
        "盘前快速更新",
        "读取状态",
        "运行状态检查",
        "券商来源健康",
        "当前模式",
        "runtime_dir",
        "正式 runtime",
        "缺失确认",
        "券商只读来源设置",
        "Longbridge read-only",
        "IBKR read-only",
        "暂不启用",
        "标的与交易想法周期确认",
        "QQQ",
        "MU",
        "TSM",
        "GLW",
        "trade_horizon",
        "instrument",
        "建议下一步",
        "下一步指引",
        "默认建议",
        "你只需要回复",
        "确认后我会执行",
        "不会写 runtime",
        "不会读取 broker",
        "不会创建真实 automation",
    ],
    "weekend_fixture_input": [
        "周末首次启动",
        "formal runtime available",
        "startup_status partial",
        "broker source needs_review",
        "不写 runtime",
    ],
    "weekend_fixture_expected": [
        "周末首次启动",
        "startup_status=partial",
        "formal runtime | available",
        "可用研究摘要",
        "降级范围",
        "ticker + trade_horizon + instrument",
        "先摘要，后授权",
        "不会写 runtime",
        "不会读取 broker",
        "不会创建、修改、取消或提交订单",
    ],
    "weekly_skill": [
        "weekend first start",
        "reduced-scope research summary",
        "do not write runtime",
        "ticker + trade_horizon + instrument",
    ],
    "macro_skill": [
        "before deep research",
        "ticker + trade_horizon + instrument",
        "watch-only summary",
    ],
    "roadmap": [
        "Daily Ops Orchestrator",
        "ops-state.md",
        "ticker + trade_horizon + instrument",
    ],
    "development_plan": [
        "Daily Ops Orchestrator",
        "ops-state.md",
        "ticker + trade_horizon + instrument",
    ],
    "project_log": [
        "Daily Ops Orchestrator",
        "ops-state.md",
        "ticker + trade_horizon + instrument",
        "active process guide",
    ],
    "plugin_design": [
        "Daily Ops Orchestrator",
        "主动日程引导",
        "ticker + trade_horizon + instrument",
    ],
}

SPEC = ContractSpec(
    name="Daily Ops Orchestrator",
    success_message="daily ops orchestrator contract ok",
    failure_header="daily ops orchestrator contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=(
                [
                    "Broker Source Setup",
                    "Daily Ops Orchestrator Output",
                    "Next Recommended Action",
                    "盘前 quick update",
                    "Ticker / Setup 周期确认",
                ]
                if key in {"orchestrator_template", "fixture_expected"}
                else []
            )
            + (["data/market-plan.md"] if key in {"router_skill", "orchestrator_reference", "orchestrator_template", "fixture_expected"} else []),
            forbidden_label="user-facing English step name",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    result = run_contract(SPEC)
    if result != 0:
        return result
    verify_first_start_broker_setup(
        FILES["router_skill"],
        FILES["orchestrator_reference"],
        FILES["orchestrator_template"],
        FILES["weekend_fixture_expected"],
    )
    print("daily ops first-start broker setup behavior ok")
    verify_exact_start_route(
        FILES["router_skill"],
        FILES["orchestrator_reference"],
        FILES["daily_tracking_skill"],
        FILES["fixture_input"],
        ROUTER_INTENTS,
    )
    print("daily ops exact start route behavior ok")
    verify_exact_weekend_first_start_route(
        FILES["router_skill"],
        FILES["weekly_skill"],
        ROUTER_INTENTS,
    )
    print("daily ops exact weekend injected-route assembly contract ok")
    print("fresh-chat UAT remains a separate required gate")
    verify_empty_environment_weekend_first_response(
        RUNTIME_HEALTH_SCRIPT,
        EMPTY_RUNTIME_WEEKEND_EXPECTED,
    )
    print("daily ops empty-environment weekend first-response behavior ok")
    verify_fixed_first_start_status(
        FILES["router_skill"],
        FILES["orchestrator_reference"],
        FILES["orchestrator_template"],
        FILES["fixture_expected"],
    )
    print("daily ops fixed first-start status behavior ok")
    verify_capability_before_broker_tables(
        FILES["orchestrator_template"],
        FILES["fixture_expected"],
    )
    print("daily ops capability-before-broker behavior ok")
    verify_runtime_origin_taxonomy(
        FILES["orchestrator_reference"],
        FILES["fixture_input"],
        FILES["fixture_expected"],
        FILES["weekend_fixture_expected"],
    )
    print("daily ops runtime origin taxonomy ok")
    verify_later_turn_broker_behavior(
        FILES["router_skill"],
        FILES["orchestrator_reference"],
        FILES["orchestrator_template"],
    )
    print("daily ops later-turn broker behavior ok")
    verify_weekend_fixture_behavior(
        FILES["weekend_fixture_input"],
        FILES["weekend_fixture_expected"],
    )
    print("daily ops weekend first-start fixture behavior ok")
    return 0


def verify_weekend_fixture_behavior(input_path, expected_path) -> None:
    input_text = input_path.read_text(encoding="utf-8")
    text = expected_path.read_text(encoding="utf-8")
    if "formal runtime available: runtime directory exists" not in input_text:
        raise AssertionError("weekend input must distinguish available runtime path from partial startup")
    forbidden_taxonomy = (
        "formal runtime partial",
        "| formal runtime | partial |",
        "formal runtime 为 partial",
    )
    combined_fixture = f"{input_text}\n{text}"
    for forbidden in forbidden_taxonomy:
        if forbidden in combined_fixture:
            raise AssertionError(f"weekend fixtures retain obsolete taxonomy {forbidden!r}")
    ordered_sections = (
        "## 当前日程阶段",
        "## 读取状态",
        "## 可用研究摘要",
        "## 降级范围",
        "## 缺失确认",
        "## 券商只读来源设置",
        "## 建议下一步",
        "## 下一步指引",
        "## 确认后我会执行",
        "## 安全边界",
    )
    positions = [text.find(section) for section in ordered_sections]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise AssertionError(f"weekend fixture sections missing or out of order: {ordered_sections!r}")

    exact_terms = (
        "| runtime_origin | default |",
        "| startup_status | partial |",
        "| formal runtime | available |",
        "| Longbridge | needs_review |",
        "| IBKR | needs_review |",
        "10Y 4.45%",
        "4.50% pressure line",
        "VIX 18.2",
        "VIX 20",
        "P0 CPI release",
        "默认建议: 先确认 setup key，再做宏观/标的深研和周度计划草稿。",
        "确认后先执行宏观/标的深研，再生成周度 Active Market Plan 草稿；只有用户另行确认才写 runtime。",
    )
    for term in exact_terms:
        if term not in text:
            raise AssertionError(f"weekend fixture missing deterministic behavior {term!r}")

    summary_start = text.index("## 可用研究摘要")
    summary_end = text.index("## 降级范围")
    summary_bullets = [
        line for line in text[summary_start:summary_end].splitlines() if line.startswith("- ")
    ]
    if len(summary_bullets) < 3:
        raise AssertionError("weekend reduced-scope summary must contain at least three concrete bullets")
    if "先用当前公开/官方来源给出" in text:
        raise AssertionError("weekend fixture must contain an example, not a promise to research later")


def verify_first_start_broker_setup(router_path, reference_path, template_path, fixture_path) -> None:
    for path in (router_path, reference_path, template_path):
        text = path.read_text(encoding="utf-8")
        marker = "every Daily Ops first start"
        marker_position = text.find(marker)
        if marker_position < 0:
            raise AssertionError(f"cross-document first-start broker setup missing {marker!r} in {path}")
        first_start_contract = text[max(0, marker_position - 100) : marker_position + 400]
        for term in ("every Daily Ops first start", "needs_review", "券商只读来源设置"):
            if term not in first_start_contract:
                raise AssertionError(f"cross-document first-start broker setup missing {term!r} in {path}")

    template = template_path.read_text(encoding="utf-8")
    setup_start = template.index("## 券商只读来源设置")
    setup_end = template.index("## 标的与交易想法周期确认")
    setup_contract = template[setup_start:setup_end]
    for term in (
        "every Daily Ops first start",
        "needs_review",
        "Longbridge read-only / IBKR read-only / 两者都启用 / 暂不启用",
    ):
        if term not in setup_contract:
            raise AssertionError(f"first-start broker setup contract missing {term!r}")

    fixture = fixture_path.read_text(encoding="utf-8")
    fixture_start = fixture.index("## 券商只读来源设置")
    fixture_end = fixture.index("## 建议下一步")
    fixture_setup = fixture[fixture_start:fixture_end]
    for term in (
        "Longbridge | needs_review",
        "IBKR | needs_review",
        "是否启用只读 broker 数据？",
        "暂不启用",
    ):
        if term not in fixture_setup:
            raise AssertionError(f"weekend first-start broker interview missing {term!r}")


def verify_exact_start_route(
    router_path, reference_path, daily_tracking_path, fixture_input_path, router_intents_path
) -> None:
    exact_prompt = "开始今天的交易研究"
    payload = json.loads(router_intents_path.read_text(encoding="utf-8"))
    fixtures = payload.get("router_intents")
    if not isinstance(fixtures, list):
        raise AssertionError("router intent fixture must contain router_intents list")
    exact_routes = [item for item in fixtures if item.get("prompt") == exact_prompt]
    if len(exact_routes) != 1:
        raise AssertionError("exact acceptance prompt must have exactly one router intent")
    if exact_routes[0].get("expected_workflows") != ["runtime_health", "daily_ops_orchestrator"]:
        raise AssertionError(
            "exact acceptance chain must be runtime_health -> daily_ops_orchestrator only"
        )

    router_text = router_path.read_text(encoding="utf-8")
    routing = markdown_section(router_text, "## Routing")
    route_item = list_item_containing(routing, exact_prompt)
    if "read `references/daily-ops-orchestrator.md` first" not in route_item:
        raise AssertionError("exact acceptance prompt must route to Daily Ops first")
    exact_start = markdown_section(router_text, "### Exact Generic First Start")
    for term in (exact_prompt, "before analysis", "daily-market-tracking", "fixed Daily Ops startup block"):
        if term not in exact_start:
            raise AssertionError(f"structured exact-start router rule missing {term!r}")

    stage_detection = markdown_section(
        reference_path.read_text(encoding="utf-8"), "## Stage Detection"
    )
    stage_item = list_item_containing(stage_detection, exact_prompt)
    if not stage_item.startswith("- `premarket_quick_update`"):
        raise AssertionError("exact acceptance prompt must enter Daily Ops stage detection")

    guard = markdown_section(
        daily_tracking_path.read_text(encoding="utf-8"), "## Daily Ops First-Start Guard"
    )
    normalized_guard = " ".join(guard.split())
    for term in (
        exact_prompt,
        "Daily Ops Orchestrator",
        "fixed startup health block",
        "before using this skill",
        "only after Daily Ops",
    ):
        if term not in normalized_guard:
            raise AssertionError(f"daily tracking first-start guard missing {term!r}")

    fixture_input = fixture_input_path.read_text(encoding="utf-8")
    match = re.search(r"User prompt:\n\n```text\n([^\n]+)\n```", fixture_input)
    if not match or match.group(1) != exact_prompt:
        raise AssertionError("Daily Ops input fixture must contain only the exact acceptance prompt")


def verify_exact_weekend_first_start_route(
    router_path, weekly_path, router_intents_path
) -> None:
    exact_prompt = "周末首次启动，先看看下周"
    payload = json.loads(router_intents_path.read_text(encoding="utf-8"))
    fixtures = payload.get("router_intents")
    if not isinstance(fixtures, list):
        raise AssertionError("router intent fixture must contain router_intents list")
    exact_routes = [item for item in fixtures if item.get("prompt") == exact_prompt]
    if len(exact_routes) != 1:
        raise AssertionError("exact Prompt 7 must have exactly one router intent")
    if exact_routes[0].get("expected_workflows") != [
        "runtime_health",
        "daily_ops_orchestrator",
    ]:
        raise AssertionError(
            "exact Prompt 7 chain must be runtime_health -> daily_ops_orchestrator only"
        )

    router_text = router_path.read_text(encoding="utf-8")
    routing = markdown_section(router_text, "## Routing")
    route_item = list_item_containing(routing, exact_prompt)
    if "read `references/daily-ops-orchestrator.md` first" not in route_item:
        raise AssertionError("exact Prompt 7 must route to Daily Ops before weekly analysis")

    contract = markdown_section(router_text, "### Exact Weekend First Start")
    normalized = " ".join(contract.split())
    for term in (
        exact_prompt,
        "status-only runtime health check before analysis",
        "`runtime_origin`",
        "`formal runtime=missing`",
        "`startup_status=uninitialized`",
        "independent axes",
        "先摘要，后授权/初始化",
        "broker read-only",
        "`ticker + trade_horizon + instrument`",
        "dry-run or initialize the private runtime",
        "separate explicit runtime-write authorization",
        "Do not write runtime",
        "Do not read private runtime file contents",
        "Do not read broker or private account data",
        "Do not generate setups or buy/sell instructions",
    ):
        if term not in normalized:
            raise AssertionError(f"model-facing exact Prompt 7 contract missing {term!r}")

    ordered_headings_in_text(
        contract,
        (
            "#### 运行状态检查",
            "#### 可用研究摘要",
            "#### 摘要后缺失确认",
            "#### 安全边界",
        ),
    )

    weekly_text = weekly_path.read_text(encoding="utf-8")
    front_matter_end = weekly_text.find("\n---\n", 4)
    if front_matter_end < 0:
        raise AssertionError("weekly skill must retain YAML front matter")
    weekly_front_matter = weekly_text[:front_matter_end]
    for term in ("weekend prep", "next-week outlook"):
        if term not in weekly_front_matter:
            raise AssertionError(
                f"weekly skill direct-activation surface missing {term!r}"
            )

    guard_heading = "## Exact Weekend First-Start Daily Ops Guard"
    guard_position = weekly_text.find(guard_heading)
    workflow_position = weekly_text.find("## Workflow")
    if guard_position < 0 or workflow_position < 0 or guard_position >= workflow_position:
        raise AssertionError(
            "weekly skill must assemble the exact Prompt 7 guard before its workflow"
        )
    weekly_guard = markdown_section(weekly_text, guard_heading)
    normalized_guard = " ".join(weekly_guard.split())
    for term in (
        exact_prompt,
        "`python3 scripts/runtime_health.py --format json`",
        "Daily Ops Orchestrator",
        "before this weekly workflow",
        "`runtime_origin`",
        "`formal runtime=missing`",
        "`startup_status=uninitialized`",
        "public-source reduced-scope weekly summary",
        "broker read-only",
        "`ticker + trade_horizon + instrument`",
        "`dry-run` or initialize the private runtime",
        "separate explicit runtime-write authorization",
        "Do not write runtime",
        "Do not read private runtime file contents",
        "Do not read broker or private account data",
        "Do not generate setups or buy/sell instructions",
    ):
        if term not in normalized_guard:
            raise AssertionError(
                f"weekly direct-entry exact Prompt 7 guard missing {term!r}"
            )
    obsolete_runtime_health_commands = (
        "`../../scripts/runtime_health.py --format json`",
        "`python3 ../../scripts/runtime_health.py --format json`",
    )
    for obsolete_runtime_health_command in obsolete_runtime_health_commands:
        if obsolete_runtime_health_command in weekly_guard:
            raise AssertionError(
                "weekly direct-entry guard retains cwd-unsafe runtime_health command "
                f"{obsolete_runtime_health_command!r}"
            )
    verify_weekly_runtime_health_repo_command(REPO)
    ordered_headings_in_text(
        weekly_guard,
        (
            "### 运行状态检查",
            "### 可用研究摘要",
            "### 摘要后缺失确认",
            "### 安全边界",
        ),
    )


def verify_weekly_runtime_health_repo_command(repo_path) -> None:
    with tempfile.TemporaryDirectory(prefix="weekly-runtime-health-repo-cwd-") as tmp:
        runtime_dir = Path(tmp) / "nonexistent-private-runtime"
        env = os.environ.copy()
        env["TRADING_RESEARCH_RUNTIME_DIR"] = str(runtime_dir)
        result = subprocess.run(
            [
                "python3",
                "plugins/trading-research-system/scripts/runtime_health.py",
                "--format",
                "json",
            ],
            cwd=repo_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                "weekly repo-cwd runtime health command failed: "
                f"{result.stderr or result.stdout}"
            )
        payload = json.loads(result.stdout)
        checks = {item["id"]: item for item in payload["checks"]}
        actual_state = {
            "runtime_origin": payload.get("runtime_origin"),
            "formal runtime": checks.get("runtime_dir", {}).get("status"),
            "startup_status": payload.get("startup_status"),
        }
        expected_state = {
            "runtime_origin": "environment",
            "formal runtime": "missing",
            "startup_status": "uninitialized",
        }
        if actual_state != expected_state:
            raise AssertionError(
                "weekly repo-cwd runtime health state mismatch: "
                f"expected {expected_state!r}, got {actual_state!r}"
            )
        if payload.get("runtime_dir") != str(runtime_dir):
            raise AssertionError("weekly repo-cwd command ignored environment runtime path")
        if runtime_dir.exists():
            raise AssertionError("weekly repo-cwd status check must not create runtime")


def verify_empty_environment_weekend_first_response(runtime_health_path, expected_path) -> None:
    with tempfile.TemporaryDirectory(prefix="daily-ops-empty-runtime-") as tmp:
        runtime_dir = Path(tmp) / "nonexistent-private-runtime"
        env = os.environ.copy()
        env["TRADING_RESEARCH_RUNTIME_DIR"] = str(runtime_dir)
        result = subprocess.run(
            [
                sys.executable,
                str(runtime_health_path),
                "--date",
                "2026-07-18",
                "--format",
                "json",
            ],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                "empty-environment runtime health failed: "
                f"{result.stderr or result.stdout}"
            )
        payload = json.loads(result.stdout)
        checks = {item["id"]: item for item in payload["checks"]}
        actual_state = {
            "runtime_origin": payload.get("runtime_origin"),
            "formal runtime": checks.get("runtime_dir", {}).get("status"),
            "startup_status": payload.get("startup_status"),
        }
        expected_state = {
            "runtime_origin": "environment",
            "formal runtime": "missing",
            "startup_status": "uninitialized",
        }
        if actual_state != expected_state:
            raise AssertionError(
                f"empty-environment state mismatch: expected {expected_state!r}, "
                f"got {actual_state!r}"
            )
        if payload.get("runtime_dir") != str(runtime_dir):
            raise AssertionError("runtime health must use the environment-selected path")
        if payload.get("current_mode") != "dry-run":
            raise AssertionError("empty runtime without broker facts must remain dry-run")
        broker_statuses = {
            item["id"]: item["status"] for item in payload["broker_source_health"]
        }
        if broker_statuses != {
            "longbridge": "needs_review",
            "ibkr": "needs_review",
            "manual": "missing",
        }:
            raise AssertionError(
                f"empty-environment test must not inject broker facts: {broker_statuses!r}"
            )
        if runtime_dir.exists():
            raise AssertionError("status-only empty-environment check must not create runtime")

        if not expected_path.exists():
            raise AssertionError(
                f"missing sanitized empty-runtime first-response fixture: {expected_path}"
            )
        response = expected_path.read_text(encoding="utf-8")
        ordered_headings_in_text(
            response,
            (
                "## 运行状态检查",
                "## 可用研究摘要",
                "## 摘要后缺失确认",
                "## 安全边界",
            ),
        )
        status_section = markdown_section(response, "## 运行状态检查")
        status_rows = rows_by_key(
            table_with_headers(status_section, ("item", "status", "effect"))
        )
        fixture_state = {
            key: status_rows.get(key, (None, None))[1] for key in expected_state
        }
        if fixture_state != actual_state:
            raise AssertionError(
                f"empty-runtime first response must preserve runtime_health state: "
                f"expected {actual_state!r}, got {fixture_state!r}"
            )

        summary = markdown_section(response, "## 可用研究摘要")
        confirmations = markdown_section(response, "## 摘要后缺失确认")
        boundaries = markdown_section(response, "## 安全边界")
        for term in (
            "公开来源",
            "不提供当前市场读数",
            "不生成 setup",
        ):
            if term not in summary:
                raise AssertionError(f"empty-runtime summary missing boundary {term!r}")
        for term in (
            "broker read-only",
            "ticker + trade_horizon + instrument",
            "dry-run",
            "初始化 private runtime",
            "独立明确授权 runtime 写入",
        ):
            if term not in confirmations:
                raise AssertionError(f"empty-runtime confirmations missing {term!r}")
        for term in (
            "本轮不写 runtime",
            "不读取 broker 或 private account data",
            "不生成 setup、买卖指令或订单动作",
        ):
            if term not in boundaries:
                raise AssertionError(f"empty-runtime safety boundary missing {term!r}")
        user_value_surface = f"{summary}\n{confirmations}"
        for forbidden in (
            "具体点位",
            "entry trigger",
            "exit trigger",
            "买入",
            "卖出",
            "加仓",
            "减仓",
            "仓位比例",
            "account_id",
            "market_value",
            "持仓数量",
            "账户余额",
        ):
            if forbidden in user_value_surface:
                raise AssertionError(
                    f"empty-runtime first response leaked actionable/private field {forbidden!r}"
                )


def verify_fixed_first_start_status(router_path, reference_path, template_path, expected_path) -> None:
    router_text = router_path.read_text(encoding="utf-8")
    router_contract = markdown_section(router_text, "### Exact Generic First Start")
    ordered_headings_in_text(
        router_contract,
        ("#### 运行状态检查", "#### 券商来源健康", "#### 宏观数据来源状态"),
    )

    for path in (reference_path, template_path, expected_path):
        text = path.read_text(encoding="utf-8")
        headings = ("### 运行状态检查", "### 券商来源健康", "### 宏观数据来源状态")
        ordered_headings_in_text(text, headings)

        runtime_block = markdown_section(text, headings[0])
        runtime_table = table_with_headers(runtime_block, ("item", "status", "note"))
        required_runtime_rows = (
            "runtime_dir",
            "runtime_origin",
            "formal runtime",
            "startup_status",
            "startup_reason",
            "current_mode",
            "ops-state.md",
            "market-plan.md",
            "trading-profile.md",
            "macro-panel.json",
            "portfolio_snapshot.csv",
            "daily/YYYY-MM-DD/",
        )
        assert_ordered_row_keys(runtime_table, required_runtime_rows, f"runtime table in {path}")
        runtime_rows = rows_by_key(runtime_table)
        for row_key in required_runtime_rows:
            if row_key not in runtime_rows:
                raise AssertionError(f"first-start runtime row missing {row_key!r} in {path}")

        broker_block = markdown_section(text, headings[1])
        capability_table = table_with_headers(broker_block, ("capability", "status", "effect"))
        broker_table = table_with_headers(broker_block, ("source", "status", "effect"))
        if capability_table["start"] >= broker_table["start"]:
            raise AssertionError(f"capability table must precede broker table in {path}")
        assert_ordered_row_keys(
            capability_table,
            (
                "Longbridge broker skill",
                "Longbridge Terminal CLI",
                "Longbridge macrodata",
                "Official source fallback",
                "IBKR connector",
                "Manual snapshot",
            ),
            f"capability table in {path}",
        )
        required_broker_rows = ("Longbridge", "IBKR", "Manual snapshot", "portfolio_reconciliation")
        assert_ordered_row_keys(broker_table, required_broker_rows, f"broker table in {path}")
        broker_rows = rows_by_key(broker_table)
        for row_key in required_broker_rows:
            if row_key not in broker_rows:
                raise AssertionError(f"first-start broker row missing {row_key!r} in {path}")

        macro_block = markdown_section(text, headings[2])
        macro_table = table_with_headers(macro_block, ("item", "source status", "effect"))
        required_macro_rows = ("macro-panel.json", "authorized/current macro values")
        assert_ordered_row_keys(macro_table, required_macro_rows, f"macro table in {path}")
        macro_rows = rows_by_key(macro_table)
        for row_key in required_macro_rows:
            if row_key not in macro_rows:
                raise AssertionError(f"first-start macro row missing {row_key!r} in {path}")

    template_missing = markdown_section(
        template_path.read_text(encoding="utf-8"), "## 缺失确认"
    )
    if "`portfolio_reconciliation=unavailable`" not in template_missing:
        raise AssertionError("template must instruct exact unavailable status in missing confirmations")

    expected_text = expected_path.read_text(encoding="utf-8")
    expected_broker = markdown_section(expected_text, "### 券商来源健康")
    expected_broker_rows = rows_by_key(
        table_with_headers(expected_broker, ("source", "status", "effect"))
    )
    reconciliation = expected_broker_rows["portfolio_reconciliation"]
    if reconciliation[1] != "unavailable":
        raise AssertionError("expected broker row must render portfolio_reconciliation=unavailable")
    for term in ("longbridge", "ibkr", "excluded", "fail-closed"):
        if term not in reconciliation[2]:
            raise AssertionError(f"expected reconciliation row missing {term!r}")

    expected_missing = markdown_section(expected_text, "## 缺失确认")
    if "`portfolio_reconciliation=unavailable`" not in expected_missing:
        raise AssertionError("missing confirmations must repeat exact reconciliation status")

    expected_macro = markdown_section(expected_text, "### 宏观数据来源状态")
    expected_macro_rows = rows_by_key(
        table_with_headers(expected_macro, ("item", "source status", "effect"))
    )
    if expected_macro_rows["authorized/current macro values"][1] != "missing":
        raise AssertionError("expected fixture must not claim authorized/current macro values")
    for term in ("synthetic fixture/debug input", "没有已授权/当前宏观数值", "不输出或虚构"):
        if term not in expected_macro:
            raise AssertionError(f"expected macro section missing {term!r}")


def markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one {heading!r} heading")
    start = matches[0]
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end])


def ordered_headings_in_text(text: str, headings: tuple[str, ...]) -> None:
    lines = text.splitlines()
    positions: list[int] = []
    for heading in headings:
        matches = [index for index, line in enumerate(lines) if line == heading]
        if len(matches) != 1:
            raise AssertionError(f"expected exactly one structured heading {heading!r}")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise AssertionError(f"structured headings out of order: {headings!r}")


def list_item_containing(section: str, term: str) -> str:
    items: list[str] = []
    current: list[str] = []
    for line in section.splitlines()[1:]:
        if line.startswith("- "):
            if current:
                items.append(" ".join(current))
            current = [line]
        elif current and line.strip():
            current.append(line.strip())
    if current:
        items.append(" ".join(current))
    matches = [item for item in items if term in item]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one list item containing {term!r}")
    return matches[0]


def markdown_tables(section: str) -> list[dict[str, object]]:
    lines = section.splitlines()
    tables: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("|"):
            index += 1
            continue
        start = index
        table_lines: list[str] = []
        while index < len(lines) and lines[index].startswith("|"):
            table_lines.append(lines[index])
            index += 1
        if len(table_lines) < 2:
            continue

        parsed = [
            tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in table_lines
        ]
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in parsed[1]):
            continue
        if any(len(row) != len(parsed[0]) for row in parsed):
            raise AssertionError("malformed markdown table")
        tables.append({"start": start, "headers": parsed[0], "rows": parsed[2:]})
    return tables


def table_with_headers(section: str, headers: tuple[str, ...]) -> dict[str, object]:
    matches = [table for table in markdown_tables(section) if table["headers"] == headers]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one table with headers {headers!r}")
    return matches[0]


def rows_by_key(table: dict[str, object]) -> dict[str, tuple[str, ...]]:
    rows = table["rows"]
    assert isinstance(rows, list)
    keyed: dict[str, tuple[str, ...]] = {}
    for row in rows:
        assert isinstance(row, tuple)
        if row[0] in keyed:
            raise AssertionError(f"duplicate table row {row[0]!r}")
        keyed[row[0]] = row
    return keyed


def assert_ordered_row_keys(
    table: dict[str, object], required_keys: tuple[str, ...], label: str
) -> None:
    rows = table["rows"]
    assert isinstance(rows, list)
    actual_keys = [row[0] for row in rows]
    positions: list[int] = []
    for key in required_keys:
        if key not in actual_keys:
            raise AssertionError(f"{label} missing ordered row {key!r}")
        positions.append(actual_keys.index(key))
    if positions != sorted(positions):
        raise AssertionError(
            f"{label} row order mismatch: required {required_keys!r}, actual {tuple(actual_keys)!r}"
        )


def verify_capability_before_broker_tables(template_path, expected_path) -> None:
    required_capabilities = (
        "Longbridge broker skill",
        "Longbridge Terminal CLI",
        "Longbridge macrodata",
        "Official source fallback",
        "IBKR connector",
        "Manual snapshot",
    )
    for path in (template_path, expected_path):
        section = markdown_section(path.read_text(encoding="utf-8"), "### 券商来源健康")
        capability = table_with_headers(section, ("capability", "status", "effect"))
        broker = table_with_headers(section, ("source", "status", "effect"))
        if capability["start"] >= broker["start"]:
            raise AssertionError(f"source capability table must precede broker source table in {path}")
        capability_rows = rows_by_key(capability)
        for label in required_capabilities:
            if label not in capability_rows:
                raise AssertionError(f"source capability row {label!r} missing in {path}")

    expected_section = markdown_section(
        expected_path.read_text(encoding="utf-8"), "### 券商来源健康"
    )
    expected_rows = rows_by_key(
        table_with_headers(expected_section, ("capability", "status", "effect"))
    )
    expected_statuses = {
        "Longbridge broker skill": "needs_review",
        "Longbridge Terminal CLI": "needs_review",
        "Longbridge macrodata": "needs_review",
        "Official source fallback": "missing",
        "IBKR connector": "needs_review",
        "Manual snapshot": "missing",
    }
    for label, status in expected_statuses.items():
        row = expected_rows[label]
        if row[1] != status:
            raise AssertionError(f"{label} capability status must be {status!r}")
        if status == "needs_review" and "authorization is not inferred" not in row[2]:
            raise AssertionError(f"{label} capability must stay distinct from broker authorization")


def verify_runtime_origin_taxonomy(reference_path, input_path, expected_path, weekend_path) -> None:
    reference = reference_path.read_text(encoding="utf-8")
    reference_runtime = markdown_section(reference, "### 运行状态检查")
    reference_rows = rows_by_key(
        table_with_headers(reference_runtime, ("item", "status", "note"))
    )
    origin_row = reference_rows.get("runtime_origin")
    if origin_row is None:
        raise AssertionError("Daily Ops reference must define runtime_origin row")
    if origin_row[1] != "explicit_argument / environment / default":
        raise AssertionError("runtime_origin taxonomy must match runtime_state.py exactly")
    for obsolete in ("env_override", "user_confirmed", "unknown"):
        if obsolete in " ".join(origin_row):
            raise AssertionError(f"runtime_origin taxonomy retains obsolete value {obsolete!r}")

    fixture_input = input_path.read_text(encoding="utf-8")
    for line in (
        "- runtime_origin: explicit_argument",
        "- startup_status: ready",
        "- macro-panel.json: missing; authorized/current macro values: missing; no actual macro values",
        "- portfolio_snapshot.csv: available; status only; no private rows read",
    ):
        if line not in fixture_input.splitlines():
            raise AssertionError(f"exact-start input fixture missing deterministic line {line!r}")

    expected_runtime = markdown_section(
        expected_path.read_text(encoding="utf-8"), "### 运行状态检查"
    )
    expected_rows = rows_by_key(table_with_headers(expected_runtime, ("item", "status", "note")))
    if expected_rows.get("runtime_origin", (None, None))[1] != "explicit_argument":
        raise AssertionError("exact-start expected fixture must preserve runtime_origin=explicit_argument")
    if expected_rows.get("startup_status", (None, None))[1] != "ready":
        raise AssertionError("exact-start expected fixture must preserve startup_status=ready")
    if expected_rows.get("macro-panel.json", (None, None))[1] != "missing":
        raise AssertionError("exact-start expected fixture must preserve Macro panel=missing")
    portfolio_row = expected_rows.get("portfolio_snapshot.csv", (None, None, ""))
    if portfolio_row[1] != "available" or "status only" not in portfolio_row[2]:
        raise AssertionError(
            "exact-start expected fixture must preserve Portfolio snapshot=available as status-only"
        )
    if "不读取私有持仓行" not in portfolio_row[2]:
        raise AssertionError("exact-start portfolio snapshot status must not expose private rows")

    weekend_runtime = markdown_section(
        weekend_path.read_text(encoding="utf-8"), "## 读取状态"
    )
    weekend_rows = rows_by_key(table_with_headers(weekend_runtime, ("item", "status", "effect")))
    if weekend_rows.get("runtime_origin", (None, None))[1] != "default":
        raise AssertionError("weekend fixture must retain runtime_origin=default coverage")


def verify_later_turn_broker_behavior(router_path, reference_path, template_path) -> None:
    required_later_turn_terms = (
        "On later turns, `missing` or `unauthorized` enters `券商只读来源设置`.",
        "On later turns, `needs_review` asks for matching verification/retry",
        "does not repeat authorization setup",
        "`stale`, `partial_data`, `upstream_error`, and `empty_positions_unverified`",
        "distinct availability or verification paths",
    )
    for path in (router_path, reference_path, template_path):
        text = path.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for term in required_later_turn_terms:
            if term not in normalized:
                raise AssertionError(f"later-turn broker behavior missing {term!r} in {path}")
        if "only `unauthorized` re-enters" in normalized:
            raise AssertionError(f"later-turn broker behavior excludes missing in {path}")


if __name__ == "__main__":
    sys.exit(main())
