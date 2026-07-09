#!/usr/bin/env python3
"""Self-test macro-panel runtime preparation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_macro_panel.py"
HEALTH = ROOT / "scripts" / "runtime_health.py"
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "longbridge-macrodata-2026-06-24.json"
DATE = "2026-06-24"


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        runtime_dir = Path(raw_tmp) / "runtime"
        target = runtime_dir / "daily" / DATE / "macro-panel.json"

        dry_run_missing = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--dry-run",
            ]
        )
        require(dry_run_missing.returncode == 0, dry_run_missing.stderr or dry_run_missing.stdout)
        require("DRY RUN" in dry_run_missing.stdout, "dry run should be explicit")
        require("macrodata JSON was not supplied" in dry_run_missing.stdout, "missing input guidance absent")
        require("No live macrodata reads" in dry_run_missing.stdout, "live macrodata safety boundary missing")
        require(not target.exists(), "dry run without input must not create macro-panel.json")

        write = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--macrodata-json",
                str(FIXTURE),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--data-status",
                "fixture",
            ]
        )
        require(write.returncode == 0, write.stderr or write.stdout)
        require(target.is_file(), "macro-panel.json missing after fixture write")
        panel = json.loads(target.read_text(encoding="utf-8"))
        require(panel["source_capability"] == "longbridge_macrodata", "wrong source capability")
        require(panel["strategy_posture"] == "balanced", "unexpected fixture strategy posture")
        require("No order actions" in write.stdout, "order safety boundary missing")

        existing = target.read_text(encoding="utf-8")
        target.write_text(existing.replace('"balanced"', '"USER_KEEP"', 1), encoding="utf-8")
        keep = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--macrodata-json",
                str(FIXTURE),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--data-status",
                "fixture",
            ]
        )
        require(keep.returncode == 0, keep.stderr or keep.stdout)
        require("kept existing" in keep.stdout, "existing macro panel should be kept by default")
        require("USER_KEEP" in target.read_text(encoding="utf-8"), "existing macro panel was overwritten")

        overwrite = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--macrodata-json",
                str(FIXTURE),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--data-status",
                "fixture",
                "--overwrite",
            ]
        )
        require(overwrite.returncode == 0, overwrite.stderr or overwrite.stdout)
        require("USER_KEEP" not in target.read_text(encoding="utf-8"), "overwrite should refresh macro panel")

        health = run_command(
            [
                str(HEALTH),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--format",
                "json",
                "--source-capability",
                "longbridge_macrodata=available",
            ]
        )
        require(health.returncode == 0, health.stderr or health.stdout)
        payload = json.loads(health.stdout)
        checks = {item["id"]: item for item in payload["checks"]}
        require(checks["macro_panel"]["status"] == "available", "runtime health should see macro panel")

    print("prepare macro panel selftest ok")


if __name__ == "__main__":
    main()
