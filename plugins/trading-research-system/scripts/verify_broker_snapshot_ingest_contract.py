#!/usr/bin/env python3
"""Verify broker snapshot ingestion is documented and wired into checks."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo

FILES = {
    "ingest_script": ROOT / "scripts" / "broker_snapshot_ingest.py",
    "selftest": ROOT / "scripts" / "verify_broker_snapshot_ingest_selftest.py",
    "expected_snapshot": ROOT / "assets" / "fixtures" / "expected" / "broker-snapshot-ingest-2026-06-24.csv",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "verify_plugin": REPO / "scripts" / "verify-plugin.sh",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "broker_contract": ROOT / "skills" / "trading-research" / "references" / "broker-data-contract.md",
    "position_automation": ROOT / "assets" / "templates" / "automation-position-daily-report.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "ingest_script": [
        "broker snapshot ingest",
        "No live broker reads",
        "portfolio_snapshot.csv",
        "--input",
        "--output",
        "--as-of",
        "IBKR",
        "Longbridge",
        "CSV_SCHEMAS",
    ],
    "selftest": [
        "broker snapshot ingest selftest ok",
        "broker-positions-ibkr-2026-06-24.csv",
        "broker-positions-longbridge-2026-06-24.csv",
        "No live broker reads",
    ],
    "contract_suite": [
        "verify_broker_snapshot_ingest_selftest.py",
        "verify_broker_snapshot_ingest_contract.py",
    ],
    "verify_plugin": ["verify_contract_suite.py", "core"],
    "root_readme": [
        "Broker snapshot ingest",
        "broker_snapshot_ingest.py",
        "No live broker reads",
    ],
    "plugin_readme": [
        "Broker snapshot ingest",
        "broker_snapshot_ingest.py",
    ],
    "broker_contract": [
        "broker_snapshot_ingest.py",
        "read-only broker export",
    ],
    "position_automation": [
        "broker_snapshot_ingest.py",
        "portfolio_snapshot.csv",
    ],
    "development_plan": [
        "Broker snapshot ingest",
        "broker_snapshot_ingest.py",
    ],
    "roadmap": [
        "Broker snapshot ingest",
        "broker_snapshot_ingest.py",
    ],
    "project_log": [
        "Broker snapshot ingest",
        "broker_snapshot_ingest.py",
    ],
}

SPEC = ContractSpec(
    name="broker snapshot ingest",
    success_message="broker snapshot ingest contract ok",
    failure_header="broker snapshot ingest contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED.get(key, ()),
            csv_header=CSV_SCHEMAS["portfolio_snapshot.csv"] if key == "expected_snapshot" else None,
            csv_rows_match_header=key == "expected_snapshot",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
