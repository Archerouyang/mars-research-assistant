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
                    "publication_environment",
                    "activation_id",
                    "activation_fingerprint",
                    "universe_fingerprint",
                    "point_in_time_status",
                    "not production activated",
                    "not valid/current",
                    "ensure_fresh_snapshot",
                    "MAX_LATEST_AGE_DAYS",
                    "is stale",
                    "invalid isolation metadata",
                    "published_at",
                    "snapshot hash mismatch",
                    "ranks are not contiguous",
                    "factor_attribution",
                    "model_intercept",
                    "top_factor",
                    "does not reconstruct prediction",
                    "主要正向因子",
                    "主要负向因子",
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
                    "nonempty factor_attribution",
                    "not production activated",
                    "not valid/current",
                    "security_id",
                    "COLD -> C",
                    "alpha leaderboard adapter selftest ok",
                ),
            ),
            "cross_uat": FileContract(
                PATHS.scripts / "verify_alpha_cross_repo_uat.py",
                required_terms=(
                    "allow_uat=True",
                    "allow_uat=False",
                    "not production activated",
                    "generated UAT attribution did not cross public adapter",
                    "normal public mode accepted an isolated UAT snapshot",
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
                    "per-factor attribution",
                    "model intercept",
                    "must reconstruct",
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
                PATHS.skills / "trading-research" / "SKILL.md",
                required_terms=(
                    "references/alpha-leaderboard.md",
                    "alpha_leaderboard_adapter.py",
                    "Alpha Leaderboard",
                    "full-universe ticker query",
                    "Alpha Decision Card",
                    "rank-only lookup",
                ),
            ),
            "daily": FileContract(
                PATHS.skills / "daily-market-tracking" / "SKILL.md",
                required_terms=(
                    "alpha-leaderboard.md",
                    "Alpha Leaderboard delta",
                    "must not re-rank",
                ),
            ),
            "weekly": FileContract(
                PATHS.skills / "weekly-trading-plan" / "SKILL.md",
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
                    "主要正向/负向贡献",
                    "agent不得重算或改写",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
