#!/usr/bin/env python3
"""Self-test the read-only Alpha Leaderboard runtime adapter."""

from __future__ import annotations

import hashlib
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

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE alpha_runs SET publication_status = 'shadow' WHERE as_of = '2026-01-07'"
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "not a published champion",
        )

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            payload = json.loads(
                connection.execute(
                    "SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07' AND ticker = 'C'"
                ).fetchone()[0]
            )
            payload["probability_positive"] = 1.5
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07' AND ticker = 'C'
                """,
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "invalid Alpha numeric range",
        )

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            payload = json.loads(
                connection.execute(
                    "SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07' AND ticker = 'C'"
                ).fetchone()[0]
            )
            payload["alpha_score"] = 0.91
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07' AND ticker = 'C'
                """,
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "snapshot hash mismatch",
        )

    print("alpha leaderboard adapter selftest ok")
    return 0


def create_fixture(path: Path, *, replace: bool = False) -> None:
    if replace and path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE alpha_runs (
            as_of TEXT PRIMARY KEY,
            model_run_id TEXT NOT NULL,
            input_fingerprint TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            model_role TEXT NOT NULL,
            publication_status TEXT NOT NULL,
            row_count INTEGER NOT NULL
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
            row("2026-01-06", "A", 1, 0.8, "persistent"),
            row("2026-01-06", "B", 2, 0.6, "persistent"),
            row("2026-01-06", "C", 3, 0.5, "new"),
        ],
        "2026-01-07": [
            row("2026-01-07", "C", 1, 0.9, "strengthening"),
            row("2026-01-07", "A", 2, 0.7, "persistent"),
            row("2026-01-07", "B", 3, 0.4, "persistent"),
        ],
    }
    for as_of, rows in snapshots.items():
        snapshot_hash = hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        connection.execute(
            "INSERT INTO alpha_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                as_of,
                "bayes-1",
                f"input-{as_of}",
                snapshot_hash,
                "champion",
                "published",
                len(rows),
            ),
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


def row(
    as_of: str, ticker: str, rank: int, score: float, trajectory: str
) -> dict[str, object]:
    return {
        "as_of": as_of,
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


def require_failure(args: list[str], term: str) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 or term not in result.stderr:
        raise AssertionError(
            f"expected failure containing {term!r}:\n{result.stdout}\n{result.stderr}"
        )


if __name__ == "__main__":
    sys.exit(main())
