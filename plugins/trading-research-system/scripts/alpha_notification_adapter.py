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
}
REQUIRED_METADATA = {"job_kind", "session_date", "status"}
ALLOWED_JOB_KINDS = {"daily", "weekly", "monthly"}
ALLOWED_STATUSES = {"success", "failed"}
ALLOWED_PROMOTION_BLOCKERS = {
    "point-in-time universe unavailable",
    "fewer than 20 shadow trading days",
    "Sol review not approved",
}
ALLOWED_NEXT_ACTIONS = {
    "none",
    "review_failed_run",
    "configure_point_in_time_universe",
    "review_promotion_blockers",
    "approve_or_reject_promotion",
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
    stored = {
        "event_id": str(row["event_id"]),
        "kind": str(row["kind"]),
        "metadata": json.loads(row["metadata_json"]),
    }
    validate_event(stored)
    return build_outbound_event(stored)


def validate_event(event: dict[str, Any]) -> None:
    if event["kind"] not in ALLOWED_KINDS:
        raise ValueError(f"non-allowlisted event kind: {event['kind']}")
    if not event["event_id"].strip() or len(event["event_id"]) > 200:
        raise ValueError("invalid notification event id")
    metadata = event["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("notification metadata must be an object")
    extra = sorted(set(metadata) - ALLOWED_METADATA)
    if extra:
        raise ValueError(f"non-allowlisted metadata: {', '.join(extra)}")
    missing = sorted(REQUIRED_METADATA - set(metadata))
    if missing:
        raise ValueError(f"notification metadata missing fields: {', '.join(missing)}")
    validate_metadata(metadata)
    searchable = json.dumps(event, ensure_ascii=False, sort_keys=True)
    if any(pattern.search(searchable) for pattern in FORBIDDEN_CONTENT):
        raise ValueError("forbidden notification content")


def validate_metadata(metadata: dict[str, Any]) -> None:
    if metadata["job_kind"] not in ALLOWED_JOB_KINDS:
        raise ValueError("invalid notification job_kind")
    if metadata["status"] not in ALLOWED_STATUSES:
        raise ValueError("invalid notification status")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(metadata["session_date"])):
        raise ValueError("invalid notification session_date")
    if "row_count" in metadata and (
        isinstance(metadata["row_count"], bool)
        or not isinstance(metadata["row_count"], int)
        or metadata["row_count"] < 0
    ):
        raise ValueError("invalid notification row_count")
    if "model_run_id" in metadata and not safe_token(metadata["model_run_id"]):
        raise ValueError("invalid notification model_run_id")
    if "report_path" in metadata:
        report_path = str(metadata["report_path"])
        if (
            report_path.startswith("/")
            or ".." in Path(report_path).parts
            or not re.fullmatch(r"[A-Za-z0-9._/\-]{1,200}", report_path)
        ):
            raise ValueError("invalid notification report_path")
    if "report_fingerprint" in metadata and not re.fullmatch(
        r"sha256:[0-9a-f]{64}", str(metadata["report_fingerprint"])
    ):
        raise ValueError("invalid notification report_fingerprint")
    if "promotion_blockers" in metadata:
        blockers = metadata["promotion_blockers"]
        if not isinstance(blockers, list) or any(
            blocker not in ALLOWED_PROMOTION_BLOCKERS for blocker in blockers
        ):
            raise ValueError("invalid notification promotion_blockers")
    if "next_action" in metadata and metadata["next_action"] not in ALLOWED_NEXT_ACTIONS:
        raise ValueError("invalid notification next_action")


def safe_token(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"[A-Za-z0-9._:\-]{1,128}", value)
    )


def build_outbound_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event["metadata"]
    subject = f"Alpha {metadata['job_kind']} run {metadata['status']}"
    labels = (
        ("job kind", "job_kind"),
        ("session date", "session_date"),
        ("status", "status"),
        ("row count", "row_count"),
        ("model run id", "model_run_id"),
        ("report path", "report_path"),
        ("report fingerprint", "report_fingerprint"),
        ("promotion blockers", "promotion_blockers"),
        ("next action", "next_action"),
    )
    lines: list[str] = []
    for label, key in labels:
        if key not in metadata:
            continue
        value = metadata[key]
        rendered = "; ".join(value) if isinstance(value, list) else str(value)
        lines.append(f"{label}: {rendered}")
    return {
        "event_id": event["event_id"],
        "kind": event["kind"],
        "subject": subject,
        "body": "\n".join(lines),
        "metadata": metadata,
    }


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
