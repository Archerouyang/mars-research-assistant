#!/usr/bin/env python3
"""Verify Longbridge Terminal CLI adapter contract."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "adapter_script": ROOT / "scripts" / "longbridge_cli_adapter.py",
    "selftest": ROOT / "scripts" / "verify_longbridge_cli_adapter_selftest.py",
    "fixture_input": ROOT / "assets" / "fixtures" / "input" / "longbridge-portfolio-cli-2026-06-24.json",
    "fixture_expected": ROOT / "assets" / "fixtures" / "expected" / "longbridge-cli-adapter-2026-06-24.csv",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "runtime_health": ROOT / "scripts" / "runtime_health.py",
    "runtime_health_reference": REFERENCES / "runtime-health.md",
    "longbridge_reference": REFERENCES / "longbridge-skill-adapter.md",
    "broker_contract": REFERENCES / "broker-data-contract.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "adapter_script": [
        "Longbridge CLI",
        "portfolio_snapshot.csv",
        "--portfolio-json",
        "--output",
        "--as-of",
        "No live broker reads",
        "No order actions",
        "cash_balances",
        "holdings",
        "CSV_SCHEMAS",
    ],
    "selftest": [
        "longbridge-portfolio-cli-2026-06-24.json",
        "longbridge-cli-adapter-2026-06-24.csv",
        "No live broker reads",
        "No order actions",
        "Longbridge CLI adapter selftest ok",
    ],
    "fixture_input": ["overview", "cash_balances", "holdings", "CRDO.US", "QQQ.US"],
    "contract_suite": [
        "verify_longbridge_cli_adapter_selftest.py",
        "verify_longbridge_cli_adapter_contract.py",
    ],
    "runtime_health": [
        "longbridge_terminal_cli",
        "Longbridge Terminal CLI",
        "--source-capability",
    ],
    "runtime_health_reference": [
        "Longbridge Terminal CLI",
        "longbridge_terminal_cli",
        "--source-capability longbridge_terminal_cli=available",
    ],
    "longbridge_reference": [
        "longbridge_terminal_cli",
        "Longbridge Terminal CLI",
        "longbridge_cli_adapter.py",
        "No live broker reads",
        "No order actions",
        "FX-convert",
        "must not run `longbridge order buy`",
    ],
    "broker_contract": [
        "Longbridge Terminal CLI",
        "longbridge_cli_adapter.py",
        "portfolio --format json",
        "No live broker reads",
        "FX conversion",
        "order actions",
    ],
    "root_readme": ["Longbridge Terminal CLI", "longbridge_cli_adapter.py", "No live broker reads"],
    "plugin_readme": ["Longbridge Terminal CLI", "longbridge_cli_adapter.py", "No live broker reads"],
    "roadmap": ["Longbridge Terminal CLI adapter", "longbridge_cli_adapter.py"],
    "development_plan": ["Longbridge Terminal CLI adapter", "longbridge_cli_adapter.py"],
    "project_log": ["Longbridge Terminal CLI adapter", "longbridge_cli_adapter.py"],
}

SPEC = ContractSpec(
    name="Longbridge Terminal CLI adapter",
    success_message="Longbridge Terminal CLI adapter contract ok",
    failure_header="Longbridge Terminal CLI adapter contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED.get(key, ()),
            csv_header=CSV_SCHEMAS["portfolio_snapshot.csv"] if key == "fixture_expected" else None,
            csv_rows_match_header=key == "fixture_expected",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
