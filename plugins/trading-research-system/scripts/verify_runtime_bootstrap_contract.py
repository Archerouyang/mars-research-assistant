#!/usr/bin/env python3
"""Verify runtime bootstrap is documented and wired into local checks."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "bootstrap_script": ROOT / "scripts" / "bootstrap_runtime.py",
    "bootstrap_selftest": ROOT / "scripts" / "verify_runtime_bootstrap_selftest.py",
    "verify_plugin": REPO / "scripts" / "verify-plugin.sh",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "mvp_runbook": REPO / "docs" / "MVP_RUNBOOK.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "bootstrap_script": [
        "bootstrap private runtime",
        "TRADING_RESEARCH_RUNTIME_DIR",
        "--dry-run",
        "--overwrite",
        "--no-daily",
        "market-plan.md",
        "trading-profile.md",
        "ops-state.md",
        "updates",
        "momentum",
        "charts",
        "No live broker reads",
    ],
    "bootstrap_selftest": [
        "runtime bootstrap selftest ok",
        "--dry-run",
        "must not overwrite existing user files by default",
        "runtime_health.py",
    ],
    "verify_plugin": [
        "verify_runtime_bootstrap_selftest.py",
        "verify_runtime_bootstrap_contract.py",
    ],
    "root_readme": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
        "No live broker reads",
    ],
    "plugin_readme": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
    ],
    "mvp_runbook": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
    ],
    "development_plan": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
    ],
    "roadmap": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
    ],
    "project_log": [
        "Runtime bootstrap",
        "bootstrap_runtime.py",
    ],
}

SPEC = ContractSpec(
    name="runtime bootstrap",
    success_message="runtime bootstrap contract ok",
    failure_header="runtime bootstrap contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
