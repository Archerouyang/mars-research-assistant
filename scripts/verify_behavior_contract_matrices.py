#!/usr/bin/env python3
"""Run high-risk Trading Research System behavior matrices."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
import sys
import tempfile

from behavior_contract_matrix import CommandCase, run_command_matrix
from behavior_contract_reconciliation_cases import build_reconciliation_cases
from behavior_contract_setup_key_cases import build_setup_key_cases
from behavior_contract_startup_cases import build_startup_cases


CaseBuilder = Callable[[Path], tuple[CommandCase, ...]]
BUILDERS: dict[str, CaseBuilder] = {
    "reconciliation": build_reconciliation_cases,
    "startup": build_startup_cases,
    "setup-key": build_setup_key_cases,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=tuple(BUILDERS), required=True)
    return parser.parse_args()


def run_family(family: str, builder: CaseBuilder) -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        result = run_command_matrix(family, builder(Path(raw_tmp)))
    if not result.ok:
        print(result.render_failures(), file=sys.stderr)
        return 1
    print(f"behavior contract matrix {family} ok")
    return 0


def main() -> int:
    args = parse_args()
    return run_family(args.family, BUILDERS[args.family])


if __name__ == "__main__":
    raise SystemExit(main())
