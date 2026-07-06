#!/usr/bin/env python3
"""Self-test read-only broker snapshot ingestion into portfolio_snapshot.csv."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "broker_snapshot_ingest.py"
FIXTURES = ROOT / "assets" / "fixtures"
EXPECTED = FIXTURES / "expected" / "broker-snapshot-ingest-2026-06-24.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "portfolio_snapshot.csv"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input",
                f"IBKR:{FIXTURES / 'input' / 'broker-positions-ibkr-2026-06-24.csv'}",
                "--input",
                f"Longbridge:{FIXTURES / 'input' / 'broker-positions-longbridge-2026-06-24.csv'}",
                "--output",
                str(output),
                "--as-of",
                "2026-06-24T20:00:00Z",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)

        expected = EXPECTED.read_text(encoding="utf-8").strip()
        actual = output.read_text(encoding="utf-8").strip()
        if actual != expected:
            raise AssertionError(f"broker snapshot ingest mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

        if "No live broker reads" not in result.stdout:
            raise AssertionError("ingest output must disclose no live broker reads")

    print("broker snapshot ingest selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
