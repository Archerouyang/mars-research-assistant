#!/usr/bin/env python3
"""Verify saved IBKR connector adapter contract."""

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
    "adapter_script": ROOT / "scripts" / "ibkr_connector_adapter.py",
    "selftest": ROOT / "scripts" / "verify_ibkr_connector_adapter_selftest.py",
    "fixture_positions": ROOT / "assets" / "fixtures" / "input" / "ibkr-connector-positions-2026-06-24.json",
    "fixture_balances": ROOT / "assets" / "fixtures" / "input" / "ibkr-connector-balances-2026-06-24.json",
    "fixture_expected": ROOT / "assets" / "fixtures" / "expected" / "ibkr-connector-adapter-2026-06-24.csv",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "broker_contract": REFERENCES / "broker-data-contract.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "adapter_script": [
        "IBKR connector",
        "portfolio_snapshot.csv",
        "--positions-json",
        "--balances-json",
        "--output",
        "--as-of",
        "No live broker reads",
        "No order actions",
        "positions",
        "balances",
        "CSV_SCHEMAS",
    ],
    "selftest": [
        "ibkr-connector-positions-2026-06-24.json",
        "ibkr-connector-balances-2026-06-24.json",
        "ibkr-connector-adapter-2026-06-24.csv",
        "No order actions",
        "consumed saved IBKR connector JSON only",
        "IBKR connector adapter selftest ok",
    ],
    "fixture_positions": ["positions", "CRDO", "QQQ", "asset_class"],
    "fixture_balances": ["balances", "BASE", "USD", "cash_balance"],
    "contract_suite": [
        "verify_ibkr_connector_adapter_selftest.py",
        "verify_ibkr_connector_adapter_contract.py",
    ],
    "broker_contract": [
        "IBKR connector adapter",
        "ibkr_connector_adapter.py",
        "get_account_positions",
        "get_account_balances",
        "No live broker reads",
        "No order actions",
    ],
    "root_readme": [
        "IBKR connector adapter",
        "ibkr_connector_adapter.py",
        "No live broker reads",
    ],
    "plugin_readme": [
        "IBKR connector adapter",
        "ibkr_connector_adapter.py",
        "No order actions",
    ],
    "roadmap": ["IBKR connector adapter", "ibkr_connector_adapter.py"],
    "development_plan": ["IBKR connector adapter", "ibkr_connector_adapter.py"],
    "project_log": ["IBKR connector adapter", "ibkr_connector_adapter.py"],
}

SPEC = ContractSpec(
    name="IBKR connector adapter",
    success_message="IBKR connector adapter contract ok",
    failure_header="IBKR connector adapter contract failed:",
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
