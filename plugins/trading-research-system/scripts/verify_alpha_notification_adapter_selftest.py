#!/usr/bin/env python3
"""Self-test the read-only, allowlisted Alpha notification adapter."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha_notification_adapter.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "outbox.sqlite"
        create_fixture(db_path)
        result = run(db_path)
        payload = json.loads(result.stdout)
        if payload["event_id"] != "daily:2026-07-10:config-a":
            raise AssertionError("adapter returned the wrong pending event")
        if set(payload["metadata"]) != {
            "job_kind",
            "session_date",
            "status",
            "row_count",
            "model_run_id",
        }:
            raise AssertionError("adapter changed the allowed metadata surface")
        if "secret-token" in payload["subject"] or "positions" in payload["body"]:
            raise AssertionError("adapter must reconstruct outbound prose from fixed fields")
        if payload["subject"] != "Alpha daily run success":
            raise AssertionError("adapter did not construct the fixed audit subject")

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE notification_outbox SET metadata_json = ? WHERE event_id = ?",
                (
                    json.dumps({"status": "success", "positions": ["MU"]}),
                    "daily:2026-07-10:config-a",
                ),
            )
            connection.commit()
        failed = run(db_path)
        if failed.returncode == 0 or "non-allowlisted metadata" not in failed.stderr:
            raise AssertionError("private outbox metadata must fail closed")

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE notification_outbox SET metadata_json = ? WHERE event_id = ?",
                (
                    json.dumps(
                        {
                            "job_kind": "daily",
                            "session_date": "2026-07-10",
                            "status": "success",
                            "next_action": "Bearer secret-token",
                        }
                    ),
                    "daily:2026-07-10:config-a",
                ),
            )
            connection.commit()
        failed = run(db_path)
        if failed.returncode == 0 or "invalid notification next_action" not in failed.stderr:
            raise AssertionError("secret-like notification content must fail closed")

    print("alpha notification adapter selftest ok")
    return 0


def create_fixture(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE notification_outbox (
                event_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        metadata = {
            "job_kind": "daily",
            "session_date": "2026-07-10",
            "status": "success",
            "row_count": 3124,
            "model_run_id": "bayes-1",
        }
        connection.execute(
            "INSERT INTO notification_outbox VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "daily:2026-07-10:config-a",
                "alpha_run_audit",
                "Bearer secret-token",
                "positions holdings raw market payload",
                json.dumps(metadata),
                "{}",
                "pending",
                "2026-07-11T00:00:00Z",
            ),
        )


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "next", "--db", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )


if __name__ == "__main__":
    sys.exit(main())
