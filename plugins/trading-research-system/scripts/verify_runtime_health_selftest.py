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
        if payload.get("runtime_origin") != "explicit_argument":
            raise AssertionError(
                "runtime_origin: expected 'explicit_argument', "
                f"got {payload.get('runtime_origin')!r}"
            )
        if payload.get("startup_status") != "partial":
            raise AssertionError(
                f"startup_status: expected 'partial', got {payload.get('startup_status')!r}"
            )
        if payload.get("current_mode") != "dry-run":
            raise AssertionError(f"current_mode: expected 'dry-run', got {payload.get('current_mode')!r}")
        assert_reconciliation(
            payload,
            status="unavailable",
            confirmed_sources=[],
            excluded_sources=["longbridge", "ibkr"],
        )

        capabilities = {item["id"]: item for item in payload["source_capability_health"]}
        assert_status(capabilities, "longbridge_broker_skill", "needs_review")
        assert_status(capabilities, "longbridge_terminal_cli", "needs_review")
        assert_status(capabilities, "longbridge_macrodata", "needs_review")
        assert_status(capabilities, "official_source_fallback", "missing")
        assert_status(capabilities, "ibkr_connector", "needs_review")
        assert_status(capabilities, "manual_snapshot", "missing")

        checks = {item["id"]: item for item in payload["checks"]}

        assert_status(checks, "market_plan", "available")
        assert_status(checks, "ops_state", "missing")
        assert_status(checks, "trading_profile", "missing")
        assert_status(checks, "updates_dir", "available")
        assert_status(checks, "daily_dir", "available")
        assert_status(checks, "macro_panel", "missing")
        assert_status(checks, "portfolio_snapshot", "missing")
        assert_status(checks, "kvn_store", "available")
        assert_status(checks, "longbridge_broker_source", "needs_review")
        assert_status(checks, "ibkr_broker_source", "needs_review")
        assert_status(checks, "broker_sources", "needs_review")

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
                "--source-capability",
                "official_source_fallback=available",
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
        assert_status(sourced_capabilities, "official_source_fallback", "available")
        assert_status(sourced_capabilities, "ibkr_connector", "not_installed")

        for source_status in (
            "unauthorized",
            "available",
            "partial_data",
            "upstream_error",
            "empty_positions_unverified",
            "needs_review",
        ):
            status_result = subprocess.run(
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
                    f"ibkr={source_status}",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if status_result.returncode != 0:
                raise AssertionError(status_result.stderr or status_result.stdout)
            status_payload = json.loads(status_result.stdout)
            status_sources = {item["id"]: item for item in status_payload["broker_source_health"]}
            assert_status(status_sources, "ibkr", source_status)
            if source_status != "unauthorized" and "not authorized" in status_sources["ibkr"]["note"]:
                raise AssertionError(f"{source_status} must not be described as unauthorized")

        partial_result = subprocess.run(
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
                "ibkr=partial_data",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if partial_result.returncode != 0:
            raise AssertionError(partial_result.stderr or partial_result.stdout)
        partial_payload = json.loads(partial_result.stdout)
        partial_checks = {item["id"]: item for item in partial_payload["checks"]}
        assert_status(partial_checks, "broker_sources", "partial_data")
        reconciliation = partial_payload.get("portfolio_reconciliation") or {}
        if reconciliation.get("status") != "not_confirmed":
            raise AssertionError(f"partial broker merge must be not_confirmed: {reconciliation!r}")
        if reconciliation.get("confirmed_sources") != ["longbridge"]:
            raise AssertionError(f"unexpected confirmed sources: {reconciliation!r}")
        if reconciliation.get("excluded_sources") != ["ibkr"]:
            raise AssertionError(f"partial IBKR must be excluded: {reconciliation!r}")

        uninitialized_runtime = Path(tmp) / "uninitialized-runtime"
        uninitialized_payload = run_health(uninitialized_runtime, "2026-07-04")
        if uninitialized_payload.get("startup_status") != "uninitialized":
            raise AssertionError(
                "missing runtime must be uninitialized: "
                f"{uninitialized_payload.get('startup_status')!r}"
            )

        ready_runtime = Path(tmp) / "ready-runtime"
        ready_runtime.mkdir()
        (ready_runtime / "market-plan.md").write_text("fixture plan\n", encoding="utf-8")
        (ready_runtime / "trading-profile.md").write_text("fixture profile\n", encoding="utf-8")
        (ready_runtime / "updates").mkdir()
        (ready_runtime / "daily" / "2026-07-04").mkdir(parents=True)
        ready_payload = run_health(
            ready_runtime,
            "2026-07-04",
            broker_sources=("longbridge=available", "ibkr=available"),
        )
        if ready_payload.get("startup_status") != "ready":
            raise AssertionError(
                f"complete runtime must be ready: {ready_payload.get('startup_status')!r}"
            )
        assert_reconciliation(
            ready_payload,
            status="confirmed",
            confirmed_sources=["longbridge", "ibkr"],
            excluded_sources=[],
        )

        (daily_dir / "macro-panel.json").write_text('{"PRIVATE": "MACRO PANEL SECRET"}\n', encoding="utf-8")
        macro_panel_result = subprocess.run(
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

        if macro_panel_result.returncode != 0:
            raise AssertionError(
                f"runtime health macro panel command failed: {macro_panel_result.stderr or macro_panel_result.stdout}"
            )
        if "PRIVATE" in macro_panel_result.stdout:
            raise AssertionError("runtime health leaked private macro-panel file content")
        macro_panel_payload = json.loads(macro_panel_result.stdout)
        macro_panel_checks = {item["id"]: item for item in macro_panel_payload["checks"]}
        assert_status(macro_panel_checks, "macro_panel", "available")

    print("runtime health selftest ok")
    return 0


def assert_status(checks: dict[str, dict[str, str]], check_id: str, status: str) -> None:
    actual = checks[check_id]["status"]
    if actual != status:
        raise AssertionError(f"{check_id}: expected {status!r}, got {actual!r}")


def run_health(
    runtime_dir: Path,
    trading_date: str,
    *,
    broker_sources: tuple[str, ...] = (),
) -> dict[str, object]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--runtime-dir",
        str(runtime_dir),
        "--date",
        trading_date,
        "--format",
        "json",
    ]
    for source in broker_sources:
        command.extend(("--broker-source", source))
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def assert_reconciliation(
    payload: dict[str, object],
    *,
    status: str,
    confirmed_sources: list[str],
    excluded_sources: list[str],
) -> None:
    reconciliation = payload.get("portfolio_reconciliation")
    if not isinstance(reconciliation, dict):
        raise AssertionError(f"missing portfolio_reconciliation: {payload!r}")
    expected = {
        "status": status,
        "confirmed_sources": confirmed_sources,
        "excluded_sources": excluded_sources,
    }
    actual = {key: reconciliation.get(key) for key in expected}
    if actual != expected:
        raise AssertionError(f"portfolio reconciliation mismatch: expected {expected!r}, got {actual!r}")


if __name__ == "__main__":
    sys.exit(main())
