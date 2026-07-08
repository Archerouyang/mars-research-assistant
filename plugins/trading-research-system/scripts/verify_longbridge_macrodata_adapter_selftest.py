#!/usr/bin/env python3
"""Self-test Longbridge macrodata adapter into macro-panel.json."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "longbridge_macrodata_adapter.py"
FIXTURES = ROOT / "assets" / "fixtures"
EXPECTED = FIXTURES / "expected" / "longbridge-macro-panel-2026-06-24.json"


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "macro-panel.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--macrodata-json",
                str(FIXTURES / "input" / "longbridge-macrodata-2026-06-24.json"),
                "--output",
                str(output),
                "--as-of",
                "2026-06-24T20:00:00Z",
                "--data-status",
                "fixture",
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
            raise AssertionError(f"Longbridge macrodata adapter mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")

        if "No live macrodata reads" not in result.stdout:
            raise AssertionError("adapter output must disclose no live macrodata reads")
        if "not a broker account source" not in result.stdout:
            raise AssertionError("adapter output must disclose macrodata is not a broker account source")
        if "No order actions" not in result.stdout:
            raise AssertionError("adapter output must disclose no order actions")

    print("Longbridge macrodata adapter selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
