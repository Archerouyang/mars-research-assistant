#!/usr/bin/env python3
"""Self-test portfolio snapshot repair for stale product/theme mappings."""

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repair_portfolio_snapshot.py"
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "portfolio-snapshot-stale-2026-06-24.csv"


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["symbol"]: row for row in csv.DictReader(handle)}


def expect(row: dict[str, str], field: str, expected: str) -> None:
    actual = row.get(field)
    if actual != expected:
        raise AssertionError(f"{row.get('symbol')} {field}: expected {expected!r}, actual {actual!r}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "portfolio_snapshot.csv"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(FIXTURE),
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)

        rows = read_rows(output)
        expect(rows["QQQ.US"], "underlying", "QQQ")
        expect(rows["QQQ.US"], "instrument_type", "etf_common")
        expect(rows["QQQ.US"], "theme_id", "tech_beta")
        expect(rows["SOXX"], "instrument_type", "sector_etf")
        expect(rows["SOXX"], "theme_id", "semiconductor")
        expect(rows["TSMX.US"], "instrument_type", "leveraged_etf")
        expect(rows["TSMX.US"], "theme_id", "ai_hardware_leverage")
        expect(rows["CRDO.US"], "theme_id", "ai_infra_momentum")
        expect(rows["CASH"], "instrument_type", "cash")
        expect(rows["CASH"], "theme_id", "cash")

        for symbol in ("QQQ.US", "TSMX.US", "CRDO.US"):
            if "Snapshot repair:" not in rows[symbol]["notes"]:
                raise AssertionError(f"{symbol} should record Snapshot repair note")

        if "No live broker reads" not in result.stdout:
            raise AssertionError("repair output must disclose no live broker reads")
        if "No order actions" not in result.stdout:
            raise AssertionError("repair output must disclose no order actions")

    print("repair portfolio snapshot selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
