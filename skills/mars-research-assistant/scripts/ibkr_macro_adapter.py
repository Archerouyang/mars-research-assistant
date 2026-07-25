#!/usr/bin/env python3
"""Normalize verified IBKR Treasury-yield index closes for Macro Preflight."""

from __future__ import annotations

from datetime import date, datetime
import math
from typing import Any, Mapping

from ibkr_provider import MARKET_SOURCE_ID


class IBKRMacroAdapterError(ValueError):
    """Raised when an IBKR candidate does not prove exact field semantics."""


_YIELD_CONTRACTS = {
    "rates.us_10y_yield": {
        "contract_id": "416921",
        "symbol": "TNX",
        "exchange": "CBOE",
        "security_type": "IND",
        "description": "Interest Rate Option On 10-Year Note",
        "scale": 0.1,
    },
    "rates.us_30y_yield": {
        "contract_id": "416933",
        "symbol": "TYX",
        "exchange": "CBOE",
        "security_type": "IND",
        "description": "Interest Rate Option On 30-Year Bond",
        "scale": 0.1,
    },
}


def normalize_ibkr_yield_history(
    payload: Mapping[str, Any],
    *,
    field_id: str,
    acquired_at: str,
) -> dict[str, Any]:
    """Return one exact completed-close field record for Macro Preflight."""

    contract_spec = _YIELD_CONTRACTS.get(field_id)
    if contract_spec is None:
        raise IBKRMacroAdapterError("ibkr_yield_field_not_supported")
    cutoff = _parse_timestamp(acquired_at)
    if not isinstance(payload, Mapping):
        raise IBKRMacroAdapterError("ibkr_yield_payload_invalid")
    contract = payload.get("contract")
    history_payload = payload.get("history")
    if not isinstance(contract, Mapping) or not _contract_matches(contract, contract_spec):
        raise IBKRMacroAdapterError("ibkr_yield_contract_identity_invalid")
    if not isinstance(history_payload, Mapping):
        raise IBKRMacroAdapterError("ibkr_yield_history_insufficient")
    if (
        history_payload.get("chart_step") != 86400
        or history_payload.get("source") != "Last"
    ):
        raise IBKRMacroAdapterError("ibkr_yield_history_semantics_invalid")
    times = history_payload.get("time")
    opens = history_payload.get("open")
    highs = history_payload.get("high")
    lows = history_payload.get("low")
    closes = history_payload.get("close")
    if not all(
        isinstance(values, list)
        for values in (times, opens, highs, lows, closes)
    ):
        raise IBKRMacroAdapterError("ibkr_yield_history_insufficient")
    if len(times) < 21 or not all(
        len(values) == len(times)
        for values in (opens, highs, lows, closes)
    ):
        raise IBKRMacroAdapterError("ibkr_yield_history_insufficient")
    chart_end = _parse_timestamp(history_payload.get("chart_end"))

    history: list[dict[str, Any]] = []
    previous_time: datetime | None = None
    for raw_time, raw_close in zip(times, closes):
        bar_time = _parse_timestamp(raw_time)
        bar_date = bar_time.date()
        if previous_time is not None and bar_time <= previous_time:
            raise IBKRMacroAdapterError("ibkr_yield_history_not_ascending")
        if bar_time > cutoff:
            raise IBKRMacroAdapterError("ibkr_yield_bar_after_capture")
        previous_time = bar_time
        close = _parse_number(raw_close)
        history.append(
            {
                "date": bar_date.isoformat(),
                "value": close * float(contract_spec["scale"]),
            }
        )
    if previous_time is None or chart_end <= previous_time:
        raise IBKRMacroAdapterError("ibkr_yield_completed_close_not_proven")
    if chart_end > cutoff:
        raise IBKRMacroAdapterError("ibkr_yield_chart_end_after_capture")
    previous_date: date | None = None
    for point in history:
        bar_date = _parse_date(point["date"])
        if previous_date is not None and bar_date <= previous_date:
            raise IBKRMacroAdapterError("ibkr_yield_history_not_ascending")
        previous_date = bar_date

    latest = history[-1]
    return {
        "field_id": field_id,
        "value": latest["value"],
        "unit": "percent",
        "status": "available",
        "data_as_of": acquired_at,
        "market_reference_date": latest["date"],
        "source_id": MARKET_SOURCE_ID,
        "retrieval_method": "broker_market_capture",
        "raw_field_path": ["structuredContent", "close"],
        "source_symbol": str(contract_spec["symbol"]),
        "source_native_id": str(contract_spec["contract_id"]),
        "source_timing": "completed_market",
        "history": history,
    }


def _contract_matches(
    candidate: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> bool:
    required = ("contract_id", "symbol", "exchange", "security_type", "description")
    return all(str(candidate.get(key) or "") == str(expected[key]) for key in required)


def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise IBKRMacroAdapterError("ibkr_yield_acquired_at_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise IBKRMacroAdapterError("ibkr_yield_acquired_at_invalid") from error
    if parsed.tzinfo is None:
        raise IBKRMacroAdapterError("ibkr_yield_acquired_at_invalid")
    return parsed


def _parse_date(value: object) -> date:
    if not isinstance(value, str):
        raise IBKRMacroAdapterError("ibkr_yield_bar_date_invalid")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise IBKRMacroAdapterError("ibkr_yield_bar_date_invalid") from error


def _parse_number(value: object) -> float:
    if isinstance(value, bool):
        raise IBKRMacroAdapterError("ibkr_yield_close_invalid")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise IBKRMacroAdapterError("ibkr_yield_close_invalid") from error
    if not math.isfinite(parsed):
        raise IBKRMacroAdapterError("ibkr_yield_close_invalid")
    return parsed
