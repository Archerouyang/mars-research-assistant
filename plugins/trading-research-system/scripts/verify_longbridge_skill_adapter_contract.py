#!/usr/bin/env python3
"""Verify Longbridge skill adapter readiness contract."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "context": REPO / "CONTEXT.md",
    "adapter_reference": REFERENCES / "longbridge-skill-adapter.md",
    "runtime_health": REFERENCES / "runtime-health.md",
    "broker_contract": REFERENCES / "broker-data-contract.md",
    "macro_contract": REFERENCES / "macro-data-source-contract.md",
    "daily_ops": REFERENCES / "daily-ops-orchestrator.md",
    "runtime_health_script": ROOT / "scripts" / "runtime_health.py",
    "runtime_health_selftest": ROOT / "scripts" / "verify_runtime_health_selftest.py",
    "runtime_health_contract": ROOT / "scripts" / "verify_runtime_health_contract.py",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "context": [
        "Longbridge Skill Adapter",
        "longbridge_broker_skill",
        "longbridge_macrodata",
        "source_capability_health",
    ],
    "adapter_reference": [
        "# Longbridge Skill Adapter",
        "Longbridge broker skill",
        "Longbridge macrodata",
        "longbridge_broker_skill",
        "longbridge_macrodata",
        "source_capability_health",
        "not visible in the current Codex session",
        "当前 chat 未暴露 Longbridge skill capability",
        "portfolio_snapshot.csv",
        "broker_executions.csv",
        "broker_orders.csv",
        "macro-panel.json",
        "10Y",
        "30Y",
        "HYG/LQD",
        "DXY",
        "Oil",
        "Gold",
        "liquidity",
        "read-only",
        "must not create",
    ],
    "runtime_health": [
        "source_capability_health",
        "Longbridge broker skill",
        "Longbridge macrodata",
        "--source-capability longbridge_macrodata=available",
    ],
    "broker_contract": [
        "Longbridge skill/plugin adapter",
        "Longbridge `macrodata` is a separate macro-data source",
    ],
    "macro_contract": [
        "Longbridge macrodata",
        "Macro Data Source Health",
        "actual macro values",
    ],
    "daily_ops": [
        "source_capability_health",
        "Longbridge broker skill",
        "Longbridge macrodata",
        "当前 chat 未暴露 Longbridge skill",
    ],
    "runtime_health_script": [
        "source_capability_health",
        "--source-capability",
        "longbridge_broker_skill",
        "longbridge_macrodata",
        "ibkr_connector",
        "manual_snapshot",
        "not visible in this Codex session",
    ],
    "runtime_health_selftest": [
        "source_capability_health",
        "longbridge_broker_skill",
        "longbridge_macrodata",
        "ibkr_connector",
        "longbridge_macrodata=not_installed",
    ],
    "runtime_health_contract": [
        "source_capability_health",
        "longbridge_broker_skill",
        "longbridge_macrodata",
    ],
    "plugin_readme": [
        "Longbridge skill adapter",
        "source_capability_health",
        "longbridge_macrodata",
    ],
    "roadmap": [
        "Longbridge skill adapter",
        "Longbridge `macrodata` adapter",
    ],
    "development_plan": [
        "Longbridge Skill Adapter",
        "source_capability_health",
    ],
    "project_log": [
        "Longbridge Skill Adapter",
        "source_capability_health",
    ],
}

SPEC = ContractSpec(
    name="Longbridge skill adapter",
    success_message="longbridge skill adapter contract ok",
    failure_header="longbridge skill adapter contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
