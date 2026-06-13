#!/usr/bin/env python3
"""Rank a watchlist CSV using configurable research scores."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


SCORE_FIELDS = (
    "macro_fit",
    "company_quality",
    "valuation",
    "catalyst",
    "technical_setup",
    "liquidity",
)
RISK_FIELD = "risk_penalty"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank trading research candidates.")
    parser.add_argument("watchlist_csv", help="Path to watchlist CSV")
    parser.add_argument("--top", type=int, default=20, help="Rows to show")
    return parser.parse_args()


def parse_score(value: str | None) -> float:
    if value is None or not value.strip():
        return 0.0
    try:
        score = float(value.strip())
    except ValueError:
        return 0.0
    return max(0.0, min(5.0, score))


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def score_row(row: dict[str, str]) -> float:
    positive = sum(parse_score(row.get(field)) for field in SCORE_FIELDS)
    risk = parse_score(row.get(RISK_FIELD))
    return positive - risk


def confidence(score: float) -> str:
    if score >= 22:
        return "High"
    if score >= 16:
        return "Medium"
    return "Low"


def render_markdown(rows: list[dict[str, str]], top: int) -> str:
    ranked = sorted(rows, key=score_row, reverse=True)[:top]
    lines = [
        "# Watchlist Ranking",
        "",
        "| Rank | Ticker | Score | Confidence | Thesis | Macro | Catalyst | Risk | Timing | Next Check |",
        "|---:|---|---:|---|---|---|---|---|---|---|",
    ]
    for index, row in enumerate(ranked, start=1):
        score = score_row(row)
        lines.append(
            "| {rank} | {ticker} | {score:.1f} | {confidence} | {thesis} | {macro} | {catalyst} | {risk} | {timing} | {next_check} |".format(
                rank=index,
                ticker=(row.get("ticker") or row.get("symbol") or "").strip().upper() or "N/A",
                score=score,
                confidence=confidence(score),
                thesis=clean(row.get("thesis")),
                macro=clean(row.get("macro_note")),
                catalyst=clean(row.get("catalyst_note")),
                risk=clean(row.get("risk_note")),
                timing=clean(row.get("timing_condition")),
                next_check=clean(row.get("next_check")),
            )
        )
    lines.extend(
        [
            "",
            "## Scoring Notes",
            "- Positive fields are scored 0-5: macro_fit, company_quality, valuation, catalyst, technical_setup, liquidity.",
            "- risk_penalty is scored 0-5 and subtracted from the total.",
            "- Treat this as prioritization for research, not as a standalone trade signal.",
        ]
    )
    return "\n".join(lines)


def clean(value: str | None) -> str:
    text = (value or "-").strip() or "-"
    return text.replace("|", "/")


def main() -> None:
    args = parse_args()
    print(render_markdown(load_rows(Path(args.watchlist_csv)), args.top))


if __name__ == "__main__":
    main()
