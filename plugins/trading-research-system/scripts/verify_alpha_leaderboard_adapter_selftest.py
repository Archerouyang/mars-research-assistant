#!/usr/bin/env python3
"""Self-test the read-only Alpha Leaderboard runtime adapter."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
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
                "Freshness: `valid`",
                "yes | yes",
                "研究优先级，不是买入名单",
            ],
        )
        if show.index("`C`") > show.index("`A`"):
            raise AssertionError("adapter changed stored Alpha Rank order")

        require_failure(
            ["show", "--db", str(db_path)],
            "is stale",
        )

        query = run(["query", "B", "--db", str(db_path), "--date", "2026-01-07"])
        require_terms(
            query,
            [
                "# Alpha 标的查询",
                "`B`",
                "Alpha Rank: `3`",
                "Freshness: `valid`",
                "candidate pool: `yes`",
                "主要正向因子: `return_20d +0.0400`",
                "主要负向因子: `hy_oas -0.0100`",
            ],
        )

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
                "当前 Freshness: `valid`",
            ],
        )

        identity_changes = run(
            ["changes", "--db", str(db_path), "--date", "2026-01-07", "--top", "3"]
        )
        require_terms(
            identity_changes,
            ["新进入 Top3: -", "滑出 Top3: -", "COLD -> C"],
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
            connection.execute(
                "UPDATE alpha_runs SET publication_environment = 'unverified' WHERE as_of = '2026-01-07'"
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "not production activated",
        )

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE alpha_runs SET quality_status = 'stale' WHERE as_of = '2026-01-07'"
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "not valid/current",
        )

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                UPDATE alpha_runs
                SET publication_environment = 'uat',
                    activation_fingerprint = 'not-synthetic'
                WHERE as_of = '2026-01-07'
                """
            )
            connection.commit()
        require_failure(
            [
                "show",
                "--db",
                str(db_path),
                "--date",
                "2026-01-07",
                "--allow-uat",
            ],
            "invalid isolation metadata",
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

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            payload = json.loads(
                connection.execute(
                    "SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07' AND ticker = 'C'"
                ).fetchone()[0]
            )
            payload["candidate_pool"] = "false"
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07' AND ticker = 'C'
                """,
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            rows = [
                json.loads(row[0])
                for row in connection.execute(
                    """
                    SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07'
                    ORDER BY alpha_rank, ticker
                    """
                )
            ]
            snapshot_hash = hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            connection.execute(
                "UPDATE alpha_runs SET snapshot_hash = ? WHERE as_of = '2026-01-07'",
                (snapshot_hash,),
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "must be Boolean",
        )

        create_fixture(db_path, replace=True)
        with sqlite3.connect(db_path) as connection:
            payload = json.loads(
                connection.execute(
                    "SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07' AND ticker = 'C'"
                ).fetchone()[0]
            )
            payload["factor_attribution"] = {}
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07' AND ticker = 'C'
                """,
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            rows = [
                json.loads(row[0])
                for row in connection.execute(
                    """
                    SELECT payload_json FROM alpha_rows WHERE as_of = '2026-01-07'
                    ORDER BY alpha_rank, ticker
                    """
                )
            ]
            snapshot_hash = hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            connection.execute(
                "UPDATE alpha_runs SET snapshot_hash = ? WHERE as_of = '2026-01-07'",
                (snapshot_hash,),
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "nonempty factor_attribution",
        )

    print("alpha leaderboard adapter selftest ok")
    return 0


def create_fixture(
    path: Path, *, replace: bool = False, current: bool = False
) -> None:
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
            quality_status TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            published_at TEXT NOT NULL,
            publication_environment TEXT NOT NULL,
            activation_id TEXT NOT NULL,
            activation_fingerprint TEXT NOT NULL,
            universe_fingerprint TEXT NOT NULL,
            point_in_time_status TEXT NOT NULL
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
    latest_date = date.today().isoformat() if current else "2026-01-07"
    previous_date = (
        (date.today() - timedelta(days=1)).isoformat()
        if current
        else "2026-01-06"
    )
    snapshots = {
        previous_date: [
            row(previous_date, "A", 1, 0.8, "persistent"),
            row(previous_date, "B", 2, 0.6, "persistent"),
            row(
                previous_date,
                "COLD",
                3,
                0.5,
                "new",
                security_id="sec-c",
            ),
        ],
        latest_date: [
            row(latest_date, "C", 1, 0.9, "strengthening"),
            row(latest_date, "A", 2, 0.7, "persistent"),
            row(latest_date, "B", 3, 0.4, "persistent"),
        ],
    }
    for as_of, rows in snapshots.items():
        snapshot_hash = hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        connection.execute(
            "INSERT INTO alpha_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                as_of,
                "bayes-1",
                f"input-{as_of}",
                snapshot_hash,
                "champion",
                "published",
                "valid",
                len(rows),
                f"{as_of}T22:30:00Z",
                "production",
                "fixture-activation",
                "sha256:" + "2" * 64,
                "sha256:" + "1" * 64,
                "available",
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
    as_of: str,
    ticker: str,
    rank: int,
    score: float,
    trajectory: str,
    *,
    security_id: str | None = None,
) -> dict[str, object]:
    return {
        "as_of": as_of,
        "security_id": security_id or f"sec-{ticker.lower()}",
        "ticker": ticker,
        "alpha_rank": rank,
        "alpha_score": score,
        "historical_percentile": 0.71,
        "probability_positive": 0.63,
        "predictive_std": 0.18,
        "expected_excess_return": 0.05,
        "model_intercept": 0.02,
        "factor_attribution": {"return_20d": 0.04, "hy_oas": -0.01},
        "top_factor": "return_20d",
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
