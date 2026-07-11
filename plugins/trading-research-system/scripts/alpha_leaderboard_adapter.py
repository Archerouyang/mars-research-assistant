#!/usr/bin/env python3
"""Read Alpha Lab leaderboard snapshots without mutating the private store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

from runtime_state import default_runtime_dir


DEFAULT_TOP = 10


def default_db_path() -> Path:
    return default_runtime_dir() / "alpha" / "leaderboard.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read immutable Alpha Leaderboard snapshots from Alpha Lab."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="Show the stored production leaderboard")
    add_common_args(show)
    show.add_argument("--top", type=int, default=DEFAULT_TOP)

    query = subparsers.add_parser("query", help="Query any ticker in the snapshot")
    query.add_argument("ticker")
    add_common_args(query)

    changes = subparsers.add_parser("changes", help="Compare stored leaderboard snapshots")
    add_common_args(changes)
    changes.add_argument("--top", type=int, default=DEFAULT_TOP)
    return parser.parse_args()


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default=str(default_db_path()))
    parser.add_argument("--date", default=None)


def connect_read_only(db_path: Path) -> sqlite3.Connection:
    path = db_path.expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Alpha Leaderboard store not found: {path}")
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    required_tables = {"alpha_runs", "alpha_rows"}
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing = sorted(required_tables - tables)
    if missing:
        connection.close()
        raise ValueError(f"Alpha Leaderboard schema missing tables: {missing}")
    return connection


def resolve_date(connection: sqlite3.Connection, requested: str | None) -> str:
    if requested:
        row = connection.execute(
            "SELECT as_of FROM alpha_runs WHERE as_of = ?", (requested,)
        ).fetchone()
    else:
        row = connection.execute("SELECT MAX(as_of) AS as_of FROM alpha_runs").fetchone()
    if row is None or row["as_of"] is None:
        label = requested or "latest"
        raise ValueError(f"Alpha Leaderboard snapshot not found: {label}")
    return str(row["as_of"])


def previous_date(connection: sqlite3.Connection, snapshot_date: str) -> str | None:
    row = connection.execute(
        """
        SELECT as_of FROM alpha_runs
        WHERE as_of < ?
        ORDER BY as_of DESC
        LIMIT 1
        """,
        (snapshot_date,),
    ).fetchone()
    return None if row is None else str(row["as_of"])


def model_run_id(connection: sqlite3.Connection, snapshot_date: str) -> str:
    row = connection.execute(
        "SELECT model_run_id FROM alpha_runs WHERE as_of = ?", (snapshot_date,)
    ).fetchone()
    return "unknown" if row is None else str(row["model_run_id"])


def fetch_rows(connection: sqlite3.Connection, snapshot_date: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT ticker, alpha_rank, payload_json
        FROM alpha_rows
        WHERE as_of = ?
        ORDER BY alpha_rank ASC, ticker ASC
        """,
        (snapshot_date,),
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict):
            raise ValueError(f"invalid Alpha payload for {row['ticker']}")
        if str(payload.get("ticker", "")).upper() != str(row["ticker"]).upper():
            raise ValueError(f"Alpha payload ticker mismatch for {row['ticker']}")
        if int(payload.get("alpha_rank", -1)) != int(row["alpha_rank"]):
            raise ValueError(f"Alpha payload rank mismatch for {row['ticker']}")
        result.append(payload)
    if not result:
        raise ValueError(f"Alpha Leaderboard has no rows for {snapshot_date}")
    return result


def render_show(
    connection: sqlite3.Connection, snapshot_date: str, top: int
) -> str:
    if top <= 0:
        raise ValueError("top must be positive")
    rows = fetch_rows(connection, snapshot_date)[:top]
    lines = [
        "# 多因子 Alpha 榜",
        "",
        f"- 数据日期: `{snapshot_date}`",
        f"- Champion run: `{model_run_id(connection, snapshot_date)}`",
        "- 说明: 严格保留脚本生成的 Alpha Rank；仅用于研究优先级，不是买入名单。",
        "- 概率成熟度: `Experimental`；必须同时读取预测不确定性。",
        "",
        "| Alpha Rank | Ticker | Alpha Score | 历史分位 | P(20D超额>0) | 预测不确定性 | Rank vs S&P500 | 轨迹 | 连续Top10 | 近20日Top10 | 上次Top10 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {rank} | `{ticker}` | {score:.4f} | {percentile} | {probability} | {uncertainty:.4f} | {rank_sp} | {trajectory} | {consecutive} | {recent} | {last_date} |".format(
                rank=int(row["alpha_rank"]),
                ticker=row["ticker"],
                score=float(row["alpha_score"]),
                percentile=percent(row.get("historical_percentile")),
                probability=percent(row.get("probability_positive")),
                uncertainty=float(row["predictive_std"]),
                rank_sp=int(row["rank_vs_sp500"]),
                trajectory=row.get("trajectory_state") or "-",
                consecutive=int(row.get("consecutive_top_display_days", 0)),
                recent=int(row.get("recent_top_display_count", 0)),
                last_date=short_date(row.get("last_top_display_date")),
            )
        )
    return "\n".join(lines)


def render_query(
    connection: sqlite3.Connection, snapshot_date: str, ticker: str
) -> str:
    ticker = ticker.upper()
    row = next(
        (item for item in fetch_rows(connection, snapshot_date) if item["ticker"].upper() == ticker),
        None,
    )
    if row is None:
        raise ValueError(f"{ticker} not found in Alpha snapshot {snapshot_date}")
    return "\n".join(
        [
            "# Alpha 标的查询",
            "",
            f"- 数据日期: `{snapshot_date}`",
            f"- Ticker: `{ticker}`",
            f"- Alpha Rank: `{int(row['alpha_rank'])}`",
            f"- Alpha Score: `{float(row['alpha_score']):.4f}`",
            f"- 历史分位: `{percent(row.get('historical_percentile'))}`",
            f"- P(20D超额>0): `{percent(row.get('probability_positive'))}` (`Experimental`)",
            f"- 预测不确定性: `{float(row['predictive_std']):.4f}`",
            f"- 轨迹: `{row.get('trajectory_state') or '-'}`",
            f"- candidate pool: `{'yes' if row.get('candidate_pool') else 'no'}`",
            f"- deep research priority: `{'yes' if row.get('deep_research_priority') else 'no'}`",
            "- 排名由 Alpha Lab champion 固定；agent 不重排。",
            "- 研究优先级，不是买入名单。",
        ]
    )


def render_changes(
    connection: sqlite3.Connection, snapshot_date: str, top: int
) -> str:
    if top <= 0:
        raise ValueError("top must be positive")
    previous = previous_date(connection, snapshot_date)
    current = [str(row["ticker"]) for row in fetch_rows(connection, snapshot_date)[:top]]
    prior = [] if previous is None else [
        str(row["ticker"]) for row in fetch_rows(connection, previous)[:top]
    ]
    current_set = set(current)
    prior_set = set(prior)
    entered = [ticker for ticker in current if ticker not in prior_set]
    dropped = [ticker for ticker in prior if ticker not in current_set]
    continued = [ticker for ticker in current if ticker in prior_set]
    return "\n".join(
        [
            "# Alpha 榜变化",
            "",
            f"- 当前日期: `{snapshot_date}`",
            f"- 上次日期: `{previous or '-'}`",
            f"- 新进入 Top{top}: {ticker_list(entered)}",
            f"- 滑出 Top{top}: {ticker_list(dropped)}",
            f"- 继续留在 Top{top}: {ticker_list(continued)}",
            "- 变化字段不改变原始 Alpha Rank。",
            "- 研究优先级，不是买入名单。",
        ]
    )


def percent(value: Any) -> str:
    if value is None:
        return "-"
    return f"{float(value) * 100:.1f}%"


def short_date(value: Any) -> str:
    if not value:
        return "-"
    return str(value)[:10]


def ticker_list(values: list[str]) -> str:
    return "-" if not values else ", ".join(f"`{value}`" for value in values)


def main() -> int:
    args = parse_args()
    try:
        with connect_read_only(Path(args.db)) as connection:
            snapshot_date = resolve_date(connection, args.date)
            if args.command == "show":
                output = render_show(connection, snapshot_date, args.top)
            elif args.command == "query":
                output = render_query(connection, snapshot_date, args.ticker)
            else:
                output = render_changes(connection, snapshot_date, args.top)
    except (ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"alpha leaderboard error: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
