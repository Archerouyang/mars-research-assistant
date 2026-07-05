#!/usr/bin/env python3
"""Import and read KVN momentum leaderboard snapshots."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import sys


TOP10_DEFAULT = 10
RECENT_WINDOW = 20

REQUIRED_FIELDS = {
    "snapshot_date": ("snapshot_date", "date", "日期"),
    "rank_vs_sp500": ("rank_vs_sp500", "Rank vs S&P500", "rank", "rank_vs_s&p500"),
    "ticker": ("ticker", "Ticker", "symbol", "标的"),
    "kvn_score": ("kvn_score", "KVN 分数", "KVN score"),
    "kvn_p": ("kvn_p", "KVN P", "kvn_percentile"),
    "is_sp500": ("is_sp500", "当前是否 S&P500", "当前是否S&P500"),
}


@dataclass(frozen=True)
class KvnRow:
    snapshot_date: str
    rank_vs_sp500: int
    ticker: str
    kvn_score: float
    kvn_p: float
    is_sp500: bool
    source: str


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


def default_db_path() -> Path:
    return default_runtime_dir() / "momentum" / "kvn.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import and read externally generated KVN leaderboard snapshots."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a KVN snapshot CSV")
    import_parser.add_argument("csv_path", help="CSV snapshot path")
    add_db_arg(import_parser)
    import_parser.add_argument("--source", default="manual", help="Snapshot source label")

    show_parser = subparsers.add_parser("show", help="Show TopN leaderboard rows")
    add_db_arg(show_parser)
    show_parser.add_argument("--date", default=None, help="Snapshot date; defaults to latest")
    show_parser.add_argument("--top", type=int, default=TOP10_DEFAULT, help="Rows to show")

    query_parser = subparsers.add_parser("query", help="Look up one ticker in a snapshot")
    query_parser.add_argument("ticker", help="Ticker to look up")
    add_db_arg(query_parser)
    query_parser.add_argument("--date", default=None, help="Snapshot date; defaults to latest")

    changes_parser = subparsers.add_parser("changes", help="Compare TopN with previous snapshot")
    add_db_arg(changes_parser)
    changes_parser.add_argument("--date", default=None, help="Snapshot date; defaults to latest")
    changes_parser.add_argument("--top", type=int, default=TOP10_DEFAULT, help="TopN window")

    return parser.parse_args()


def add_db_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--db",
        default=str(default_db_path()),
        help="KVN SQLite path; defaults to TRADING_RESEARCH_RUNTIME_DIR/momentum/kvn.sqlite",
    )


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS kvn_snapshots (
            snapshot_date TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kvn_rankings (
            snapshot_date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            rank_vs_sp500 INTEGER NOT NULL,
            kvn_score REAL NOT NULL,
            kvn_p REAL NOT NULL,
            is_sp500 INTEGER NOT NULL,
            source TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            PRIMARY KEY (snapshot_date, ticker)
        );

        CREATE INDEX IF NOT EXISTS idx_kvn_rankings_snapshot_score
            ON kvn_rankings(snapshot_date, kvn_score DESC, ticker ASC);
        """
    )


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    return connection


def import_snapshot(connection: sqlite3.Connection, csv_path: Path, source: str) -> tuple[str, int]:
    rows = parse_snapshot_csv(csv_path, source)
    if not rows:
        raise ValueError(f"no KVN rows found in {csv_path}")

    snapshot_dates = {row.snapshot_date for row in rows}
    if len(snapshot_dates) != 1:
        raise ValueError(f"snapshot CSV must contain exactly one snapshot_date, got {sorted(snapshot_dates)!r}")

    snapshot_date = rows[0].snapshot_date
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with connection:
        connection.execute("DELETE FROM kvn_rankings WHERE snapshot_date = ?", (snapshot_date,))
        connection.execute(
            """
            INSERT INTO kvn_snapshots(snapshot_date, source, imported_at)
            VALUES(?, ?, ?)
            ON CONFLICT(snapshot_date) DO UPDATE SET
                source=excluded.source,
                imported_at=excluded.imported_at
            """,
            (snapshot_date, source, imported_at),
        )
        connection.executemany(
            """
            INSERT INTO kvn_rankings(
                snapshot_date,
                ticker,
                rank_vs_sp500,
                kvn_score,
                kvn_p,
                is_sp500,
                source,
                imported_at
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.snapshot_date,
                    row.ticker,
                    row.rank_vs_sp500,
                    row.kvn_score,
                    row.kvn_p,
                    int(row.is_sp500),
                    row.source,
                    imported_at,
                )
                for row in rows
            ],
        )

    return snapshot_date, len(rows)


def parse_snapshot_csv(csv_path: Path, source: str) -> list[KvnRow]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV header in {csv_path}")

        header_map = build_header_map(reader.fieldnames)
        missing = sorted(set(REQUIRED_FIELDS) - set(header_map))
        if missing:
            raise ValueError(f"missing KVN CSV fields {missing!r} in {csv_path}")

        rows: list[KvnRow] = []
        for row_number, raw in enumerate(reader, start=2):
            rows.append(
                KvnRow(
                    snapshot_date=clean(raw[header_map["snapshot_date"]]),
                    rank_vs_sp500=parse_int(raw[header_map["rank_vs_sp500"]], row_number, "rank_vs_sp500"),
                    ticker=clean(raw[header_map["ticker"]]).upper(),
                    kvn_score=parse_float(raw[header_map["kvn_score"]], row_number, "kvn_score"),
                    kvn_p=parse_float(raw[header_map["kvn_p"]], row_number, "kvn_p"),
                    is_sp500=parse_bool(raw[header_map["is_sp500"]]),
                    source=source,
                )
            )
        return rows


def build_header_map(fieldnames: list[str]) -> dict[str, str]:
    normalized = {normalize_header(field): field for field in fieldnames}
    header_map: dict[str, str] = {}
    for canonical, aliases in REQUIRED_FIELDS.items():
        for alias in aliases:
            actual = normalized.get(normalize_header(alias))
            if actual is not None:
                header_map[canonical] = actual
                break
    return header_map


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def clean(value: str | None) -> str:
    return (value or "").strip()


def parse_int(value: str | None, row_number: int, field: str) -> int:
    try:
        return int(float(clean(value)))
    except ValueError as error:
        raise ValueError(f"row {row_number}: invalid {field}: {value!r}") from error


def parse_float(value: str | None, row_number: int, field: str) -> float:
    try:
        return float(clean(value))
    except ValueError as error:
        raise ValueError(f"row {row_number}: invalid {field}: {value!r}") from error


def parse_bool(value: str | None) -> bool:
    normalized = clean(value).lower()
    return normalized in {"1", "true", "yes", "y", "是"}


def latest_snapshot_date(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT MAX(snapshot_date) AS snapshot_date FROM kvn_snapshots").fetchone()
    if row is None or row["snapshot_date"] is None:
        raise ValueError("no KVN snapshots imported")
    return str(row["snapshot_date"])


def resolve_snapshot_date(connection: sqlite3.Connection, requested: str | None) -> str:
    snapshot_date = requested or latest_snapshot_date(connection)
    row = connection.execute(
        "SELECT snapshot_date FROM kvn_snapshots WHERE snapshot_date = ?",
        (snapshot_date,),
    ).fetchone()
    if row is None:
        raise ValueError(f"KVN snapshot not found for {snapshot_date}")
    return snapshot_date


def snapshot_source(connection: sqlite3.Connection, snapshot_date: str) -> str:
    row = connection.execute(
        "SELECT source FROM kvn_snapshots WHERE snapshot_date = ?",
        (snapshot_date,),
    ).fetchone()
    return str(row["source"]) if row else "unknown"


def fetch_rows(connection: sqlite3.Connection, snapshot_date: str) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            """
            SELECT snapshot_date, ticker, rank_vs_sp500, kvn_score, kvn_p, is_sp500, source
            FROM kvn_rankings
            WHERE snapshot_date = ?
            ORDER BY kvn_score DESC, ticker ASC
            """,
            (snapshot_date,),
        )
    )


def top_rows(connection: sqlite3.Connection, snapshot_date: str, top: int) -> list[sqlite3.Row]:
    return fetch_rows(connection, snapshot_date)[:top]


def top_tickers(connection: sqlite3.Connection, snapshot_date: str, top: int) -> list[str]:
    return [str(row["ticker"]) for row in top_rows(connection, snapshot_date, top)]


def snapshot_dates_through(connection: sqlite3.Connection, snapshot_date: str, limit: int | None = None) -> list[str]:
    query = """
        SELECT snapshot_date
        FROM kvn_snapshots
        WHERE snapshot_date <= ?
        ORDER BY snapshot_date DESC
    """
    if limit is not None:
        query += " LIMIT ?"
        rows = connection.execute(query, (snapshot_date, limit)).fetchall()
    else:
        rows = connection.execute(query, (snapshot_date,)).fetchall()
    return [str(row["snapshot_date"]) for row in rows]


def previous_snapshot_date(connection: sqlite3.Connection, snapshot_date: str) -> str | None:
    row = connection.execute(
        """
        SELECT snapshot_date
        FROM kvn_snapshots
        WHERE snapshot_date < ?
        ORDER BY snapshot_date DESC
        LIMIT 1
        """,
        (snapshot_date,),
    ).fetchone()
    return str(row["snapshot_date"]) if row else None


def top10_memory(connection: sqlite3.Connection, snapshot_date: str, ticker: str) -> tuple[int, int, str]:
    dates = snapshot_dates_through(connection, snapshot_date, RECENT_WINDOW)
    ticker = ticker.upper()

    recent_count = 0
    consecutive = 0
    last_top10_date = "-"
    still_consecutive = True

    for index, date_value in enumerate(dates):
        is_top10 = ticker in set(top_tickers(connection, date_value, TOP10_DEFAULT))
        if is_top10:
            recent_count += 1
            if index > 0 and last_top10_date == "-":
                last_top10_date = date_value
        if still_consecutive and is_top10:
            consecutive += 1
        else:
            still_consecutive = False

    return consecutive, recent_count, last_top10_date


def render_show(connection: sqlite3.Connection, snapshot_date: str, top: int) -> str:
    rows = top_rows(connection, snapshot_date, top)
    lines = [
        "# KVN Momentum Leaderboard",
        "",
        f"- Snapshot date: `{snapshot_date}`",
        f"- Source: `{snapshot_source(connection, snapshot_date)}`",
        "- Note: research priority only, not a buy list.",
        "",
        "| Rank vs S&P500 | Ticker | KVN 分数 | KVN P | 当前是否 S&P500 | 连续入选Top10天数 | 近20日入选Top10次数 | 上次入选Top10时间 |",
        "| ---: | --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        consecutive, recent_count, last_top10 = top10_memory(connection, snapshot_date, str(row["ticker"]))
        lines.append(
            "| {rank} | {ticker} | {score:.4f} | {kvn_p:.4f} | {is_sp500} | {consecutive} | {recent_count} | {last_top10} |".format(
                rank=int(row["rank_vs_sp500"]),
                ticker=row["ticker"],
                score=float(row["kvn_score"]),
                kvn_p=float(row["kvn_p"]),
                is_sp500="是" if row["is_sp500"] else "否",
                consecutive=consecutive,
                recent_count=recent_count,
                last_top10=last_top10,
            )
        )
    return "\n".join(lines)


def render_query(connection: sqlite3.Connection, snapshot_date: str, ticker: str) -> str:
    ticker = ticker.upper()
    row = connection.execute(
        """
        SELECT snapshot_date, ticker, rank_vs_sp500, kvn_score, kvn_p, is_sp500
        FROM kvn_rankings
        WHERE snapshot_date = ? AND ticker = ?
        """,
        (snapshot_date, ticker),
    ).fetchone()
    if row is None:
        raise ValueError(f"{ticker} not found in KVN snapshot {snapshot_date}")

    current_top10 = ticker in set(top_tickers(connection, snapshot_date, TOP10_DEFAULT))
    consecutive, recent_count, last_top10 = top10_memory(connection, snapshot_date, ticker)
    lines = [
        "# KVN Ticker Lookup",
        "",
        f"- Snapshot date: `{snapshot_date}`",
        f"- Ticker: `{ticker}`",
        f"- Rank vs S&P500: `{int(row['rank_vs_sp500'])}`",
        f"- KVN 分数: `{float(row['kvn_score']):.4f}`",
        f"- KVN P: `{float(row['kvn_p']):.4f}`",
        f"- 当前是否 S&P500: `{'是' if row['is_sp500'] else '否'}`",
        f"- current top10: {'yes' if current_top10 else 'no'}",
        f"- 连续入选Top10天数: `{consecutive}`",
        f"- 近20日入选Top10次数: `{recent_count}`",
        f"- 上次入选Top10时间: `{last_top10}`",
        "- Research priority only, not a buy list.",
    ]
    return "\n".join(lines)


def render_changes(connection: sqlite3.Connection, snapshot_date: str, top: int) -> str:
    previous = previous_snapshot_date(connection, snapshot_date)
    current = top_tickers(connection, snapshot_date, top)

    if previous is None:
        previous_tickers: list[str] = []
    else:
        previous_tickers = top_tickers(connection, previous, top)

    previous_set = set(previous_tickers)
    current_set = set(current)
    new = [ticker for ticker in current if ticker not in previous_set]
    dropped = [ticker for ticker in previous_tickers if ticker not in current_set]
    continued = [ticker for ticker in current if ticker in previous_set]

    lines = [
        "# KVN Top10 Changes",
        "",
        f"- Snapshot date: `{snapshot_date}`",
        f"- Previous snapshot date: `{previous or '-'}`",
        f"- New Top10: {format_tickers(new)}",
        f"- Dropped from Top10: {format_tickers(dropped)}",
        f"- Continued Top10: {format_tickers(continued)}",
        "- Research priority only, not a buy list.",
    ]
    return "\n".join(lines)


def format_tickers(tickers: list[str]) -> str:
    if not tickers:
        return "-"
    return ", ".join(f"`{ticker}`" for ticker in tickers)


def main() -> int:
    args = parse_args()
    try:
        with connect(Path(args.db)) as connection:
            if args.command == "import":
                snapshot_date, count = import_snapshot(connection, Path(args.csv_path), args.source)
                print(f"imported {count} KVN rows for {snapshot_date} into {Path(args.db).expanduser()}")
                return 0

            snapshot_date = resolve_snapshot_date(connection, args.date)
            if args.command == "show":
                print(render_show(connection, snapshot_date, args.top))
            elif args.command == "query":
                print(render_query(connection, snapshot_date, args.ticker))
            elif args.command == "changes":
                print(render_changes(connection, snapshot_date, args.top))
            else:
                raise ValueError(f"unknown command {args.command!r}")
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"kvn_leaderboard error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
