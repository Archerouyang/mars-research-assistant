#!/usr/bin/env python3
"""Self-test the repo-level Behavior Contract Matrix Module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from behavior_contract_matrix import (
    CommandCase,
    FileExpectation,
    MatrixHarnessError,
    run_command_matrix,
)


def main() -> int:
    try:
        run_command_matrix(
            "selftest",
            (
                CommandCase(
                    case_id="ids/duplicate",
                    command=("definitely-not-a-command",),
                ),
                CommandCase(
                    case_id="ids/duplicate",
                    command=("definitely-not-a-command",),
                ),
            ),
        )
    except MatrixHarnessError as error:
        if "duplicate case ID 'ids/duplicate'" not in str(error):
            raise AssertionError(f"unexpected duplicate-ID diagnostic: {error}")
    else:
        raise AssertionError("duplicate case IDs must fail before command execution")

    try:
        run_command_matrix(
            "selftest",
            (
                CommandCase(
                    case_id="IDs contain spaces",
                    command=("definitely-not-a-command",),
                ),
            ),
        )
    except MatrixHarnessError as error:
        if "invalid case ID 'IDs contain spaces'" not in str(error):
            raise AssertionError(f"unexpected invalid-ID diagnostic: {error}")
    else:
        raise AssertionError("invalid case IDs must fail before command execution")

    result = run_command_matrix(
        "selftest",
        (
            CommandCase(
                case_id="output/first-mismatch",
                command=(sys.executable, "-c", "print('actual one')"),
                required_stdout=("expected one",),
            ),
            CommandCase(
                case_id="output/second-mismatch",
                command=(sys.executable, "-c", "print('actual two')"),
                forbidden_stdout=("actual two",),
            ),
        ),
    )

    if result.ok:
        raise AssertionError("matrix must report observable behavior mismatches")
    if result.failed_case_ids != (
        "output/first-mismatch",
        "output/second-mismatch",
    ):
        raise AssertionError(f"matrix did not preserve stable case IDs: {result!r}")

    rendered = result.render_failures()
    for term in (
        "selftest/output/first-mismatch",
        "missing stdout term 'expected one'",
        "selftest/output/second-mismatch",
        "forbidden stdout term 'actual two'",
    ):
        if term not in rendered:
            raise AssertionError(f"aggregated matrix diagnostics missing {term!r}: {rendered}")

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        created = tmp / "created.txt"
        untouched = tmp / "untouched.txt"
        absent = tmp / "absent.txt"
        untouched.write_text("keep me\n", encoding="utf-8")
        file_result = run_command_matrix(
            "selftest-files",
            (
                CommandCase(
                    case_id="files/observable-effects",
                    command=(
                        sys.executable,
                        "-c",
                        f"from pathlib import Path; Path({str(created)!r}).write_text('made\\n')",
                    ),
                    files=(
                        FileExpectation(created, "created", required_terms=("made",)),
                        FileExpectation(untouched, "unchanged"),
                        FileExpectation(absent, "absent"),
                    ),
                ),
            ),
        )
        if not file_result.ok:
            raise AssertionError(file_result.render_failures())

        must_not_run = tmp / "must-not-run.txt"
        try:
            run_command_matrix(
                "selftest-harness",
                (
                    CommandCase(
                        case_id="harness/earlier-valid-case",
                        command=(
                            sys.executable,
                            "-c",
                            f"from pathlib import Path; Path({str(must_not_run)!r}).touch()",
                        ),
                    ),
                    CommandCase(
                        case_id="harness/missing-executable",
                        command=("definitely-not-a-command",),
                    ),
                ),
            )
        except MatrixHarnessError as error:
            if "command executable not found" not in str(error):
                raise AssertionError(f"unexpected command preflight diagnostic: {error}")
        else:
            raise AssertionError("missing command executable must fail harness preflight")
        if must_not_run.exists():
            raise AssertionError("harness corruption must fail before any case executes")

        try:
            run_command_matrix(
                "selftest-harness",
                (
                    CommandCase(
                        case_id="harness/invalid-cwd",
                        command=(sys.executable, "-c", "pass"),
                        cwd=tmp / "missing-cwd",
                    ),
                ),
            )
        except MatrixHarnessError as error:
            if "cwd is not a directory" not in str(error):
                raise AssertionError(f"unexpected cwd preflight diagnostic: {error}")
        else:
            raise AssertionError("invalid cwd must fail harness preflight")

    print("behavior contract matrix selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
