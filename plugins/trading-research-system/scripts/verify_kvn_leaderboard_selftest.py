#!/usr/bin/env python3
"""Self-test KVN snapshot import, display, query, and change summary."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kvn_leaderboard.py"
FIXTURE_DIR = ROOT / "assets" / "fixtures" / "input"
EXPECTED_TOP10 = ROOT / "assets" / "fixtures" / "expected" / "kvn-leaderboard-2026-06-24.md"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "kvn.sqlite"

        run_command(
            "import first snapshot",
            [
                str(SCRIPT),
                "import",
                str(FIXTURE_DIR / "kvn-snapshot-2026-06-21.csv"),
                "--db",
                str(db_path),
                "--source",
                "fixture",
            ],
        )
        run_command(
            "import second snapshot",
            [
                str(SCRIPT),
                "import",
                str(FIXTURE_DIR / "kvn-snapshot-2026-06-24.csv"),
                "--db",
                str(db_path),
                "--source",
                "fixture",
            ],
        )

        top10 = run_command(
            "show top10",
            [str(SCRIPT), "show", "--db", str(db_path), "--date", "2026-06-24", "--top", "10"],
        )
        expected = EXPECTED_TOP10.read_text(encoding="utf-8").strip()
        if top10.stdout.strip() != expected:
            raise AssertionError(diff_message("top10 output mismatch", expected, top10.stdout.strip()))

        query = run_command(
            "query symbol",
            [str(SCRIPT), "query", "SOXX", "--db", str(db_path), "--date", "2026-06-24"],
        ).stdout
        require_terms(
            query,
            [
                "# KVN Ticker Lookup",
                "SOXX",
                "0.0310",
                "current top10: no",
                "Research priority only, not a buy list.",
            ],
        )

        changes = run_command(
            "changes",
            [str(SCRIPT), "changes", "--db", str(db_path), "--date", "2026-06-24"],
        ).stdout
        require_terms(
            changes,
            [
                "# KVN Top10 Changes",
                "New Top10: `GLW`, `ARM`, `BE`, `TSM`, `NVDA`",
                "Dropped from Top10: `CSTM`, `SNEX`, `NEXA`, `DY`, `GM`",
                "Continued Top10: `SNDK`, `CRDO`, `LITE`, `FN`, `MXL`",
                "Research priority only, not a buy list.",
            ],
        )

    print("kvn leaderboard selftest ok")
    return 0


def run_command(label: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"{label} failed: {result.stderr or result.stdout}")
    return result


def require_terms(text: str, terms: list[str]) -> None:
    missing = [term for term in terms if term not in text]
    if missing:
        raise AssertionError(f"missing terms {missing!r} in:\n{text}")


def diff_message(title: str, expected: str, actual: str) -> str:
    return f"{title}\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}"


if __name__ == "__main__":
    sys.exit(main())
