#!/usr/bin/env python3
"""Verify the public read-only Alpha Leaderboard consumption contract."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)


def build_spec() -> ContractSpec:
    return ContractSpec(
        name="alpha leaderboard adapter",
        success_message="alpha leaderboard adapter contract ok",
        failure_header="alpha leaderboard adapter contract failed:",
        files={
            "adapter": FileContract(
                PATHS.scripts / "alpha_leaderboard_adapter.py",
                required_terms=(
                    "connect_read_only",
                    "?mode=ro",
                    "alpha_runs",
                    "alpha_rows",
                    "Alpha Rank",
                    "Experimental",
                    "agent 不重排",
                    "研究优先级，不是买入名单",
                    "publication_status",
                    "quality_status",
                    "published_at",
                    "snapshot hash mismatch",
                    "ranks are not contiguous",
                    "decision-card",
                    "render_decision_card",
                    "model_run_id = ?",
                    "ambiguous published champions",
                    "模型字段来自 published champion",
                ),
                forbidden_terms=("INSERT INTO", "DELETE FROM", "CREATE TABLE"),
            ),
            "selftest": FileContract(
                PATHS.scripts / "verify_alpha_leaderboard_adapter_selftest.py",
                required_terms=(
                    "adapter changed stored Alpha Rank order",
                    "candidate pool",
                    "missing Alpha store must fail without being created",
                    "not a published champion",
                    "invalid Alpha numeric range",
                    "must be Boolean",
                    "same-date shadow rows",
                    "## C 决策卡",
                    "Experimental: 63.0% / 0.1800",
                    "alpha leaderboard adapter selftest ok",
                ),
            ),
            "reference": FileContract(
                PATHS.references / "alpha-leaderboard.md",
                required_headings=(
                    "# Alpha Leaderboard",
                    "## Runtime Contract",
                    "## Agent Boundary",
                    "## Output Contract",
                    "## Legacy KVN Compatibility",
                ),
                required_terms=(
                    "alpha/leaderboard.sqlite",
                    "Top10",
                    "Top20",
                    "Top5",
                    "historical percentile",
                    "P(20D excess return > 0)",
                    "predictive uncertainty",
                    "challenger",
                    "must not re-rank",
                    "model_role=champion",
                    "publication_status=published",
                    "snapshot_hash",
                    "freshness status",
                    "candidate/deep-research flags",
                    "immutable `model_run_id`",
                    "matching successful `decision_card` analysis snapshot",
                ),
            ),
            "runtime_health": FileContract(
                PATHS.scripts / "runtime_health.py",
                required_terms=(
                    "alpha_leaderboard_store",
                    "alpha",
                    "leaderboard.sqlite",
                ),
            ),
            "router": FileContract(
                PATHS.skills / "trading-research-system" / "SKILL.md",
                required_terms=(
                    "references/alpha-leaderboard.md",
                    "alpha_leaderboard_adapter.py",
                    "Alpha Leaderboard",
                    "full-universe ticker query",
                ),
            ),
            "daily": FileContract(
                PATHS.references / "workflow-daily-market-tracking.md",
                required_terms=(
                    "alpha-leaderboard.md",
                    "Alpha Leaderboard delta",
                    "must not re-rank",
                ),
            ),
            "weekly": FileContract(
                PATHS.references / "workflow-weekly-trading-plan.md",
                required_terms=(
                    "alpha-leaderboard.md",
                    "Top20",
                    "Top5",
                    "must not re-rank",
                ),
            ),
            "output": FileContract(
                PATHS.references / "output-templates.md",
                required_headings=("## Alpha Decision Card",),
                required_terms=(
                    "上次运行增量",
                    "Alpha Rank / trajectory",
                    "P(20D超额>0) / predictive uncertainty",
                    "主分析时间框架",
                    "执行观察时间框架",
                    "加仓区 / TP或再平衡区",
                    "比例式仓位语言",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
