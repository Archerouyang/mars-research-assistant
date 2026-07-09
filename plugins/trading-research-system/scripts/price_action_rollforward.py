#!/usr/bin/env python3
"""Generate a rolling price-action note from authorized or fixture OHLCV JSON.

This script is a pure local transformation. No live broker reads; it does not fetch market data, read broker accounts, or perform order actions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from chart_artifact import ema_points, normalize_candles, normalize_levels, normalize_zones


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OHLCV-backed rolling PA note.")
    parser.add_argument("--ohlcv-json", required=True, help="Authorized or fixture OHLCV JSON")
    parser.add_argument("--ticker", default=None, help="Ticker label; defaults to JSON symbol")
    parser.add_argument("--date", default=None, help="Analysis date label")
    parser.add_argument("--main-timeframe", required=True, help="Main background timeframe, e.g. 1D/4H/1W")
    parser.add_argument("--aux-timeframe", required=True, help="Auxiliary execution timeframe, e.g. 1H/15m")
    parser.add_argument("--prior-analysis", default="", help="Prior PA note or concise prior-level summary")
    parser.add_argument("--cost-context", default="", help="Cost/buy-record context from holdings or user input")
    parser.add_argument("--event-context", default="", help="Macro/news/event context mapped to this PA read")
    parser.add_argument("--output", default=None, help="Optional Markdown output path")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit("OHLCV JSON must be an object")
    return payload


def price(value: float | int | str) -> str:
    number = float(value)
    text = f"{number:.2f}"
    return text.rstrip("0").rstrip(".")


def latest_ema(candles: list[dict[str, Any]], period: int) -> float | None:
    points = ema_points(candles, period)
    if not points:
        return None
    return float(points[-1]["value"])


def recent_high(candles: list[dict[str, Any]], lookback: int) -> float:
    window = candles[-min(lookback, len(candles)) :]
    return max(float(row["high"]) for row in window)


def recent_low(candles: list[dict[str, Any]], lookback: int) -> float:
    window = candles[-min(lookback, len(candles)) :]
    return min(float(row["low"]) for row in window)


def market_state(candles: list[dict[str, Any]]) -> str:
    latest = float(candles[-1]["close"])
    ema20 = latest_ema(candles, 20)
    ema50 = latest_ema(candles, 50)
    high20 = recent_high(candles, 20)
    low20 = recent_low(candles, 20)
    if ema20 is not None and ema50 is not None and latest > ema20 > ema50 and latest >= high20 * 0.97:
        return "强趋势后的回撤/修复观察"
    if ema20 is not None and ema50 is not None and latest > ema50 and latest < ema20:
        return "趋势内回撤，等待 reclaim"
    if latest < low20:
        return "短期破位，需要复核"
    return "区间/修复观察"


def level_rows(payload: dict[str, Any], candles: list[dict[str, Any]], main_timeframe: str) -> list[tuple[str, str, str, str, str]]:
    latest = candles[-1]
    rows: list[tuple[str, str, str, str, str]] = [
        ("last close", "当前价", price(float(latest["close"])), main_timeframe, "当前读数锚点"),
    ]
    ema20 = latest_ema(candles, 20)
    ema50 = latest_ema(candles, 50)
    if ema20 is not None:
        rows.append(("EMA20", "支撑/压力", price(ema20), main_timeframe, "趋势内回踩/收复参考"))
    if ema50 is not None:
        rows.append(("EMA50", "支撑/压力", price(ema50), main_timeframe, "中期结构复核参考"))

    rows.extend(
        [
            ("recent 20-bar high", "压力", price(recent_high(candles, 20)), main_timeframe, "强弱延伸参考"),
            ("recent 20-bar low", "支撑", price(recent_low(candles, 20)), main_timeframe, "短期防守参考"),
        ]
    )
    for level in normalize_levels(payload):
        kind = str(level.get("kind") or "level")
        label = str(level.get("label") or kind)
        level_type = "压力" if kind in {"profit", "rebalance", "target"} else "支撑/压力"
        if kind in {"support", "trigger"}:
            level_type = "支撑"
        if kind in {"review", "invalid", "invalidation"}:
            level_type = "暂停/复核"
        rows.append((label, level_type, price(level["price"]), main_timeframe, "来自 OHLCV 快照 levels"))
    return rows


def zone_rows(payload: dict[str, Any], main_timeframe: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for zone in normalize_zones(payload):
        kind = str(zone.get("kind") or "zone").lower()
        label = str(zone.get("label") or kind)
        zone_text = f"{price(zone['low'])}-{price(zone['high'])}"
        if kind in {"trigger", "add", "support"}:
            action = "加仓观察区；只在确认后少量/1/10-1/5"
        elif kind in {"rebalance", "profit", "target"}:
            action = "TP/再平衡区；中等/1/5-1/3，非强制卖出"
        elif kind in {"invalid", "invalidation", "review", "risk"}:
            action = "暂停加仓并复核；不自动反手"
        else:
            action = "参考区；等待确认"
        rows.append((label, zone_text, main_timeframe, action))
    if not rows:
        rows.append(("EMA20/近期支撑", "见强弱点位表", main_timeframe, "加仓只在收复/确认后少量"))
        rows.append(("近期高点", "见强弱点位表", main_timeframe, "TP/再平衡只在延伸或失败突破时考虑"))
    return rows


def render_note(
    *,
    payload: dict[str, Any],
    candles: list[dict[str, Any]],
    ticker: str,
    date_label: str,
    main_timeframe: str,
    aux_timeframe: str,
    prior_analysis: str,
    cost_context: str,
    event_context: str,
) -> str:
    lines = [
        f"# Price Action Rollforward - {ticker}",
        "",
        "This is decision support only. It is not a buy/sell instruction.",
        "这是决策辅助，不是买卖指令。",
        "",
        "## 结论",
        "",
        f"- 日期: {date_label}",
        f"- 市场状态: {market_state(candles)}",
        f"- 数据来源: {payload.get('source') or 'authorized/user-provided OHLCV'}; as_of: {payload.get('data_as_of') or payload.get('as_of') or candles[-1]['time']}",
        "",
        "## 时间框架声明",
        "",
        "| 项目 | 时间框架 | 用途 |",
        "| --- | --- | --- |",
        f"| 主分析时间框架 | {main_timeframe} | 判断背景、趋势/区间、主要支撑压力 |",
        f"| 辅助时间框架 | {aux_timeframe} | 只用于执行观察和短线确认，不改变大级别背景 |",
        "",
        "## 上次分析对照",
        "",
        prior_analysis or "上次分析对照: 未找到可用记录，本次作为基准分析",
        "",
        "## 走势强弱参考点位",
        "",
        "| 点位 | 支撑/压力 | 价格/区间 | 点位所属时间框架 | 用途 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for label, kind, value, timeframe, use in level_rows(payload, candles, main_timeframe):
        lines.append(f"| {label} | {kind} | {value} | {timeframe} | {use} |")

    lines.extend(
        [
            "",
            "## 加仓/减仓/暂停区",
            "",
            "| 区域 | 价格/区间 | 点位所属时间框架 | 计划动作 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for label, zone_text, timeframe, action in zone_rows(payload, main_timeframe):
        lines.append(f"| {label} | {zone_text} | {timeframe} | {action} |")

    lines.extend(
        [
            "",
            "比例式加减仓: 默认用少量/中等/较大或 1/10、1/5、1/3；不输出具体股数，除非用户要求。",
            "",
            "## 成本/买入记录",
            "",
            cost_context or "未提供成本/买入记录；不要把低成本核心仓和高成本追高批次混为一类。",
            "",
            "## 本周事件映射",
            "",
            event_context or "未提供事件上下文；需要结合本周宏观、利率、政策、财报/行业事件再确认。",
            "",
            "## 下一步",
            "",
            "1. 如果价格接近加仓/TP/暂停区，再用辅助时间框架确认信号 K 和 follow-through。",
            "2. 若宏观/利率/行业事件与当前点位冲突，优先降级为 `needs_review`。",
            "3. 若需要图表展示，用同一 OHLCV JSON 生成 PA Scenario Board 或 chart artifact。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    payload = load_payload(Path(args.ohlcv_json).expanduser())
    candles = normalize_candles(payload)
    ticker = args.ticker or str(payload.get("symbol") or "UNKNOWN")
    date_label = args.date or str(payload.get("data_as_of") or payload.get("as_of") or candles[-1]["time"])
    note = render_note(
        payload=payload,
        candles=candles,
        ticker=ticker,
        date_label=date_label,
        main_timeframe=args.main_timeframe,
        aux_timeframe=args.aux_timeframe,
        prior_analysis=args.prior_analysis,
        cost_context=args.cost_context,
        event_context=args.event_context,
    )
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(note, encoding="utf-8")
    else:
        print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
