#!/usr/bin/env python3
"""Render a plan-scoped intraday setup scan from intraday-watchlist.csv.

Do not scan the whole market; this script only reads prepared setup rows.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys


STATUS_PRIORITY = {
    "invalidated": 0,
    "triggered": 1,
    "needs_review": 2,
    "approaching": 3,
    "active": 4,
    "candidate": 5,
    "completed": 6,
}

INSTRUMENT_URGENCY = (
    ("0dte", 0),
    ("swing_option", 1),
    ("option", 1),
    ("leveraged", 2),
    ("2x", 2),
    ("3x", 2),
    ("stock", 3),
    ("etf", 3),
    ("leap", 4),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a compact intraday setup scan for prepared Active Market Plan setups."
    )
    parser.add_argument("watchlist_csv", help="Path to intraday-watchlist.csv")
    parser.add_argument("--date", default=None, help="Scan date label, YYYY-MM-DD")
    parser.add_argument("--output", default=None, help="Optional Markdown output path")
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return rows


def normalized_status(row: dict[str, str]) -> str:
    return (row.get("current_status") or row.get("status") or "needs_review").strip()


def instrument_priority(instrument_type: str, ticker: str) -> int:
    value = f"{instrument_type} {ticker}".lower()
    for marker, priority in INSTRUMENT_URGENCY:
        if marker in value:
            return priority
    return 5


def sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    status = normalized_status(row)
    return (
        STATUS_PRIORITY.get(status, STATUS_PRIORITY["needs_review"]),
        instrument_priority(row.get("instrument_type", ""), row.get("ticker", "")),
        row.get("setup_id", ""),
    )


def next_step(row: dict[str, str]) -> str:
    status = normalized_status(row)
    execution_required = row.get("execution_check_required", "").lower() in {"yes", "true", "1"}

    if status == "invalidated":
        return "archive or create a new setup later"
    if status == "triggered":
        if execution_required:
            return "execution_check_required; confirm trigger-timeframe follow-through and risk"
        return "confirm trigger-timeframe follow-through and risk before any action"
    if status == "needs_review":
        return "review plan quality, holdings facts, and missing data"
    if status == "approaching":
        return "wait for trigger-timeframe confirmation; verify blockers"
    if status == "active":
        return "keep monitoring planned trigger zone"
    if status == "candidate":
        return "complete plan prep before active tracking"
    if status == "completed":
        return "archive after review"
    return "human review required"


def render_scan(rows: list[dict[str, str]], date_label: str | None) -> str:
    sorted_rows = sorted(rows, key=sort_key)
    title = f"# Intraday Setup Scan - {date_label}" if date_label else "# Intraday Setup Scan"
    if not sorted_rows:
        return "\n".join(
            [
                title,
                "",
                "This is decision support only. It is not a buy/sell instruction.",
                "这是决策辅助，不是买卖指令。",
                "",
                "## 结论",
                "",
                "- 没有已准备的 setup 行；先从 Active Market Plan 或用户确认的交易想法补齐 `intraday-watchlist.csv`。",
                "- 如果今天只做盘前/盘中研究，可以继续更新宏观、新闻、持仓风险和候选 setup，但不能声称有 approaching / triggered 信号。",
                "",
                "## 下一步",
                "",
                "| 状态 | 需要做什么 |",
                "| --- | --- |",
                "| daily package available | 填入计划内 setup 后再运行 formal intraday scan |",
                "",
            ]
        )
    lines = [
        title,
        "",
        "This is decision support only. It is not a buy/sell instruction.",
        "",
        "## 结论",
        "",
    ]

    for row in sorted_rows:
        status = normalized_status(row)
        ticker = row.get("ticker") or row.get("underlying") or row.get("setup_id", "unknown")
        reason = row.get("attention_reason") or row.get("notes") or "human review required"
        suffix = ""
        if status == "triggered" and row.get("execution_check_required", "").lower() in {"yes", "true", "1"}:
            suffix = ": execution_check_required and human decision needed"
        lines.append(f"- {ticker} is `{status}`{suffix}: {reason}.")

    lines.extend(
        [
            "",
            "## Setup 状态",
            "",
            "| setup_id | 状态 | 为什么 | 下一步 |",
            "| --- | --- | --- | --- |",
        ]
    )

    for row in sorted_rows:
        lines.append(
            "| {setup_id} | {status} | {reason} | {next_step} |".format(
                setup_id=row.get("setup_id", "unknown"),
                status=normalized_status(row),
                reason=(row.get("attention_reason") or row.get("notes") or "human review required"),
                next_step=next_step(row),
            )
        )

    lines.extend(["", "## 风险/失效", ""])
    for row in sorted_rows:
        ticker = row.get("underlying") or row.get("ticker") or row.get("setup_id", "unknown")
        risk_parts = [
            part
            for part in (
                row.get("invalidation", "").strip(),
                row.get("notes", "").strip(),
            )
            if part
        ]
        risk = "; ".join(risk_parts) if risk_parts else "no explicit risk note"
        lines.append(f"- {ticker}: {risk}.")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows(Path(args.watchlist_csv).expanduser())
        output = render_scan(rows, args.date)
        if args.output:
            output_path = Path(args.output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    except (OSError, ValueError) as error:
        print(f"intraday scan failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
