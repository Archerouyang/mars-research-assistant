#!/usr/bin/env python3
"""Self-test saved IBKR connector JSON normalization into portfolio_snapshot.csv."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ibkr_connector_adapter.py"
FIXTURES = ROOT / "assets" / "fixtures"
EXPECTED = FIXTURES / "expected" / "ibkr-connector-adapter-2026-06-24.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "portfolio_snapshot.csv"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--positions-json",
                str(FIXTURES / "input" / "ibkr-connector-positions-2026-06-24.json"),
                "--balances-json",
                str(FIXTURES / "input" / "ibkr-connector-balances-2026-06-24.json"),
                "--output",
                str(output),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--account-id",
                "SIM-IBKR",
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
            raise AssertionError(f"IBKR connector adapter mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

        if "No order actions" not in result.stdout:
            raise AssertionError("adapter output must disclose no order actions")
        if "consumed saved IBKR connector JSON only" not in result.stdout:
            raise AssertionError("adapter output must disclose saved JSON boundary")

    print("IBKR connector adapter selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
