#!/usr/bin/env python3
"""Self-test the full OHLCV-backed price-action rendering path.

Setup-key completeness, OHLCV precedence, and file side effects are covered by
the repo-level Behavior Contract Matrix gate.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile

from contract_suite import PluginPaths


def main() -> None:
    paths = PluginPaths.from_script(__file__)
    script = paths.scripts / "price_action_rollforward.py"
    fixture = paths.fixture_input / "chart-ohlcv-qqq-sample.json"

    help_result = subprocess.run(
        [sys.executable, str(script), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    if help_result.returncode != 0:
        raise AssertionError(help_result.stderr or help_result.stdout)
    normalized_help = " ".join(help_result.stdout.split())
    if "Explicitly confirmed ticker required by the complete setup key" not in normalized_help:
        raise AssertionError(
            "--ticker help must describe the explicit pre-payload setup-key requirement"
        )
    if "defaults to JSON symbol" in normalized_help:
        raise AssertionError("--ticker help must not imply ticker can be inferred from OHLCV")

    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "qqq-pa.md"
        display_output = Path(raw_tmp) / "qqq-pa-scenario-board.svg"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--ohlcv-json",
                str(fixture),
                "--ticker",
                "QQQ",
                "--date",
                "2026-06-12",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H/15m",
                "--trade-horizon",
                "medium-term swing",
                "--instrument",
                "equity",
                "--analysis-intent",
                "position_reassessment",
                "--ohlcv-status",
                "authorized",
                "--display-output",
                str(display_output),
                "--cost-context",
                "long-term core ETF; add/TP only; do not treat TP as stop loss",
                "--event-context",
                "FOMC next week; watch 10Y/30Y and VIX confirmation",
                "--prior-analysis",
                "Prior plan: add only after 715-711 reclaim; TP/rebalance near 748.63",
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)

        text = output.read_text(encoding="utf-8")
        for term in (
            "# Price Action Rollforward - QQQ",
            "主分析时间框架 | 1D",
            "trigger zone: add only after confirmation",
            "prior high / TP/rebalance watch",
            "## PA Scenario Board",
            f"![PA Scenario Board]({display_output.resolve()})",
        ):
            if term not in text:
                raise AssertionError(f"missing {term!r} in output:\n{text}")
        if not display_output.is_file():
            raise AssertionError("full rendering path must create a PA Scenario Board")

    print("price action rollforward selftest ok")


if __name__ == "__main__":
    main()
