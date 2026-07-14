#!/usr/bin/env python3
"""Verify Longbridge OHLCV adapter contract."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo
REFERENCES = PATHS.references

FILES = {
    "adapter_script": ROOT / "scripts" / "longbridge_ohlcv_adapter.py",
    "selftest": ROOT / "scripts" / "verify_longbridge_ohlcv_adapter_selftest.py",
    "fixture": ROOT / "assets" / "fixtures" / "input" / "longbridge-kline-qqq-day-2026-07-09.json",
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "price_action_reference": REFERENCES / "price-action-timing.md",
    "daily_tracking_skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-daily-market-tracking.md",
    "plugin_readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
    "acceptance_results": REPO / "docs" / "1.0_ACCEPTANCE_RESULTS.md",
    "project_log": REPO / "docs" / "PROJECT_LOG.md",
}

REQUIRED = {
    "adapter_script": [
        "Normalize saved Longbridge kline JSON",
        "longbridge kline",
        "--kline-json",
        "--symbol",
        "--period",
        "No live market data calls",
        "No live broker reads",
        "No order actions",
        "Longbridge kline saved JSON",
    ],
    "selftest": [
        "Longbridge OHLCV adapter selftest ok",
        "longbridge-kline-qqq-day-2026-07-09.json",
        "price_action_rollforward.py",
        "No live market data calls",
        "No live broker reads",
        "No order actions",
    ],
    "fixture": [
        "2026-06-01T04:00:00Z",
        "turnover",
        "volume",
        "close",
    ],
    "contract_suite": [
        "verify_longbridge_ohlcv_adapter_selftest.py",
        "verify_longbridge_ohlcv_adapter_contract.py",
    ],
    "price_action_reference": [
        "longbridge_ohlcv_adapter.py",
        "Longbridge kline",
        "saved JSON",
        "price_action_rollforward.py",
    ],
    "daily_tracking_skill": [
        "longbridge_ohlcv_adapter.py",
        "Longbridge kline",
        "OHLCV",
    ],
    "plugin_readme": [
        "longbridge_ohlcv_adapter.py",
        "Longbridge kline",
        "OHLCV",
    ],
    "roadmap": [
        "Longbridge OHLCV adapter",
        "longbridge_ohlcv_adapter.py",
    ],
    "development_plan": [
        "Longbridge OHLCV adapter",
        "longbridge_ohlcv_adapter.py",
    ],
    "acceptance_results": [
        "Longbridge OHLCV adapter",
        "longbridge_ohlcv_adapter.py",
    ],
    "project_log": [
        "Longbridge OHLCV adapter",
        "longbridge_ohlcv_adapter.py",
    ],
}

SPEC = ContractSpec(
    name="Longbridge OHLCV adapter",
    success_message="Longbridge OHLCV adapter contract ok",
    failure_header="Longbridge OHLCV adapter contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
