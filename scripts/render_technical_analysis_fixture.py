#!/usr/bin/env python3
"""Run the package-local technical-analysis renderer against an offline fixture."""

from pathlib import Path
import runpy


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "technical-analysis"
    / "scripts"
    / "technical_analysis.py"
)


if __name__ == "__main__":
    runpy.run_path(str(RUNTIME), run_name="__main__")
