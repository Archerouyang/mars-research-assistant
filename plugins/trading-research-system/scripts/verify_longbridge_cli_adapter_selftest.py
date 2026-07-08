#!/usr/bin/env python3
"""Self-test Longbridge CLI JSON adapter into portfolio_snapshot.csv."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "longbridge_cli_adapter.py"
FIXTURES = ROOT / "assets" / "fixtures"
EXPECTED = FIXTURES / "expected" / "longbridge-cli-adapter-2026-06-24.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "portfolio_snapshot.csv"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--portfolio-json",
                str(FIXTURES / "input" / "longbridge-portfolio-cli-2026-06-24.json"),
                "--output",
                str(output),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--account-id",
                "SIM-LB",
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
            raise AssertionError(f"Longbridge CLI adapter mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

        if "No live broker reads" not in result.stdout:
            raise AssertionError("adapter output must disclose no live broker reads")
        if "No order actions" not in result.stdout:
            raise AssertionError("adapter output must disclose no order actions")

    print("Longbridge CLI adapter selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
