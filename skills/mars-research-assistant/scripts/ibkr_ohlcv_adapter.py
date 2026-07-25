#!/usr/bin/env python3
"""Normalize IBKR get_price_history output for named-instrument research."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any, Mapping


class IBKROHLCVAdapterError(ValueError):
    """Raised when IBKR history cannot be normalized without guessing."""


_STEP_SECONDS = {
    "ONE_HOUR": 3600,
    "TWO_HOURS": 7200,
    "FOUR_HOURS": 14400,
    "ONE_DAY": 86400,
    "ONE_WEEK": 604800,
}


def normalize_ibkr_ohlcv(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Return candles bound to one IBKR contract and request receipt."""

    if not isinstance(payload, Mapping):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_payload_invalid")
    request = payload.get("request")
    contract = payload.get("contract")
    history = payload.get("history")
    if not all(isinstance(value, Mapping) for value in (request, contract, history)):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_receipt_invalid")
    contract_id = _identity(contract.get("contract_id"))
    requested_contract_id = _identity(request.get("contract_id"))
    if contract_id != requested_contract_id:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_contract_receipt_mismatch")
    symbol = _identity(contract.get("symbol"))
    security_type = _identity(contract.get("security_type"))
    exchange = _identity(contract.get("exchange"))
    timeframe = _identity(request.get("timeframe"))
    if timeframe not in _STEP_SECONDS:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_timeframe_not_supported")
    if history.get("source") != "Last":
        raise IBKROHLCVAdapterError("ibkr_ohlcv_payload_invalid")
    if history.get("chart_step") != _STEP_SECONDS[timeframe]:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_step_mismatch")

    keys = ("time", "open", "high", "low", "close")
    arrays = {key: history.get(key) for key in keys}
    if not all(isinstance(value, list) and value for value in arrays.values()):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_arrays_missing")
    length = len(arrays["time"])
    if any(len(arrays[key]) != length for key in keys):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_array_length_mismatch")
    volume = history.get("volume")
    if volume is not None and (
        not isinstance(volume, list) or len(volume) != length
    ):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_array_length_mismatch")

    candles: list[dict[str, Any]] = []
    previous: datetime | None = None
    for index in range(length):
        timestamp = _timestamp(arrays["time"][index])
        if previous is not None and timestamp <= previous:
            raise IBKROHLCVAdapterError("ibkr_ohlcv_time_not_ascending")
        previous = timestamp
        open_value = _number(arrays["open"][index])
        high_value = _number(arrays["high"][index])
        low_value = _number(arrays["low"][index])
        close_value = _number(arrays["close"][index])
        if high_value < max(open_value, close_value) or low_value > min(
            open_value, close_value
        ):
            raise IBKROHLCVAdapterError("ibkr_ohlcv_price_range_invalid")
        candle: dict[str, Any] = {
            "time": timestamp.isoformat().replace("+00:00", "Z"),
            "open": open_value,
            "high": high_value,
            "low": low_value,
            "close": close_value,
        }
        if volume is not None:
            candle["volume"] = _number(volume[index])
        candles.append(candle)
    chart_end = _timestamp(history.get("chart_end"))
    if previous is None or previous + timedelta(seconds=_STEP_SECONDS[timeframe]) > chart_end:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_completed_bar_not_proven")

    return {
        "title": f"{symbol} IBKR {timeframe} OHLCV",
        "subtitle": "IBKR get_price_history normalized for Mars Research Assistant",
        "symbol": symbol,
        "contract_id": contract_id,
        "security_type": security_type,
        "exchange": exchange,
        "source": "IBKR get_price_history",
        "timeframe": timeframe,
        "data_as_of": candles[-1]["time"],
        "candles": candles,
        "notes": [
            "Market data only; no account, holdings, order, or credential fields retained.",
            "Decision support only; no order actions.",
        ],
    }


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_time_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_time_invalid") from error
    if parsed.tzinfo is None:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_time_invalid")
    return parsed


def _identity(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_contract_identity_invalid")
    return text


def _number(value: object) -> float:
    if isinstance(value, bool):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_number_invalid")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise IBKROHLCVAdapterError("ibkr_ohlcv_number_invalid") from error
    if not math.isfinite(parsed):
        raise IBKROHLCVAdapterError("ibkr_ohlcv_number_invalid")
    return parsed
