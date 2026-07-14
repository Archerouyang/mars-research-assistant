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
        analysis_db = Path(tmp) / "knowledge" / "analysis.sqlite"
        create_fixture(db_path)
        create_analysis_fixture(analysis_db)

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
        if "SHADOW" in show:
            raise AssertionError("adapter mixed same-date shadow rows into champion output")

        card = run(
            [
                "decision-card",
                "C",
                "--db",
                str(db_path),
                "--analysis-db",
                str(analysis_db),
                "--date",
                "2026-01-07",
            ]
        )
        require_terms(
            card,
            [
                "## C 决策卡",
                "上次运行增量",
                "Alpha Rank / trajectory",
                "1 / strengthening",
                "P(20D超额>0) / predictive uncertainty",
                "Experimental: 63.0% / 0.1800",
                "主分析时间框架",
                "执行观察时间框架",
                "PA + EMA",
                "加仓区 / TP或再平衡区",
                "比例式仓位语言",
                "模型字段来自 published champion，不得由分析层改写",
            ],
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
                """
                UPDATE alpha_runs SET publication_status = 'shadow'
                WHERE as_of = '2026-01-07' AND model_run_id = 'bayes-1'
                """
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
                    """
                    SELECT payload_json FROM alpha_rows
                    WHERE as_of = '2026-01-07'
                      AND model_run_id = 'bayes-1' AND ticker = 'C'
                    """
                ).fetchone()[0]
            )
            payload["probability_positive"] = 1.5
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07'
                  AND model_run_id = 'bayes-1' AND ticker = 'C'
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
                    """
                    SELECT payload_json FROM alpha_rows
                    WHERE as_of = '2026-01-07'
                      AND model_run_id = 'bayes-1' AND ticker = 'C'
                    """
                ).fetchone()[0]
            )
            payload["alpha_score"] = 0.91
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07'
                  AND model_run_id = 'bayes-1' AND ticker = 'C'
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
                    """
                    SELECT payload_json FROM alpha_rows
                    WHERE as_of = '2026-01-07'
                      AND model_run_id = 'bayes-1' AND ticker = 'C'
                    """
                ).fetchone()[0]
            )
            payload["candidate_pool"] = "false"
            connection.execute(
                """
                UPDATE alpha_rows SET payload_json = ?
                WHERE as_of = '2026-01-07'
                  AND model_run_id = 'bayes-1' AND ticker = 'C'
                """,
                (json.dumps(payload, sort_keys=True, separators=(",", ":")),),
            )
            rows = [
                json.loads(row[0])
                for row in connection.execute(
                    """
                    SELECT payload_json FROM alpha_rows
                    WHERE as_of = '2026-01-07' AND model_run_id = 'bayes-1'
                    ORDER BY alpha_rank, ticker
                    """
                )
            ]
            snapshot_hash = hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            connection.execute(
                """
                UPDATE alpha_runs SET snapshot_hash = ?
                WHERE as_of = '2026-01-07' AND model_run_id = 'bayes-1'
                """,
                (snapshot_hash,),
            )
            connection.commit()
        require_failure(
            ["show", "--db", str(db_path), "--date", "2026-01-07"],
            "must be Boolean",
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
            as_of TEXT NOT NULL,
            model_run_id TEXT NOT NULL,
            input_fingerprint TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            model_role TEXT NOT NULL,
            publication_status TEXT NOT NULL,
            quality_status TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            published_at TEXT NOT NULL,
            PRIMARY KEY (as_of, model_run_id)
        );
        CREATE TABLE alpha_rows (
            as_of TEXT NOT NULL,
            model_run_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            alpha_rank INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (as_of, model_run_id, ticker)
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
            "INSERT INTO alpha_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            ),
        )
        connection.executemany(
            "INSERT INTO alpha_rows VALUES (?, ?, ?, ?, ?)",
            [
                (as_of, "bayes-1", item["ticker"], item["alpha_rank"], json.dumps(item))
                for item in rows
            ],
        )
    shadow = row("2026-01-07", "SHADOW", 1, 0.99, "new")
    shadow_hash = hashlib.sha256(
        json.dumps([shadow], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    connection.execute(
        "INSERT INTO alpha_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "2026-01-07",
            "lightgbm-shadow-1",
            "input-shadow-2026-01-07",
            shadow_hash,
            "challenger",
            "shadow",
            "valid",
            1,
            "2026-01-07T22:35:00Z",
        ),
    )
    connection.execute(
        "INSERT INTO alpha_rows VALUES (?, ?, ?, ?, ?)",
        (
            "2026-01-07",
            "lightgbm-shadow-1",
            shadow["ticker"],
            shadow["alpha_rank"],
            json.dumps(shadow),
        ),
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
        "factor_attribution": {
            "momentum": 0.4,
            "volume": 0.2,
            "volatility": -0.1,
        },
    }


def create_analysis_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "decision_state": "setup候选",
        "primary_regime": "1D 上涨，4H 整理",
        "execution_context": "1H 等待 reclaim 确认",
        "pa_ema": "bull flag; above 20/50/200 EMA",
        "levels": ["1D support 95", "1D resistance 105"],
        "zones": ["add 98-100", "trim 108-110"],
        "events": ["weekly earnings review"],
        "invalidation": "1D close below 95",
        "next_check": "next 1H close",
        "sizing_language": "少量，确认后最多增加 1/5",
    }
    delta = {
        "decision_state": "updated",
        "levels": "updated",
        "pa_ema": "unchanged",
    }
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE analysis_runs (
                sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                stable_key TEXT NOT NULL,
                symbol_or_scope TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                primary_timeframe TEXT NOT NULL,
                strategy_horizon TEXT NOT NULL,
                as_of TEXT NOT NULL,
                model_version TEXT NOT NULL,
                rule_version TEXT NOT NULL,
                input_fingerprint TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                delta_json TEXT NOT NULL,
                comparison_mode TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO analysis_runs (
                run_id, stable_key, symbol_or_scope, analysis_type,
                primary_timeframe, strategy_horizon, as_of, model_version,
                rule_version, input_fingerprint, payload_json, delta_json,
                comparison_mode, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "decision-card-c-2026-01-07",
                "C|decision_card|1D|swing",
                "C",
                "decision_card",
                "1D",
                "swing",
                "2026-01-07",
                "bayes-1",
                "decision-card-1",
                "analysis-input-2026-01-07",
                json.dumps(snapshot),
                json.dumps(delta),
                "incremental",
                "success",
            ),
        )


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
