#!/usr/bin/env python3
"""Self-test runtime bootstrap initializes only blank private runtime files."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap_runtime.py"
HEALTH = ROOT / "scripts" / "runtime_health.py"
DATE = "2026-07-06"


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
        runtime_dir = Path(raw_tmp) / "dailytrades-runtime"

        dry_run = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--dry-run",
            ]
        )
        require(dry_run.returncode == 0, dry_run.stderr or dry_run.stdout)
        require("DRY RUN" in dry_run.stdout, "dry run output should be explicit")
        require(not runtime_dir.exists(), "dry run must not create runtime files")

        first = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
            ]
        )
        require(first.returncode == 0, first.stderr or first.stdout)
        require((runtime_dir / "market-plan.md").is_file(), "market-plan.md missing")
        require((runtime_dir / "trading-profile.md").is_file(), "trading-profile.md missing")
        require((runtime_dir / "ops-state.md").is_file(), "ops-state.md missing")
        require((runtime_dir / "config.toml").is_file(), "config.toml missing")
        require((runtime_dir / "updates" / f"{DATE}.md").is_file(), "update note missing")
        require((runtime_dir / "momentum").is_dir(), "momentum dir missing")
        require((runtime_dir / "charts").is_dir(), "charts dir missing")
        require((runtime_dir / "daily" / DATE / "intraday-watchlist.csv").is_file(), "daily templates missing")

        user_text = "USER PLAN MUST STAY\n"
        (runtime_dir / "market-plan.md").write_text(user_text, encoding="utf-8")
        second = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
            ]
        )
        require(second.returncode == 0, second.stderr or second.stdout)
        require(
            (runtime_dir / "market-plan.md").read_text(encoding="utf-8") == user_text,
            "bootstrap must not overwrite existing user files by default",
        )
        require("kept existing" in second.stdout, "rerun should report kept existing files")

        health = run_command(
            [
                str(HEALTH),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--format",
                "json",
                "--broker-source",
                "manual=available",
            ]
        )
        require(health.returncode == 0, health.stderr or health.stdout)
        payload = json.loads(health.stdout)
        by_name = {item["id"]: item for item in payload["checks"]}
        for name in ("runtime_dir", "market_plan", "trading_profile", "updates_dir", "daily_dir"):
            require(by_name[name]["status"] == "available", f"{name} should be available after bootstrap")

    print("runtime bootstrap selftest ok")


if __name__ == "__main__":
    main()
