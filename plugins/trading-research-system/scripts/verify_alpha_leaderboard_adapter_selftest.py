#!/usr/bin/env python3
"""Self-test the read-only Alpha Leaderboard runtime adapter."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha_leaderboard_adapter.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "alpha" / "leaderboard.sqlite"
        create_fixture(db_path)

        show = run(["show", "--db", str(db_path), "--date", "2026-01-07"])
        require_terms(
            show,
            [
                "# 多因子 Alpha 榜",
                "`C`",
                "0.9000",
                "71.0%",
                "strengthening",
                "研究优先级，不是买入名单",
            ],
        )
        if show.index("`C`") > show.index("`A`"):
            raise AssertionError("adapter changed stored Alpha Rank order")

        query = run(["query", "B", "--db", str(db_path), "--date", "2026-01-07"])
        require_terms(query, ["# Alpha 标的查询", "`B`", "Alpha Rank: `3`", "candidate pool: `yes`"])

        changes = run(
            ["changes", "--db", str(db_path), "--date", "2026-01-07", "--top", "2"]
        )
        require_terms(
            changes,
            [
                "# Alpha 榜变化",
                "新进入 Top2: `C`",
                "滑出 Top2: `B`",
                "继续留在 Top2: `A`",
            ],
        )

        missing = Path(tmp) / "missing.sqlite"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "show", "--db", str(missing)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 or missing.exists():
            raise AssertionError("missing Alpha store must fail without being created")

    print("alpha leaderboard adapter selftest ok")
    return 0


def create_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE alpha_runs (
            as_of TEXT PRIMARY KEY,
            model_run_id TEXT NOT NULL,
            input_fingerprint TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL
        );
        CREATE TABLE alpha_rows (
            as_of TEXT NOT NULL,
            ticker TEXT NOT NULL,
            alpha_rank INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (as_of, ticker)
        );
        """
    )
    snapshots = {
        "2026-01-06": [
            row("A", 1, 0.8, "persistent"),
            row("B", 2, 0.6, "persistent"),
            row("C", 3, 0.5, "new"),
        ],
        "2026-01-07": [
            row("C", 1, 0.9, "strengthening"),
            row("A", 2, 0.7, "persistent"),
            row("B", 3, 0.4, "persistent"),
        ],
    }
    for as_of, rows in snapshots.items():
        connection.execute(
            "INSERT INTO alpha_runs VALUES (?, ?, ?, ?)",
            (as_of, "bayes-1", f"input-{as_of}", f"hash-{as_of}"),
        )
        connection.executemany(
            "INSERT INTO alpha_rows VALUES (?, ?, ?, ?)",
            [
                (as_of, item["ticker"], item["alpha_rank"], json.dumps(item))
                for item in rows
            ],
        )
    connection.commit()
    connection.close()


def row(ticker: str, rank: int, score: float, trajectory: str) -> dict[str, object]:
    return {
        "as_of": "2026-01-07",
        "ticker": ticker,
        "alpha_rank": rank,
        "alpha_score": score,
        "historical_percentile": 0.71,
        "probability_positive": 0.63,
        "predictive_std": 0.18,
        "rank_vs_sp500": rank,
        "trajectory_state": trajectory,
        "consecutive_top_display_days": 2,
        "recent_top_display_count": 2,
        "last_top_display_date": "2026-01-06T00:00:00",
        "candidate_pool": True,
        "deep_research_priority": rank == 1,
        "challenger_rank": 4 - rank,
    }


def run(args: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def require_terms(text: str, terms: list[str]) -> None:
    missing = [term for term in terms if term not in text]
    if missing:
        raise AssertionError(f"missing terms {missing!r} in:\n{text}")


if __name__ == "__main__":
    sys.exit(main())
