#!/usr/bin/env python3
"""Regression checks for exact IBKR Treasury-yield normalization."""

from __future__ import annotations

import copy
from datetime import date, timedelta

from ibkr_macro_adapter import IBKRMacroAdapterError, normalize_ibkr_yield_history


AS_OF = "2026-07-25T12:00:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def payload(symbol: str = "TNX") -> dict[str, object]:
    if symbol == "TNX":
        contract_id = "416921"
        description = "Interest Rate Option On 10-Year Note"
    else:
        contract_id = "416933"
        description = "Interest Rate Option On 30-Year Bond"
    start = date(2026, 6, 25)
    timestamps = [
        f"{(start + timedelta(days=index)).isoformat()}T20:00:00Z"
        for index in range(21)
    ]
    return {
        "contract": {
            "contract_id": contract_id,
            "symbol": symbol,
            "exchange": "CBOE",
            "security_type": "IND",
            "description": description,
        },
        "history": {
            "chart_step": 86400,
            "chart_start": f"{start.isoformat()}T00:00:00Z",
            "chart_end": f"{(start + timedelta(days=21)).isoformat()}T00:00:00Z",
            "source": "Last",
            "time": timestamps,
            "open": [45.0 + index / 10 for index in range(21)],
            "high": [45.2 + index / 10 for index in range(21)],
            "low": [44.8 + index / 10 for index in range(21)],
            "close": [45.0 + index / 10 for index in range(21)],
        },
    }


def require_error(
    candidate: dict[str, object],
    field_id: str,
    expected: str,
) -> None:
    try:
        normalize_ibkr_yield_history(candidate, field_id=field_id, acquired_at=AS_OF)
    except IBKRMacroAdapterError as error:
        require(str(error) == expected, f"expected {expected!r}, got {error!s}")
    else:
        raise AssertionError(f"expected IBKRMacroAdapterError: {expected}")


def main() -> int:
    tnx = normalize_ibkr_yield_history(
        payload(),
        field_id="rates.us_10y_yield",
        acquired_at=AS_OF,
    )
    require(tnx["value"] == 4.7, "TNX index points must convert to percent with the locked scale")
    require(tnx["unit"] == "percent", "Treasury yield unit must remain percent")
    require(tnx["source_native_id"] == "416921", "IBKR contract identity must be retained")
    require(tnx["source_symbol"] == "TNX", "IBKR symbol must be retained")
    require(tnx["market_reference_date"] == "2026-07-15", "latest complete close must be retained")
    require(len(tnx["history"]) == 21, "history must preserve the required twenty-one closes")

    tyx = normalize_ibkr_yield_history(
        payload("TYX"),
        field_id="rates.us_30y_yield",
        acquired_at=AS_OF,
    )
    require(tyx["value"] == 4.7, "TYX must use the same verified index-point scale")

    ticker_only = payload()
    ticker_only["contract"] = {"symbol": "TNX"}
    require_error(
        ticker_only,
        "rates.us_10y_yield",
        "ibkr_yield_contract_identity_invalid",
    )

    wrong_contract = payload()
    wrong_contract["contract"]["contract_id"] = "999999"  # type: ignore[index]
    require_error(
        wrong_contract,
        "rates.us_10y_yield",
        "ibkr_yield_contract_identity_invalid",
    )

    auction = payload()
    auction["contract"]["security_type"] = "AUCTION"  # type: ignore[index]
    require_error(
        auction,
        "rates.us_10y_yield",
        "ibkr_yield_contract_identity_invalid",
    )

    incomplete = payload()
    incomplete["history"]["chart_end"] = incomplete["history"]["time"][-1]  # type: ignore[index]
    require_error(
        incomplete,
        "rates.us_10y_yield",
        "ibkr_yield_completed_close_not_proven",
    )

    future_end = payload()
    future_end["history"]["chart_end"] = "2026-07-26T00:00:00Z"  # type: ignore[index]
    require_error(
        future_end,
        "rates.us_10y_yield",
        "ibkr_yield_chart_end_after_capture",
    )

    require_error(
        payload(),
        "rates.us_2y_yield",
        "ibkr_yield_field_not_supported",
    )

    mismatched = copy.deepcopy(payload())
    require_error(
        mismatched,
        "rates.us_30y_yield",
        "ibkr_yield_contract_identity_invalid",
    )

    print("IBKR macro adapter selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
