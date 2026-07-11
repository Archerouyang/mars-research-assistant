#!/usr/bin/env python3
"""Self-test Longbridge kline JSON adapter into normalized OHLCV JSON."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "longbridge_ohlcv_adapter.py"
PA = ROOT / "scripts" / "price_action_rollforward.py"
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "longbridge-kline-qqq-day-2026-07-09.json"


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        output = Path(raw_tmp) / "qqq-ohlcv.json"
        adapter_result = subprocess.run(
            [
                sys.executable,
                str(ADAPTER),
                "--kline-json",
                str(FIXTURE),
                "--symbol",
                "QQQ.US",
                "--period",
                "day",
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if adapter_result.returncode != 0:
            raise AssertionError(adapter_result.stderr or adapter_result.stdout)

        payload = json.loads(output.read_text(encoding="utf-8"))
        if payload["symbol"] != "QQQ.US":
            raise AssertionError("symbol should be preserved")
        if payload["source"] != "Longbridge kline saved JSON":
            raise AssertionError("source should disclose saved Longbridge kline JSON")
        if payload["timeframe"] != "day":
            raise AssertionError("timeframe should be day")
        if len(payload["candles"]) != 10:
            raise AssertionError("expected 10 normalized candles")
        first = payload["candles"][0]
        if first["time"] != "2026-06-01" or first["open"] != 700.0:
            raise AssertionError(f"unexpected first candle: {first!r}")
        if "No live market data calls" not in adapter_result.stdout:
            raise AssertionError("adapter must disclose no live market data calls")
        if "No live broker reads" not in adapter_result.stdout:
            raise AssertionError("adapter must disclose no live broker reads")
        if "No order actions" not in adapter_result.stdout:
            raise AssertionError("adapter must disclose no order actions")

        pa_output = Path(raw_tmp) / "qqq-pa.md"
        pa_result = subprocess.run(
            [
                sys.executable,
                str(PA),
                "--ohlcv-json",
                str(output),
                "--ticker",
                "QQQ",
                "--trade-horizon",
                "medium-term swing",
                "--instrument",
                "ETF",
                "--date",
                "2026-07-09",
                "--main-timeframe",
                "1D",
                "--aux-timeframe",
                "1H/15m",
                "--prior-analysis",
                "上次分析对照: 本次作为基准分析",
                "--cost-context",
                "长期核心 ETF；只讨论加仓和 TP/再平衡",
                "--event-context",
                "FOMC minutes / 10Y / VIX context",
                "--output",
                str(pa_output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if pa_result.returncode != 0:
            raise AssertionError(pa_result.stderr or pa_result.stdout)
        text = pa_output.read_text(encoding="utf-8")
        for term in (
            "# Price Action Rollforward - QQQ",
            "Longbridge kline saved JSON",
            "主分析时间框架 | 1D",
            "走势强弱参考点位",
            "加仓/减仓/暂停区",
        ):
            if term not in text:
                raise AssertionError(f"missing {term!r} in PA output")

    print("Longbridge OHLCV adapter selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
