#!/usr/bin/env python3
"""Normalize an in-memory Price Action chart payload without artifact I/O."""

from __future__ import annotations

from typing import Any


def normalize_candles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("candles") or payload.get("ohlcv") or payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise ValueError("candles_invalid")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("candles_invalid")
        try:
            candle = {
                "time": str(row["time"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("candles_invalid") from error
        if row.get("volume") not in (None, ""):
            try:
                candle["volume"] = float(row["volume"])
            except (TypeError, ValueError) as error:
                raise ValueError("candles_invalid") from error
        normalized.append(candle)
    return normalized


def ema_points(candles: list[dict[str, Any]], period: int) -> list[dict[str, Any]]:
    if len(candles) < period:
        return []
    closes = [float(candle["close"]) for candle in candles]
    multiplier = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    points = [{"time": candles[period - 1]["time"], "value": round(ema, 4)}]
    for index in range(period, len(candles)):
        ema = closes[index] * multiplier + ema * (1 - multiplier)
        points.append({"time": candles[index]["time"], "value": round(ema, 4)})
    return points


def _normalized_levels(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("levels") or []
    if not isinstance(rows, list):
        raise ValueError("levels_invalid")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("levels_invalid")
        try:
            price = float(row["price"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("levels_invalid") from error
        normalized.append(
            {
                "price": price,
                "label": str(row.get("label") or price),
                "kind": str(row.get("kind") or "level"),
            }
        )
    return normalized


def _normalized_zones(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("zones") or []
    if not isinstance(rows, list):
        raise ValueError("zones_invalid")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("zones_invalid")
        try:
            low, high = sorted((float(row["low"]), float(row["high"])))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("zones_invalid") from error
        normalized.append(
            {
                "low": low,
                "high": high,
                "label": str(row.get("label") or "zone"),
                "kind": str(row.get("kind") or "zone"),
            }
        )
    return normalized


def build_chart_payload(payload: dict[str, Any], title_override: str | None) -> dict[str, Any]:
    """Prepare the one source-consistent chart data used by the PA renderer."""

    candles = normalize_candles(payload)
    chart = dict(payload)
    chart["title"] = title_override or str(payload.get("title") or payload.get("ticker") or "Price Action")
    chart["candles"] = candles
    chart["ema20"] = payload.get("ema20") or ema_points(candles, 20)
    chart["ema50"] = payload.get("ema50") or ema_points(candles, 50)
    chart["levels"] = _normalized_levels(payload)
    chart["zones"] = _normalized_zones(payload)
    return chart
