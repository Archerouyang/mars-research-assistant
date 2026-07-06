#!/usr/bin/env python3
"""Verify trade plan preparation stays between research and setup pool."""

from __future__ import annotations

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)
ROOT = PATHS.root

FILES = {
    "weekly_skill": ROOT / "skills" / "weekly-trading-plan" / "SKILL.md",
    "macro_skill": ROOT / "skills" / "macro-equity-research" / "SKILL.md",
    "active_plan": ROOT / "skills" / "trading-research" / "references" / "active-market-plan.md",
    "macro_filter": ROOT / "skills" / "trading-research" / "references" / "macro-policy-filter.md",
    "equity_screening": ROOT / "skills" / "trading-research" / "references" / "equity-screening.md",
    "momentum_leaderboard": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "momentum-leaderboard.md",
    "output_templates": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "output-templates.md",
    "market_template": ROOT / "assets" / "templates" / "market-plan.md",
    "weekly_template": ROOT / "assets" / "templates" / "weekly-plan.md",
    "fixture": ROOT / "assets" / "fixtures" / "expected" / "weekly-outlook-2026-06-15.md",
    "kvn_fixture": ROOT
    / "assets"
    / "fixtures"
    / "expected"
    / "trade-plan-preparation-with-kvn-2026-06-24.md",
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
        "KVN Momentum Leaderboard",
        "imported snapshot",
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
        "imported KVN snapshot",
    ],
    "active_plan": [
        "Trade Plan Preparation",
        "Cross-Section Candidate Pool",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "KVN Momentum Leaderboard",
        "higher-timeframe regime",
        "price_structure",
        "risk_context",
        "candidate",
        "active",
    ],
    "macro_filter": [
        "Trade Plan Preparation Output",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "read",
        "supports",
        "pressures",
        "blocks",
        "evidence",
        "next_check",
        "Cross-Section Candidate Pool",
    ],
    "momentum_leaderboard": [
        "KVN is an imported snapshot",
        "research priority only, not a buy list",
        "Feed KVN names into Trade Plan Preparation",
        "macro/financial",
        "industry strength",
        "company thesis",
        "price structure",
        "portfolio risk",
    ],
    "equity_screening": [
        "Trade Plan Preparation Output",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "read",
        "supports",
        "pressures",
        "blocks",
        "evidence",
        "next_check",
        "Cross-Section Candidate Pool",
    ],
    "output_templates": [
        "## 交易计划准备",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "KVN Momentum Leaderboard",
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
        "KVN Momentum Leaderboard",
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
        "KVN Momentum Leaderboard",
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
    "kvn_fixture": [
        "## 交易计划准备",
        "KVN Momentum Leaderboard",
        "SNDK",
        "CRDO",
        "SOXX",
        "Cross-Section Candidate Pool",
        "截面候选池",
        "Macro Regime",
        "Financial Conditions",
        "Policy/Event Risk",
        "Industry/Sector Strength",
        "Company Thesis Check",
        "不是买入名单",
        "candidate setup",
        "price_structure / risk_context",
        "4H/1D/1W",
    ],
}

FORBIDDEN_TERMS = {
    "weekly_skill": [
        "momentum leaderboard update: strongest and weakest symbols/themes",
        "Momentum Leaderboard update: strongest and weakest symbols/themes",
        "Momentum leaderboard output is a separate future quantitative model",
        "momentum candidate pool TODO",
    ],
    "macro_skill": [
        "Rank candidates by research priority, not as standalone trade recommendations.",
    ],
}


SPEC = ContractSpec(
    name="trade plan preparation",
    success_message="trade plan preparation contract ok",
    files={
        name: FileContract(
            path=path,
            required_terms=REQUIRED_TERMS[name],
            forbidden_terms=FORBIDDEN_TERMS.get(name, ()),
            forbidden_label="forbidden stale wording",
        )
        for name, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
