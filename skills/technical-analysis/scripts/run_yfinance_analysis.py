#!/usr/bin/env python3
"""Fetch yfinance daily history and build a technical-analysis artifact package."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Callable


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from technical_analysis import (  # noqa: E402
    DataQualityError,
    TechnicalAnalysisError,
    _qualified_history,
    render_fixture,
)


DOWNLOAD_PERIODS = ("18mo", "3y")


def _frame_payload(frame: Any, now: datetime) -> dict[str, Any]:
    bars: list[dict[str, Any]] = []
    for timestamp, row in frame.iterrows():
        timestamp_text = timestamp.isoformat()
        bar = {
            "timestamp": timestamp_text,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
        }
        bars.append(bar)
    if bars:
        last_timestamp = datetime.fromisoformat(str(bars[-1]["timestamp"]))
        if (
            last_timestamp.tzinfo is not None
            and last_timestamp.date()
            >= now.astimezone(last_timestamp.tzinfo).date()
        ):
            bars[-1]["complete"] = False
        timezone_name = str(last_timestamp.tzinfo or "")
        coverage_start = str(bars[0]["timestamp"])[:10]
        completed = [
            bar for bar in bars if bar.get("complete", True) is not False
        ]
        coverage_end = (
            str(completed[-1]["timestamp"])[:10]
            if completed
            else coverage_start
        )
    else:
        timezone_name = ""
        coverage_start = now.date().isoformat()
        coverage_end = coverage_start
    return {
        "timeframe": "1D",
        "time_range_suitable": True,
        "time_range": f"{coverage_start} 至 {coverage_end}",
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "timezone": timezone_name,
        "adjustment": "adjusted",
        "bars": bars,
    }


def build_yfinance_fixture(
    symbol: str,
    *,
    ticker_factory: Callable[[str], Any],
    now: datetime,
) -> dict[str, Any]:
    """Download at most twice from yfinance, widening only the history period."""
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise TechnicalAnalysisError("symbol requires text")
    if now.tzinfo is None or now.utcoffset() is None:
        raise TechnicalAnalysisError("now requires a timezone-aware timestamp")
    ticker = ticker_factory(normalized_symbol)
    attempts: list[dict[str, Any]] = []
    download_error: Exception | None = None
    for period in DOWNLOAD_PERIODS:
        try:
            frame = ticker.history(
                period=period,
                interval="1d",
                auto_adjust=True,
                actions=False,
                repair=True,
                raise_errors=False,
            )
            payload = _frame_payload(frame, now)
            attempts.append(payload)
            _qualified_history(payload, "1D")
            break
        except (DataQualityError, TechnicalAnalysisError) as error:
            download_error = error
            continue
        except Exception as error:  # yfinance/network boundary
            download_error = error
            continue

    as_of = now.isoformat()
    fixture: dict[str, Any] = {
        "instrument": normalized_symbol,
        "timeframe": "1D",
        "research_as_of": as_of,
        "provider": {
            "name": "yfinance EOD",
            "kind": "public_best_effort",
            "as_of": as_of,
            "status": "available" if attempts else "unavailable",
        },
    }
    if attempts:
        fixture["attempts"] = attempts
    elif download_error is not None:
        fixture["download_status"] = type(download_error).__name__
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Release-time yfinance contract runner. It performs no scheduled or "
            "background checks."
        )
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--market-context", type=Path)
    arguments = parser.parse_args()
    try:
        import yfinance  # type: ignore[import-not-found]

        now = datetime.now(timezone.utc)
        fixture = build_yfinance_fixture(
            arguments.symbol,
            ticker_factory=yfinance.Ticker,
            now=now,
        )
        if arguments.market_context is not None:
            fixture["market_context"] = json.loads(
                arguments.market_context.read_text(encoding="utf-8")
            )
        render_fixture(fixture, arguments.output_dir)
    except (
        OSError,
        json.JSONDecodeError,
        TechnicalAnalysisError,
        DataQualityError,
    ) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
