#!/usr/bin/env python3
"""Verify workflow-level visual trigger behavior is documented and enforced."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "visual_trigger_reference": REFERENCES / "visual-trigger-policy.md",
    "output_templates": REFERENCES / "output-templates.md",
    "daily_ops": REFERENCES / "daily-ops-orchestrator.md",
    "price_action": REFERENCES / "price-action-timing.md",
    "intraday_reference": REFERENCES / "intraday-setup-scan.md",
    "position_reference": REFERENCES / "position-daily-report.md",
    "daily_skill": ROOT / "skills" / "daily-market-tracking" / "SKILL.md",
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "intraday_skill": ROOT / "skills" / "intraday-setup-scan" / "SKILL.md",
    "position_template": ROOT / "assets" / "templates" / "position-daily-report.md",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "visual_trigger_reference": [
        "# Visual Trigger Policy",
        "视觉触发矩阵",
        "PA Scenario Board",
        "Macro Regime Mini-Panel",
        "Position Risk Visual",
        "用户直接要求图表",
        "关键点位接近",
        "approaching",
        "triggered",
        "invalidated",
        "needs_review",
        "macro-panel.json",
        "portfolio_snapshot.csv",
        "chart_artifact.py",
        "macro_regime_artifact.py",
        ".scratch/visual-artifacts",
        "No broker write actions",
        "Do Not Trigger",
    ],
    "output_templates": [
        "visual-trigger-policy.md",
        "视觉触发矩阵",
        "PA Scenario Board",
        "Macro Regime Mini-Panel",
    ],
    "daily_ops": [
        "visual-trigger-policy.md",
        "宏观图触发判断",
        "macro-panel.json",
        "portfolio_snapshot.csv",
    ],
    "price_action": [
        "visual-trigger-policy.md",
        "PA Scenario Board",
        "关键点位接近",
    ],
    "intraday_reference": [
        "visual-trigger-policy.md",
        "approaching",
        "triggered",
        "invalidated",
        "needs_review",
        "PA Scenario Board",
    ],
    "position_reference": [
        "visual-trigger-policy.md",
        "Position Risk Visual",
        "portfolio_snapshot.csv",
    ],
    "daily_skill": [
        "visual-trigger-policy.md",
        "Macro Regime Mini-Panel",
        "macro-panel.json",
    ],
    "weekly_skill": [
        "visual-trigger-policy.md",
        "Macro Regime Mini-Panel",
        "PA Scenario Board",
    ],
    "intraday_skill": [
        "visual-trigger-policy.md",
        "PA Scenario Board",
    ],
    "position_template": [
        "Position Risk Visual",
        "visual trigger",
    ],
    "contract_suite": [
        "visual-trigger",
        "verify_visual_trigger_contract.py",
    ],
    "roadmap": [
        "Visual Trigger Policy",
        "visual-trigger-policy.md",
    ],
    "development_plan": [
        "Visual Trigger Policy",
        "visual-trigger-policy.md",
    ],
    "project_log": [
        "Visual Trigger Policy",
        "visual-trigger-policy.md",
    ],
}

SPEC = ContractSpec(
    name="visual trigger policy",
    success_message="visual trigger contract ok",
    failure_header="visual trigger contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
