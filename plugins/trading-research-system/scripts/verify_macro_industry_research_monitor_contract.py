#!/usr/bin/env python3
"""Verify the scheduled macro/industry research monitor contract is wired."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
TEMPLATES = PATHS.templates
FIXTURES = PATHS.fixtures

FILES = {
    "automation_contract": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "automation-contract.md",
    "template": TEMPLATES / "automation-macro-industry-research-monitor.md",
    "input_focus": FIXTURES / "input" / "macro-industry-monitor-focus-2026-07-06.md",
    "expected": FIXTURES / "expected" / "macro-industry-monitor-2026-07-06.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "automation_contract": [
        "macro_industry_research_monitor",
        "automation-macro-industry-research-monitor.md",
        "weekly P0/P1 focus variables",
        "public/authorized sources",
        "without bypassing paywalls",
    ],
    "template": [
        "Macro / Industry Research Monitor Automation Prompt",
        "weekly P0/P1 focus variables",
        "Source Priority",
        "Query Generation",
        "Research Report Intake",
        "Trade Plan Preparation",
        "Verification Queue",
        "Active Market Plan impact",
        "Do not bypass paywalls",
        "Do not promote reports directly into setups",
    ],
    "input_focus": [
        "Weekly Focus Fixture",
        "Fed minutes",
        "ISM Services",
        "TSMC monthly revenue",
        "AI compute / custom chip",
        "Memory/DRAM/NAND",
        "MU/MUU/DRAM",
        "TSMX",
        "GLW",
    ],
    "expected": [
        "## 结论",
        "## 重点变化",
        "## 信源优先级",
        "## 研报/资料线索",
        "## Verification Queue",
        "## Active Market Plan impact",
        "## 需要用户决策",
        "FOMC minutes",
        "TSMC June revenue",
        "AI hardware",
        "DRAM pricing",
        "不能直接升级为 setup",
    ],
    "roadmap": [
        "Scheduled macro/industry research monitor",
        "automation-macro-industry-research-monitor.md",
        "macro-industry-monitor-2026-07-06.md",
    ],
    "development_plan": [
        "Add scheduled macro/industry research monitor",
        "automation-macro-industry-research-monitor.md",
        "verify_macro_industry_research_monitor_contract.py",
    ],
}

SPEC = ContractSpec(
    name="macro industry research monitor",
    success_message="macro industry research monitor contract ok",
    failure_header="macro industry research monitor contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
