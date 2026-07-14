#!/usr/bin/env python3
"""Verify actual trade record update workflow stays wired end to end."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

FILES = {
    "skill": ROOT / "skills" / "trading-research-system" / "references" / "workflow-trade-review.md",
    "interactive_review": ROOT / "skills" / "trading-research-system" / "references"
    / "interactive-trade-review.md",
    "trade_journal": ROOT / "skills" / "trading-research-system" / "references"
    / "trade-journal.md",
    "records_module": ROOT / "scripts" / "trade_records.py",
    "update_script": ROOT / "scripts" / "update_trade_record.py",
    "selftest": ROOT / "scripts" / "verify_trade_record_update_selftest.py",
    "record_schemas": ROOT / "scripts" / "record_schemas.py",
    "readme": ROOT / "README.md",
    "roadmap": REPO / "docs" / "ROADMAP.md",
    "development_plan": REPO / "docs" / "DEVELOPMENT_PLAN.md",
}

REQUIRED = {
    "skill": [
        "update_trade_record.py",
        "post-order",
        "post-exit",
        "fields JSON",
        "--allow-unknown-execution-fields",
    ],
    "interactive_review": [
        "update_trade_record.py",
        "fields JSON",
        "post-order",
        "post-exit",
    ],
    "trade_journal": [
        "update_trade_record.py",
        "post-order",
        "post-exit",
        "fields-json",
        "--allow-unknown-execution-fields",
    ],
    "records_module": [
        "TradeRecordUpdate",
        "apply_trade_update",
        "post-order",
        "post-exit",
        "unknown trades.csv fields",
        "UNKNOWNABLE_EXECUTION_FIELDS",
    ],
    "update_script": [
        "--stage",
        "--trade-id",
        "--fields-json",
        "--review-file",
        "--allow-unknown-execution-fields",
        "apply_trade_update",
    ],
    "selftest": [
        "trade record update selftest ok",
        "post-order",
        "post-exit",
        "unknown-field failure",
        "--allow-unknown-execution-fields",
    ],
    "record_schemas": [
        '"trades.csv"',
        "trade_id",
        "entry_review",
        "exit_review",
    ],
    "readme": [
        "update_trade_record.py",
        "--fields-json",
    ],
    "roadmap": [
        "Actual trade record module",
        "update_trade_record.py",
    ],
    "development_plan": [
        "Actual trade record module",
        "update_trade_record.py",
    ],
}

SPEC = ContractSpec(
    name="actual trade record",
    success_message="actual trade record contract ok",
    files={
        key: FileContract(path=path, required_terms=REQUIRED[key])
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
