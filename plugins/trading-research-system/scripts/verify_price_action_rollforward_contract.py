#!/usr/bin/env python3
"""Verify rolling price-action analysis has a stable user-facing shape."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

FILES = {
    "price_action_reference": PATHS.references / "price-action-timing.md",
    "output_templates": PATHS.references / "output-templates.md",
    "daily_tracking_skill": PATHS.skills / "trading-research-system" / "references" / "workflow-daily-market-tracking.md",
    "daily_tracking_template": PATHS.templates / "daily-market-tracking.md",
    "script": PATHS.scripts / "price_action_rollforward.py",
    "selftest": PATHS.scripts / "verify_price_action_rollforward_selftest.py",
    "plugin_readme": PATHS.root / "README.md",
    "development_plan": PATHS.repo / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": PATHS.repo / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "price_action_reference": [
        "Rolling Price Action Update",
        "上次分析对照",
        "主分析时间框架",
        "辅助时间框架",
        "走势强弱参考点位",
        "加仓/减仓/暂停区",
        "本周事件映射",
        "支撑/压力",
        "成本/买入记录",
        "比例式加减仓",
        "点位所属时间框架",
        "price_action_rollforward.py",
        "OHLCV",
        "does not fetch market data",
        "medium-term swing",
        "position reassessment",
        "automatically attach",
        "complete setup key",
        "Price Action Watch-only",
        "do not normalize",
        "before opening or parsing",
        "non-JSON OHLCV",
        "--ohlcv-json` may be omitted",
        "missing-data failure",
    ],
    "output_templates": [
        "## Price Action 滚动盘面分析",
        "## 时间框架声明",
        "## 上次分析对照",
        "## 走势强弱参考点位",
        "## 加仓/减仓/暂停区",
        "## 本周事件映射",
        "支撑/压力",
        "成本/买入记录",
        "比例式加减仓",
        "点位所属时间框架",
    ],
    "daily_tracking_skill": [
        "Price Action 滚动盘面分析",
        "上次分析对照",
        "主分析时间框架",
        "辅助时间框架",
        "走势强弱参考点位",
        "加仓/减仓/暂停区",
        "本周事件映射",
        "支撑/压力",
        "成本/买入记录",
        "比例式加减仓",
        "点位所属时间框架",
        "price_action_rollforward.py",
        "OHLCV",
    ],
    "daily_tracking_template": [
        "## Price Action 滚动盘面分析",
        "## 时间框架声明",
        "## 上次分析对照",
        "## 走势强弱参考点位",
        "## 加仓/减仓/暂停区",
        "## 本周事件映射",
        "支撑/压力",
        "成本/买入记录",
        "比例式加减仓",
        "点位所属时间框架",
    ],
    "script": [
        "Generate a rolling price-action note",
        "--ohlcv-json",
        "Explicitly confirmed ticker required by the complete setup key",
        "--main-timeframe",
        "--aux-timeframe",
        "--trade-horizon",
        "--instrument",
        "--analysis-intent",
        "--ohlcv-status",
        "--display-output",
        "PA Scenario Board",
        "missing_setup_key_fields",
        "Price Action Watch-only",
        "setup key incomplete",
        "OHLCV 未读取：complete setup key missing",
        "complete setup key requires --ohlcv-json authorized or fixture OHLCV data",
        "This is decision support only",
        "not a buy/sell instruction",
        "No live broker reads",
        "does not fetch market data",
        "点位所属时间框架",
        "比例式加减仓",
    ],
    "selftest": [
        "price action rollforward selftest ok",
        "chart-ohlcv-qqq-sample.json",
        "主分析时间框架 | 1D",
        "trigger zone: add only after confirmation",
        "prior high / TP/rebalance watch",
        "position_reassessment",
        "PA Scenario Board",
        "missing_cases",
        "trade_horizon",
        "ticker",
        "instrument",
        "must not generate a PA Scenario Board",
        "invalid-ohlcv.txt",
        "this is not JSON and must not be read",
        "missing setup key must not read invalid OHLCV or create an artifact",
        "omitted-ohlcv-watch-only.md",
        "incomplete setup key with omitted OHLCV must not create an artifact",
        "complete setup key without OHLCV must fail clearly",
        "--ticker help must describe the explicit pre-payload setup-key requirement",
        "defaults to JSON symbol",
    ],
    "plugin_readme": [
        "price_action_rollforward.py",
        "OHLCV",
        "rolling price-action",
    ],
    "development_plan": [
        "PA OHLCV rollforward",
        "price_action_rollforward.py",
    ],
    "project_log": [
        "PA OHLCV rollforward",
        "price_action_rollforward.py",
    ],
}

SPEC = ContractSpec(
    name="price action rollforward",
    success_message="price action rollforward contract ok",
    failure_header="price action rollforward contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
