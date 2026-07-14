#!/usr/bin/env python3
"""Compute basic trading-system statistics from trades.csv."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


CLOSED_OUTCOMES = {"win", "loss", "breakeven", "scratch"}
WIN_OUTCOMES = {"win"}
LOSS_OUTCOMES = {"loss"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize trade statistics.")
    parser.add_argument("trades_csv", help="Path to trades.csv")
    parser.add_argument("--group-by", default=None, help="Optional column to group by")
    return parser.parse_args()


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
        try:
            return float(cleaned) / 100.0
        except ValueError:
            return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def row_realized_r(row: dict[str, str]) -> float | None:
    existing = parse_number(row.get("realized_R"))
    if existing is not None:
        return existing
    pnl = parse_number(row.get("pnl"))
    risk_amount = parse_number(row.get("risk_amount"))
    if pnl is None or risk_amount in (None, 0):
        return None
    return pnl / risk_amount


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    closed = [
        row
        for row in rows
        if (row.get("outcome") or "").strip().lower() in CLOSED_OUTCOMES
        or (row.get("status") or "").strip().lower() == "closed"
    ]
    wins = [row for row in closed if (row.get("outcome") or "").strip().lower() in WIN_OUTCOMES]
    losses = [row for row in closed if (row.get("outcome") or "").strip().lower() in LOSS_OUTCOMES]
    r_values = [value for row in closed if (value := row_realized_r(row)) is not None]
    pnl_values = [value for row in closed if (value := parse_number(row.get("pnl"))) is not None]
    mistake_counts: dict[str, int] = defaultdict(int)
    for row in closed:
        tag = (row.get("mistake_tag") or "unclassified").strip() or "unclassified"
        mistake_counts[tag] += 1

    total = len(closed)
    win_rate = len(wins) / total if total else None
    avg_r = sum(r_values) / len(r_values) if r_values else None
    expectancy = avg_r
    total_pnl = sum(pnl_values) if pnl_values else None
    avg_win_r = average([value for row in wins if (value := row_realized_r(row)) is not None])
    avg_loss_r = average([value for row in losses if (value := row_realized_r(row)) is not None])
    return {
        "total": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "avg_r": avg_r,
        "expectancy": expectancy,
        "total_pnl": total_pnl,
        "avg_win_r": avg_win_r,
        "avg_loss_r": avg_loss_r,
        "mistake_counts": dict(sorted(mistake_counts.items(), key=lambda item: item[1], reverse=True)),
    }


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def render_summary(title: str, summary: dict[str, object]) -> list[str]:
    def fmt(value: object) -> str:
        if value is None:
            return "unavailable"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    win_rate = summary["win_rate"]
    win_rate_text = "unavailable" if win_rate is None else f"{float(win_rate) * 100:.1f}%"
    lines = [
        f"## {title}",
        f"- Closed trades: {summary['total']}",
        f"- Wins: {summary['wins']}",
        f"- Losses: {summary['losses']}",
        f"- Win rate: {win_rate_text}",
        f"- Average R: {fmt(summary['avg_r'])}",
        f"- Expectancy: {fmt(summary['expectancy'])}",
        f"- Total PnL: {fmt(summary['total_pnl'])}",
        f"- Average win R: {fmt(summary['avg_win_r'])}",
        f"- Average loss R: {fmt(summary['avg_loss_r'])}",
        "",
        "### Mistake Tags",
    ]
    mistake_counts = summary["mistake_counts"]
    if isinstance(mistake_counts, dict) and mistake_counts:
        for tag, count in mistake_counts.items():
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("- none")
    return lines


def render(rows: list[dict[str, str]], group_by: str | None) -> str:
    lines = ["# Trade Statistics", ""]
    lines.extend(render_summary("All Trades", summarize(rows)))
    if group_by:
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            groups[(row.get(group_by) or "unclassified").strip() or "unclassified"].append(row)
        for group, group_rows in sorted(groups.items()):
            lines.extend(["", *render_summary(f"{group_by}: {group}", summarize(group_rows))])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    print(render(load_rows(Path(args.trades_csv)), args.group_by))


if __name__ == "__main__":
    main()
