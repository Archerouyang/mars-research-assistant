#!/usr/bin/env python3
"""Summarize portfolio exposure from a holdings CSV.

Expected columns are documented in assets/templates/holdings.csv. The script is
intentionally dependency-free so it can run in a plain Codex environment.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable


WEIGHT_FIELDS = ("weight", "portfolio_weight", "weight_pct")
VALUE_FIELDS = ("market_value", "notional", "value")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize portfolio risk exposures.")
    parser.add_argument("holdings_csv", help="Path to holdings CSV")
    parser.add_argument("--top", type=int, default=10, help="Rows to show in concentration table")
    return parser.parse_args()


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    is_percent = cleaned.endswith("%")
    if is_percent:
        cleaned = cleaned[:-1]
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if is_percent:
        return number / 100.0
    return number


def parse_direction(value: str | None) -> int:
    normalized = (value or "long").strip().lower()
    if normalized in {"short", "s", "-1", "sell"}:
        return -1
    if normalized in {"cash", "flat", "0"}:
        return 0
    return 1


def first_number(row: dict[str, str], fields: Iterable[str]) -> float | None:
    for field in fields:
        value = parse_number(row.get(field))
        if value is not None:
            return value
    return None


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total_abs_value = 0.0
    values: list[float | None] = []
    for row in rows:
        value = first_number(row, VALUE_FIELDS)
        values.append(value)
        if value is not None:
            total_abs_value += abs(value)

    enriched: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        direction = parse_direction(row.get("direction"))
        raw_weight = first_number(row, WEIGHT_FIELDS)
        value = values[index]
        if raw_weight is None and value is not None and total_abs_value:
            raw_weight = abs(value) / total_abs_value
        weight = raw_weight if raw_weight is not None else 0.0
        signed_weight = weight * direction
        enriched.append(
            {
                "ticker": (row.get("ticker") or row.get("symbol") or "").strip().upper(),
                "direction": direction,
                "weight": weight,
                "signed_weight": signed_weight,
                "sector": (row.get("sector") or "Unclassified").strip() or "Unclassified",
                "asset_class": (row.get("asset_class") or "Equity").strip() or "Equity",
                "beta": parse_number(row.get("beta")),
                "rate_sensitivity": (row.get("rate_sensitivity") or "").strip(),
                "usd_sensitivity": (row.get("usd_sensitivity") or "").strip(),
                "policy_sensitivity": (row.get("policy_sensitivity") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            }
        )
    return enriched


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def aggregate_by(rows: list[dict[str, object]], field: str) -> dict[str, float]:
    output: dict[str, float] = defaultdict(float)
    for row in rows:
        key = str(row[field])
        output[key] += float(row["signed_weight"])
    return dict(sorted(output.items(), key=lambda item: abs(item[1]), reverse=True))


def weighted_average_beta(rows: list[dict[str, object]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        beta = row["beta"]
        if beta is None:
            continue
        weight = abs(float(row["signed_weight"]))
        numerator += float(beta) * weight
        denominator += weight
    if denominator == 0:
        return None
    return numerator / denominator


def render_markdown(rows: list[dict[str, object]], top: int) -> str:
    gross = sum(abs(float(row["signed_weight"])) for row in rows)
    net = sum(float(row["signed_weight"]) for row in rows)
    long_exposure = sum(max(float(row["signed_weight"]), 0.0) for row in rows)
    short_exposure = -sum(min(float(row["signed_weight"]), 0.0) for row in rows)
    beta = weighted_average_beta(rows)
    sectors = aggregate_by(rows, "sector")
    asset_classes = aggregate_by(rows, "asset_class")
    top_rows = sorted(rows, key=lambda row: abs(float(row["signed_weight"])), reverse=True)[:top]

    lines = [
        "# Portfolio Risk Summary",
        "",
        "## Exposure",
        f"- Gross exposure: {pct(gross)}",
        f"- Net exposure: {pct(net)}",
        f"- Long exposure: {pct(long_exposure)}",
        f"- Short exposure: {pct(short_exposure)}",
        f"- Weighted beta: {beta:.2f}" if beta is not None else "- Weighted beta: unavailable",
        "",
        "## Sector Exposure",
        "| Sector | Net Weight |",
        "|---|---:|",
    ]
    for sector, value in sectors.items():
        lines.append(f"| {sector} | {pct(value)} |")

    lines.extend(["", "## Asset Class Exposure", "| Asset Class | Net Weight |", "|---|---:|"])
    for asset_class, value in asset_classes.items():
        lines.append(f"| {asset_class} | {pct(value)} |")

    lines.extend(
        [
            "",
            "## Top Concentrations",
            "| Ticker | Direction | Weight | Sector | Rate | USD | Policy | Notes |",
            "|---|---|---:|---|---|---|---|---|",
        ]
    )
    for row in top_rows:
        direction = "Long" if int(row["direction"]) >= 0 else "Short"
        lines.append(
            "| {ticker} | {direction} | {weight} | {sector} | {rate} | {usd} | {policy} | {notes} |".format(
                ticker=row["ticker"] or "N/A",
                direction=direction,
                weight=pct(float(row["signed_weight"])),
                sector=row["sector"],
                rate=row["rate_sensitivity"] or "-",
                usd=row["usd_sensitivity"] or "-",
                policy=row["policy_sensitivity"] or "-",
                notes=str(row["notes"]).replace("|", "/") or "-",
            )
        )

    lines.extend(
        [
            "",
            "## Follow-up Checks",
            "- Verify current prices, options delta, and event dates before using this for sizing.",
            "- Check whether top positions share the same rate, USD, AI/semiconductor, tariff, or liquidity factor.",
            "- Stress test the book against yield spikes, USD strength, risk-off, and earnings misses.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    rows = enrich_rows(load_rows(Path(args.holdings_csv)))
    print(render_markdown(rows, args.top))


if __name__ == "__main__":
    main()
