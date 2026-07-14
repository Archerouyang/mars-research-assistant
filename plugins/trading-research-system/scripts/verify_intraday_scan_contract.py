#!/usr/bin/env python3
"""Verify the plan-scoped intraday scan script and docs are wired."""

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-intraday-setup-scan.md",
    "reference": ROOT / "skills" / "trading-research-system" / "references"
    / "intraday-setup-scan.md",
    "script": ROOT / "scripts" / "intraday_scan.py",
    "selftest": ROOT / "scripts" / "verify_intraday_scan_selftest.py",
    "expected": ROOT / "assets" / "fixtures" / "expected" / "intraday-scan-2026-06-24.md",
    "readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "skill": [
        "intraday_scan.py",
        "setup-scoped intraday monitoring",
        "not an order instruction",
        "Sort by attention priority",
    ],
    "reference": [
        "intraday_scan.py",
        "current `market-plan.md`, update note, watchlist, or prepared setup plan",
        "not trade recommendation strength",
        "price contact alone",
    ],
    "script": [
        "plan-scoped intraday setup scan",
        "STATUS_PRIORITY",
        "execution_check_required",
        "not a buy/sell instruction",
        "Do not scan",
    ],
    "selftest": [
        "intraday scan selftest ok",
        "glw-optical-reversal | invalidated",
        "qqq-0dte-breakout-pullback | triggered",
    ],
    "expected": [
        "not a buy/sell instruction",
        "execution_check_required",
        "invalidated",
        "triggered",
        "needs_review",
        "approaching",
    ],
    "readme": [
        "intraday_scan.py",
        "setup-scoped intraday scanning",
    ],
    "roadmap": [
        "Plan-scoped intraday scan script",
        "intraday_scan.py",
    ],
    "development_plan": [
        "Plan-scoped intraday scan script",
        "intraday_scan.py",
    ],
}

SPEC = ContractSpec(
    name="intraday scan",
    success_message="intraday scan contract ok",
    failure_header="intraday scan contract failed:",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
