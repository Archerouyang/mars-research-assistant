#!/usr/bin/env python3
"""Verify the local 1.0 acceptance plan stays user-workflow focused."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


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
        "security-master-check --require-training-ready",
        "production-activation.json",
        "full eligible universe",
        "without `--allow-uat`",
        "refuses UAT, stale, unactivated, current-only",
        "2026-07-08",
        "2026-07-12",
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
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
