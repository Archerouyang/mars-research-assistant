#!/usr/bin/env python3
"""Verify bundled local record templates match canonical schemas."""

from __future__ import annotations

from pathlib import Path
import sys

from contract_verifier import ContractSpec, FileContract, run_contract
from record_schemas import CSV_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "assets" / "templates"

SPEC = ContractSpec(
    name="record templates",
    success_message="record template contract ok",
    files={
        name: FileContract(
            path=TEMPLATE_DIR / name,
            csv_header=schema,
            csv_rows_match_header=True,
        )
        for name, schema in CSV_SCHEMAS.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
