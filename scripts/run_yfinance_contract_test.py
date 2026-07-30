#!/usr/bin/env python3
"""Run the package-local yfinance contract check before a release."""

from pathlib import Path
import runpy


ANALYSIS_ENTRYPOINT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "mars-research-assistant"
    / "skills"
    / "technical-analysis"
    / "scripts"
    / "analyze_with_yfinance.py"
)


if __name__ == "__main__":
    runpy.run_path(str(ANALYSIS_ENTRYPOINT), run_name="__main__")
