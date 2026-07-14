#!/usr/bin/env python3
"""Normalize saved Longbridge kline JSON into standard OHLCV JSON.

This adapter consumes JSON that was already produced by a read-only Longbridge
market-data command such as `longbridge kline QQQ.US --format json`. It does not
run the Longbridge CLI, read broker accounts, call live market data, or perform
order actions.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize saved Longbridge kline JSON into standard OHLCV JSON."
    )
    parser.add_argument(
        "--kline-json",
        required=True,
        help="Saved output from `longbridge kline SYMBOL --format json`; use '-' for stdin",
    )
    parser.add_argument("--symbol", required=True, help="Symbol label, e.g. QQQ.US")
    parser.add_argument("--period", required=True, help="Longbridge kline period, e.g. day/1h/15m")
    parser.add_argument("--output", required=True, help="Output normalized OHLCV JSON path")
    parser.add_argument(
        "--title",
        default=None,
        help="Optional chart/note title; defaults to '<symbol> Longbridge <period> OHLCV'",
    )
    return parser.parse_args()


def read_json(path_text: str) -> Any:
    raw = sys.stdin.read() if path_text == "-" else Path(path_text).expanduser().read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("[")
        end = raw.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise SystemExit("Longbridge OHLCV adapter expected a JSON array")
        return json.loads(raw[start : end + 1])


def as_float(value: Any, field: str, index: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"kline row {index} has invalid {field}") from exc


def normalize_time(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    if "T" not in text:
        return text
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text


def normalize_rows(payload: Any) -> list[dict[str, Any]]:
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise SystemExit("Longbridge OHLCV adapter expected a non-empty JSON array or data list")

    candles: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise SystemExit(f"kline row {index} must be an object")
        try:
            candle = {
                "time": normalize_time(row["time"]),
                "open": as_float(row["open"], "open", index),
                "high": as_float(row["high"], "high", index),
                "low": as_float(row["low"], "low", index),
                "close": as_float(row["close"], "close", index),
            }
        except KeyError as exc:
            raise SystemExit(f"kline row {index} missing field: {exc.args[0]}") from exc
        if row.get("volume") not in (None, ""):
            candle["volume"] = as_float(row.get("volume"), "volume", index)
        if row.get("turnover") not in (None, ""):
            candle["turnover"] = as_float(row.get("turnover"), "turnover", index)
        candles.append(candle)

    return sorted(candles, key=lambda candle: str(candle["time"]))


def output_payload(*, symbol: str, period: str, title: str | None, candles: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": title or f"{symbol} Longbridge {period} OHLCV",
        "subtitle": "Saved Longbridge kline JSON normalized for Trading Research System",
        "symbol": symbol,
        "source": "Longbridge kline saved JSON",
        "timeframe": period,
        "data_as_of": candles[-1]["time"],
        "candles": candles,
        "notes": [
            "No live market data calls in this adapter; use only saved authorized Longbridge kline JSON.",
            "Decision support only; no order actions.",
        ],
    }


def main() -> int:
    args = parse_args()
    candles = normalize_rows(read_json(args.kline_json))
    output = output_payload(symbol=args.symbol, period=args.period, title=args.title, candles=candles)
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Longbridge OHLCV adapter wrote {len(candles)} candle(s) to {output_path}")
    print("No live market data calls; consumed saved Longbridge kline JSON only.")
    print("No live broker reads; this adapter never reads accounts or positions.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
