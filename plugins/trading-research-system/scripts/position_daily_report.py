#!/usr/bin/env python3
"""Render a concise position daily report from a portfolio snapshot CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class Position:
    as_of: str
    broker: str
    account_id: str
    symbol: str
    underlying: str
    instrument_type: str
    direction: str
    market_value: float
    unrealized_pnl: float
    delta_exposure: float
    notional_exposure: float
    theme_id: str
    source_timestamp: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a broker-live style position daily report from a standard portfolio snapshot CSV."
    )
    parser.add_argument("portfolio_snapshot_csv", help="Standard portfolio_snapshot.csv path")
    parser.add_argument("--date", default=None, help="Report date; defaults to the first as_of date")
    parser.add_argument("--source", default="broker-live fixture", help="Source disclosure")
    parser.add_argument("--read-time", default=None, help="Read timestamp; defaults to latest source timestamp")
    parser.add_argument("--coverage", default=None, help="Broker/account coverage disclosure")
    parser.add_argument("--data-status", default="fixture", help="live / delayed / prior close / partial / fixture")
    parser.add_argument("--snapshot-saved", default="fixture", help="yes / no / fixture")
    return parser.parse_args()


def parse_float(value: str | None) -> float:
    cleaned = (value or "").strip().replace(",", "").replace("$", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_positions(path: Path) -> list[Position]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV header in {path}")
        positions: list[Position] = []
        for row in reader:
            symbol = clean(row.get("symbol")).upper()
            if not symbol:
                continue
            positions.append(
                Position(
                    as_of=clean(row.get("as_of")),
                    broker=clean(row.get("broker")) or "unknown",
                    account_id=clean(row.get("account_id")) or "unknown",
                    symbol=symbol,
                    underlying=(clean(row.get("underlying")) or symbol).upper(),
                    instrument_type=clean(row.get("instrument_type")) or "unspecified",
                    direction=clean(row.get("direction")) or "long",
                    market_value=parse_float(row.get("market_value")),
                    unrealized_pnl=parse_float(row.get("unrealized_pnl")),
                    delta_exposure=parse_float(row.get("delta_exposure")),
                    notional_exposure=parse_float(row.get("notional_exposure")),
                    theme_id=clean(row.get("theme_id")) or "unmapped",
                    source_timestamp=clean(row.get("source_timestamp")),
                    notes=clean(row.get("notes")),
                )
            )
        return positions


def clean(value: str | None) -> str:
    return (value or "").strip()


def report_date(positions: list[Position], requested: str | None) -> str:
    if requested:
        return requested
    if not positions:
        return "unknown"
    return (positions[0].as_of or positions[0].source_timestamp or "unknown").split("T")[0]


def latest_timestamp(positions: list[Position], requested: str | None) -> str:
    if requested:
        return requested
    timestamps = sorted({position.source_timestamp or position.as_of for position in positions if position.source_timestamp or position.as_of})
    return timestamps[-1] if timestamps else "unknown"


def coverage_text(positions: list[Position], requested: str | None) -> str:
    if requested:
        return requested
    accounts = sorted({f"{position.broker}:{position.account_id}" for position in positions})
    return f"{len(accounts)} broker/account source(s): {', '.join(accounts)}"


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def non_cash_positions(positions: list[Position]) -> list[Position]:
    return [position for position in positions if position.instrument_type.lower() != "cash" and position.symbol != "CASH"]


def aggregate_weights(positions: list[Position], total_assets: float, field: str) -> dict[str, float]:
    output: dict[str, float] = defaultdict(float)
    if total_assets <= 0:
        return {}
    for position in positions:
        key = getattr(position, field)
        output[key] += abs(position.market_value) / total_assets
    return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))


def top_item(weights: dict[str, float]) -> tuple[str, float]:
    if not weights:
        return "-", 0.0
    return next(iter(weights.items()))


def render_report(
    positions: list[Position],
    *,
    date: str,
    source: str,
    read_time: str,
    coverage: str,
    data_status: str,
    snapshot_saved: str,
) -> str:
    total_assets = sum(abs(position.market_value) for position in positions)
    invested = sum(abs(position.market_value) for position in non_cash_positions(positions))
    cash = sum(abs(position.market_value) for position in positions if position.instrument_type.lower() == "cash" or position.symbol == "CASH")
    unrealized_pnl = sum(position.unrealized_pnl for position in positions)
    theme_weights = aggregate_weights(non_cash_positions(positions), total_assets, "theme_id")
    symbol_weights = aggregate_weights(non_cash_positions(positions), total_assets, "symbol")
    top_theme, top_theme_weight = top_item(theme_weights)
    top_symbol, top_symbol_weight = top_item(symbol_weights)

    lines = [
        f"# 持仓日报 - {date}",
        "",
        f"Source: {source}",
        f"Read time: {read_time}",
        f"Coverage: {coverage}",
        f"Data status: {data_status}",
        f"Snapshot saved: {snapshot_saved}",
        "",
        "## 结论",
        "",
        f"- 总资产 {money(total_assets)}；已投资 {pct(invested / total_assets) if total_assets else '0.0%'}；现金 {pct(cash / total_assets) if total_assets else '0.0%'}。",
        f"- 最大主题 `{top_theme}` 为 {pct(top_theme_weight)}；最大单一持仓 `{top_symbol}` 为 {pct(top_symbol_weight)}。",
        f"- 未实现盈亏合计 {money(unrealized_pnl)}；本报告只提示复核项，不生成任何订单动作。",
        "",
        "## 需要用户决策",
        "",
        "| 优先级 | 持仓/主题 | 问题 | 可选动作 | 需要确认 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in decision_rows(top_theme, top_theme_weight, top_symbol, top_symbol_weight, cash, total_assets):
        lines.append("| {} | {} | {} | {} | {} |".format(*row))

    lines.extend(
        [
            "",
            "## 风险变化",
            "",
            "| 风险 | 当前状态 | 变化 | 影响 | 需要观察 |",
            "| --- | --- | --- | --- | --- |",
            f"| 集中度 | `{top_theme}` {pct(top_theme_weight)} / `{top_symbol}` {pct(top_symbol_weight)} | 来自当前 snapshot | 限制新增同向风险 | Active Market Plan risk budget |",
            f"| 现金 | {pct(cash / total_assets) if total_assets else '0.0%'} | 来自当前 snapshot | 决定是否有新增仓位空间 | buying power / planned adds |",
            f"| Broker coverage | {coverage} | {data_status} | 缺失来源会降低置信度 | authorization and stale data |",
        ]
    )
    if any("option" in position.instrument_type.lower() for position in positions):
        lines.append("| 期权 | detected | expiry / delta fields may be incomplete | 需要单独复核 | broker option Greeks |")
    else:
        lines.append("| 期权 | no option positions in snapshot | - | 无 0DTE/LEAP 仓位字段 | broker orders/executions if needed |")

    lines.extend(
        [
            "",
            "## 持仓影响",
            "",
            "| 持仓 | 定位 | 当前影响 | Active Market Plan 动作 | 备注 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for position in sorted(non_cash_positions(positions), key=lambda item: abs(item.market_value), reverse=True):
        weight = abs(position.market_value) / total_assets if total_assets else 0.0
        action = "继续持有；新增同主题风险前先复核" if weight >= 0.25 else "继续观察；按 setup/计划复核"
        lines.append(
            "| {symbol} | {theme} / {instrument} | weight {weight}; uPnL {pnl} | {action} | {notes} |".format(
                symbol=position.symbol,
                theme=position.theme_id,
                instrument=position.instrument_type,
                weight=pct(weight),
                pnl=money(position.unrealized_pnl),
                action=action,
                notes=escape_cell(position.notes) or "-",
            )
        )

    lines.extend(
        [
            "",
            "## 可视化",
            "",
            f"- Allocation by symbol: {format_weights(symbol_weights)}",
            f"- Theme / sector exposure: {format_weights(theme_weights)}",
            f"- PnL contribution: total unrealized {money(unrealized_pnl)}",
            f"- Risk heatmap: top theme `{top_theme}` and top symbol `{top_symbol}` need review before adding correlated exposure.",
            "",
            "## 数据缺口",
            "",
            "- This report uses the provided standard portfolio snapshot; it does not verify live broker authorization by itself.",
            "- Account-level margin, buying power, option Greeks, and current orders may require broker-live reads.",
            "- Values may be delayed, fixture, or user-provided according to the data status above.",
        ]
    )
    return "\n".join(lines)


def decision_rows(
    top_theme: str,
    top_theme_weight: float,
    top_symbol: str,
    top_symbol_weight: float,
    cash: float,
    total_assets: float,
) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    if top_theme_weight >= 0.35:
        rows.append(
            (
                "P1",
                top_theme,
                f"主题集中度 {pct(top_theme_weight)}",
                "维持 / 暂停新增同主题 / 降低相关风险",
                "是否仍允许新增同主题 setup",
            )
        )
    if top_symbol_weight >= 0.30:
        rows.append(
            (
                "P1",
                top_symbol,
                f"单一持仓权重 {pct(top_symbol_weight)}",
                "继续持有 / TP再平衡复核 / 暂停加仓",
                "Active Market Plan 对该持仓的动作",
            )
        )
    cash_weight = cash / total_assets if total_assets else 0.0
    if cash_weight >= 0.05:
        rows.append(("P2", "cash", f"现金 {pct(cash_weight)}", "保留 / 等待计划内 setup / 补充风险缓冲", "今日是否有计划内新增风险"))
    if not rows:
        rows.append(("P2", "portfolio", "无 P0/P1 决策", "继续观察", "下次 broker read"))
    return rows


def format_weights(weights: dict[str, float], limit: int = 5) -> str:
    if not weights:
        return "-"
    return ", ".join(f"{key} {pct(value)}" for key, value in list(weights.items())[:limit])


def escape_cell(value: str) -> str:
    return value.replace("|", "/")


def main() -> int:
    args = parse_args()
    try:
        positions = load_positions(Path(args.portfolio_snapshot_csv))
        if not positions:
            raise ValueError("no positions found in portfolio snapshot")
        print(
            render_report(
                positions,
                date=report_date(positions, args.date),
                source=args.source,
                read_time=latest_timestamp(positions, args.read_time),
                coverage=coverage_text(positions, args.coverage),
                data_status=args.data_status,
                snapshot_saved=args.snapshot_saved,
            )
        )
    except (OSError, ValueError) as error:
        print(f"position_daily_report error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
