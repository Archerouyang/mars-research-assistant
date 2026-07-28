#!/usr/bin/env python3
"""Run the package-local yfinance contract check before a release."""

from pathlib import Path
import runpy


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "technical-analysis"
    / "scripts"
    / "run_yfinance_analysis.py"
)


if __name__ == "__main__":
    runpy.run_path(str(RUNTIME), run_name="__main__")
