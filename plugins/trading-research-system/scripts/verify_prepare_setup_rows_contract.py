#!/usr/bin/env python3
"""Verify setup-row preparation script and docs are wired."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "script": ROOT / "scripts" / "prepare_setup_rows.py",
    "selftest": ROOT / "scripts" / "verify_prepare_setup_rows_selftest.py",
    "fixture": ROOT / "assets" / "fixtures" / "input" / "confirmed-setups-2026-06-24.json",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "intraday_reference": REFERENCES / "intraday-setup-scan.md",
    "router_skill": ROOT / "skills" / "trading-research" / "SKILL.md",
    "daily_orchestrator": ROOT / "assets" / "templates" / "daily-ops-orchestrator.md",
    "root_readme": REPO / "README.md",
    "plugin_readme": ROOT / "README.md",
    "mvp_runbook": REPO / "docs" / "MVP_RUNBOOK.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "script": [
        "Populate daily setup CSV rows",
        "--setup-json",
        "trade-plans.csv",
        "intraday-watchlist.csv",
        "user-confirmed setup JSON",
        "header-only",
        "kept existing populated",
        "No live broker reads",
        "no live market data",
        "no order actions",
        "does not parse free-form trade ideas",
    ],
    "selftest": [
        "prepare setup rows selftest ok",
        "confirmed-setups-2026-06-24.json",
        "would fill header-only",
        "kept existing populated",
        "intraday_scan.py",
        "qqq-0dte-breakout-pullback | triggered",
    ],
    "fixture": [
        "user_confirmed_active_market_plan_fixture",
        "qqq-0dte-breakout-pullback",
        "soxx-sector-confirmation",
        "execution_check_required",
    ],
    "contract_suite": [
        "verify_prepare_setup_rows_selftest.py",
        "verify_prepare_setup_rows_contract.py",
    ],
    "intraday_reference": [
        "prepare_setup_rows.py",
        "user-confirmed setup JSON",
        "trade-plans.csv",
        "intraday-watchlist.csv",
        "does not parse free-form trade ideas",
    ],
    "router_skill": [
        "prepare_setup_rows.py",
        "user-confirmed setup JSON",
        "trade-plans.csv",
        "intraday-watchlist.csv",
    ],
    "daily_orchestrator": [
        "prepare_setup_rows.py",
        "user-confirmed setup JSON",
        "populate setup rows",
    ],
    "root_readme": [
        "prepare_setup_rows.py",
        "user-confirmed setup JSON",
        "intraday-watchlist.csv",
    ],
    "plugin_readme": [
        "prepare_setup_rows.py",
        "user-confirmed setup JSON",
        "intraday-watchlist.csv",
    ],
    "mvp_runbook": [
        "prepare_setup_rows.py",
        "confirmed setup JSON",
        "intraday-watchlist.csv",
    ],
    "development_plan": [
        "Setup row preparation",
        "prepare_setup_rows.py",
    ],
    "project_log": [
        "Setup row preparation",
        "prepare_setup_rows.py",
    ],
}

SPEC = ContractSpec(
    name="setup row preparation",
    success_message="setup row preparation contract ok",
    failure_header="setup row preparation contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
