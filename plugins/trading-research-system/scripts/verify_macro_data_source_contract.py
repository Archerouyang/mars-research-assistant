#!/usr/bin/env python3
"""Verify macro data source selection and output contract."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references
TEMPLATES = PATHS.templates

FILES = {
    "context": REPO / "CONTEXT.md",
    "macro_data_contract": REFERENCES / "macro-data-source-contract.md",
    "macro_policy_filter": REFERENCES / "macro-policy-filter.md",
    "output_templates": REFERENCES / "output-templates.md",
    "router_skill": ROOT / "skills" / "trading-research-system" / "SKILL.md",
    "daily_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-daily-market-tracking.md",
    "weekly_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-weekly-trading-plan.md",
    "macro_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-macro-equity-research.md",
    "daily_template": TEMPLATES / "daily-market-tracking.md",
    "weekly_template": TEMPLATES / "weekly-plan.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "context": [
        "Macro Data Source Contract",
        "Longbridge Macrodata Source",
        "Longbridge macrodata",
        "IBKR 行情数据",
        "官方来源 fallback",
    ],
    "macro_data_contract": [
        "# Macro Data Source Contract",
        "Macro Data Source Health",
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "preferred S1 source for macro values",
        "IBKR market data",
        "price and OHLCV transmission",
        "official source fallback",
        "S0 official",
        "10Y",
        "30Y",
        "HYG/LQD",
        "DXY",
        "Oil",
        "Gold",
        "策略姿态",
        "high beta momentum",
        "balanced",
        "defensive",
        "数据时间戳",
        "Do not claim macro analysis if no actual macro values were read",
    ],
    "macro_policy_filter": [
        "Macro Data Source Contract",
        "Longbridge macrodata is the preferred S1 source for macro values",
        "IBKR market data is price and OHLCV transmission",
        "official source fallback",
        "宏观数据来源状态",
        "实际宏观指标读数",
    ],
    "output_templates": [
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
        "当前值",
        "近5日/20日变化",
        "阈值",
        "对策略姿态影响",
    ],
    "router_skill": [
        "macro-data-source-contract.md",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
    ],
    "daily_skill": [
        "macro-data-source-contract.md",
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
        "Do not claim macro analysis if no actual macro values were read",
    ],
    "weekly_skill": [
        "macro-data-source-contract.md",
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
    ],
    "macro_skill": [
        "macro-data-source-contract.md",
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
    ],
    "daily_template": [
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
        "策略姿态",
        "数据时间戳",
    ],
    "weekly_template": [
        "宏观数据来源状态",
        "实际宏观指标读数",
        "Longbridge macrodata",
        "IBKR market data",
        "official source fallback",
        "策略姿态",
    ],
    "roadmap": [
        "Macro Data Source Contract",
        "Longbridge macrodata",
        "actual macro indicator reads",
    ],
    "development_plan": [
        "Macro Data Source Contract",
        "Longbridge macrodata",
        "actual macro indicator reads",
    ],
    "project_log": [
        "Macro Data Source Contract",
        "Longbridge macrodata",
        "actual macro indicator reads",
    ],
}

SPEC = ContractSpec(
    name="macro data source",
    success_message="macro data source contract ok",
    failure_header="macro data source contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
