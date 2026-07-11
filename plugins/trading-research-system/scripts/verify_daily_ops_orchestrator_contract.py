#!/usr/bin/env python3
"""Verify Daily Ops Orchestrator contract and fixtures."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references
TEMPLATES = PATHS.templates
FIXTURES = PATHS.fixtures

FILES = {
    "context": REPO / "CONTEXT.md",
    "router_skill": ROOT / "skills" / "trading-research" / "SKILL.md",
    "orchestrator_reference": REFERENCES / "daily-ops-orchestrator.md",
    "active_plan": REFERENCES / "active-market-plan.md",
    "orchestrator_template": TEMPLATES / "daily-ops-orchestrator.md",
    "ops_state_template": TEMPLATES / "ops-state.md",
    "fixture_input": FIXTURES / "input" / "daily-ops-orchestrator-start-today.md",
    "fixture_expected": FIXTURES / "expected" / "daily-ops-orchestrator-start-today.md",
    "weekend_fixture_input": FIXTURES / "input" / "daily-ops-weekend-first-start.md",
    "weekend_fixture_expected": FIXTURES / "expected" / "daily-ops-weekend-first-start.md",
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "macro_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
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
        "开始今天的交易研究日程",
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
    verify_later_turn_broker_behavior(
        FILES["router_skill"],
        FILES["orchestrator_reference"],
        FILES["orchestrator_template"],
    )
    print("daily ops later-turn broker behavior ok")
    verify_startup_status_taxonomy(FILES["orchestrator_template"])
    print("daily ops startup status taxonomy ok")
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


def verify_later_turn_broker_behavior(router_path, reference_path, template_path) -> None:
    required_later_turn_terms = (
        "On later turns, `needs_review` asks for matching verification/retry",
        "does not repeat authorization setup",
        "only `unauthorized` re-enters",
    )
    for path in (router_path, reference_path, template_path):
        text = path.read_text(encoding="utf-8")
        for term in required_later_turn_terms:
            if term not in text:
                raise AssertionError(f"later-turn broker behavior missing {term!r} in {path}")


def verify_startup_status_taxonomy(template_path) -> None:
    text = template_path.read_text(encoding="utf-8")
    if "startup_status=partial / uninitialized" not in text:
        raise AssertionError("weekend first-start template must use startup_status=partial / uninitialized")
    if "formal runtime 为 partial / uninitialized" in text:
        raise AssertionError("formal runtime availability must not use startup_status values")


if __name__ == "__main__":
    sys.exit(main())
