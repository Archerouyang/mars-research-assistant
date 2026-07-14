#!/usr/bin/env python3
"""Verify Active Market Plan automation prompt templates are wired."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
TEMPLATES = ROOT / "assets" / "templates"

FILES = {
    "automation_contract": ROOT / "skills" / "trading-research-system" / "references"
    / "automation-contract.md",
    "deep_update": TEMPLATES / "automation-active-plan-deep-update.md",
    "quick_update": TEMPLATES / "automation-active-plan-quick-update.md",
    "intraday_monitor": TEMPLATES / "automation-intraday-trigger-monitor.md",
    "post_market": TEMPLATES / "automation-post-market-review.md",
    "position_daily": TEMPLATES / "automation-position-daily-report.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "automation_contract": [
        "automation-active-plan-deep-update.md",
        "automation-active-plan-quick-update.md",
        "automation-intraday-trigger-monitor.md",
        "automation-post-market-review.md",
        "automation-position-daily-report.md",
        "Do not edit files without user confirmation",
        "Do not require a local `trades.csv`, Google Sheet, or durable broker CSV",
    ],
    "deep_update": [
        "Active Market Plan Deep Update Automation Prompt",
        "runtime health",
        "Trade Plan Preparation",
        "Cross-Section Candidate Pool",
        "Ask before writing runtime files",
        "Do not silently overwrite `market-plan.md`",
    ],
    "quick_update": [
        "Active Market Plan Quick Update Automation Prompt",
        "what changed",
        "Setup 状态",
        "triggered",
        "拟追加 update note",
        "No buy/sell instruction",
    ],
    "intraday_monitor": [
        "Intraday Trigger Monitor Automation Prompt",
        "Limit scope to prepared setups",
        "execution_check_required",
        "price contact alone",
        "Do not scan the entire market",
    ],
    "post_market": [
        "Post-Market Review Automation Prompt",
        "post-order",
        "post-exit",
        "明日队列",
        "Do not require Google Sheets",
    ],
    "position_daily": [
        "Position Daily Report Automation Prompt",
        "Source Order",
        "position_daily_report.py",
        "Do not place, modify, cancel, close, or approve orders",
    ],
    "roadmap": [
        "Active Plan automation prompts",
        "automation-active-plan-deep-update.md",
    ],
    "development_plan": [
        "Active Plan automation prompts",
        "automation-active-plan-deep-update.md",
    ],
}

SPEC = ContractSpec(
    name="active plan automation prompts",
    success_message="active plan automation contract ok",
    failure_header="active plan automation contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
