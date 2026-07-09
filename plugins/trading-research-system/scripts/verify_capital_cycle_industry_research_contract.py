#!/usr/bin/env python3
"""Verify supply-side capital-cycle industry research is part of planning."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "capital_cycle_reference": REFERENCES / "capital-cycle-industry-research.md",
    "macro_equity_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "equity_screening": REFERENCES / "equity-screening.md",
    "research_report_intake": REFERENCES / "research-report-intake.md",
    "macro_industry_monitor": ROOT / "assets" / "templates" / "automation-macro-industry-research-monitor.md",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "capital_cycle_reference": [
        "# Capital Cycle Industry Research",
        "supply-side",
        "capital cycle",
        "Flood",
        "Boom",
        "Collapse",
        "Inheritance",
        "demand can be noisy",
        "capital committed upfront",
        "capex",
        "capacity additions",
        "utilization",
        "pricing power",
        "vendor financing",
        "circular financing",
        "depreciation",
        "AI infrastructure",
        "hyperscaler",
        "data center",
        "GPU",
        "memory",
        "optical networking",
        "power",
        "Primary Verification Queue",
        "not a setup trigger",
    ],
    "macro_equity_skill": [
        "capital-cycle-industry-research.md",
        "Supply-Side Cycle Check",
        "Industry/Sector Strength",
    ],
    "weekly_skill": [
        "capital-cycle-industry-research.md",
        "Supply-Side Cycle Check",
        "AI infrastructure",
    ],
    "equity_screening": [
        "Capital Cycle Industry Research",
        "supply-side",
        "capital intensity",
        "capacity additions",
        "pricing power",
    ],
    "research_report_intake": [
        "capital-cycle-industry-research.md",
        "video",
        "podcast",
        "S3 research / opinion",
        "Primary Verification Queue",
    ],
    "macro_industry_monitor": [
        "capital-cycle-industry-research.md",
        "capex",
        "vendor financing",
        "AI infrastructure",
    ],
    "contract_suite": [
        "capital-cycle-industry-research",
        "verify_capital_cycle_industry_research_contract.py",
    ],
    "roadmap": [
        "Capital Cycle Industry Research",
        "capital-cycle-industry-research.md",
    ],
    "project_log": [
        "Capital Cycle Industry Research",
        "capital-cycle-industry-research.md",
    ],
}

SPEC = ContractSpec(
    name="capital cycle industry research",
    success_message="capital cycle industry research contract ok",
    failure_header="capital cycle industry research contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
