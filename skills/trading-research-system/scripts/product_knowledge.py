#!/usr/bin/env python3
"""Canonical Broker-Live Data View product knowledge.

This domain module owns reusable facts about known products. Broker adapters
remain responsible for translating source records; callers must not infer
look-through metadata for symbols absent from this catalog.
"""

from __future__ import annotations

from dataclasses import dataclass


_MARKET_SUFFIXES = (".US", ".HK", ".SG", ".SH", ".SZ")


@dataclass(frozen=True)
class ProductKnowledge:
    symbol: str
    known: bool
    product_type: str
    underlying: str | None
    underlying_kind: str
    direction: str
    leverage_multiple: float | None
    theme: str

    @property
    def signed_leverage(self) -> float | None:
        if self.leverage_multiple is None:
            return None
        return -self.leverage_multiple if self.direction == "inverse" else self.leverage_multiple


def _product(
    symbol: str,
    product_type: str,
    theme: str,
    *,
    underlying: str | None = None,
    underlying_kind: str = "direct",
    direction: str = "long",
    leverage_multiple: float = 1.0,
) -> ProductKnowledge:
    return ProductKnowledge(
        symbol=symbol,
        known=True,
        product_type=product_type,
        underlying=underlying or symbol,
        underlying_kind=underlying_kind,
        direction=direction,
        leverage_multiple=leverage_multiple,
        theme=theme,
    )


def _catalog() -> dict[str, ProductKnowledge]:
    products: dict[str, ProductKnowledge] = {}

    for symbol in ("DIA", "IWM", "QQQ", "SPY", "VOO"):
        products[symbol] = _product(symbol, "etf_common", "tech_beta")
    for symbol in ("HYG", "IEF", "LQD", "SHY", "TLT"):
        products[symbol] = _product(symbol, "etf_common", "rates_credit")
    for symbol in ("GLD", "SLV"):
        products[symbol] = _product(symbol, "etf_common", "gold_precious_metals")

    sector_themes = {
        "DRAM": "memory_storage",
        "SMH": "semiconductor",
        "SOXX": "semiconductor",
        "XLK": "tech_beta",
        "XLV": "defensive_healthcare",
        "XLY": "consumer_discretionary",
    }
    for symbol, theme in sector_themes.items():
        products[symbol] = _product(symbol, "sector_etf", theme)

    stock_themes = {
        "AMD": "ai_hardware",
        "ARM": "ai_hardware",
        "BE": "ai_power",
        "CRDO": "ai_infra_momentum",
        "GLW": "ai_networking",
        "GOOGL": "mag7",
        "LITE": "ai_networking",
        "META": "mag7",
        "MRVL": "ai_hardware",
        "MU": "memory_storage",
        "NVDA": "ai_hardware",
        "SKHY": "memory_storage",
        "SKHYV": "memory_storage",
        "SNDK": "memory_storage",
        "TSM": "ai_hardware",
    }
    for symbol, theme in stock_themes.items():
        products[symbol] = _product(symbol, "stock_common", theme)

    leveraged_products = {
        "KORU": ("EWY", "benchmark_proxy", "long", 3.0, "korea_equity_leverage"),
        "MVLL": ("MRVL", "single_name", "long", 2.0, "ai_hardware_leverage"),
        "MUU": ("MU", "single_name", "long", 2.0, "memory_storage_leverage"),
        "NVDL": ("NVDA", "single_name", "long", 2.0, "ai_hardware_leverage"),
        "SOXL": ("SOXX", "benchmark_proxy", "long", 3.0, "semiconductor_leverage"),
        "SQQQ": ("QQQ", "benchmark_proxy", "inverse", 3.0, "tech_inverse_leverage"),
        "TQQQ": ("QQQ", "benchmark_proxy", "long", 3.0, "tech_beta_leverage"),
        "TSLL": ("TSLA", "single_name", "long", 2.0, "tesla_leverage"),
        "TSMX": ("TSM", "single_name", "long", 2.0, "ai_hardware_leverage"),
    }
    for symbol, (underlying, kind, direction, multiple, theme) in leveraged_products.items():
        products[symbol] = _product(
            symbol,
            "leveraged_etf",
            theme,
            underlying=underlying,
            underlying_kind=kind,
            direction=direction,
            leverage_multiple=multiple,
        )

    return products


_PRODUCT_CATALOG = _catalog()


def normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper()
    for suffix in _MARKET_SUFFIXES:
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def product_knowledge(symbol: str) -> ProductKnowledge:
    normalized = normalize_symbol(symbol)
    known = _PRODUCT_CATALOG.get(normalized)
    if known is not None:
        return known
    return ProductKnowledge(
        symbol=normalized,
        known=False,
        product_type="unknown",
        underlying=None,
        underlying_kind="unknown",
        direction="unknown",
        leverage_multiple=None,
        theme="unmapped",
    )


def effective_exposure(
    symbol: str,
    market_value: float,
    supplied_exposure: float | None = None,
) -> float:
    """Return known product look-through while preserving explicit source exposure."""
    product = product_knowledge(symbol)
    direct = abs(float(market_value))
    if supplied_exposure is not None:
        supplied = float(supplied_exposure)
        if not product.known or product.product_type != "leveraged_etf":
            return supplied or direct
        if abs(abs(supplied) - direct) >= 1e-6:
            return supplied
    if product.known and product.product_type == "leveraged_etf":
        return direct * float(product.signed_leverage or 0.0)
    return direct if supplied_exposure is None else float(supplied_exposure or direct)
