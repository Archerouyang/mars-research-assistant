#!/usr/bin/env python3
"""Verify runtime health is documented and executable."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "script": ROOT / "scripts" / "runtime_health.py",
    "selftest": ROOT / "scripts" / "verify_runtime_health_selftest.py",
    "reference": ROOT / "skills" / "trading-research" / "references" / "runtime-health.md",
    "router": ROOT / "skills" / "trading-research" / "SKILL.md",
    "automation": ROOT / "skills" / "trading-research" / "references" / "automation-contract.md",
    "plugin_readme": ROOT / "README.md",
    "design": REPO / "docs" / "PLUGIN_DESIGN.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "script": [
        "available",
        "missing",
        "stale",
        "unauthorized",
        "not_installed",
        "current_mode",
        "broker_source_health",
        "longbridge_broker_source",
        "ibkr_broker_source",
        "manual_snapshot_source",
        "live read-only",
        "manual snapshot",
        "dry-run",
        "No file contents were read.",
        "--broker-source",
        "--stale-after-days",
    ],
    "selftest": [
        "PRIVATE MARKET PLAN SECRET",
        "runtime health selftest ok",
        "broker_sources",
        "unauthorized",
        "current_mode",
        "longbridge_broker_source",
        "ibkr_broker_source",
        "manual_snapshot_source",
        "live read-only",
    ],
    "reference": [
        "# Runtime Health",
        "available",
        "missing",
        "stale",
        "unauthorized",
        "not_installed",
        "current_mode",
        "broker_source_health",
        "Longbridge",
        "IBKR",
        "Manual snapshot",
        "live read-only",
        "manual snapshot",
        "dry-run",
        "Do not read or copy private file contents",
        "runtime_health.py",
        "market-plan.md",
        "trading-profile.md",
        "kvn.sqlite",
        "broker_sources",
    ],
    "router": [
        "runtime-health.md",
        "runtime_health.py",
    ],
    "automation": [
        "runtime_health.py",
        "available",
        "missing",
        "stale",
        "unauthorized",
    ],
    "plugin_readme": [
        "runtime_health.py",
        "--format json",
        "current_mode",
        "broker_source_health",
    ],
    "design": [
        "Runtime health reports only status categories",
        "available, missing",
        "stale, or unauthorized",
    ],
    "development_plan": [
        "runtime health contract",
        "available/missing/stale/unauthorized",
    ],
}


SPEC = ContractSpec(
    name="runtime health",
    success_message="runtime health contract ok",
    failure_header="runtime health contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
