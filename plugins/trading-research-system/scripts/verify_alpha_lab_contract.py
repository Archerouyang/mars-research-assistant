#!/usr/bin/env python3
"""Verify the public Alpha Lab and knowledge-base integration contract."""

from __future__ import annotations

import sys
from pathlib import Path

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)


def build_spec() -> ContractSpec:
    return ContractSpec(
        name="alpha lab",
        success_message="alpha lab contract ok",
        failure_header="alpha lab contract verification failed",
        files={
            "architecture": FileContract(
                PATHS.repo / "docs" / "ALPHA_LAB_PLAN.md",
                required_headings=(
                    "# Alpha Lab 1.0 Plan",
                    "## Product Boundary",
                    "## Data Architecture",
                    "## Factor Architecture",
                    "## Model Architecture",
                    "## Knowledge Base",
                    "## Plugin Integration",
                    "## Model Governance",
                    "## 1.0 Acceptance",
                ),
                required_terms=(
                    "dailytrades-quant",
                    "FMP",
                    "FMP_API_KEY",
                    "redacts it from URLs/errors/logs",
                    "SEC EDGAR",
                    "Nasdaq Trader",
                    "FRED/ALFRED",
                    "Parquet",
                    "SQLite FTS5",
                    "Bayesian champion",
                    "LightGBM challenger",
                    "future 20-trading-day excess return versus SPY",
                    "P(20D excess return > 0)",
                    "predictive uncertainty",
                    "Experimental",
                    "full eligible universe",
                    "Top10",
                    "Top20",
                    "Top5",
                    "full snapshot",
                    "delta",
                    "Personal positions, broker exports, raw market data",
                    "no order actions",
                    "Sol review",
                    "autonomous promotion is blocked",
                ),
            ),
            "agents": FileContract(
                PATHS.repo / "AGENTS.md",
                required_headings=("## Model-tier Subagents",),
                required_terms=(
                    "GPT-5.6 Luna",
                    "GPT-5.6 Terra",
                    "GPT-5.6 Sol",
                    "Luna prepares",
                    "Terra performs the primary analysis",
                    "Sol escalation",
                    "self-check",
                    "must not claim a model tier was used when it was unavailable",
                ),
            ),
            "language": FileContract(
                PATHS.repo / "CONTEXT.md",
                required_terms=(
                    "**多因子 Alpha 榜**:",
                    "**Alpha Score**:",
                    "**历史分位**:",
                    "**Alpha 轨迹状态**:",
                    "**分析运行快照**:",
                    "**分析增量**:",
                    "**模型概率边界**:",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
