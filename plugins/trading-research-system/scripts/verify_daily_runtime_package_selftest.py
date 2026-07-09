#!/usr/bin/env python3
"""Self-test Daily Ops runtime package preparation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare_daily_runtime.py"
HEALTH = ROOT / "scripts" / "runtime_health.py"
SCAN = ROOT / "scripts" / "intraday_scan.py"
DATE = "2026-07-08"


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


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def main() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        runtime_dir = Path(raw_tmp) / "dailytrades-runtime"

        dry_run = run_command(
            [
                str(PREPARE),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--dry-run",
            ]
        )
        require(dry_run.returncode == 0, dry_run.stderr or dry_run.stdout)
        require("DRY RUN" in dry_run.stdout, "dry run output should be explicit")
        require("No live broker reads" in dry_run.stdout, "safety boundary missing")
        require(not runtime_dir.exists(), "dry run must not create runtime files")

        first = run_command(
            [
                str(PREPARE),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
            ]
        )
        require(first.returncode == 0, first.stderr or first.stdout)
        require((runtime_dir / "ops-state.md").is_file(), "ops-state.md missing")
        require((runtime_dir / "updates" / f"{DATE}.md").is_file(), "daily update note missing")

        daily_dir = runtime_dir / "daily" / DATE
        trade_plans = daily_dir / "trade-plans.csv"
        intraday = daily_dir / "intraday-watchlist.csv"
        require(trade_plans.is_file(), "trade-plans.csv missing")
        require(intraday.is_file(), "intraday-watchlist.csv missing")

        trade_rows = read_csv_rows(trade_plans)
        intraday_rows = read_csv_rows(intraday)
        require(trade_rows == [list(CSV_SCHEMAS["trade-plans.csv"])], "trade plans should be header-only")
        require(
            intraday_rows == [list(CSV_SCHEMAS["intraday-watchlist.csv"])],
            "intraday watchlist should be header-only",
        )
        require("QQQ 0DTE" not in trade_plans.read_text(encoding="utf-8"), "runtime template leaked sample trade")
        require("QQQ 0DTE" not in intraday.read_text(encoding="utf-8"), "runtime template leaked sample setup")

        user_text = ",".join(CSV_SCHEMAS["trade-plans.csv"]) + "\nUSER,PLAN,MUST,STAY\n"
        trade_plans.write_text(user_text, encoding="utf-8")
        second = run_command(
            [
                str(PREPARE),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
            ]
        )
        require(second.returncode == 0, second.stderr or second.stdout)
        require(trade_plans.read_text(encoding="utf-8") == user_text, "must not overwrite user trade plans")
        require("kept existing" in second.stdout, "rerun should report kept existing files")

        intraday.write_text(",".join(CSV_SCHEMAS["intraday-watchlist.csv"]) + "\n", encoding="utf-8")
        scan = run_command([str(SCAN), str(intraday), "--date", DATE])
        require(scan.returncode == 0, scan.stderr or scan.stdout)
        require("没有已准备的 setup 行" in scan.stdout, "empty scan should guide instead of failing")
        require("不是买卖指令" in scan.stdout, "empty scan should keep safety boundary")

        health = run_command(
            [
                str(HEALTH),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--format",
                "json",
            ]
        )
        require(health.returncode == 0, health.stderr or health.stdout)
        payload = json.loads(health.stdout)
        by_name = {item["id"]: item for item in payload["checks"]}
        for name in ("daily_dir", "trade_plans", "intraday_watchlist"):
            require(by_name[name]["status"] == "available", f"{name} should be available after package prep")

    print("daily runtime package selftest ok")


if __name__ == "__main__":
    main()
