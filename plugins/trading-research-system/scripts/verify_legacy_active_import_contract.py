#!/usr/bin/env python3
"""Verify legacy active CSV import workflow stays wired and documented."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "importer": ROOT / "scripts" / "import_legacy_active_csv.py",
    "selftest": ROOT / "scripts" / "verify_legacy_active_import_selftest.py",
    "fixture": ROOT / "assets" / "fixtures" / "input" / "legacy-active-trades.csv",
    "trade_journal": ROOT / "skills" / "trading-research-system" / "references"
    / "trade-journal.md",
    "readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "importer": [
        "Import legacy active Sheet CSV rows",
        "REQUIRED_HEADERS",
        "allow_unknown_execution_fields=True",
        "should_import_exit",
        "not_counted",
        "legacy active",
    ],
    "selftest": [
        "legacy active import selftest ok",
        "legacy-active-trades.csv",
        "20260115-QQQ-001",
        "20260115-MU-001",
        "not_counted",
    ],
    "fixture": [
        "entry_date,symbol,direction,trade_type,product,timeframe",
        "2026-01-15,qqq,long,daytrade,call,5min",
        "2026-01-15,mu,long,swing,bull call spread,15min",
        "未计入统计",
    ],
    "trade_journal": [
        "import_legacy_active_csv.py",
        "legacy `active`",
    ],
    "readme": [
        "import_legacy_active_csv.py",
        "legacy-active-trades.csv",
    ],
    "roadmap": [
        "Legacy active import module",
        "import_legacy_active_csv.py",
    ],
    "development_plan": [
        "legacy active Sheet CSV importer",
        "import_legacy_active_csv.py",
    ],
}

SPEC = ContractSpec(
    name="legacy active import",
    success_message="legacy active import contract ok",
    files={key: FileContract(path=path, required_terms=REQUIRED[key]) for key, path in FILES.items()},
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
