#!/usr/bin/env python3
"""Self-test OHLCV-backed rolling price-action note generation."""

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
        raise AssertionError("--ticker help must describe the explicit pre-payload setup-key requirement")
    if "defaults to JSON symbol" in normalized_help:
        raise AssertionError("--ticker help must not imply ticker can be inferred from the OHLCV payload")

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
        raise AssertionError("--ticker help must describe the explicit pre-payload setup-key requirement")
    if "defaults to JSON symbol" in normalized_help:
        raise AssertionError("--ticker help must not imply ticker can be inferred from the OHLCV payload")

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
        expected_terms = (
            "# Price Action Rollforward - QQQ",
            "This is decision support only. It is not a buy/sell instruction.",
            "## 时间框架声明",
            "主分析时间框架 | 1D",
            "辅助时间框架 | 1H/15m",
            "## 上次分析对照",
            "Prior plan: add only after 715-711 reclaim",
            "## 走势强弱参考点位",
            "支撑/压力",
            "点位所属时间框架",
            "last close",
            "EMA20",
            "EMA50",
            "prior high / TP/rebalance watch",
            "## 加仓/减仓/暂停区",
            "trigger zone: add only after confirmation",
            "TP/rebalance",
            "invalidation / review zone",
            "比例式加减仓",
            "## 成本/买入记录",
            "long-term core ETF",
            "## 本周事件映射",
            "FOMC next week",
            "## 下一步",
            "## PA Scenario Board",
            f"![PA Scenario Board]({display_output.resolve()})",
        )
        for term in expected_terms:
            if term not in text:
                raise AssertionError(f"missing {term!r} in output:\n{text}")
        if not display_output.is_file():
            raise AssertionError("authorized medium-term position reassessment must auto-generate a visible PA Scenario Board")
        display_text = display_output.read_text(encoding="utf-8")
        for term in ("<svg", "QQQ", "price reference table", "Decision panel"):
            if term not in display_text:
                raise AssertionError(f"scenario board missing {term!r}")

        base_args = [
            sys.executable,
            str(script),
            "--ohlcv-json",
            str(fixture),
            "--main-timeframe",
            "1D",
            "--aux-timeframe",
            "1H",
            "--analysis-intent",
            "position_reassessment",
            "--ohlcv-status",
            "authorized",
        ]
        missing_cases = {
            "trade_horizon": ["--ticker", "QQQ", "--instrument", "equity"],
            "ticker": ["--trade-horizon", "medium-term swing", "--instrument", "equity"],
            "instrument": ["--ticker", "QQQ", "--trade-horizon", "medium-term swing"],
        }
        for missing_field, supplied_args in missing_cases.items():
            watch_output = Path(raw_tmp) / f"missing-{missing_field}.md"
            watch_board = Path(raw_tmp) / f"missing-{missing_field}.svg"
            watch_result = subprocess.run(
                [
                    *base_args,
                    *supplied_args,
                    "--display-output",
                    str(watch_board),
                    "--output",
                    str(watch_output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if watch_result.returncode != 0:
                raise AssertionError(watch_result.stderr or watch_result.stdout)
            watch_text = watch_output.read_text(encoding="utf-8")
            for term in (
                "# Price Action Watch-only",
                "## 缺失确认",
                "ticker + trade_horizon + instrument",
                f"`{missing_field}`",
                "## 确认后我会执行",
            ):
                if term not in watch_text:
                    raise AssertionError(f"missing-key output missing {term!r}:\n{watch_text}")
            for forbidden in (
                "## 走势强弱参考点位",
                "## 加仓/减仓/暂停区",
                "## PA Scenario Board",
                "![PA Scenario Board]",
            ):
                if forbidden in watch_text:
                    raise AssertionError(f"missing-key output must not contain {forbidden!r}")
            if watch_board.exists():
                raise AssertionError(f"missing {missing_field} must not generate a PA Scenario Board")

        omitted_ohlcv_output = Path(raw_tmp) / "omitted-ohlcv-watch-only.md"
        omitted_ohlcv_board = Path(raw_tmp) / "omitted-ohlcv-board.svg"
        omitted_ohlcv_result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--ticker",
                "QQQ",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
                "--display-output",
                str(omitted_ohlcv_board),
                "--output",
                str(omitted_ohlcv_output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if omitted_ohlcv_result.returncode != 0:
            raise AssertionError(omitted_ohlcv_result.stderr or omitted_ohlcv_result.stdout)
        omitted_ohlcv_text = omitted_ohlcv_output.read_text(encoding="utf-8")
        if "# Price Action Watch-only - QQQ" not in omitted_ohlcv_text or "`trade_horizon`" not in omitted_ohlcv_text:
            raise AssertionError(f"omitted-OHLCV watch-only output is incomplete:\n{omitted_ohlcv_text}")
        if omitted_ohlcv_board.exists() or "![PA Scenario Board]" in omitted_ohlcv_text:
            raise AssertionError("incomplete setup key with omitted OHLCV must not create an artifact")

        complete_key_without_ohlcv = subprocess.run(
            [
                sys.executable,
                str(script),
                "--ticker",
                "QQQ",
                "--trade-horizon",
                "medium-term swing",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if complete_key_without_ohlcv.returncode == 0:
            raise AssertionError("complete setup key without OHLCV must fail clearly")
        if "complete setup key requires --ohlcv-json authorized or fixture OHLCV data" not in complete_key_without_ohlcv.stderr:
            raise AssertionError(complete_key_without_ohlcv.stderr or complete_key_without_ohlcv.stdout)

        invalid_ohlcv = Path(raw_tmp) / "invalid-ohlcv.txt"
        invalid_ohlcv.write_text("this is not JSON and must not be read\n", encoding="utf-8")
        invalid_output = Path(raw_tmp) / "invalid-ohlcv-watch-only.md"
        invalid_board = Path(raw_tmp) / "invalid-ohlcv-board.svg"
        invalid_result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--ohlcv-json",
                str(invalid_ohlcv),
                "--ticker",
                "QQQ",
                "--instrument",
                "ETF",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H",
                "--display-output",
                str(invalid_board),
                "--output",
                str(invalid_output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if invalid_result.returncode != 0:
            raise AssertionError(invalid_result.stderr or invalid_result.stdout)
        invalid_text = invalid_output.read_text(encoding="utf-8")
        for term in (
            "# Price Action Watch-only - QQQ",
            "`trade_horizon`",
            "OHLCV 未读取：complete setup key missing",
        ):
            if term not in invalid_text:
                raise AssertionError(f"invalid-OHLCV watch-only output missing {term!r}")
        if invalid_board.exists() or "![PA Scenario Board]" in invalid_text:
            raise AssertionError("missing setup key must not read invalid OHLCV or create an artifact")

    print("price action rollforward selftest ok")


if __name__ == "__main__":
    main()
