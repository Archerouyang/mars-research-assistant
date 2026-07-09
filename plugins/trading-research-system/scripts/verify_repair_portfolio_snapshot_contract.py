#!/usr/bin/env python3
"""Verify portfolio snapshot repair contract."""

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
    "script": ROOT / "scripts" / "repair_portfolio_snapshot.py",
    "selftest": ROOT / "scripts" / "verify_repair_portfolio_snapshot_selftest.py",
    "fixture": ROOT / "assets" / "fixtures" / "input" / "portfolio-snapshot-stale-2026-06-24.csv",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "broker_contract": REFERENCES / "broker-data-contract.md",
    "portfolio_skill": ROOT / "skills" / "portfolio-risk" / "SKILL.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "acceptance_results": REPO / "docs" / "1.0_ACCEPTANCE_RESULTS.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "script": [
        "Repair stale product/theme mappings",
        "portfolio_snapshot.csv",
        "--input",
        "--output",
        "--allow-same-path",
        "No live broker reads",
        "No order actions",
        "Snapshot repair:",
        "leveraged_etf",
        "sector_etf",
    ],
    "selftest": [
        "repair portfolio snapshot selftest ok",
        "portfolio-snapshot-stale-2026-06-24.csv",
        "TSMX.US",
        "leveraged_etf",
        "ai_hardware_leverage",
        "No live broker reads",
        "No order actions",
    ],
    "fixture": [
        "QQQ.US",
        "SOXX",
        "TSMX.US",
        "CRDO.US",
        "unmapped",
    ],
    "contract_suite": [
        "verify_repair_portfolio_snapshot_selftest.py",
        "verify_repair_portfolio_snapshot_contract.py",
    ],
    "broker_contract": [
        "repair_portfolio_snapshot.py",
        "stale or unmapped product/theme",
        "No live broker reads",
        "No order actions",
    ],
    "portfolio_skill": [
        "repair_portfolio_snapshot.py",
        "stale or unmapped product/theme",
        "portfolio_snapshot.csv",
    ],
    "root_readme": [
        "repair_portfolio_snapshot.py",
        "stale/unmapped product/theme",
        "portfolio_snapshot.csv",
    ],
    "plugin_readme": [
        "repair_portfolio_snapshot.py",
        "stale/unmapped product/theme",
        "portfolio_snapshot.csv",
    ],
    "roadmap": [
        "Portfolio snapshot repair",
        "repair_portfolio_snapshot.py",
    ],
    "development_plan": [
        "Runtime snapshot normalization repair",
        "repair_portfolio_snapshot.py",
    ],
    "acceptance_results": [
        "Runtime snapshot normalization repair",
        "repair_portfolio_snapshot.py",
    ],
    "project_log": [
        "Runtime snapshot normalization repair",
        "repair_portfolio_snapshot.py",
    ],
}

SPEC = ContractSpec(
    name="portfolio snapshot repair",
    success_message="portfolio snapshot repair contract ok",
    failure_header="portfolio snapshot repair contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            csv_header=CSV_SCHEMAS["portfolio_snapshot.csv"] if key == "fixture" else None,
            csv_rows_match_header=key == "fixture",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
