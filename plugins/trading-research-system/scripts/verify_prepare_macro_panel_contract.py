#!/usr/bin/env python3
"""Verify macro-panel preparation contract."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "script": ROOT / "scripts" / "prepare_macro_panel.py",
    "selftest": ROOT / "scripts" / "verify_prepare_macro_panel_selftest.py",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "longbridge_reference": REFERENCES / "longbridge-skill-adapter.md",
    "macro_data_contract": REFERENCES / "macro-data-source-contract.md",
    "daily_ops_reference": REFERENCES / "daily-ops-orchestrator.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "script": [
        "prepare_macro_panel.py",
        "macro-panel.json",
        "--macrodata-json",
        "macrodata JSON was not supplied",
        "No live macrodata reads",
        "not a broker account source",
        "No order actions",
        "kept existing",
        "--overwrite",
    ],
    "selftest": [
        "longbridge-macrodata-2026-06-24.json",
        "runtime_health.py",
        "macrodata JSON was not supplied",
        "kept existing",
        "prepare macro panel selftest ok",
    ],
    "contract_suite": [
        "verify_prepare_macro_panel_selftest.py",
        "verify_prepare_macro_panel_contract.py",
    ],
    "longbridge_reference": ["prepare_macro_panel.py", "macro-panel.json", "--macrodata-json"],
    "macro_data_contract": ["prepare_macro_panel.py", "macro-panel.json", "No live macrodata reads"],
    "daily_ops_reference": ["prepare_macro_panel.py", "macro-panel.json"],
    "root_readme": ["prepare_macro_panel.py", "macro-panel.json", "--macrodata-json"],
    "plugin_readme": ["prepare_macro_panel.py", "macro-panel.json", "--macrodata-json"],
    "roadmap": ["Macro panel runtime preparation", "prepare_macro_panel.py", "macro-panel.json"],
    "development_plan": ["Macro panel runtime preparation", "prepare_macro_panel.py", "macro-panel.json"],
    "project_log": ["Macro panel runtime preparation", "prepare_macro_panel.py", "macro-panel.json"],
}

SPEC = ContractSpec(
    name="Macro panel runtime preparation",
    success_message="prepare macro panel contract ok",
    failure_header="prepare macro panel contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
