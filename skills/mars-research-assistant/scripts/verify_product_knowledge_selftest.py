#!/usr/bin/env python3
"""Focused behavior checks for broker normalization product knowledge."""

from __future__ import annotations

from product_knowledge import effective_exposure, normalize_symbol, product_knowledge


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(normalize_symbol(" tsmx.us ") == "TSMX", "market suffix normalization drifted")
    require(product_knowledge("NVDA").underlying == "NVDA", "equity knowledge drifted")
    require(product_knowledge("TSMX").leverage_multiple == 2.0, "known product metadata drifted")
    require(not product_knowledge("mystery.us").known, "unknown product must remain explicit")
    require(effective_exposure("SQQQ", 100.0) == -300.0, "inverse product direction drifted")
    print("product knowledge selftest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
