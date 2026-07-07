#!/usr/bin/env python3
"""Verify rolling price-action analysis has a stable user-facing shape."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

FILES = {
    "price_action_reference": PATHS.references / "price-action-timing.md",
    "output_templates": PATHS.references / "output-templates.md",
    "daily_tracking_skill": PATHS.skills / "daily-market-tracking" / "SKILL.md",
    "daily_tracking_template": PATHS.templates / "daily-market-tracking.md",
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
