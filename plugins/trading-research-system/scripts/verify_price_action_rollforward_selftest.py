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
    fixture = paths.templates / "chart-ohlcv-qqq-sample.json"

    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "qqq-pa.md"
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
        )
        for term in expected_terms:
            if term not in text:
                raise AssertionError(f"missing {term!r} in output:\n{text}")

    print("price action rollforward selftest ok")


if __name__ == "__main__":
    main()
