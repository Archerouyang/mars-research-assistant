#!/usr/bin/env python3
"""Run a registered Trading Research contract suite."""

from __future__ import annotations

import argparse
import sys

from contract_suite import run_contract_suite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Trading Research contract suites.")
    parser.add_argument("suite", nargs="?", default="core", help="Suite name; defaults to core")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run_contract_suite(args.suite)
    except ValueError as error:
        print(f"contract suite failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
