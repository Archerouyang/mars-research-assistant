#!/usr/bin/env python3
"""Self-test read-only previous-analysis and delta retrieval."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analysis_delta_adapter.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "knowledge" / "analysis.sqlite"
        create_fixture(db_path)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "latest",
                "--db",
                str(db_path),
                "--symbol",
                "SOXX",
                "--analysis-type",
                "decision_card",
                "--primary-timeframe",
                "1D",
                "--strategy-horizon",
                "swing",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        if payload["as_of"] != "2026-07-11":
            raise AssertionError("adapter did not return latest run")
        if payload["comparison_mode"] != "incremental":
            raise AssertionError("adapter lost stored comparison mode")
        if payload["delta"] != {"decision": "updated", "support": "unchanged"}:
            raise AssertionError(f"unexpected delta: {payload['delta']!r}")
        if payload["snapshot"]["decision"] != "research":
            raise AssertionError("adapter did not return full latest snapshot")

        missing = Path(tmp) / "missing.sqlite"
        failed = subprocess.run(
            [sys.executable, str(SCRIPT), "latest", "--db", str(missing), "--symbol", "SOXX"],
            text=True,
            capture_output=True,
            check=False,
        )
        if failed.returncode == 0 or missing.exists():
            raise AssertionError("missing analysis store must fail without being created")

    print("analysis delta adapter selftest ok")
    return 0


def create_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
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
            comparison_mode TEXT NOT NULL
        )
        """
    )
    rows = [
        ("run-1", "2026-07-10", {"decision": "wait", "support": 550}, {"decision": "added", "support": "added"}, "baseline"),
        ("run-2", "2026-07-11", {"decision": "research", "support": 550}, {"decision": "updated", "support": "unchanged"}, "incremental"),
    ]
    connection.executemany(
        """
        INSERT INTO analysis_runs (
            run_id, stable_key, symbol_or_scope, analysis_type,
            primary_timeframe, strategy_horizon, as_of, model_version,
            rule_version, input_fingerprint, payload_json, delta_json,
            comparison_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                run_id,
                "SOXX|decision_card|1D|swing",
                "SOXX",
                "decision_card",
                "1D",
                "swing",
                as_of,
                "bayes-1",
                "decision-card-1",
                f"input-{as_of}",
                json.dumps(snapshot),
                json.dumps(delta),
                mode,
            )
            for run_id, as_of, snapshot, delta, mode in rows
        ],
    )
    connection.commit()
    connection.close()


if __name__ == "__main__":
    sys.exit(main())
