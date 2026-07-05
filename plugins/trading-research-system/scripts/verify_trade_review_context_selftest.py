#!/usr/bin/env python3
"""Self-test the two-stage review-context artifact path."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("write_trade_review_context.py")


def run_context_write(daily_dir: Path, stage: str, trade_id: str, fields: dict[str, str], note: str) -> None:
    fields_path = daily_dir / f"{stage}.json"
    review_path = daily_dir / f"{stage}.md"
    fields_path.write_text(json.dumps(fields), encoding="utf-8")
    review_path.write_text(note, encoding="utf-8")

    result = subprocess.run(
        [
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
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        daily_dir = Path(raw_tmp)
        trade_id = "20260624-QQQ-001"
        run_context_write(
            daily_dir,
            "post-order",
            trade_id,
            {
                "symbol": "QQQ 0DTE 726C",
                "underlying": "QQQ",
                "product": "0DTE call",
                "direction": "long",
                "broker": "IBKR",
                "account_id": "SIM",
                "execution_id": "SIM-EXEC-001",
                "setup_id": "qqq-0dte-breakout-pullback",
                "analysis_timeframe": "1H / 15m",
                "trigger_timeframe": "5m",
                "market_background": "VIX contained and QQQ above 20/50 EMA",
                "entry_reason": "breakout pullback with follow-through",
                "signal_bar": "5m strong bull signal bar",
                "confidence": "medium",
                "risk_plan": "no averaging down; exit on failed follow-through",
            },
            "Entry context while memory is fresh.",
        )

        run_context_write(
            daily_dir,
            "post-exit",
            trade_id,
            {
                "symbol": "QQQ 0DTE 726C",
                "underlying": "QQQ",
                "product": "0DTE call",
                "direction": "long",
                "broker": "IBKR",
                "account_id": "SIM",
                "execution_id": "SIM-EXEC-EXIT-001",
                "setup_id": "qqq-0dte-breakout-pullback",
                "analysis_timeframe": "1H / 15m",
                "trigger_timeframe": "5m",
                "exit_result": "scratch exit after failed follow-through",
                "pnl": "0",
                "realized_R": "0.0",
                "outcome": "scratch",
                "execution_quality": "acceptable",
                "mistake_tag": "none",
                "lesson": "wait for second entry if the first trigger fails",
            },
            "Exit review after trade completion.",
        )

        reviews_path = daily_dir / "reviews.md"
        reviews = reviews_path.read_text(encoding="utf-8")
        expected_terms = (
            "### 20260624-QQQ-001 - QQQ 0DTE 726C",
            "- 阶段：post_order",
            "- 阶段：post_exit",
            "Broker facts：IBKR / SIM / SIM-EXEC-001",
            "Entry context while memory is fresh.",
            "Exit review after trade completion.",
            "scratch exit after failed follow-through / 0 / 0.0 / scratch",
        )
        for expected in expected_terms:
            if expected not in reviews:
                raise AssertionError(f"missing {expected!r} in {reviews!r}")

        if (daily_dir / "trades.csv").exists():
            raise AssertionError("review-context writer must not create trades.csv")

    print("trade review context selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
