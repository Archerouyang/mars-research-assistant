#!/usr/bin/env python3
"""Verify trade plan preparation stays between research and setup pool."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "macro_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
    "active_plan": ROOT / "skills" / "trading-research" / "references" / "active-market-plan.md",
    "output_templates": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "output-templates.md",
    "market_template": ROOT / "assets" / "templates" / "market-plan.md",
    "weekly_template": ROOT / "assets" / "templates" / "weekly-plan.md",
    "fixture": ROOT / "assets" / "fixtures" / "expected" / "weekly-outlook-2026-06-15.md",
}

REQUIRED_TERMS = {
    "weekly_skill": [
        "Trade Plan Preparation",
        "Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "4H",
        "1D",
        "1W",
        "price structure",
        "preliminary risk context",
        "candidate",
        "active",
    ],
    "macro_skill": [
        "Trade Plan Preparation",
        "Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "动量候选池",
        "TODO",
    ],
    "active_plan": [
        "Trade Plan Preparation",
        "Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "higher-timeframe regime",
        "price_structure",
        "risk_context",
        "candidate",
        "active",
    ],
    "output_templates": [
        "## 交易计划准备",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "Cross-Section Candidate Pool",
        "截面候选池",
        "price_structure / risk_context",
    ],
    "market_template": [
        "## Trade Plan Preparation",
        "### Input Reads",
        "### Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "Price structure / risk context",
    ],
    "weekly_template": [
        "## Trade Plan Preparation",
        "### Input Reads",
        "### Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "Price structure / risk context",
    ],
    "fixture": [
        "## 交易计划准备",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "截面候选池",
        "price_structure / risk_context",
        "4H/1D/1W",
        "candidate setup",
    ],
}

FORBIDDEN_TERMS = {
    "weekly_skill": [
        "momentum leaderboard update: strongest and weakest symbols/themes",
        "Momentum Leaderboard update: strongest and weakest symbols/themes",
    ],
    "macro_skill": [
        "Rank candidates by research priority, not as standalone trade recommendations.",
    ],
}


def main() -> None:
    failures: list[str] = []

    for name, path in FILES.items():
        if not path.exists():
            failures.append(f"{path}: missing expected file")
            continue
        text = path.read_text(encoding="utf-8")
        for term in REQUIRED_TERMS[name]:
            if term not in text:
                failures.append(f"{path}: missing {term!r}")
        for term in FORBIDDEN_TERMS.get(name, []):
            if term in text:
                failures.append(f"{path}: forbidden stale wording {term!r}")

    if failures:
        raise SystemExit("\n".join(failures))

    print("trade plan preparation contract ok")


if __name__ == "__main__":
    main()
