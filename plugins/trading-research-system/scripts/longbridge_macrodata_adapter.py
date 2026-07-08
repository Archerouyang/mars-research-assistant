#!/usr/bin/env python3
"""Normalize saved Longbridge macrodata JSON into macro-panel.json.

This adapter consumes JSON that was already produced by an authorized
Longbridge macrodata read. It does not call Longbridge, read broker accounts,
call market data, or perform order actions.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


CANONICAL_INDICATORS = (
    "10Y",
    "30Y",
    "HYG/LQD",
    "DXY",
    "Oil",
    "Gold",
    "liquidity",
)

ALIASES = {
    "10Y": {"10Y", "US10Y", "US 10Y", "10Y Treasury", "10Y Treasury yield"},
    "30Y": {"30Y", "US30Y", "US 30Y", "30Y Treasury", "30Y Treasury yield"},
    "HYG/LQD": {"HYG/LQD", "HYG_LQD", "Credit", "Credit risk appetite"},
    "DXY": {"DXY", "USD", "US Dollar Index"},
    "Oil": {"Oil", "WTI", "WTI crude", "WTI crude oil", "Crude oil"},
    "Gold": {"Gold", "XAU", "XAUUSD"},
    "liquidity": {"liquidity", "Liquidity", "Liquidity proxy", "reserves/RRP/TGA"},
}

DEFAULTS = {
    "10Y": {
        "label": "10Y Treasury yield",
        "unit": "%",
        "threshold": "4.50 pressure line",
        "strategy_impact": "balanced; high-beta adds need rate confirmation",
    },
    "30Y": {
        "label": "30Y Treasury yield",
        "unit": "%",
        "threshold": "5.00 stress line",
        "strategy_impact": "duration pressure near 5.00%",
    },
    "HYG/LQD": {
        "label": "Credit risk appetite",
        "unit": "",
        "threshold": "widening/tightening confirmation",
        "strategy_impact": "credit supports risk if ratio is stable or rising",
    },
    "DXY": {
        "label": "US Dollar Index",
        "unit": "",
        "threshold": "breakout/breakdown confirmation",
        "strategy_impact": "lower USD pressure supports liquidity",
    },
    "Oil": {
        "label": "WTI crude oil",
        "unit": "USD",
        "threshold": "geopolitical spike / breakdown",
        "strategy_impact": "oil spike would pressure inflation and volatility",
    },
    "Gold": {
        "label": "Gold",
        "unit": "USD",
        "threshold": "trend confirmation",
        "strategy_impact": "defensive / easing hedge confirmation",
    },
    "liquidity": {
        "label": "Liquidity proxy",
        "unit": "",
        "threshold": "reserves / RRP / TGA proxy",
        "strategy_impact": "liquidity proxy gates beta sizing",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize saved Longbridge macrodata JSON into standard macro-panel.json."
    )
    parser.add_argument(
        "--macrodata-json",
        required=True,
        help="Saved Longbridge macrodata JSON; use '-' for stdin",
    )
    parser.add_argument("--output", required=True, help="Output standard macro-panel.json path")
    parser.add_argument("--as-of", required=True, help="Snapshot timestamp, e.g. 2026-06-24T20:00:00Z")
    parser.add_argument("--data-status", default="live", help="live / delayed / prior close / partial / fixture")
    parser.add_argument(
        "--source-status",
        default="available",
        help="available / unauthorized / not_installed / missing / stale",
    )
    return parser.parse_args()


def read_json(path_text: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path_text == "-" else Path(path_text).expanduser().read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise SystemExit("Longbridge macrodata adapter expected a JSON object")
        payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, dict):
        raise SystemExit("Longbridge macrodata adapter expected a macrodata JSON object")
    return payload


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def decimal_or_text(value: Any) -> int | float | str:
    text = clean(value).replace(",", "").replace("%", "")
    if not text:
        return ""
    try:
        number = Decimal(text)
    except InvalidOperation:
        return clean(value)
    if number == number.to_integral():
        return int(number)
    return float(number.normalize())


def raw_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("items", "indicators", "data", "results", "values"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def canonical_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower().replace(" ", "").replace("_", "/")
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            alias_normalized = alias.strip().lower().replace(" ", "").replace("_", "/")
            if normalized == alias_normalized:
                return canonical
    return raw_name.strip()


def item_name(item: dict[str, Any]) -> str:
    return clean(
        item.get("indicator")
        or item.get("name")
        or item.get("symbol")
        or item.get("ticker")
        or item.get("series")
    )


def normalize_indicator(item: dict[str, Any], canonical: str, as_of: str) -> dict[str, Any]:
    defaults = DEFAULTS[canonical]
    return {
        "name": canonical,
        "label": clean(item.get("label")) or defaults["label"],
        "value": decimal_or_text(first_present(item.get("value"), item.get("latest"), item.get("current"))),
        "unit": clean(item.get("unit")) or defaults["unit"],
        "change_5d": decimal_or_text(first_present(item.get("change_5d"), item.get("change5d"), item.get("delta_5d"))),
        "change_20d": decimal_or_text(first_present(item.get("change_20d"), item.get("change20d"), item.get("delta_20d"))),
        "threshold": clean(item.get("threshold")) or defaults["threshold"],
        "strategy_impact": clean(item.get("strategy_impact")) or defaults["strategy_impact"],
        "source": "Longbridge macrodata",
        "timestamp": clean(item.get("timestamp") or item.get("time") or item.get("as_of")) or as_of,
    }


def normalize_panel(
    payload: dict[str, Any],
    *,
    as_of: str,
    data_status: str,
    source_status: str,
) -> dict[str, Any]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in raw_items(payload):
        raw_name = item_name(item)
        canonical = canonical_name(raw_name)
        if canonical in CANONICAL_INDICATORS:
            indexed[canonical] = item

    indicators = [
        normalize_indicator(indexed[name], name, as_of)
        for name in CANONICAL_INDICATORS
        if name in indexed
    ]
    missing = [name for name in CANONICAL_INDICATORS if name not in indexed]
    degraded = bool(missing) or source_status != "available"
    return {
        "as_of": as_of,
        "data_status": data_status,
        "degraded": degraded,
        "indicators": indicators,
        "missing_indicators": missing,
        "source_capability": "longbridge_macrodata",
        "source_notes": [
            "Longbridge macrodata is S1 macro/financial data, not a broker account source.",
            "Policy facts, official speeches, and release status still require S0 official confirmation.",
        ],
        "source_status": source_status,
        "strategy_posture": infer_strategy_posture(indicators, degraded),
        "summary": summarize_panel(indicators, degraded),
    }


def indicator_value(indicators: list[dict[str, Any]], name: str) -> float | None:
    for indicator in indicators:
        if indicator["name"] != name:
            continue
        value = indicator["value"]
        if isinstance(value, (int, float)):
            return float(value)
    return None


def infer_strategy_posture(indicators: list[dict[str, Any]], degraded: bool) -> str:
    if degraded:
        return "degraded"
    ten_year = indicator_value(indicators, "10Y")
    thirty_year = indicator_value(indicators, "30Y")
    credit = indicator_value(indicators, "HYG/LQD")
    dxy_change = next((indicator["change_5d"] for indicator in indicators if indicator["name"] == "DXY"), 0)
    oil_change = next((indicator["change_5d"] for indicator in indicators if indicator["name"] == "Oil"), 0)
    if (ten_year is not None and ten_year >= 4.5) or (thirty_year is not None and thirty_year >= 5.0):
        return "defensive"
    if credit is not None and credit < 0.75:
        return "defensive"
    if isinstance(dxy_change, (int, float)) and dxy_change > 1:
        return "defensive"
    if isinstance(oil_change, (int, float)) and oil_change > 5:
        return "defensive"
    if (ten_year is not None and ten_year >= 4.35) or (thirty_year is not None and thirty_year >= 4.85):
        return "balanced"
    return "high beta momentum"


def summarize_panel(indicators: list[dict[str, Any]], degraded: bool) -> str:
    if degraded:
        return "Macro panel is degraded because one or more required indicators are missing or unavailable."
    posture = infer_strategy_posture(indicators, False)
    if posture == "defensive":
        return "Rates, credit, USD, oil, or liquidity conditions argue for a defensive posture."
    if posture == "high beta momentum":
        return "Macro and financial-condition reads support high beta momentum if price confirmation agrees."
    return "Rates are near pressure thresholds, but credit, USD, oil, gold, and liquidity do not force a defensive posture."


def write_panel(path: Path, panel: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(panel, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload = read_json(args.macrodata_json)
    panel = normalize_panel(
        payload,
        as_of=args.as_of,
        data_status=args.data_status,
        source_status=args.source_status,
    )
    write_panel(Path(args.output).expanduser(), panel)
    print(f"Longbridge macrodata adapter wrote macro panel to {args.output}")
    print("No live macrodata reads; consumed saved Longbridge macrodata JSON only.")
    print("Longbridge macrodata is not a broker account source.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
