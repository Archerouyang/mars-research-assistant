#!/usr/bin/env python3
"""Verify deterministic 1.0 docs plus skill/fixture contracts.

This verifier does not invoke a model. Fresh-chat UAT remains a separate release
gate after plugin installation.
"""

from __future__ import annotations

import csv
import re
import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


PATHS = PluginPaths.from_script(__file__)
REPO = PATHS.repo
ROOT = PATHS.root

FILES = {
    "acceptance_plan": REPO / "docs" / "1.0_ACCEPTANCE.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
    "mvp_runbook": REPO / "docs" / "MVP_RUNBOOK.md",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "daily_tracking_skill": ROOT / "skills" / "daily-market-tracking" / "SKILL.md",
    "rolling_pa_input": ROOT
    / "assets"
    / "fixtures"
    / "input"
    / "daily-market-tracking-rolling-pa-missing-setup-key.md",
    "rolling_pa_confirmed_trade_plans": ROOT
    / "assets"
    / "fixtures"
    / "input"
    / "daily-market-tracking-rolling-pa-confirmed-trade-plans.csv",
    "rolling_pa_expected": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "daily-market-tracking-rolling-pa-watch-only.md",
}

REQUIRED = {
    "acceptance_plan": [
        "# 1.0 Acceptance Plan",
        "1.0 = local trading research workflow",
        "Non-goals",
        "Acceptance Prompts",
        "开始今天的交易研究",
        "宏观数据来源状态",
        "macro-panel.json",
        "portfolio_snapshot.csv",
        "position_daily_report.py",
        "intraday_scan.py",
        "滚动盘面分析",
        "post-order",
        "post-exit",
        "No broker write actions",
        "verify-plugin.sh",
        "verify-mvp.sh",
        "2026-07-08",
        "2026-07-12",
        "runtime_origin",
        "startup_status",
        "partial_data",
        "upstream_error",
        "empty_positions_unverified",
        "portfolio_reconciliation",
        "PA Scenario Board",
        "ticker + trade_horizon + instrument",
        "周末首次启动",
        "先给可用研究摘要",
    ],
    "roadmap": [
        "1.0 Acceptance Plan",
        "docs/1.0_ACCEPTANCE.md",
        "local trading research workflow",
    ],
    "development_plan": [
        "Define 1.0 acceptance plan",
        "docs/1.0_ACCEPTANCE.md",
        "Acceptance Prompts",
    ],
    "project_log": [
        "1.0 Acceptance Plan",
        "docs/1.0_ACCEPTANCE.md",
        "verify_1_0_acceptance_contract.py",
    ],
    "mvp_runbook": [
        "docs/1.0_ACCEPTANCE.md",
        "1.0 acceptance",
    ],
    "contract_suite": [
        "one-zero-acceptance",
        "verify_1_0_acceptance_contract.py",
    ],
    "daily_tracking_skill": [
        "Daily Market Tracking",
        "Price Action Rolling Output",
    ],
    "rolling_pa_input": [
        "做 DRAM/SOXX/QQQ 的滚动盘面分析",
        "trade_horizon: missing for every ticker",
        "instrument: missing for every ticker",
        "repo fixture",
    ],
    "rolling_pa_confirmed_trade_plans": [
        "date,trade_id,setup_id,theme_id,status,ticker",
        "sector_etf",
        "etf_common",
        "DRAM",
        "SOXX",
        "QQQ",
    ],
    "rolling_pa_expected": [
        "watch-only",
        "repo fixture 未读取、未借用",
        "Watch-only 摘要",
        "聚焦确认问题",
        "trade_horizon",
        "instrument",
    ],
}

SPEC = ContractSpec(
    name="1.0 acceptance plan",
    success_message="1.0 acceptance contract ok",
    failure_header="1.0 acceptance contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    result = run_contract(SPEC)
    if result != 0:
        return result
    verify_rolling_pa_missing_setup_key(
        FILES["daily_tracking_skill"],
        FILES["rolling_pa_input"],
        FILES["rolling_pa_expected"],
    )
    verify_rolling_pa_confirmed_keys(FILES["rolling_pa_confirmed_trade_plans"])
    print("1.0 rolling PA setup-key skill/fixture contract ok")
    print("fresh-chat UAT still required; deterministic verifier did not call a model")
    return 0


def markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one structured heading {heading!r}")
    start = matches[0]
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end])


def assert_no_concrete_rolling_pa_output(text: str) -> None:
    forbidden_terms = (
        "点位",
        "支撑",
        "压力",
        "触发",
        "失效",
        "加仓",
        "减仓",
        "暂停",
        "比例",
        "support",
        "resistance",
        "trigger",
        "invalidation",
        "add suggestion",
        "trim suggestion",
        "pause suggestion",
        "sizing suggestion",
    )
    normalized = text.lower()
    for forbidden in forbidden_terms:
        if forbidden.lower() in normalized:
            raise AssertionError(
                f"watch-only expected response contains concrete PA output {forbidden!r}"
            )
    if re.search(r"(?<![A-Za-z])\d+(?:\.\d+)?", text):
        raise AssertionError("watch-only expected response contains a concrete numeric level")


SETUP_KEY_SOURCE_FIELDS = (
    ("current_confirmation", "instrument"),
    ("trade_plans", "instrument_type"),
    ("intraday_watchlist", "instrument_type"),
    ("active_plan_markdown", "instrument_type"),
)


def resolve_key_from_source(rows, ticker, instrument_field):
    matching_rows = [
        row for row in rows if (row.get("ticker") or "").strip() == ticker
    ]
    if not matching_rows:
        return False, None

    candidates = set()
    for row in matching_rows:
        trade_horizon = (row.get("trade_horizon") or "").strip()
        instrument = (row.get(instrument_field) or "").strip()
        if not trade_horizon or not instrument:
            return True, None
        candidates.add((trade_horizon, instrument))
    if len(candidates) != 1:
        return True, None

    trade_horizon, instrument = next(iter(candidates))
    return True, {
        "ticker": ticker,
        "trade_horizon": trade_horizon,
        "instrument": instrument,
    }


def resolve_ordered_setup_keys(source_rows, requested_tickers):
    resolved = {}
    for ticker in requested_tickers:
        for source_name, instrument_field in SETUP_KEY_SOURCE_FIELDS:
            present, key = resolve_key_from_source(
                source_rows.get(source_name, []), ticker, instrument_field
            )
            if not present:
                continue
            if key is None:
                return None
            resolved[ticker] = key
            break
        else:
            return None
    return resolved


def rolling_pa_setup_key_route(source_rows, requested_tickers):
    resolved = resolve_ordered_setup_keys(source_rows, requested_tickers)
    if resolved is None:
        return "watch-only", True, None
    return "continue normal rolling PA", False, resolved


def verify_rolling_pa_confirmed_keys(trade_plans_path) -> None:
    with trade_plans_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(CSV_SCHEMAS["trade-plans.csv"]):
            raise AssertionError(
                "synthetic trade-plans fixture must use the exact formal runtime schema"
            )
        rows = list(reader)
        if not rows or any(
            None in row or any(value is None for value in row.values()) for row in rows
        ):
            raise AssertionError("synthetic trade-plans rows must match the full schema width")

    requested_tickers = ("DRAM", "SOXX", "QQQ")
    ordered_sources = {
        "current_confirmation": [],
        "trade_plans": rows,
        "intraday_watchlist": [],
        "active_plan_markdown": [],
    }
    route, missing_key_question, resolved = rolling_pa_setup_key_route(
        ordered_sources, requested_tickers
    )
    if route != "continue normal rolling PA" or missing_key_question:
        raise AssertionError("confirmed setup keys must continue without a missing-key question")
    expected_resolution = {
        "DRAM": {
            "ticker": "DRAM",
            "trade_horizon": "medium-term swing",
            "instrument": "sector_etf",
        },
        "SOXX": {
            "ticker": "SOXX",
            "trade_horizon": "medium-term swing",
            "instrument": "sector_etf",
        },
        "QQQ": {
            "ticker": "QQQ",
            "trade_horizon": "long-term holding",
            "instrument": "etf_common",
        },
    }
    if resolved != expected_resolution:
        raise AssertionError(
            "instrument_type must copy exactly to the setup key's instrument component: "
            f"expected {expected_resolution!r}, got {resolved!r}"
        )

    rows_by_ticker = {row["ticker"]: row for row in rows}
    priority_sources = {
        "current_confirmation": [
            {
                "ticker": "DRAM",
                "trade_horizon": "intraday",
                "instrument": "etf_common",
            }
        ],
        "trade_plans": rows,
        "intraday_watchlist": [
            {
                **rows_by_ticker["QQQ"],
                "trade_horizon": "intraday",
                "instrument_type": "sector_etf",
            }
        ],
        "active_plan_markdown": [],
    }
    priority_route, priority_question, priority_resolution = (
        rolling_pa_setup_key_route(priority_sources, requested_tickers)
    )
    expected_priority_resolution = {
        **expected_resolution,
        "DRAM": {
            "ticker": "DRAM",
            "trade_horizon": "intraday",
            "instrument": "etf_common",
        },
    }
    if (
        priority_route != "continue normal rolling PA"
        or priority_question
        or priority_resolution != expected_priority_resolution
    ):
        raise AssertionError(
            "higher-priority complete keys must win per ticker without lower-source override"
        )

    fallback_sources = {
        "current_confirmation": [],
        "trade_plans": [rows_by_ticker["DRAM"]],
        "intraday_watchlist": [rows_by_ticker["SOXX"]],
        "active_plan_markdown": [rows_by_ticker["QQQ"]],
    }
    fallback_route, fallback_question, fallback_resolution = (
        rolling_pa_setup_key_route(fallback_sources, requested_tickers)
    )
    if (
        fallback_route != "continue normal rolling PA"
        or fallback_question
        or fallback_resolution != expected_resolution
    ):
        raise AssertionError("missing ticker rows must fall through to the next ordered source")

    incomplete_first_source = {
        **ordered_sources,
        "current_confirmation": [
            {"ticker": "DRAM", "trade_horizon": "", "instrument": "etf_common"}
        ],
    }
    if rolling_pa_setup_key_route(incomplete_first_source, ("DRAM",))[:2] != (
        "watch-only",
        True,
    ):
        raise AssertionError("incomplete first-present source must not fall through")

    conflicting_first_source = {
        **ordered_sources,
        "current_confirmation": [
            {
                "ticker": "DRAM",
                "trade_horizon": "intraday",
                "instrument": "etf_common",
            },
            {
                "ticker": "DRAM",
                "trade_horizon": "medium-term swing",
                "instrument": "sector_etf",
            },
        ],
    }
    if rolling_pa_setup_key_route(conflicting_first_source, ("DRAM",))[:2] != (
        "watch-only",
        True,
    ):
        raise AssertionError("conflicting first-present source must not fall through")

    empty_sources = {source_name: [] for source_name, _ in SETUP_KEY_SOURCE_FIELDS}
    if rolling_pa_setup_key_route(empty_sources, ("DRAM",))[:2] != (
        "watch-only",
        True,
    ):
        raise AssertionError("zero setup keys across all sources must remain watch-only")

    conflicting_rows = rows + [
        {**rows[0], "trade_horizon": "intraday", "instrument_type": "etf_common"}
    ]
    conflicting_sources = {**ordered_sources, "trade_plans": conflicting_rows}
    conflict_route, conflict_question_required, conflict_resolution = (
        rolling_pa_setup_key_route(conflicting_sources, requested_tickers)
    )
    if conflict_route != "watch-only" or not conflict_question_required:
        raise AssertionError("conflicting setup keys must route to watch-only confirmation")
    if conflict_resolution is not None:
        raise AssertionError("conflicting duplicate setup keys must remain unresolved")


def verify_rolling_pa_missing_setup_key(skill_path, input_path, expected_path) -> None:
    exact_prompt = "做 DRAM/SOXX/QQQ 的滚动盘面分析"
    expected_actions = [
        "- 初始化今日运行包：仅在用户明确授权 runtime 写入后执行。",
        "- 生成盘中观察清单：先确认 DRAM、SOXX、QQQ 各自完整 setup key，并在用户明确授权 runtime 写入后再生成。",
    ]
    input_text = input_path.read_text(encoding="utf-8")
    prompt_match = re.search(r"User prompt:\n\n```text\n([^\n]+)\n```", input_text)
    if not prompt_match or prompt_match.group(1) != exact_prompt:
        raise AssertionError("rolling PA fixture must use the exact acceptance prompt")

    skill_text = skill_path.read_text(encoding="utf-8")
    gate = markdown_section(skill_text, "## Rolling PA Setup-Key Gate")
    normalized_gate = " ".join(gate.split())
    for term in (
        exact_prompt,
        "ticker + trade_horizon + instrument",
        "Bare tickers trigger this lookup; they are not automatically unresolved",
        "Resolve each ticker's complete `ticker + trade_horizon + instrument` setup key in this bounded order",
        "explicit confirmation in the current request or current chat",
        "today's formal runtime `daily/YYYY-MM-DD/trade-plans.csv`",
        "`daily/YYYY-MM-DD/intraday-watchlist.csv`",
        "structured setup records",
        "`ticker`, `trade_horizon`, and `instrument_type`",
        "map `instrument_type` to the setup key's `instrument` component",
        "An Active Plan Markdown row is a final fallback only when it explicitly carries all three canonical fields",
        "Do not infer a missing horizon from `Symbol` or `Instrument` labels",
        "Apply this order independently for each ticker",
        "Fall through only when a higher-priority source has no row for that ticker",
        "lower-priority rows do not override it",
        "do not fall through",
        "exactly one unambiguous complete key exists for every requested ticker",
        "zero, incomplete, or multiple conflicting keys",
        "watch-only",
        "When the request supplies ticker names only, label each as an unconfirmed watch ticker and assert no structure, direction, or risk role",
        "one focused confirmation question",
        "repo fixture",
        "Do not read prior levels or OHLCV, and do not begin deep research, until key resolution completes",
        "concrete levels, triggers, invalidations, sizing, or instrument-specific risk advice",
    ):
        if term not in normalized_gate:
            raise AssertionError(f"rolling PA setup-key gate missing {term!r}")

    request_position = normalized_gate.index(
        "explicit confirmation in the current request or current chat"
    )
    trade_plans_position = normalized_gate.index(
        "today's formal runtime `daily/YYYY-MM-DD/trade-plans.csv`"
    )
    watchlist_position = normalized_gate.index(
        "`daily/YYYY-MM-DD/intraday-watchlist.csv`"
    )
    markdown_position = normalized_gate.index(
        "An Active Plan Markdown row is a final fallback only when it explicitly carries all three canonical fields"
    )
    if not request_position < trade_plans_position < watchlist_position < markdown_position:
        raise AssertionError(
            "rolling PA setup-key lookup order must be current confirmation, "
            "formal runtime trade plans, formal runtime watchlist, then canonical Markdown"
        )

    for overbroad in (
        "before reading any Active Plan or prior analysis",
        "do not infer the horizon or instrument from an ETF name, repo example, prior chat, holding, or market-plan row",
        "do not read or borrow an Active Plan, prior-analysis level, or repo fixture",
    ):
        if overbroad in normalized_gate:
            raise AssertionError(f"rolling PA setup-key gate retains over-broad rule {overbroad!r}")

    special_output = markdown_section(
        skill_text, "### Unresolved Setup Key + Formal Runtime Unavailable"
    )
    normalized_special_output = " ".join(special_output.split())
    for term in (
        f"Apply this exact five-section, exact-two-action special case only when the current request is exactly `{exact_prompt}` and its setup keys remain unresolved and formal runtime is unavailable",
        "For every other ticker request, use the generic dynamic Runtime Guidance Contract, adapt ticker names and actions, and never inherit DRAM/SOXX/QQQ from this acceptance-only block",
        "Primary status: `待复核`; keep `watch-only` only as a secondary qualifier",
        "This special case overrides the general Runtime Guidance Contract choice of 2-4 executable next actions only for this state",
        "Ask exactly one focused confirmation question",
    ):
        if term not in normalized_special_output:
            raise AssertionError(f"model-facing unavailable-runtime contract missing {term!r}")
    if (
        "When the setup key remains unresolved and formal runtime is unavailable, render"
        in normalized_special_output
    ):
        raise AssertionError(
            "model-facing unavailable-runtime contract must not apply to unrelated tickers"
        )
    special_positions = [
        special_output.index(f"`{section}`")
        for section in (
            "运行状态",
            "当前范围",
            "Watch-only 摘要",
            "可执行下一步",
            "聚焦确认问题",
        )
    ]
    if special_positions != sorted(special_positions):
        raise AssertionError("model-facing unavailable-runtime sections are out of order")
    skill_action_lines = [
        line
        for line in special_output.splitlines()
        if line.startswith("- 初始化今日运行包：") or line.startswith("- 生成盘中观察清单：")
    ]
    if skill_action_lines != expected_actions:
        raise AssertionError(
            "model-facing unavailable-runtime contract must preserve both runtime-write gates"
        )

    pa_output = markdown_section(skill_text, "## Price Action Rolling Output")
    normalized_pa_output = " ".join(pa_output.split())
    for term in (
        "Only enter this section after every ticker has a complete confirmed setup key",
        "If the setup key is incomplete, use the watch-only gate above and do not render this section",
    ):
        if term not in normalized_pa_output:
            raise AssertionError(f"Price Action output section weakens setup-key gate: missing {term!r}")

    expected_text = expected_path.read_text(encoding="utf-8")
    assert_no_concrete_rolling_pa_output(expected_text)
    for mutation in (
        "\n- 支撑 724\n",
        "\n- trigger above prior high\n",
        "\n- add suggestion / trim suggestion\n",
    ):
        try:
            assert_no_concrete_rolling_pa_output(expected_text + mutation)
        except AssertionError:
            continue
        raise AssertionError(f"concrete-output mutation was not rejected: {mutation!r}")

    ordered_sections = (
        "## 运行状态",
        "## 当前范围",
        "## Watch-only 摘要",
        "## 可执行下一步",
        "## 聚焦确认问题",
    )
    positions = []
    for heading in ordered_sections:
        matches = [index for index, line in enumerate(expected_text.splitlines()) if line == heading]
        if len(matches) != 1:
            raise AssertionError(f"rolling PA expected fixture missing {heading!r}")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise AssertionError("rolling PA watch-only sections are out of order")

    status = markdown_section(expected_text, "## 运行状态")
    status_lines = [line for line in status.splitlines()[1:] if line.strip()]
    if status_lines != ["- 当前状态：待复核（内部限定：watch-only）"]:
        raise AssertionError(
            "watch-only output must present 待复核 as the primary Chinese status"
        )
    if re.search(r"(?m)^- mode:", expected_text):
        raise AssertionError("English mode must not be the primary user status")

    actions = markdown_section(expected_text, "## 可执行下一步")
    action_lines = [line for line in actions.splitlines()[1:] if line.strip()]
    if action_lines != expected_actions:
        raise AssertionError(
            "formal-runtime-unavailable output must contain exactly the two allowed actions"
        )
    if "？" in actions or expected_text.count("？") != 1:
        raise AssertionError(
            "watch-only output must keep exactly one Chinese question mark in the focused question"
        )

    watch_only = markdown_section(expected_text, "## Watch-only 摘要")
    bullets = [line for line in watch_only.splitlines() if line.startswith("- ")]
    expected_bullets = [
        f"- {ticker}：仍是未确认的 watch ticker；不主张结构、方向或风险角色。"
        for ticker in ("DRAM", "SOXX", "QQQ")
    ]
    if bullets != expected_bullets:
        raise AssertionError(
            "watch-only summary must avoid unsupported ticker classification: "
            f"expected {expected_bullets!r}, got {bullets!r}"
        )
    question = markdown_section(expected_text, "## 聚焦确认问题")
    question_lines = [line for line in question.splitlines()[1:] if line.strip()]
    if len(question_lines) != 1 or question_lines[0].count("？") != 1:
        raise AssertionError("missing setup key must yield exactly one focused question")
    for term in ("DRAM", "SOXX", "QQQ", "trade_horizon", "instrument"):
        if term not in question_lines[0]:
            raise AssertionError(f"focused setup-key question missing {term!r}")


if __name__ == "__main__":
    sys.exit(main())
