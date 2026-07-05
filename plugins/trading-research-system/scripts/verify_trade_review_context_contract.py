#!/usr/bin/env python3
"""Verify the two-stage review-context workflow is wired as the default path."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "skill": ROOT / "skills" / "trade-review" / "SKILL.md",
    "interactive_review": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "interactive-trade-review.md",
    "trade_journal": ROOT
    / "skills"
    / "trading-research"
    / "references"
    / "trade-journal.md",
    "writer": ROOT / "scripts" / "write_trade_review_context.py",
    "selftest": ROOT / "scripts" / "verify_trade_review_context_selftest.py",
    "fixture_reviews": ROOT
    / "assets"
    / "fixtures"
    / "runtime"
    / "active-market-plan-2026-06-24"
    / "daily"
    / "2026-06-24"
    / "reviews.md",
    "readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "skill": [
        "review-context",
        "write_trade_review_context.py",
        "broker-live facts",
        "Compatibility path",
        "update_trade_record.py",
    ],
    "interactive_review": [
        "review-context draft",
        "write_trade_review_context.py",
        "Compatibility path",
        "update_trade_record.py",
        "post-order",
        "post-exit",
    ],
    "trade_journal": [
        "review context",
        "write_trade_review_context.py",
        "Compatibility path",
        "broker-live",
    ],
    "writer": [
        "Append a two-stage trade review context section",
        "post-order",
        "post-exit",
        "reviews.md",
        "trades.csv",
    ],
    "selftest": [
        "trade review context selftest ok",
        "post-order",
        "post-exit",
        "must not create trades.csv",
    ],
    "fixture_reviews": [
        "Stage: post_order",
        "Stage: post_exit",
        "Entry facts:",
        "Exit facts:",
        "broker-live fixture",
    ],
    "readme": [
        "write_trade_review_context.py",
        "Interactive post-order and post-exit review context intake",
    ],
    "roadmap": [
        "Two-stage review context",
        "write_trade_review_context.py",
    ],
    "development_plan": [
        "Two-stage review context",
        "write_trade_review_context.py",
    ],
}

FORBIDDEN = {
    "skill": ["Use this skill to turn actual trades into structured `trades.csv` records"],
    "interactive_review": ["Each stage should produce two default outputs:"],
}

SPEC = ContractSpec(
    name="trade review context",
    success_message="trade review context contract ok",
    failure_header="trade review context contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=FORBIDDEN.get(key, ()),
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
