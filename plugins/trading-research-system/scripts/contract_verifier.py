#!/usr/bin/env python3
"""Shared contract verification helpers for Trading Research System scripts."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class FileContract:
    """Observable requirements for one contract-owned file."""

    path: Path
    required_terms: Sequence[str] = field(default_factory=tuple)
    required_headings: Sequence[str] = field(default_factory=tuple)
    forbidden_terms: Sequence[str] = field(default_factory=tuple)
    forbidden_label: str = "forbidden term"
    csv_header: Sequence[str] | None = None


@dataclass(frozen=True)
class ContractSpec:
    """A public contract check with stable CLI success/failure wording."""

    name: str
    files: Mapping[str, FileContract]
    success_message: str
    failure_header: str | None = None


def verify_contract(spec: ContractSpec) -> list[str]:
    """Return human-readable contract failures without printing or exiting."""

    failures: list[str] = []
    for key, contract in spec.files.items():
        path = contract.path
        if not path.exists():
            failures.append(f"{key}: missing {path}")
            continue

        text = path.read_text(encoding="utf-8-sig")
        failures.extend(_verify_required_terms(key, path, text, contract.required_terms))
        failures.extend(_verify_required_headings(key, path, text, contract.required_headings))
        failures.extend(
            _verify_forbidden_terms(
                key,
                path,
                text,
                contract.forbidden_terms,
                contract.forbidden_label,
            )
        )
        if contract.csv_header is not None:
            failures.extend(_verify_csv_header(key, path, text, tuple(contract.csv_header)))

    return failures


def run_contract(spec: ContractSpec) -> int:
    """Run a contract check as a command-line script."""

    failures = verify_contract(spec)
    if failures:
        if spec.failure_header:
            print(spec.failure_header)
            for failure in failures:
                print(f"- {failure}")
        else:
            for failure in failures:
                print(failure)
        return 1

    print(spec.success_message)
    return 0


def _verify_required_terms(
    key: str,
    path: Path,
    text: str,
    required_terms: Sequence[str],
) -> list[str]:
    return [
        f"{key}: missing {term!r} in {path}"
        for term in required_terms
        if term not in text
    ]


def _verify_required_headings(
    key: str,
    path: Path,
    text: str,
    required_headings: Sequence[str],
) -> list[str]:
    return [
        f"{key}: missing heading {heading!r} in {path}"
        for heading in required_headings
        if heading not in text
    ]


def _verify_forbidden_terms(
    key: str,
    path: Path,
    text: str,
    forbidden_terms: Sequence[str],
    forbidden_label: str,
) -> list[str]:
    return [
        f"{key}: {forbidden_label} {term!r} in {path}"
        for term in forbidden_terms
        if term in text
    ]


def _verify_csv_header(
    key: str,
    path: Path,
    text: str,
    expected_header: tuple[str, ...],
) -> list[str]:
    reader = csv.reader(StringIO(text))
    actual_header = tuple(next(reader, ()))
    if actual_header == expected_header:
        return []

    return [
        (
            f"{key}: CSV header mismatch in {path}; "
            f"expected {list(expected_header)!r}; actual {list(actual_header)!r}"
        )
    ]
