#!/usr/bin/env python3
"""Verify KVN leaderboard contract files and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEADER = (
    "snapshot_date",
    "rank_vs_sp500",
    "ticker",
    "kvn_score",
    "kvn_p",
    "is_sp500",
)


def build_spec() -> ContractSpec:
    return ContractSpec(
        name="kvn leaderboard",
        success_message="kvn leaderboard contract ok",
        failure_header="kvn leaderboard contract verification failed",
        files={
            "reference": FileContract(
                ROOT / "skills" / "trading-research" / "references" / "momentum-leaderboard.md",
                required_terms=(
                    "# Momentum Leaderboard",
                    "KVN is an imported snapshot",
                    "does not construct the quantitative model",
                    "{runtime_dir}/momentum/kvn.sqlite",
                    "snapshot_date,rank_vs_sp500,ticker,kvn_score,kvn_p,is_sp500",
                    "Top10 means the first 10 rows after sorting by `kvn_score` descending",
                    "research priority only, not a buy list",
                    "kvn_leaderboard.py import",
                    "kvn_leaderboard.py show",
                    "kvn_leaderboard.py query",
                    "kvn_leaderboard.py changes",
                ),
            ),
            "router skill": FileContract(
                ROOT / "skills" / "trading-research" / "SKILL.md",
                required_terms=(
                    "use `momentum-leaderboard`",
                    "references/momentum-leaderboard.md",
                    "kvn_leaderboard.py",
                    "KVN snapshot",
                ),
            ),
            "focused skill": FileContract(
                ROOT / "skills" / "momentum-leaderboard" / "SKILL.md",
                required_terms=(
                    "name: momentum-leaderboard",
                    "KVN Momentum Leaderboard",
                    "references/momentum-leaderboard.md",
                    "kvn_leaderboard.py",
                    "runtime-health.md",
                    "Top10",
                    "query",
                    "changes",
                    "research priority only, not a buy list",
                    "does not construct the quantitative model",
                    "Cross-Section Candidate Pool",
                ),
            ),
            "daily skill": FileContract(
                ROOT / "skills" / "daily-market-tracking" / "SKILL.md",
                required_terms=(
                    "KVN Momentum Leaderboard",
                    "runtime-health.md",
                    "momentum-leaderboard.md",
                    "kvn_leaderboard.py",
                    "missing or stale",
                    "Do not rebuild KVN",
                    "Do not label public market data as KVN",
                    "continue without KVN",
                ),
            ),
            "daily template": FileContract(
                ROOT / "assets" / "templates" / "daily-market-tracking.md",
                required_terms=(
                    "KVN source status",
                    "imported snapshot / missing / stale",
                    "Do not rebuild KVN",
                    "continue without KVN",
                ),
            ),
            "script": FileContract(
                ROOT / "scripts" / "kvn_leaderboard.py",
                required_terms=(
                    "sqlite3",
                    "kvn_snapshots",
                    "kvn_rankings",
                    "import",
                    "show",
                    "query",
                    "changes",
                    "Research priority only, not a buy list.",
                ),
            ),
            "selftest": FileContract(
                ROOT / "scripts" / "verify_kvn_leaderboard_selftest.py",
                required_terms=(
                    "kvn-snapshot-2026-06-21.csv",
                    "kvn-snapshot-2026-06-24.csv",
                    "current top10: no",
                    "New Top10",
                    "Dropped from Top10",
                ),
            ),
            "fixture 2026-06-21": FileContract(
                ROOT / "assets" / "fixtures" / "input" / "kvn-snapshot-2026-06-21.csv",
                csv_header=EXPECTED_HEADER,
                csv_rows_match_header=True,
            ),
            "fixture 2026-06-24": FileContract(
                ROOT / "assets" / "fixtures" / "input" / "kvn-snapshot-2026-06-24.csv",
                csv_header=EXPECTED_HEADER,
                csv_rows_match_header=True,
            ),
            "expected top10": FileContract(
                ROOT / "assets" / "fixtures" / "expected" / "kvn-leaderboard-2026-06-24.md",
                required_terms=(
                    "# KVN Momentum Leaderboard",
                    "Snapshot date: `2026-06-24`",
                    "Rank vs S&P500",
                    "KVN 分数",
                    "连续入选Top10天数",
                    "近20日入选Top10次数",
                    "上次入选Top10时间",
                    "research priority only, not a buy list",
                ),
            ),
            "plugin readme": FileContract(
                ROOT / "README.md",
                required_terms=(
                    "KVN snapshot import",
                    "kvn_leaderboard.py",
                ),
            ),
            "roadmap": FileContract(
                ROOT.parents[1] / "docs" / "ROADMAP.md",
                required_terms=(
                    "KVN snapshot leaderboard contract",
                    "kvn_leaderboard.py",
                    "kvn-leaderboard-2026-06-24.md",
                ),
            ),
            "development plan": FileContract(
                ROOT.parents[1] / "docs" / "DEVELOPMENT_PLAN.md",
                required_terms=(
                    "Define KVN snapshot leaderboard contract",
                    "kvn_leaderboard.py",
                    "verify_kvn_leaderboard_selftest.py",
                    "verify_kvn_leaderboard_contract.py",
                ),
            ),
        },
    )


if __name__ == "__main__":
    sys.exit(run_contract(build_spec()))
