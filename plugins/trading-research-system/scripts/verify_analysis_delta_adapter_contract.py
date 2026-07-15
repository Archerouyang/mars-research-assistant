#!/usr/bin/env python3
"""Verify stable-key previous-analysis retrieval stays read-only."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

SPEC = ContractSpec(
    name="analysis delta adapter",
    success_message="analysis delta adapter contract ok",
    failure_header="analysis delta adapter contract failed:",
    files={
        "adapter": FileContract(
            PATHS.scripts / "analysis_delta_adapter.py",
            required_terms=(
                "connect_read_only",
                "?mode=ro",
                "analysis_runs",
                "stable_key",
                "comparison_mode",
                "payload_json",
                "delta_json",
                "status = 'success'",
                "ORDER BY as_of DESC, sequence_id DESC",
            ),
            forbidden_terms=("INSERT INTO", "DELETE FROM", "CREATE TABLE"),
        ),
        "selftest": FileContract(
            PATHS.scripts / "verify_analysis_delta_adapter_selftest.py",
            required_terms=(
                "adapter did not return latest run",
                "adapter lost stored comparison mode",
                "missing analysis store must fail without being created",
                "model/rule change must force full_recompute",
                "analysis delta adapter selftest ok",
            ),
        ),
        "reference": FileContract(
            PATHS.references / "analysis-delta.md",
            required_terms=(
                "symbol/scope + analysis_type + primary_timeframe + strategy_horizon",
                "knowledge/analysis.sqlite",
                "latest successful full snapshot",
                "updated",
                "invalidated",
                "full_recompute",
                "本次作为基准分析",
                "status=success",
                "as_of DESC, sequence_id DESC",
            ),
        ),
        "router": FileContract(
            PATHS.skills / "trading-research-system" / "SKILL.md",
            required_terms=(
                "references/analysis-delta.md",
                "analysis_delta_adapter.py",
                "本次作为基准分析",
            ),
        ),
        "runtime_health": FileContract(
            PATHS.scripts / "runtime_health.py",
            required_terms=("analysis_store", "knowledge", "analysis.sqlite"),
        ),
    },
)


if __name__ == "__main__":
    sys.exit(run_contract(SPEC))
