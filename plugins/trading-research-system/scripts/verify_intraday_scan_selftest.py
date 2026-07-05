#!/usr/bin/env python3
"""Self-test plan-scoped intraday setup scan rendering."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "intraday_scan.py"
FIXTURE = (
    ROOT
    / "assets"
    / "fixtures"
    / "runtime"
    / "active-market-plan-2026-06-24"
    / "daily"
    / "2026-06-24"
    / "intraday-watchlist.csv"
)


def main() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(FIXTURE),
            "--date",
            "2026-06-24",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)

    output = result.stdout
    expected_terms = (
        "This is decision support only. It is not a buy/sell instruction.",
        "glw-optical-reversal | invalidated",
        "qqq-0dte-breakout-pullback | triggered",
        "soxx-sector-confirmation | needs_review",
        "crdo-ai-infra-pullback | approaching",
        "execution_check_required; confirm trigger-timeframe follow-through and risk",
        "archive or create a new setup later",
    )
    for expected in expected_terms:
        if expected not in output:
            raise AssertionError(f"missing {expected!r} in {output!r}")

    order = [
        output.index("glw-optical-reversal | invalidated"),
        output.index("qqq-0dte-breakout-pullback | triggered"),
        output.index("soxx-sector-confirmation | needs_review"),
        output.index("crdo-ai-infra-pullback | approaching"),
    ]
    if order != sorted(order):
        raise AssertionError(f"scan rows are not sorted by attention priority: {order!r}")

    print("intraday scan selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
