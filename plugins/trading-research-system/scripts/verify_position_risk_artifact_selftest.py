#!/usr/bin/env python3
"""Behavior tests for the Position Risk synthetic artifact renderer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "position_risk_artifact.py"


def run_case(tmp: Path, name: str, payload: dict[str, object]) -> str:
    input_path = tmp / f"{name}.json"
    output_path = tmp / f"{name}.svg"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(input_path), "--display-output", str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return output_path.read_text(encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        empty = run_case(
            tmp,
            "empty",
            {"title": "Position Risk", "data_status": "empty", "source": "synthetic fixture"},
        )
        if "No exposure data provided" not in empty or "0.0%" in empty:
            raise AssertionError("empty input must disclose missing data without invented zero exposure")

        partial = run_case(
            tmp,
            "partial",
            {
                "title": "Position Risk",
                "data_status": "partial",
                "source": "synthetic fixture",
                "concentration": [{"label": "SYNTH-A", "weight": 0.42}],
                "missing_dimensions": ["instrument", "theme", "broker"],
            },
        )
        for term in ("SYNTH-A", "42.0%", "Not provided", "partial"):
            if term not in partial:
                raise AssertionError(f"partial input missing {term}")
        if "SYNTH-B" in partial:
            raise AssertionError("partial input must not invent additional positions")

        representative = run_case(
            tmp,
            "representative",
            {
                "title": "Position Risk",
                "subtitle": "Synthetic fixture; not a real account",
                "data_status": "synthetic_complete",
                "source": "synthetic fixture",
                "as_of": "2026-07-14",
                "concentration": [
                    {"label": "SYNTH-A", "weight": 0.32},
                    {"label": "SYNTH-B", "weight": 0.21},
                ],
                "instrument": [
                    {"label": "Equity", "weight": 0.62},
                    {"label": "ETF", "weight": 0.38},
                ],
                "theme": [
                    {"label": "AI hardware", "weight": 0.44},
                    {"label": "Broad market", "weight": 0.36},
                    {"label": "Defensive", "weight": 0.20},
                ],
                "broker": [
                    {"label": "Broker A", "weight": 0.58},
                    {"label": "Broker B", "weight": 0.42},
                ],
                "risk_flags": [
                    {"severity": "attention", "label": "Theme concentration", "detail": "AI hardware is 44%."},
                    {"severity": "risk", "label": "Single-name concentration", "detail": "SYNTH-A is 32%."},
                ],
            },
        )
        for term in (
            "concentration",
            "instrument / product",
            "theme exposure",
            "broker exposure",
            "Theme concentration",
            "Single-name concentration",
            "Synthetic fixture",
        ):
            if term not in representative:
                raise AssertionError(f"representative input missing {term}")

    print("position risk artifact selftest ok")


if __name__ == "__main__":
    main()
