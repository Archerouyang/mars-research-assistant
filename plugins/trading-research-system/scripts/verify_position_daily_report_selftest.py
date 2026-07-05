#!/usr/bin/env python3
"""Self-test position daily report rendering against the fixture package."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "position_daily_report.py"
DAILY_DIR = ROOT / "assets" / "fixtures" / "runtime" / "active-market-plan-2026-06-24" / "daily" / "2026-06-24"
EXPECTED = DAILY_DIR / "position-daily-report.md"


def main() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(DAILY_DIR / "portfolio_snapshot.csv"),
            "--date",
            "2026-06-24",
            "--source",
            "broker-live fixture",
            "--data-status",
            "fixture",
            "--snapshot-saved",
            "fixture",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)

    expected = EXPECTED.read_text(encoding="utf-8").strip()
    actual = result.stdout.strip()
    if actual != expected:
        raise AssertionError(f"position daily report mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

    print("position daily report selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
