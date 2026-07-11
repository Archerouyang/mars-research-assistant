#!/usr/bin/env python3
"""Read and validate one sanitized Alpha audit event without mutating outbox state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any


ALLOWED_KINDS = {"alpha_run_audit"}
ALLOWED_METADATA = {
    "job_kind",
    "session_date",
    "status",
    "row_count",
    "model_run_id",
    "report_path",
    "report_fingerprint",
    "promotion_blockers",
    "next_action",
    "error_code",
}
FORBIDDEN_CONTENT = (
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"apikey", re.IGNORECASE),
    re.compile(r"bearer\s+", re.IGNORECASE),
    re.compile(r"\b(access|refresh)?_?token\b", re.IGNORECASE),
    re.compile(r"\b(password|secret)\b", re.IGNORECASE),
    re.compile(r"\b(account|positions?|holdings?|executions?)\b", re.IGNORECASE),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read one pending Alpha audit event through a fail-closed allowlist."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    next_event = subparsers.add_parser("next")
    next_event.add_argument("--db", required=True)
    return parser.parse_args()


def connect_read_only(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"notification outbox not found: {resolved}")
    connection = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    columns = {
        str(row[1])
        for row in connection.execute(
            "PRAGMA table_info(notification_outbox)"
        ).fetchall()
    }
    required = {
        "event_id",
        "kind",
        "subject",
        "body",
        "metadata_json",
        "status",
        "created_at",
    }
    missing = sorted(required - columns)
    if missing:
        connection.close()
        raise ValueError(f"notification outbox schema missing columns: {missing}")
    return connection


def next_validated(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT event_id, kind, subject, body, metadata_json
        FROM notification_outbox
        WHERE status = 'pending'
        ORDER BY created_at, event_id
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    event = {
        "event_id": str(row["event_id"]),
        "kind": str(row["kind"]),
        "subject": str(row["subject"]),
        "body": str(row["body"]),
        "metadata": json.loads(row["metadata_json"]),
    }
    validate_event(event)
    return event


def validate_event(event: dict[str, Any]) -> None:
    if event["kind"] not in ALLOWED_KINDS:
        raise ValueError(f"non-allowlisted event kind: {event['kind']}")
    if not event["event_id"].strip() or len(event["event_id"]) > 200:
        raise ValueError("invalid notification event id")
    if not event["subject"].strip() or len(event["subject"]) > 200:
        raise ValueError("invalid notification subject")
    if not event["body"].strip() or len(event["body"]) > 4000:
        raise ValueError("invalid notification body")
    metadata = event["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("notification metadata must be an object")
    extra = sorted(set(metadata) - ALLOWED_METADATA)
    if extra:
        raise ValueError(f"non-allowlisted metadata: {', '.join(extra)}")
    for key, value in metadata.items():
        if not valid_metadata_value(value):
            raise ValueError(f"invalid notification metadata value: {key}")
    searchable = json.dumps(event, ensure_ascii=False, sort_keys=True)
    if any(pattern.search(searchable) for pattern in FORBIDDEN_CONTENT):
        raise ValueError("forbidden notification content")


def valid_metadata_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def main() -> int:
    args = parse_args()
    try:
        with connect_read_only(Path(args.db)) as connection:
            event = next_validated(connection)
    except (ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"alpha notification error: {error}", file=sys.stderr)
        return 1
    print("null" if event is None else json.dumps(event, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
