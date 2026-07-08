#!/usr/bin/env python3
"""Self-test runtime health output stays private and machine-readable."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "runtime_health.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        runtime_dir = Path(tmp) / "runtime"
        runtime_dir.mkdir()
        (runtime_dir / "market-plan.md").write_text("PRIVATE MARKET PLAN SECRET\n", encoding="utf-8")
        (runtime_dir / "updates").mkdir()
        daily_dir = runtime_dir / "daily" / "2026-07-04"
        daily_dir.mkdir(parents=True)
        (daily_dir / "trade-plans.csv").write_text("PRIVATE TRADE PLAN SECRET\n", encoding="utf-8")
        (runtime_dir / "momentum").mkdir()
        (runtime_dir / "momentum" / "kvn.sqlite").write_bytes(b"not a real sqlite fixture")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                "2026-07-04",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            raise AssertionError(f"runtime health command failed: {result.stderr or result.stdout}")

        if "PRIVATE" in result.stdout:
            raise AssertionError("runtime health leaked private file content")

        payload = json.loads(result.stdout)
        if payload.get("current_mode") != "dry-run":
            raise AssertionError(f"current_mode: expected 'dry-run', got {payload.get('current_mode')!r}")

        capabilities = {item["id"]: item for item in payload["source_capability_health"]}
        assert_status(capabilities, "longbridge_broker_skill", "unauthorized")
        assert_status(capabilities, "longbridge_terminal_cli", "unauthorized")
        assert_status(capabilities, "longbridge_macrodata", "unauthorized")
        assert_status(capabilities, "ibkr_connector", "unauthorized")
        assert_status(capabilities, "manual_snapshot", "missing")

        checks = {item["id"]: item for item in payload["checks"]}

        assert_status(checks, "market_plan", "available")
        assert_status(checks, "trading_profile", "missing")
        assert_status(checks, "updates_dir", "available")
        assert_status(checks, "daily_dir", "available")
        assert_status(checks, "kvn_store", "available")
        assert_status(checks, "longbridge_broker_source", "unauthorized")
        assert_status(checks, "ibkr_broker_source", "unauthorized")
        assert_status(checks, "broker_sources", "unauthorized")

        sourced_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                "2026-07-04",
                "--format",
                "json",
                "--broker-source",
                "longbridge=available",
                "--broker-source",
                "ibkr=not_installed",
                "--broker-source",
                "manual=available",
                "--source-capability",
                "longbridge_broker_skill=not_installed",
                "--source-capability",
                "longbridge_terminal_cli=available",
                "--source-capability",
                "longbridge_macrodata=not_installed",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        if sourced_result.returncode != 0:
            raise AssertionError(f"runtime health sourced command failed: {sourced_result.stderr or sourced_result.stdout}")

        sourced_payload = json.loads(sourced_result.stdout)
        if sourced_payload.get("current_mode") != "live read-only":
            raise AssertionError(
                f"current_mode: expected 'live read-only', got {sourced_payload.get('current_mode')!r}"
            )

        sourced_checks = {item["id"]: item for item in sourced_payload["checks"]}
        assert_status(sourced_checks, "longbridge_broker_source", "available")
        assert_status(sourced_checks, "longbridge_terminal_cli", "available")
        assert_status(sourced_checks, "ibkr_broker_source", "not_installed")
        assert_status(sourced_checks, "manual_snapshot_source", "available")
        assert_status(sourced_checks, "broker_sources", "available")
        sourced_capabilities = {item["id"]: item for item in sourced_payload["source_capability_health"]}
        assert_status(sourced_capabilities, "longbridge_broker_skill", "not_installed")
        assert_status(sourced_capabilities, "longbridge_terminal_cli", "available")
        assert_status(sourced_capabilities, "longbridge_macrodata", "not_installed")
        assert_status(sourced_capabilities, "ibkr_connector", "not_installed")

    print("runtime health selftest ok")
    return 0


def assert_status(checks: dict[str, dict[str, str]], check_id: str, status: str) -> None:
    actual = checks[check_id]["status"]
    if actual != status:
        raise AssertionError(f"{check_id}: expected {status!r}, got {actual!r}")


if __name__ == "__main__":
    sys.exit(main())
