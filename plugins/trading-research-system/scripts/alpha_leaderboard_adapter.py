#!/usr/bin/env python3
"""Read Alpha Lab leaderboard snapshots without mutating the private store."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any

from runtime_state import default_runtime_dir


DEFAULT_TOP = 10
REQUIRED_RUN_COLUMNS = {
    "as_of",
    "model_run_id",
    "input_fingerprint",
    "snapshot_hash",
    "model_role",
    "publication_status",
    "row_count",
}
REQUIRED_ROW_FIELDS = {
    "as_of",
    "ticker",
    "alpha_rank",
    "alpha_score",
    "probability_positive",
    "predictive_std",
    "rank_vs_sp500",
}
TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]{0,14}$")


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
    run_columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(alpha_runs)").fetchall()
    }
    missing_columns = sorted(REQUIRED_RUN_COLUMNS - run_columns)
    if missing_columns:
        connection.close()
        raise ValueError(
            f"Alpha Leaderboard run metadata missing columns: {missing_columns}"
        )
    return connection


def resolve_date(connection: sqlite3.Connection, requested: str | None) -> str:
    if requested:
        row = connection.execute(
            "SELECT as_of FROM alpha_runs WHERE as_of = ?", (requested,)
        ).fetchone()
    else:
        row = connection.execute(
            """
            SELECT MAX(as_of) AS as_of FROM alpha_runs
            WHERE model_role = 'champion' AND publication_status = 'published'
            """
        ).fetchone()
    if row is None or row["as_of"] is None:
        label = requested or "latest"
        raise ValueError(f"Alpha Leaderboard snapshot not found: {label}")
    return str(row["as_of"])


def previous_date(connection: sqlite3.Connection, snapshot_date: str) -> str | None:
    row = connection.execute(
        """
        SELECT as_of FROM alpha_runs
        WHERE as_of < ?
          AND model_role = 'champion'
          AND publication_status = 'published'
        ORDER BY as_of DESC
        LIMIT 1
        """,
        (snapshot_date,),
    ).fetchone()
    return None if row is None else str(row["as_of"])


def run_metadata(
    connection: sqlite3.Connection, snapshot_date: str
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT model_run_id, input_fingerprint, snapshot_hash,
               model_role, publication_status, row_count
        FROM alpha_runs WHERE as_of = ?
        """,
        (snapshot_date,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Alpha Leaderboard snapshot not found: {snapshot_date}")
    metadata = dict(row)
    if (
        metadata["model_role"] != "champion"
        or metadata["publication_status"] != "published"
    ):
        raise ValueError(f"Alpha snapshot {snapshot_date} is not a published champion")
    if not str(metadata["model_run_id"]).strip() or not str(
        metadata["input_fingerprint"]
    ).strip():
        raise ValueError(f"Alpha snapshot {snapshot_date} has incomplete run identity")
    snapshot_hash = str(metadata["snapshot_hash"])
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        raise ValueError(f"Alpha snapshot {snapshot_date} has invalid snapshot hash")
    if int(metadata["row_count"]) <= 0:
        raise ValueError(f"Alpha snapshot {snapshot_date} has invalid row count")
    return metadata


def fetch_rows(connection: sqlite3.Connection, snapshot_date: str) -> list[dict[str, Any]]:
    metadata = run_metadata(connection, snapshot_date)
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
        validate_payload(payload, snapshot_date)
        result.append(payload)
    if not result:
        raise ValueError(f"Alpha Leaderboard has no rows for {snapshot_date}")
    if len(result) != int(metadata["row_count"]):
        raise ValueError(f"Alpha snapshot {snapshot_date} row count mismatch")
    ranks = [int(payload["alpha_rank"]) for payload in result]
    if ranks != list(range(1, len(result) + 1)):
        raise ValueError(f"Alpha snapshot {snapshot_date} ranks are not contiguous")
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
    actual_hash = hashlib.sha256(canonical.encode()).hexdigest()
    if actual_hash != metadata["snapshot_hash"]:
        raise ValueError(f"Alpha snapshot {snapshot_date} snapshot hash mismatch")
    return result


def validate_payload(payload: dict[str, Any], snapshot_date: str) -> None:
    missing = sorted(REQUIRED_ROW_FIELDS - payload.keys())
    if missing:
        raise ValueError(f"Alpha payload missing fields: {missing}")
    ticker = str(payload["ticker"]).upper()
    if not TICKER_PATTERN.fullmatch(ticker):
        raise ValueError(f"invalid Alpha ticker: {ticker}")
    if str(payload["as_of"])[:10] != snapshot_date:
        raise ValueError(f"Alpha payload as_of mismatch for {ticker}")
    rank = int(payload["alpha_rank"])
    rank_vs_sp500 = int(payload["rank_vs_sp500"])
    if rank <= 0 or rank_vs_sp500 <= 0:
        raise ValueError(f"invalid Alpha rank for {ticker}")
    score = finite_float(payload["alpha_score"], "alpha_score", ticker)
    probability = finite_float(
        payload["probability_positive"], "probability_positive", ticker
    )
    uncertainty = finite_float(payload["predictive_std"], "predictive_std", ticker)
    if not math.isfinite(score) or not 0.0 <= probability <= 1.0 or uncertainty < 0.0:
        raise ValueError(f"invalid Alpha numeric range for {ticker}")
    percentile = payload.get("historical_percentile")
    if percentile is not None:
        percentile_value = finite_float(
            percentile, "historical_percentile", ticker
        )
        if not 0.0 <= percentile_value <= 1.0:
            raise ValueError(f"invalid Alpha historical percentile for {ticker}")


def finite_float(value: Any, field: str, ticker: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid Alpha {field} for {ticker}") from error
    if not math.isfinite(number):
        raise ValueError(f"invalid Alpha {field} for {ticker}")
    return number


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
        f"- Champion run: `{run_metadata(connection, snapshot_date)['model_run_id']}`",
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
