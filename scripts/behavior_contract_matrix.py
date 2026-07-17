#!/usr/bin/env python3
"""Run observable command scenarios and aggregate behavior mismatches."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Literal, Sequence


CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:[/-][a-z0-9]+(?:-[a-z0-9]+)*)*")


class MatrixHarnessError(ValueError):
    """The Matrix definition is invalid and no scenario should run."""


@dataclass(frozen=True)
class FileExpectation:
    """Expected observable state of one file after a command finishes."""

    path: Path
    state: Literal["created", "absent", "unchanged", "changed"]
    required_terms: Sequence[str] = field(default_factory=tuple)
    forbidden_terms: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommandCase:
    """One command scenario observed through its process Interface."""

    case_id: str
    command: Sequence[str]
    cwd: Path | None = None
    expected_returncode: int = 0
    required_stdout: Sequence[str] = field(default_factory=tuple)
    forbidden_stdout: Sequence[str] = field(default_factory=tuple)
    required_stderr: Sequence[str] = field(default_factory=tuple)
    forbidden_stderr: Sequence[str] = field(default_factory=tuple)
    files: Sequence[FileExpectation] = field(default_factory=tuple)


@dataclass(frozen=True)
class CaseResult:
    """Observable result and mismatches for one case."""

    case_id: str
    returncode: int
    stdout: str
    stderr: str
    failures: tuple[str, ...]


@dataclass(frozen=True)
class MatrixResult:
    """All behavior results for one scenario family."""

    family: str
    cases: tuple[CaseResult, ...]

    @property
    def ok(self) -> bool:
        return all(not case.failures for case in self.cases)

    @property
    def failed_case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.cases if case.failures)

    def render_failures(self) -> str:
        lines: list[str] = []
        for case in self.cases:
            lines.extend(
                f"{self.family}/{case.case_id}: {failure}"
                for failure in case.failures
            )
        return "\n".join(lines)


def run_command_matrix(
    family: str,
    cases: Sequence[CommandCase],
) -> MatrixResult:
    """Run every case and aggregate observable behavior mismatches."""

    snapshots = _validate_and_snapshot(cases)
    results: list[CaseResult] = []
    for case in cases:
        completed = subprocess.run(
            list(case.command),
            cwd=case.cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        failures: list[str] = []
        if completed.returncode != case.expected_returncode:
            failures.append(
                "return code mismatch: "
                f"expected {case.expected_returncode}; actual {completed.returncode}"
            )
        failures.extend(
            f"missing stdout term {term!r}"
            for term in case.required_stdout
            if term not in completed.stdout
        )
        failures.extend(
            f"forbidden stdout term {term!r}"
            for term in case.forbidden_stdout
            if term in completed.stdout
        )
        failures.extend(
            f"missing stderr term {term!r}"
            for term in case.required_stderr
            if term not in completed.stderr
        )
        failures.extend(
            f"forbidden stderr term {term!r}"
            for term in case.forbidden_stderr
            if term in completed.stderr
        )
        for expected_file in case.files:
            before = snapshots[(case.case_id, expected_file.path)]
            failures.extend(_file_failures(expected_file, before))
        results.append(
            CaseResult(
                case_id=case.case_id,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                failures=tuple(failures),
            )
        )

    return MatrixResult(family=family, cases=tuple(results))


def _validate_and_snapshot(
    cases: Sequence[CommandCase],
) -> dict[tuple[str, Path], bytes | None]:
    seen: set[str] = set()
    snapshots: dict[tuple[str, Path], bytes | None] = {}
    for case in cases:
        if not isinstance(case, CommandCase):
            raise MatrixHarnessError(f"invalid command case: {case!r}")
        if CASE_ID_PATTERN.fullmatch(case.case_id) is None:
            raise MatrixHarnessError(f"invalid case ID {case.case_id!r}")
        if case.case_id in seen:
            raise MatrixHarnessError(f"duplicate case ID {case.case_id!r}")
        seen.add(case.case_id)

    for case in cases:
        _validate_command(case)
        _validate_terms(case.case_id, "required_stdout", case.required_stdout)
        _validate_terms(case.case_id, "forbidden_stdout", case.forbidden_stdout)
        _validate_terms(case.case_id, "required_stderr", case.required_stderr)
        _validate_terms(case.case_id, "forbidden_stderr", case.forbidden_stderr)
        case_paths: set[Path] = set()
        for expected_file in case.files:
            if not isinstance(expected_file, FileExpectation):
                raise MatrixHarnessError(
                    f"invalid file expectation in {case.case_id!r}: {expected_file!r}"
                )
            path = expected_file.path
            if not isinstance(path, Path):
                raise MatrixHarnessError(
                    f"file path must be pathlib.Path in {case.case_id!r}: {path!r}"
                )
            if path in case_paths:
                raise MatrixHarnessError(
                    f"duplicate file expectation in {case.case_id!r}: {path}"
                )
            case_paths.add(path)
            if expected_file.state not in {"created", "absent", "unchanged", "changed"}:
                raise MatrixHarnessError(
                    f"invalid file state in {case.case_id!r}: {expected_file.state!r}"
                )
            _validate_terms(
                case.case_id,
                f"file {path} required_terms",
                expected_file.required_terms,
            )
            _validate_terms(
                case.case_id,
                f"file {path} forbidden_terms",
                expected_file.forbidden_terms,
            )
            before = path.read_bytes() if path.is_file() else None
            if expected_file.state == "created" and before is not None:
                raise MatrixHarnessError(
                    f"created-file precondition failed in {case.case_id!r}: {path}"
                )
            if expected_file.state in {"unchanged", "changed"} and before is None:
                raise MatrixHarnessError(
                    f"{expected_file.state}-file precondition failed in "
                    f"{case.case_id!r}: {path}"
                )
            snapshots[(case.case_id, path)] = before
    return snapshots


def _validate_command(case: CommandCase) -> None:
    if isinstance(case.command, (str, bytes)) or not case.command:
        raise MatrixHarnessError(f"command must be a non-empty string sequence in {case.case_id!r}")
    if any(not isinstance(arg, str) for arg in case.command) or not case.command[0]:
        raise MatrixHarnessError(f"command contains an invalid argument in {case.case_id!r}")
    if isinstance(case.expected_returncode, bool) or not isinstance(
        case.expected_returncode, int
    ):
        raise MatrixHarnessError(f"return code must be an integer in {case.case_id!r}")
    if case.cwd is not None and (
        not isinstance(case.cwd, Path) or not case.cwd.is_dir()
    ):
        raise MatrixHarnessError(f"cwd is not a directory in {case.case_id!r}: {case.cwd}")

    executable = case.command[0]
    if os.sep in executable:
        executable_path = Path(executable)
        if not executable_path.is_absolute():
            executable_path = (case.cwd or Path.cwd()) / executable_path
        found = executable_path.is_file() and os.access(executable_path, os.X_OK)
    else:
        found = shutil.which(executable) is not None
    if not found:
        raise MatrixHarnessError(
            f"command executable not found in {case.case_id!r}: {executable!r}"
        )


def _validate_terms(case_id: str, field_name: str, terms: Sequence[str]) -> None:
    if isinstance(terms, (str, bytes)) or any(
        not isinstance(term, str) or not term for term in terms
    ):
        raise MatrixHarnessError(f"invalid {field_name} in {case_id!r}")


def _file_failures(
    expectation: FileExpectation,
    before: bytes | None,
) -> list[str]:
    path = expectation.path
    after = path.read_bytes() if path.is_file() else None
    failures: list[str] = []
    if expectation.state == "created" and after is None:
        failures.append(f"expected file to be created: {path}")
    elif expectation.state == "absent" and after is not None:
        failures.append(f"expected file to remain absent: {path}")
    elif expectation.state == "unchanged" and after != before:
        failures.append(f"expected file to remain unchanged: {path}")
    elif expectation.state == "changed" and (after is None or after == before):
        failures.append(f"expected file to change: {path}")

    if after is not None and (expectation.required_terms or expectation.forbidden_terms):
        try:
            text = after.decode("utf-8")
        except UnicodeDecodeError:
            failures.append(f"expected UTF-8 text file: {path}")
        else:
            failures.extend(
                f"missing file term {term!r}: {path}"
                for term in expectation.required_terms
                if term not in text
            )
            failures.extend(
                f"forbidden file term {term!r}: {path}"
                for term in expectation.forbidden_terms
                if term in text
            )
    return failures
