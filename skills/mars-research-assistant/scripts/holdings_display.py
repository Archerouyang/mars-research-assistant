#!/usr/bin/env python3
"""Render an explicitly consented broker snapshot as a factual holdings display.

This module consumes a previously normalized read-only snapshot. It does not
contact a broker, infer missing fields, calculate portfolio risk, or create an
order. The caller owns the per-request consent and the broker read.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from ibkr_provider import require_holdings_broker


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

    for row in normalized_rows:
        require_holdings_broker(row.get("broker"))
    broker = "IBKR"

    positions: list[dict[str, str]] = []
    cash: list[dict[str, str]] = []
    for row in normalized_rows:
        row_type = row.get("row_type")
        if row_type == "cash":
            if set(row) != {"row_type", *CASH_FIELDS}:
                raise ValueError("holdings_display_row_schema_invalid")
            cash.append(
                {
                    "broker": broker,
                    "currency": _text(row.get("currency")),
                    "cash": _text(row.get("cash")),
                    "retrieved_at": _text(row.get("retrieved_at")),
                }
            )
            continue
        if row_type != "position" or set(row) != {"row_type", *POSITION_FIELDS}:
            raise ValueError("holdings_display_row_schema_invalid")
        positions.append(
            {
                "broker": broker,
                "symbol": _text(row.get("symbol")),
                "quantity": _text(row.get("quantity")),
                "latest_price": _text(row.get("latest_price")),
                "market_value": _text(row.get("market_value")),
                "cost": _text(row.get("cost")),
                "unrealized_pnl": _text(row.get("unrealized_pnl")),
                "currency": _text(row.get("currency")),
                "retrieved_at": _text(row.get("retrieved_at")),
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
