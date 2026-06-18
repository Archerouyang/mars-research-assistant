#!/usr/bin/env python3
"""Import legacy active Sheet CSV rows into canonical local trade records."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import os
from pathlib import Path
import re
import sys

from trade_records import TradeRecordUpdate, apply_trade_update


REQUIRED_HEADERS = (
    "entry_date",
    "symbol",
    "direction",
    "trade_type",
    "product",
    "timeframe",
    "信号k类型",
    "background",
    "辅助信号",
    "入场价格",
    "初始止损",
    "初始目标",
    "初始盈亏比",
    "总成本",
    "盈亏",
    "思考复盘",
    "信心",
    "tradingview_link",
    "currency",
)

SIGNAL_QUALITY = {
    "强信号": "strong",
    "中等": "medium",
    "中": "medium",
    "弱": "weak",
    "弱信号": "weak",
}

CONFIDENCE = {
    "强": "high",
    "高": "high",
    "中等": "medium",
    "中": "medium",
    "弱": "low",
    "低": "low",
}


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import legacy active Sheet CSV rows.")
    parser.add_argument("active_csv", help="CSV export of the legacy active tab")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument("--root", default=None, help="Daily root override. Defaults to <runtime-dir>/daily")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print planned imports without writing")
    return parser.parse_args()


def load_legacy_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        missing = [header for header in REQUIRED_HEADERS if header not in headers]
        if missing:
            raise ValueError(f"{path}: missing required active CSV headers: {', '.join(missing)}")
        return [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def daily_root(args: argparse.Namespace) -> Path:
    if args.root:
        return Path(args.root).expanduser()
    return Path(args.runtime_dir).expanduser() / "daily"


def import_rows(rows: list[dict[str, str]], root: Path, dry_run: bool) -> list[str]:
    counters: defaultdict[tuple[str, str], int] = defaultdict(int)
    messages: list[str] = []
    for row in rows:
        trade_id = next_trade_id(row, counters)
        daily_dir = root / row["entry_date"]
        trades_path = daily_dir / "trades.csv"
        reviews_path = daily_dir / "reviews.md"
        post_order = map_post_order(row)
        post_exit = map_post_exit(row)

        if dry_run:
            messages.append(f"would import {trade_id} into {daily_dir}")
            continue

        messages.append(
            apply_trade_update(
                trades_path,
                reviews_path,
                TradeRecordUpdate(
                    stage="post-order",
                    trade_id=trade_id,
                    fields=post_order,
                    review_text=render_post_order_note(row),
                    allow_unknown_execution_fields=True,
                ),
            )
        )
        if should_import_exit(row):
            messages.append(
                apply_trade_update(
                    trades_path,
                    reviews_path,
                    TradeRecordUpdate(
                        stage="post-exit",
                        trade_id=trade_id,
                        fields=post_exit,
                        review_text=render_post_exit_note(row),
                    ),
                )
            )
    return messages


def next_trade_id(row: dict[str, str], counters: defaultdict[tuple[str, str], int]) -> str:
    symbol = normalized_underlying(row)
    date_key = row["entry_date"].replace("-", "")
    key = (date_key, symbol)
    counters[key] += 1
    return f"{date_key}-{symbol}-{counters[key]:03d}"


def map_post_order(row: dict[str, str]) -> dict[str, str]:
    underlying = normalized_underlying(row)
    product = clean(row["product"]).lower()
    return {
        "theme_id": f"{underlying.lower()}-legacy-active-import",
        "entry_date": row["entry_date"],
        "symbol": legacy_symbol(row, underlying, product),
        "underlying": underlying,
        "direction": clean(row["direction"]).lower(),
        "trade_type": clean(row["trade_type"]).lower(),
        "product": product,
        "instrument_type": infer_instrument_type(underlying, product, row["trade_type"]),
        "analysis_timeframe": clean(row["timeframe"]),
        "trigger_timeframe": clean(row["timeframe"]),
        "setup_tag": infer_setup_tag(row),
        "signal_quality": map_signal_quality(row["信号k类型"]),
        "confidence": map_confidence(row["信心"]),
        "entry_price": clean(row["入场价格"]),
        "stop_price": clean(row["初始止损"]),
        "target_price": clean(row["初始目标"]),
        "cost": clean(row["总成本"]),
        "planned_R": clean(row["初始盈亏比"]),
        "setup_review": clean(row["background"]),
        "entry_review": clean(row["辅助信号"]),
        "review_raw": "legacy active tab import",
        "chart_link": clean(row["tradingview_link"]),
        "currency": clean(row["currency"]).lower(),
        "broker": "manual",
    }


def map_post_exit(row: dict[str, str]) -> dict[str, str]:
    return {
        "exit_date": row["entry_date"],
        "pnl": clean(row["盈亏"]) or "unknown",
        "realized_R": "unknown",
        "outcome": infer_outcome(row["盈亏"]),
        "mistake_tag": infer_mistake_tag(row["思考复盘"]),
        "exit_review": summarize_exit_review(row["思考复盘"]),
        "lesson": summarize_lesson(row["思考复盘"]),
        "review_raw": clean(row["思考复盘"]),
        "status": infer_status(row),
    }


def should_import_exit(row: dict[str, str]) -> bool:
    return bool(clean(row["盈亏"]) or clean(row["思考复盘"]))


def render_post_order_note(row: dict[str, str]) -> str:
    return (
        "Legacy active Sheet import.\n\n"
        f"- Background: {clean(row['background'])}\n"
        f"- Auxiliary signal: {clean(row['辅助信号'])}\n"
        "- Missing legacy execution fields are written as unknown: quantity, fees, risk_amount."
    )


def render_post_exit_note(row: dict[str, str]) -> str:
    return f"Legacy active Sheet post-exit review.\n\n{clean(row['思考复盘'])}"


def normalized_underlying(row: dict[str, str]) -> str:
    return re.sub(r"[^A-Z0-9._-]", "", clean(row["symbol"]).upper()) or "UNKNOWN"


def legacy_symbol(row: dict[str, str], underlying: str, product: str) -> str:
    if product in {"call", "put"}:
        return f"{underlying} {product}"
    return underlying


def infer_instrument_type(underlying: str, product: str, trade_type: str) -> str:
    normalized_trade_type = clean(trade_type).lower()
    if underlying == "QQQ" and normalized_trade_type == "daytrade" and product == "call":
        return "qqq_0dte_call"
    if underlying == "QQQ" and normalized_trade_type == "daytrade" and product == "put":
        return "qqq_0dte_put"
    if underlying == "SPY" and normalized_trade_type == "daytrade" and product == "call":
        return "spy_0dte_call"
    if underlying == "SPY" and normalized_trade_type == "daytrade" and product == "put":
        return "spy_0dte_put"
    if "spread" in product:
        return "swing_option_call" if "call" in product else "swing_option_put"
    if product == "call":
        return "swing_option_call"
    if product == "put":
        return "swing_option_put"
    return "other"


def infer_setup_tag(row: dict[str, str]) -> str:
    text = f"{row['background']} {row['辅助信号']}"
    if "三推" in text:
        return "three_push_pullback"
    if "回撤" in text:
        return "pullback_signal_bar"
    if "突破" in text:
        return "breakout"
    return "legacy_active_setup"


def map_signal_quality(value: str) -> str:
    text = clean(value)
    return SIGNAL_QUALITY.get(text, "medium" if text else "unknown")


def map_confidence(value: str) -> str:
    text = clean(value)
    return CONFIDENCE.get(text, "medium" if text else "unknown")


def infer_outcome(pnl: str) -> str:
    value = parse_number(pnl)
    if value is None:
        return "not_counted"
    if value > 0:
        return "win"
    if value < 0:
        return "loss"
    return "breakeven"


def infer_status(row: dict[str, str]) -> str:
    if clean(row["盈亏"]):
        return "closed"
    if clean(row["思考复盘"]):
        return "not_counted"
    return "open"


def infer_mistake_tag(review: str) -> str:
    text = clean(review)
    if "离场" in text or "止盈" in text:
        return "poor_exit"
    if "快速止损" in text or "止损" in text:
        return "ignored_invalidation"
    return "none"


def summarize_exit_review(review: str) -> str:
    text = clean(review)
    sentences = split_chinese_sentences(text)
    for marker in ("止盈", "反转", "震荡", "机会", "离场"):
        for sentence in sentences:
            if marker in sentence:
                return sentence
    return text[:180]


def summarize_lesson(review: str) -> str:
    text = clean(review)
    lesson_sentences = [
        sentence
        for sentence in split_chinese_sentences(text)
        if "应该" in sentence or "机会" in sentence or "不好" in sentence
    ]
    return "；".join(lesson_sentences[:2]) or text[:180]


def split_chinese_sentences(text: str) -> list[str]:
    return [part.strip("。；; ") for part in re.split(r"[。；;]", text) if part.strip()]


def parse_number(value: str) -> float | None:
    cleaned = clean(value).replace(",", "").replace("$", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean(value: str | None) -> str:
    return (value or "").strip()


def main() -> int:
    args = parse_args()
    try:
        rows = load_legacy_rows(Path(args.active_csv))
        messages = import_rows(rows, daily_root(args), args.dry_run)
    except (OSError, ValueError) as error:
        print(f"legacy active import failed: {error}", file=sys.stderr)
        return 1

    verb = "validated" if args.dry_run else "imported"
    print(f"{verb} {len(rows)} legacy active rows")
    for message in messages:
        print(f"- {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
