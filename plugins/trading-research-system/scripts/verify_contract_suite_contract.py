#!/usr/bin/env python3
"""Verify Contract Suite module and verify-plugin orchestration."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root
REPO = PATHS.repo

FILES = {
    "contract_suite": ROOT / "scripts" / "contract_suite.py",
    "runner": ROOT / "scripts" / "verify_contract_suite.py",
    "selftest": ROOT / "scripts" / "verify_contract_suite_selftest.py",
    "verify_plugin": REPO / "scripts" / "verify-plugin.sh",
}

REQUIRED = {
    "contract_suite": [
        "PluginPaths",
        "ContractScript",
        "CORE_SUITE",
        "SUITES",
        "suite_scripts",
        "run_scripts",
        "run_contract_suite",
        "verify_source_routing_contract.py",
        "verify_macro_data_source_contract.py",
        "verify_contract_suite_selftest.py",
        "verify_contract_suite_contract.py",
        "verify_visual_artifact_selftest.py",
        "verify_visual_artifact_contract.py",
        "verify_broker_snapshot_ingest_contract.py",
    ],
    "runner": [
        "Run a registered Trading Research contract suite",
        "run_contract_suite",
        "suite",
        "core",
    ],
    "selftest": [
        "contract suite selftest ok",
        "PluginPaths.from_script",
        "suite_scripts(\"core\"",
        "run_scripts",
        "emit_output=False",
        "source-routing",
        "macro-data-source",
        "broker-snapshot-ingest-contract",
    ],
    "verify_plugin": [
        "verify_contract_suite.py",
        "core",
        "uv_run --group dev python \"$VALIDATE_PLUGIN\" \"$PLUGIN_ROOT\"",
    ],
}

FORBIDDEN = {
    "verify_plugin": [
        "verify_source_routing_contract.py",
        "verify_daily_ops_orchestrator_contract.py",
        "verify_daily_market_tracking_contract.py",
        "verify_macro_industry_research_monitor_contract.py",
        "verify_trade_plan_preparation_contract.py",
        "verify_automation_setup_contract.py",
        "verify_router_contract.py",
        "verify_runtime_state_selftest.py",
        "verify_runtime_state_contract.py",
        "verify_runtime_bootstrap_selftest.py",
        "verify_runtime_bootstrap_contract.py",
        "verify_visual_artifact_selftest.py",
        "verify_visual_artifact_contract.py",
        "verify_broker_snapshot_ingest_selftest.py",
        "verify_broker_snapshot_ingest_contract.py",
    ],
}

SPEC = ContractSpec(
    name="contract suite",
    success_message="contract suite contract ok",
    failure_header="contract suite contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=FORBIDDEN.get(key, ()),
            forbidden_label="duplicated suite orchestration",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
