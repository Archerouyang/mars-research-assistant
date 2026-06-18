#!/usr/bin/env python3
"""Self-test post-order and post-exit trade record updates through the CLI."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from record_schemas import CSV_SCHEMAS


SCRIPT = Path(__file__).resolve().with_name("update_trade_record.py")


def _write_trades_header(path: Path) -> None:
    path.write_text(",".join(CSV_SCHEMAS["trades.csv"]) + "\n", encoding="utf-8")


def _run_update(
    daily_dir: Path,
    stage: str,
    trade_id: str,
    fields: dict[str, str],
    review: str,
    extra_args: list[str] | None = None,
) -> None:
    fields_path = daily_dir / f"{stage}.json"
    review_path = daily_dir / f"{stage}.md"
    fields_path.write_text(json.dumps(fields), encoding="utf-8")
    review_path.write_text(review, encoding="utf-8")

    command = [
            sys.executable,
            str(SCRIPT),
            "--daily-dir",
            str(daily_dir),
            "--stage",
            stage,
            "--trade-id",
            trade_id,
            "--fields-json",
            str(fields_path),
            "--review-file",
            str(review_path),
    ]
    if extra_args:
        command.extend(extra_args)

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


def _load_trade_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        daily_dir = Path(raw_tmp)
        trades_path = daily_dir / "trades.csv"
        reviews_path = daily_dir / "reviews.md"
        _write_trades_header(trades_path)

        _run_update(
            daily_dir,
            "post-order",
            "20260618-QQQ-001",
            {
                "symbol": "QQQ 0DTE 485C",
                "underlying": "QQQ",
                "direction": "long",
                "trade_type": "daytrade",
                "product": "call",
                "instrument_type": "qqq_0dte_call",
                "analysis_timeframe": "Daily;1h;15m",
                "trigger_timeframe": "5m",
                "setup_tag": "breakout_pullback",
                "signal_quality": "strong",
                "confidence": "medium",
                "entry_date": "2026-06-18 10:15",
                "entry_price": "2.10",
                "stop_price": "1.70",
                "target_price": "3.10",
                "quantity": "1",
                "cost": "210",
                "fees": "1.00",
                "risk_amount": "120",
                "planned_R": "2.0",
                "setup_review": "Daily trend up; 15m above 20/50EMA",
                "entry_review": "5m breakout pullback with follow-through",
                "review_raw": "No chasing range middle.",
                "currency": "USD",
                "broker": "manual",
            },
            "Entry memory while fresh.",
        )

        rows = _load_trade_rows(trades_path)
        if len(rows) != 1:
            raise AssertionError(f"expected one trade row after post-order, got {len(rows)}")
        row = rows[0]
        if row["status"] != "open" or row["outcome"] != "open":
            raise AssertionError(f"post-order defaults not applied: {row!r}")
        if row["entry_review"] != "5m breakout pullback with follow-through":
            raise AssertionError("entry review was not written")

        _run_update(
            daily_dir,
            "post-exit",
            "20260618-QQQ-001",
            {
                "exit_date": "2026-06-18 11:05",
                "pnl": "180",
                "realized_R": "1.5",
                "outcome": "win",
                "mistake_tag": "none",
                "exit_review": "Took profit after two weak follow-through bars.",
                "lesson": "Scale only after confirmation.",
                "review_raw": "Good patience on entry; exit was acceptable.",
            },
            "Exit review after close.",
        )

        rows = _load_trade_rows(trades_path)
        if len(rows) != 1:
            raise AssertionError(f"expected post-exit to update one row, got {len(rows)}")
        row = rows[0]
        if row["status"] != "closed" or row["outcome"] != "win":
            raise AssertionError(f"post-exit fields not applied: {row!r}")
        if row["entry_review"] != "5m breakout pullback with follow-through":
            raise AssertionError("post-exit overwrote preserved entry review")
        if "[post-order] No chasing range middle." not in row["review_raw"]:
            raise AssertionError(f"post-order review_raw was not preserved: {row['review_raw']!r}")
        if "[post-exit] Good patience on entry; exit was acceptable." not in row["review_raw"]:
            raise AssertionError(f"post-exit review_raw was not appended: {row['review_raw']!r}")

        reviews = reviews_path.read_text(encoding="utf-8")
        for expected in (
            "### 20260618-QQQ-001 - QQQ 0DTE 485C",
            "- 阶段：post_order",
            "- 阶段：post_exit",
            "Entry memory while fresh.",
            "Exit review after close.",
        ):
            if expected not in reviews:
                raise AssertionError(f"missing review text {expected!r} in {reviews!r}")

        bad_fields_path = daily_dir / "bad-fields.json"
        bad_fields_path.write_text(json.dumps({"not_a_trade_field": "bad"}), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--daily-dir",
                str(daily_dir),
                "--stage",
                "post-order",
                "--trade-id",
                "20260618-QQQ-002",
                "--fields-json",
                str(bad_fields_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "unknown trades.csv fields" not in result.stderr:
            raise AssertionError(f"expected unknown-field failure, got: {result!r}")

        missing_open_fields = daily_dir / "missing-open-exit.json"
        missing_open_fields.write_text(
            json.dumps(
                {
                    "exit_date": "2026-06-18 12:00",
                    "pnl": "10",
                    "realized_R": "0.1",
                    "outcome": "scratch",
                    "mistake_tag": "none",
                    "exit_review": "No matching open trade.",
                    "lesson": "Match the open row first.",
                    "review_raw": "Tried to close a missing trade.",
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--daily-dir",
                str(daily_dir),
                "--stage",
                "post-exit",
                "--trade-id",
                "20260618-QQQ-404",
                "--fields-json",
                str(missing_open_fields),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "requires an existing trade_id" not in result.stderr:
            raise AssertionError(f"expected missing-open-trade failure, got: {result!r}")

        legacy_fields = {
            "symbol": "QQQ call",
            "underlying": "QQQ",
            "direction": "long",
            "trade_type": "daytrade",
            "product": "call",
            "instrument_type": "qqq_0dte_call",
            "analysis_timeframe": "5min",
            "trigger_timeframe": "5min",
            "setup_tag": "pullback_signal_bar",
            "signal_quality": "strong",
            "confidence": "medium",
            "entry_date": "2026-01-15",
            "entry_price": "100,101",
            "stop_price": "95",
            "target_price": "110",
            "cost": "1000",
            "planned_R": "2",
            "setup_review": "合成测试：高开突破关键压力后回撤",
            "entry_review": "合成测试：50%支撑和三推后出现信号K",
            "review_raw": "Legacy active tab row without quantity, fees, or risk_amount.",
            "currency": "usd",
            "broker": "manual",
        }
        legacy_fields_path = daily_dir / "legacy-fields.json"
        legacy_fields_path.write_text(json.dumps(legacy_fields), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--daily-dir",
                str(daily_dir),
                "--stage",
                "post-order",
                "--trade-id",
                "20260115-QQQ-001",
                "--fields-json",
                str(legacy_fields_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "missing required fields: quantity, fees, risk_amount" not in result.stderr:
            raise AssertionError(f"expected strict missing-field failure, got: {result!r}")

        _run_update(
            daily_dir,
            "post-order",
            "20260115-QQQ-001",
            legacy_fields,
            "Legacy active row import should preserve row while marking missing execution facts.",
            ["--allow-unknown-execution-fields"],
        )
        rows = _load_trade_rows(trades_path)
        legacy = next(row for row in rows if row["trade_id"] == "20260115-QQQ-001")
        for field in ("quantity", "fees", "risk_amount"):
            if legacy[field] != "unknown":
                raise AssertionError(f"expected {field}=unknown for legacy import, got {legacy[field]!r}")

    print("trade record update selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
