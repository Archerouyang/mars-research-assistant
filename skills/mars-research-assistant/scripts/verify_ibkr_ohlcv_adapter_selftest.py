#!/usr/bin/env python3
"""Regression checks for IBKR-only OHLCV normalization."""

from __future__ import annotations

import copy

from ibkr_ohlcv_adapter import IBKROHLCVAdapterError, normalize_ibkr_ohlcv


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def payload() -> dict[str, object]:
    return {
        "request": {
            "contract_id": "265598",
            "timeframe": "FOUR_HOURS",
        },
        "contract": {
            "contract_id": "265598",
            "symbol": "AAPL",
            "security_type": "STK",
            "exchange": "SMART",
        },
        "history": {
            "chart_step": 14400,
            "chart_start": "2026-07-23T00:00:00Z",
            "chart_end": "2026-07-25T00:00:00Z",
            "source": "Last",
            "time": [
                "2026-07-23T14:00:00Z",
                "2026-07-23T18:00:00Z",
                "2026-07-24T14:00:00Z",
            ],
            "open": [190.0, 191.0, 193.0],
            "high": [192.0, 194.0, 196.0],
            "low": [189.0, 190.0, 192.0],
            "close": [191.0, 193.0, 195.0],
            "volume": [1000, 1200, 1500],
        },
    }


def require_error(candidate: dict[str, object], expected: str) -> None:
    try:
        normalize_ibkr_ohlcv(
            candidate,
        )
    except IBKROHLCVAdapterError as error:
        require(str(error) == expected, f"expected {expected!r}, got {error!s}")
    else:
        raise AssertionError(f"expected IBKROHLCVAdapterError: {expected}")


def main() -> int:
    result = normalize_ibkr_ohlcv(
        payload(),
    )
    require(result["source"] == "IBKR get_price_history", "source must remain IBKR")
    require(result["symbol"] == "AAPL", "user-named symbol must remain explicit")
    require(result["contract_id"] == "265598", "contract identity must remain explicit")
    require(result["timeframe"] == "FOUR_HOURS", "requested timeframe must remain explicit")
    require(result["candles"][-1]["close"] == 195.0, "parallel arrays must normalize by index")
    require(result["candles"][-1]["volume"] == 1500.0, "volume must remain optional factual data")

    mismatched = payload()
    mismatched["history"]["high"] = [192.0]  # type: ignore[index]
    require_error(mismatched, "ibkr_ohlcv_array_length_mismatch")

    unsupported = payload()
    unsupported["history"]["chart_step"] = 3600  # type: ignore[index]
    require_error(unsupported, "ibkr_ohlcv_step_mismatch")

    unordered = copy.deepcopy(payload())
    unordered["history"]["time"][1] = unordered["history"]["time"][0]  # type: ignore[index]
    require_error(unordered, "ibkr_ohlcv_time_not_ascending")

    wrong_contract = copy.deepcopy(payload())
    wrong_contract["request"]["contract_id"] = "999999"  # type: ignore[index]
    require_error(wrong_contract, "ibkr_ohlcv_contract_receipt_mismatch")

    print("IBKR OHLCV adapter selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
