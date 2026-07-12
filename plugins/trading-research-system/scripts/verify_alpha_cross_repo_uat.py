#!/usr/bin/env python3
"""Verify that a generated quant UAT store crosses the public read boundary."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from alpha_leaderboard_adapter import (
    connect_read_only,
    fetch_rows,
    render_query,
    render_show,
    resolve_date,
    run_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with connect_read_only(Path(args.db)) as connection:
        snapshot_date = resolve_date(connection, None, allow_uat=True)
        rows = fetch_rows(connection, snapshot_date, allow_uat=True)
        show = render_show(
            connection, snapshot_date, min(3, len(rows)), allow_uat=True
        )
        query = render_query(
            connection,
            snapshot_date,
            str(rows[0]["ticker"]),
            allow_uat=True,
        )
        if "主因子" not in show or "主要正向因子" not in query:
            raise AssertionError("generated UAT attribution did not cross public adapter")
        try:
            run_metadata(connection, snapshot_date, allow_uat=False)
        except ValueError as error:
            if "not production activated" not in str(error):
                raise
        else:
            raise AssertionError("normal public mode accepted an isolated UAT snapshot")
    print(
        f"alpha cross-repo UAT ok: date={snapshot_date} rows={len(rows)} "
        "allow_uat=accepted normal=refused"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
