#!/usr/bin/env python3
"""Verify Longbridge macrodata adapter contract."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "adapter_script": ROOT / "scripts" / "longbridge_macrodata_adapter.py",
    "selftest": ROOT / "scripts" / "verify_longbridge_macrodata_adapter_selftest.py",
    "fixture_input": ROOT / "assets" / "fixtures" / "input" / "longbridge-macrodata-2026-06-24.json",
    "fixture_expected": ROOT / "assets" / "fixtures" / "expected" / "longbridge-macro-panel-2026-06-24.json",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "longbridge_reference": REFERENCES / "longbridge-skill-adapter.md",
    "macro_data_contract": REFERENCES / "macro-data-source-contract.md",
    "runtime_health_reference": REFERENCES / "runtime-health.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "adapter_script": [
        "Longbridge macrodata",
        "macro-panel.json",
        "--macrodata-json",
        "--output",
        "--as-of",
        "No live macrodata reads",
        "not a broker account source",
        "No order actions",
        "10Y",
        "30Y",
        "HYG/LQD",
        "DXY",
        "Oil",
        "Gold",
        "liquidity",
    ],
    "selftest": [
        "longbridge-macrodata-2026-06-24.json",
        "longbridge-macro-panel-2026-06-24.json",
        "No live macrodata reads",
        "not a broker account source",
        "No order actions",
        "Longbridge macrodata adapter selftest ok",
    ],
    "fixture_input": [
        "Longbridge macrodata fixture",
        "10Y",
        "30Y",
        "HYG/LQD",
        "DXY",
        "Oil",
        "Gold",
        "liquidity",
    ],
    "fixture_expected": [
        "source_capability",
        "longbridge_macrodata",
        "strategy_posture",
        "balanced",
        "missing_indicators",
        "source_notes",
        "not a broker account source",
    ],
    "contract_suite": [
        "verify_longbridge_macrodata_adapter_selftest.py",
        "verify_longbridge_macrodata_adapter_contract.py",
    ],
    "longbridge_reference": [
        "Macrodata Adapter",
        "longbridge_macrodata_adapter.py",
        "macro-panel.json",
        "No live macrodata reads",
        "not a broker account source",
        "No order actions",
    ],
    "macro_data_contract": [
        "longbridge_macrodata_adapter.py",
        "macro-panel.json",
        "10Y",
        "30Y",
        "HYG/LQD",
        "DXY",
        "Oil",
        "Gold",
        "liquidity",
    ],
    "runtime_health_reference": ["longbridge_macrodata", "Longbridge macrodata"],
    "root_readme": ["longbridge_macrodata_adapter.py", "macro-panel.json", "No live macrodata reads"],
    "plugin_readme": ["longbridge_macrodata_adapter.py", "macro-panel.json", "No live macrodata reads"],
    "roadmap": ["Longbridge macrodata adapter", "longbridge_macrodata_adapter.py", "macro-panel.json"],
    "development_plan": ["Longbridge macrodata adapter", "longbridge_macrodata_adapter.py", "macro-panel.json"],
    "project_log": ["Longbridge macrodata adapter", "longbridge_macrodata_adapter.py", "macro-panel.json"],
}

SPEC = ContractSpec(
    name="Longbridge macrodata adapter",
    success_message="Longbridge macrodata adapter contract ok",
    failure_header="Longbridge macrodata adapter contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
