#!/usr/bin/env python3
"""Verify the fixture-backed local MVP smoke contract."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "mvp_smoke_script": REPO / "scripts" / "verify-mvp.sh",
    "mvp_runbook": REPO / "docs" / "MVP_RUNBOOK.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "development": REPO / "docs" / "DEVELOPMENT.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "mvp_smoke_script": [
        "verify-plugin.sh",
        "runtime_health.py",
        "kvn_leaderboard.py import",
        "kvn_leaderboard.py show",
        "kvn_leaderboard.py query",
        "kvn_leaderboard.py changes",
        "intraday_scan.py",
        "position_daily_report.py",
        "verify_position_daily_report_selftest.py",
        "verify_intraday_scan_selftest.py",
        "verify_active_market_plan_fixture_contract.py",
        "No live broker reads",
    ],
    "mvp_runbook": [
        "# Local MVP Runbook",
        "fixture-backed local MVP",
        "bash scripts/verify-mvp.sh",
        "What This MVP Covers",
        "What This MVP Does Not Cover",
        "No live broker reads",
        "No real Codex automations",
        "No live market data",
        "New Chat Validation",
        "MVP Definition Of Done",
    ],
    "root_readme": [
        "Local MVP",
        "bash scripts/verify-mvp.sh",
        "fixture-backed",
    ],
    "plugin_readme": [
        "MVP smoke",
        "bash scripts/verify-mvp.sh",
    ],
    "development": [
        "MVP smoke",
        "scripts/verify-mvp.sh",
    ],
    "development_plan": [
        "Fixture-backed local MVP",
        "scripts/verify-mvp.sh",
    ],
    "roadmap": [
        "Fixture-backed local MVP",
        "scripts/verify-mvp.sh",
    ],
    "project_log": [
        "Fixture-backed local MVP",
        "scripts/verify-mvp.sh",
    ],
}

SPEC = ContractSpec(
    name="fixture-backed local MVP smoke",
    success_message="mvp smoke contract ok",
    failure_header="mvp smoke contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
