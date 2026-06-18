#!/usr/bin/env python3
"""Self-test the shared contract verifier behavior."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contract_verifier import ContractSpec, FileContract, verify_contract


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _assert_contains(failures: list[str], expected: str) -> None:
    if not any(expected in failure for failure in failures):
        raise AssertionError(f"expected {expected!r} in failures: {failures!r}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        note = _write(tmp / "note.md", "## Decision\nalpha\n")
        csv_file = _write(tmp / "records.csv", "id,name\n1,QQQ\n")

        good = ContractSpec(
            name="good",
            success_message="ok",
            files={
                "note": FileContract(
                    path=note,
                    required_terms=("alpha",),
                    required_headings=("## Decision",),
                    forbidden_terms=("stale",),
                ),
                "csv": FileContract(path=csv_file, csv_header=("id", "name")),
            },
        )
        failures = verify_contract(good)
        if failures:
            raise AssertionError(f"expected no failures, got: {failures!r}")

        missing_required = ContractSpec(
            name="missing required",
            success_message="ok",
            files={"note": FileContract(path=note, required_terms=("beta",))},
        )
        _assert_contains(verify_contract(missing_required), "missing 'beta'")

        forbidden = ContractSpec(
            name="forbidden",
            success_message="ok",
            files={"note": FileContract(path=note, forbidden_terms=("alpha",))},
        )
        _assert_contains(verify_contract(forbidden), "forbidden term 'alpha'")

        bad_header = ContractSpec(
            name="bad header",
            success_message="ok",
            files={"csv": FileContract(path=csv_file, csv_header=("id", "ticker"))},
        )
        _assert_contains(verify_contract(bad_header), "CSV header mismatch")

    print("contract verifier selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
