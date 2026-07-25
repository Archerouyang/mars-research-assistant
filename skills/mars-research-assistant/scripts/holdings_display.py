#!/usr/bin/env python3
"""Render an explicitly consented broker snapshot as a factual holdings display.

This module consumes a previously normalized read-only snapshot. It does not
contact a broker, infer missing fields, calculate portfolio risk, or create an
order. The caller owns the per-request consent and the broker read.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from record_schemas import CSV_SCHEMAS


SNAPSHOT_HEADER = frozenset(CSV_SCHEMAS["portfolio_snapshot.csv"])
POSITION_FIELDS = (
    "broker",
    "symbol",
    "quantity",
    "latest_price",
    "market_value",
    "cost",
    "unrealized_pnl",
    "currency",
    "retrieved_at",
)
CASH_FIELDS = ("broker", "currency", "cash", "retrieved_at")
UNAVAILABLE = "不可用"


def build_holdings_display(
    rows: Iterable[Mapping[str, Any]],
    *,
    consented_at: str,
) -> dict[str, Any]:
    """Build a single-broker factual display from an already-read snapshot."""

    _parse_timestamp(consented_at, "consented_at")
    normalized_rows = [dict(row) for row in rows if isinstance(row, Mapping)]
    if not normalized_rows:
        raise ValueError("holdings_display_snapshot_empty")

    brokers = {
        value
        for row in normalized_rows
        for value in [_text(row.get("broker"))]
        if value != UNAVAILABLE
    }
    if len(brokers) != 1:
        raise ValueError("holdings_display_single_broker_required")
    broker = next(iter(brokers))

    positions: list[dict[str, str]] = []
    cash: list[dict[str, str]] = []
    for row in normalized_rows:
        if _is_cash(row):
            cash.append(
                {
                    "broker": broker,
                    "currency": _text(row.get("currency")),
                    "cash": _text(row.get("market_value")),
                    "retrieved_at": _timestamp(row),
                }
            )
            continue
        positions.append(
            {
                "broker": broker,
                "symbol": _text(row.get("symbol")),
                "quantity": _text(row.get("quantity")),
                "latest_price": _text(row.get("market_price")),
                "market_value": _text(row.get("market_value")),
                "cost": _text(row.get("avg_cost")),
                "unrealized_pnl": _text(row.get("unrealized_pnl")),
                "currency": _text(row.get("currency")),
                "retrieved_at": _timestamp(row),
            }
        )

    return {
        "broker": broker,
        "consented_at": consented_at,
        "positions": positions,
        "cash": cash,
    }


def render_holdings_display_markdown(display: Mapping[str, Any]) -> str:
    """Render the approved factual fields without totals or risk calculations."""

    broker = _text(display.get("broker"))
    consented_at = _text(display.get("consented_at"))
    positions = display.get("positions")
    cash = display.get("cash")
    if not isinstance(positions, list) or not isinstance(cash, list):
        raise ValueError("holdings_display_invalid")

    lines = [
        "## 持仓展示",
        "",
        f"- 券商：{_markdown(broker)}",
        f"- 本次读取时间：{_markdown(_latest_retrieval(positions, cash))}",
        f"- 持仓读取确认时间：{_markdown(consented_at)}",
        "",
        "| 券商 | 标的 | 数量 | 最新价格 | 市值 | 成本 | 未实现盈亏 | 币种 | 读取时间 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if positions:
        for row in positions:
            if not isinstance(row, Mapping):
                raise ValueError("holdings_display_invalid")
            lines.append(
                "| "
                + " | ".join(
                    _markdown(_text(row.get(field)))
                    for field in POSITION_FIELDS
                )
                + " |"
            )
    else:
        lines.append("| " + " | ".join([UNAVAILABLE] * len(POSITION_FIELDS)) + " |")

    lines.extend(
        [
            "",
            "### 现金",
            "",
            "| 券商 | 币种 | 现金 | 读取时间 |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if cash:
        for row in cash:
            if not isinstance(row, Mapping):
                raise ValueError("holdings_display_invalid")
            lines.append(
                "| "
                + " | ".join(
                    _markdown(_text(row.get(field)))
                    for field in CASH_FIELDS
                )
                + " |"
            )
    else:
        lines.append("| " + " | ".join([UNAVAILABLE] * len(CASH_FIELDS)) + " |")
    return "\n".join(lines) + "\n"


def load_snapshot(path: str | Path) -> list[dict[str, str]]:
    """Load only the standard normalized snapshot, never raw broker output."""

    with Path(path).expanduser().open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not SNAPSHOT_HEADER.issubset(reader.fieldnames):
            raise ValueError("holdings_display_snapshot_schema_invalid")
        return [dict(row) for row in reader]


def _is_cash(row: Mapping[str, Any]) -> bool:
    return str(row.get("instrument_type") or "").casefold() == "cash" or str(
        row.get("symbol") or ""
    ).upper() == "CASH"


def _timestamp(row: Mapping[str, Any]) -> str:
    source_timestamp = _text(row.get("source_timestamp"))
    if source_timestamp != UNAVAILABLE:
        return source_timestamp
    return _text(row.get("as_of"))


def _latest_retrieval(positions: list[dict[str, str]], cash: list[dict[str, str]]) -> str:
    values = [row["retrieved_at"] for row in [*positions, *cash] if row["retrieved_at"] != UNAVAILABLE]
    return max(values) if values else UNAVAILABLE


def _text(value: Any) -> str:
    if value is None:
        return UNAVAILABLE
    text = str(value).strip()
    return text or UNAVAILABLE


def _markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError(f"{field_name}_invalid") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name}_invalid")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="Normalized portfolio_snapshot.csv path")
    parser.add_argument("--consented-at", required=True, help="Per-request holdings consent timestamp")
    args = parser.parse_args()
    display = build_holdings_display(load_snapshot(args.snapshot), consented_at=args.consented_at)
    print(render_holdings_display_markdown(display), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
