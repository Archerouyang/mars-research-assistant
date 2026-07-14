#!/usr/bin/env python3
"""Verify the weekly outlook output contract stays decision-oriented."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-weekly-trading-plan.md",
    "output": ROOT / "skills" / "trading-research-system" / "references" / "output-templates.md",
    "template": ROOT / "assets" / "templates" / "weekly-plan.md",
    "fixture": ROOT / "assets" / "fixtures" / "expected" / "weekly-outlook-2026-06-15.md",
}

REQUIRED_TERMS = {
    "skill": [
        "信源优先级",
        "宏观/利率",
        "政策/新闻",
        "对当前持仓的总体影响",
        "事件重要性排序",
        "策略姿态建议",
        "当周重点财报",
        "宏观/政策/新闻时间线",
        "特朗普/白宫公开讲话与政策风险",
        "对现有持仓计划的影响",
        "对新增持仓计划的影响",
        "下周事件预览",
        "需要用户决策的事项",
        "candidate（候选，只表示值得继续观察，不代表可以交易）",
        "P0",
        "P1",
        "P2",
    ],
    "output": [
        "信源优先级",
        "本周真正重要的 3 个变量",
        "宏观/利率",
        "政策/新闻",
        "对当前持仓的总体影响",
        "事件重要性排序",
        "策略姿态建议",
        "当周重点财报",
        "特朗普/白宫公开讲话与政策风险",
        "对现有持仓计划的影响",
        "对新增持仓计划的影响",
        "下周事件预览",
        "需要用户决策的事项",
    ],
    "template": [
        "Source Priority",
        "S4 social / rumor / unsourced commentary",
        "Current Holding Impact",
        "Event Importance Ranking",
        "Strategy Posture",
        "Key Earnings This Week",
        "Macro / Rates",
        "Policy / News",
        "Macro / Policy / News Timeline",
        "Next Week Preview",
        "Trump / White House Public Remarks And Policy Risk",
        "Existing Holding Plan Impact",
        "New Position Plan Impact",
        "User Decisions Needed",
    ],
    "fixture": [
        "信源优先级",
        "S4 social / rumor / unsourced commentary",
        "宏观/利率",
        "政策/新闻",
        "策略姿态建议",
        "当周重点财报",
        "防御",
        "平衡",
        "高 beta 动量",
        "FOMC",
        "SEP",
        "零售销售",
        "初请失业金",
        "Philadelphia Fed",
        "Juneteenth",
        "10Y",
        "4.5%",
        "伊朗",
        "霍尔木兹",
        "oil",
        "tariffs",
        "Fed independence",
        "QQQ",
        "VOO",
        "DRAM",
        "SOXX",
    ],
}

REQUIRED_HEADINGS = {
    "output": [
        "## 结论",
        "## 本周真正重要的 3 个变量",
        "## 信源优先级",
        "## 宏观/利率",
        "## 政策/新闻",
        "## 对当前持仓的总体影响",
        "## 策略姿态建议",
        "## 当周重点财报",
        "## 事件重要性排序",
        "## 宏观/政策/新闻时间线",
        "## 下周事件预览",
        "## 特朗普/白宫公开讲话与政策风险",
        "## 对现有持仓计划的影响",
        "## 对新增持仓计划的影响",
        "## 组合风险",
        "## 需要用户决策的事项",
    ],
    "template": [
        "## Source Priority",
        "## Current Holding Impact",
        "## Strategy Posture",
        "## Key Earnings This Week",
        "## Macro / Rates",
        "## Policy / News",
        "## Event Importance Ranking",
        "## Macro / Policy / News Timeline",
        "## Next Week Preview",
        "## Trump / White House Public Remarks And Policy Risk",
        "## Existing Holding Plan Impact",
        "## New Position Plan Impact",
        "## User Decisions Needed",
    ],
    "fixture": [
        "## 结论",
        "## 本周真正重要的 3 个变量",
        "## 信源优先级",
        "## 宏观/利率",
        "## 政策/新闻",
        "## 对当前持仓的总体影响",
        "## 策略姿态建议",
        "## 当周重点财报",
        "## 事件重要性排序",
        "## 宏观/政策/新闻时间线",
        "## 下周事件预览",
        "## 特朗普/白宫公开讲话与政策风险",
        "## 对现有持仓计划的影响",
        "## 对新增持仓计划的影响",
        "## 组合风险",
        "## 需要用户决策的事项",
    ],
}

FORBIDDEN_UNEXPLAINED = [
    "candidate 升级",
    "active 升级",
    "triggered 升级",
]


SPEC = ContractSpec(
    name="weekly outlook",
    success_message="weekly outlook contract ok",
    files={
        name: FileContract(
            path=path,
            required_terms=REQUIRED_TERMS[name],
            required_headings=REQUIRED_HEADINGS.get(name, ()),
            forbidden_terms=FORBIDDEN_UNEXPLAINED,
            forbidden_label="forbidden unexplained status phrase",
        )
        for name, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
