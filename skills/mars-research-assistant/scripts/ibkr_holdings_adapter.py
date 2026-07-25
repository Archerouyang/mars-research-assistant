#!/usr/bin/env python3
"""Normalize minimal IBKR position and cash facts for Holdings Display."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


def position_rows(
    payload: Mapping[str, Any],
    *,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Return only the approved factual position fields."""

    _timestamp(retrieved_at)
    positions = payload.get("positions")
    if not isinstance(positions, list):
        raise ValueError("ibkr_holdings_positions_invalid")
    return [
        {
            "row_type": "position",
            "broker": "IBKR",
            "symbol": _value(position.get("contract_description") or position.get("symbol")),
            "quantity": _value(position.get("position")),
            "latest_price": _value(position.get("market_price")),
            "market_value": _value(position.get("market_value")),
            "cost": _value(position.get("average_price")),
            "unrealized_pnl": _value(position.get("unrealized_pnl")),
            "currency": _value(position.get("currency")),
            "retrieved_at": retrieved_at,
        }
        for position in positions
        if isinstance(position, Mapping)
    ]


def cash_rows(
    payload: Mapping[str, Any],
    *,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Return cash by currency without totals, conversion, or risk fields."""

    _timestamp(retrieved_at)
    balances = payload.get("balances")
    if not isinstance(balances, list):
        raise ValueError("ibkr_holdings_balances_invalid")
    currencies = {
        str(balance.get("currency") or "").strip().upper()
        for balance in balances
        if isinstance(balance, Mapping)
    }
    skip_base = "USD" in currencies
    rows: list[dict[str, Any]] = []
    for balance in balances:
        if not isinstance(balance, Mapping):
            continue
        currency = str(balance.get("currency") or "").strip().upper()
        if currency == "BASE" and skip_base:
            continue
        if currency == "BASE":
            currency = "USD"
        rows.append(
            {
                "row_type": "cash",
                "broker": "IBKR",
                "currency": _value(currency),
                "cash": _value(
                    balance.get("cash_balance")
                    if balance.get("cash_balance") is not None
                    else balance.get("settled_cash")
                ),
                "retrieved_at": retrieved_at,
            }
        )
    return rows


def _value(value: Any) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("ibkr_holdings_retrieved_at_invalid") from error
    if timestamp.tzinfo is None:
        raise ValueError("ibkr_holdings_retrieved_at_invalid")
    return timestamp
