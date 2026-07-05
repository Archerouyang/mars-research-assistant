#!/usr/bin/env python3
"""Verify Daily Ops automation setup checklist contract."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
TEMPLATES = ROOT / "assets" / "templates"
FIXTURES = ROOT / "assets" / "fixtures"

FILES = {
    "automation_contract": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "automation-contract.md",
    "setup_template": TEMPLATES / "automation-setup-checklist.md",
    "setup_input": FIXTURES / "input" / "automation-setup-request-daily-ops.md",
    "setup_expected": FIXTURES / "expected" / "automation-setup-checklist-daily-ops.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "automation_contract": [
        "Automation Setup Checklist",
        "automation-setup-checklist.md",
        "Do not create real Codex automations until every required confirmation",
        "Daily Ops thread",
        "runtime_dir",
        "Longbridge macrodata",
        "Seeking Alpha",
        "read-only broker",
    ],
    "setup_template": [
        "Daily Ops Automation Setup Checklist",
        "Required Confirmations",
        "Daily Ops thread",
        "timezone",
        "runtime_dir",
        "enabled automations",
        "allowed sources",
        "Longbridge macrodata",
        "IBKR connector",
        "Seeking Alpha",
        "runtime write policy",
        "read-only broker",
        "no broker write actions",
        "no paywall bypass",
        "Automation Setup Summary",
        "Missing Decisions",
        "Draft Automation Plan",
        "Do not create real Codex automations",
    ],
    "setup_input": [
        "Daily Ops",
        "weekly deep update",
        "weekday premarket quick update",
        "intraday trigger monitor",
        "post-market review",
        "position daily report",
        "macro/industry/news research monitor",
        "Longbridge macrodata",
        "IBKR",
        "Longbridge",
        "Seeking Alpha",
        "read-only",
    ],
    "setup_expected": [
        "Automation Setup Summary",
        "Confirmed Configuration",
        "Missing Decisions",
        "Draft Automation Plan",
        "Safety Boundaries",
        "Next Action",
        "Asia/Shanghai",
        "~/Documents/dailytrades-runtime",
        "Do not create real Codex automations yet",
        "no broker write actions",
        "no paywall bypass",
    ],
    "roadmap": [
        "Automation setup checklist",
        "automation-setup-checklist.md",
        "real Codex automations still require setup confirmation",
    ],
    "development_plan": [
        "Automation setup checklist",
        "automation-setup-checklist.md",
        "real Codex automations still require setup confirmation",
    ],
    "project_log": [
        "automation-setup-checklist.md",
        "Daily Ops automation setup checklist",
        "before creating real Codex automations",
    ],
}

SPEC = ContractSpec(
    name="Daily Ops automation setup checklist",
    success_message="automation setup contract ok",
    failure_header="automation setup contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
