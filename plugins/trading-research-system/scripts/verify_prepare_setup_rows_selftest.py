#!/usr/bin/env python3
"""Self-test daily setup row preparation into scanner-ready CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys
import tempfile

from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_setup_rows.py"
SCAN = ROOT / "scripts" / "intraday_scan.py"
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "confirmed-setups-2026-06-24.json"
DATE = "2026-06-24"


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], text=True, capture_output=True, check=False)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        runtime_dir = Path(raw_tmp) / "runtime"
        daily_dir = runtime_dir / "daily" / DATE
        daily_dir.mkdir(parents=True)
        trade_plans = daily_dir / "trade-plans.csv"
        intraday_watchlist = daily_dir / "intraday-watchlist.csv"
        trade_plans.write_text(",".join(CSV_SCHEMAS["trade-plans.csv"]) + "\n", encoding="utf-8")
        intraday_watchlist.write_text(",".join(CSV_SCHEMAS["intraday-watchlist.csv"]) + "\n", encoding="utf-8")

        dry_run = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--setup-json",
                str(FIXTURE),
                "--dry-run",
            ]
        )
        require(dry_run.returncode == 0, dry_run.stderr or dry_run.stdout)
        require("DRY RUN Daily setup rows target" in dry_run.stdout, "dry run target missing")
        require("would fill header-only" in dry_run.stdout, "dry run should identify header-only files")
        require("No live broker reads" in dry_run.stdout, "broker safety boundary missing")
        require("no order actions" in dry_run.stdout, "order safety boundary missing")
        require(not csv_rows(trade_plans), "dry run must not write trade plan rows")
        require(not csv_rows(intraday_watchlist), "dry run must not write watchlist rows")

        write = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--setup-json",
                str(FIXTURE),
            ]
        )
        require(write.returncode == 0, write.stderr or write.stdout)
        require("confirmed setups: 2" in write.stdout, "setup count missing")
        require("wrote" in write.stdout, "write output missing")

        trade_rows = csv_rows(trade_plans)
        watch_rows = csv_rows(intraday_watchlist)
        require(len(trade_rows) == 2, f"expected 2 trade rows, got {len(trade_rows)}")
        require(len(watch_rows) == 2, f"expected 2 watch rows, got {len(watch_rows)}")
        require(trade_rows[0]["setup_id"] == "qqq-0dte-breakout-pullback", "trade setup id mismatch")
        require(watch_rows[0]["current_status"] == "triggered", "watch status mismatch")
        require(watch_rows[0]["execution_check_required"] == "yes", "execution check flag mismatch")

        keep = run_command(
            [
                str(SCRIPT),
                "--runtime-dir",
                str(runtime_dir),
                "--date",
                DATE,
                "--setup-json",
                str(FIXTURE),
            ]
        )
        require(keep.returncode == 0, keep.stderr or keep.stdout)
        require("kept existing populated" in keep.stdout, "populated files should be kept without overwrite")

        scan = run_command([str(SCAN), str(intraday_watchlist), "--date", DATE])
        require(scan.returncode == 0, scan.stderr or scan.stdout)
        require("qqq-0dte-breakout-pullback | triggered" in scan.stdout, "scanner did not see triggered setup")
        require("soxx-sector-confirmation | needs_review" in scan.stdout, "scanner did not see needs_review setup")
        require(
            "execution_check_required; confirm trigger-timeframe follow-through and risk" in scan.stdout,
            "scanner execution-check guidance missing",
        )

    print("prepare setup rows selftest ok")


if __name__ == "__main__":
    main()
