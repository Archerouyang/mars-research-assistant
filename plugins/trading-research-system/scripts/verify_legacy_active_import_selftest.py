#!/usr/bin/env python3
"""Self-test legacy active Sheet CSV import into local canonical records."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_legacy_active_csv.py"
FIXTURE = ROOT / "assets" / "fixtures" / "input" / "legacy-active-trades.csv"


def _load_trade_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        runtime_dir = Path(raw_tmp)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURE),
                "--runtime-dir",
                str(runtime_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        if "imported 2 legacy active rows" not in result.stdout:
            raise AssertionError(f"unexpected importer output: {result.stdout!r}")

        daily_dir = runtime_dir / "daily" / "2026-01-15"
        trades_path = daily_dir / "trades.csv"
        reviews_path = daily_dir / "reviews.md"
        rows = _load_trade_rows(trades_path)
        if len(rows) != 2:
            raise AssertionError(f"expected two imported rows, got {len(rows)}")

        row = next(row for row in rows if row["trade_id"] == "20260115-QQQ-001")
        expected = {
            "trade_id": "20260115-QQQ-001",
            "status": "closed",
            "entry_date": "2026-01-15",
            "exit_date": "2026-01-15",
            "symbol": "QQQ call",
            "underlying": "QQQ",
            "direction": "long",
            "trade_type": "daytrade",
            "product": "call",
            "instrument_type": "qqq_0dte_call",
            "analysis_timeframe": "5min",
            "trigger_timeframe": "5min",
            "signal_quality": "strong",
            "confidence": "medium",
            "entry_price": "100,101",
            "stop_price": "95",
            "target_price": "110",
            "quantity": "unknown",
            "fees": "unknown",
            "pnl": "250.00",
            "risk_amount": "unknown",
            "planned_R": "2",
            "realized_R": "unknown",
            "outcome": "win",
            "mistake_tag": "poor_exit",
            "chart_link": "https://www.tradingview.com/x/example/",
            "currency": "usd",
            "broker": "manual",
        }
        for key, value in expected.items():
            if row[key] != value:
                raise AssertionError(f"{key}: expected {value!r}, got {row[key]!r}")

        if "[post-order]" not in row["review_raw"] or "[post-exit]" not in row["review_raw"]:
            raise AssertionError("expected staged review_raw text")

        uncounted_row = next(row for row in rows if row["trade_id"] == "20260115-MU-001")
        if uncounted_row["status"] != "not_counted" or uncounted_row["outcome"] != "not_counted":
            raise AssertionError(f"expected MU row to be settled but not counted, got {uncounted_row!r}")
        if uncounted_row["pnl"] != "unknown":
            raise AssertionError(f"expected uncounted MU row to preserve missing pnl as unknown, got {uncounted_row['pnl']!r}")
        if uncounted_row["instrument_type"] != "swing_option_call":
            raise AssertionError(f"unexpected MU instrument type: {uncounted_row['instrument_type']!r}")
        if "[post-exit]" not in uncounted_row["review_raw"]:
            raise AssertionError(f"uncounted legacy row should preserve post-exit raw text: {uncounted_row['review_raw']!r}")

        reviews = reviews_path.read_text(encoding="utf-8")
        for expected_text in (
            "### 20260115-QQQ-001 - QQQ call",
            "### 20260115-MU-001 - MU",
            "- 阶段：post_order",
            "- 阶段：post_exit",
            "50%回撤支撑和三推后出现信号K",
            "止盈离场的时机偏慢",
        ):
            if expected_text not in reviews:
                raise AssertionError(f"missing review text {expected_text!r}")
        if reviews.count("- 阶段：post_exit") != 2:
            raise AssertionError(f"expected exactly two post_exit sections, got reviews: {reviews!r}")

    print("legacy active import selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
