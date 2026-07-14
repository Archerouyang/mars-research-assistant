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

import analysis_delta_adapter
from runtime_state import default_runtime_dir


DEFAULT_TOP = 10
REQUIRED_RUN_COLUMNS = {
    "as_of",
    "model_run_id",
    "input_fingerprint",
    "snapshot_hash",
    "model_role",
    "publication_status",
    "quality_status",
    "row_count",
    "published_at",
}
REQUIRED_ROW_COLUMNS = {
    "as_of",
    "model_run_id",
    "ticker",
    "alpha_rank",
    "payload_json",
}
REQUIRED_ROW_FIELDS = {
    "as_of",
    "ticker",
    "alpha_rank",
    "alpha_score",
    "probability_positive",
    "predictive_std",
    "rank_vs_sp500",
    "candidate_pool",
    "deep_research_priority",
    "factor_attribution",
}
REQUIRED_DECISION_FIELDS = {
    "decision_state",
    "primary_regime",
    "execution_context",
    "pa_ema",
    "levels",
    "zones",
    "events",
    "invalidation",
    "next_check",
    "sizing_language",
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

    card = subparsers.add_parser(
        "decision-card", help="Render a fixed card from champion and analysis stores"
    )
    card.add_argument("ticker")
    add_common_args(card)
    card.add_argument(
        "--analysis-db", default=str(analysis_delta_adapter.default_db_path())
    )
    card.add_argument("--primary-timeframe", default="1D")
    card.add_argument("--strategy-horizon", default="swing")
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
    row_columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(alpha_rows)").fetchall()
    }
    missing_row_columns = sorted(REQUIRED_ROW_COLUMNS - row_columns)
    if missing_row_columns:
        connection.close()
        raise ValueError(
            f"Alpha Leaderboard rows missing columns: {missing_row_columns}"
        )
    return connection


def resolve_date(connection: sqlite3.Connection, requested: str | None) -> str:
    if requested:
        rows = connection.execute(
            """
            SELECT as_of, model_role, publication_status FROM alpha_runs
            WHERE as_of = ?
            """,
            (requested,),
        ).fetchall()
        eligible = [
            row
            for row in rows
            if row["model_role"] == "champion"
            and row["publication_status"] == "published"
        ]
        if not rows:
            raise ValueError(f"Alpha Leaderboard snapshot not found: {requested}")
        if not eligible:
            raise ValueError(f"Alpha snapshot {requested} is not a published champion")
        if len(eligible) != 1:
            raise ValueError(f"Alpha snapshot {requested} has ambiguous published champions")
        row = eligible[0]
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
    rows = connection.execute(
        """
        SELECT model_run_id, input_fingerprint, snapshot_hash,
               model_role, publication_status, quality_status, row_count,
               published_at
        FROM alpha_runs
        WHERE as_of = ?
          AND model_role = 'champion'
          AND publication_status = 'published'
        """,
        (snapshot_date,),
    ).fetchall()
    if not rows:
        raise ValueError(f"Alpha Leaderboard snapshot not found: {snapshot_date}")
    if len(rows) != 1:
        raise ValueError(
            f"Alpha snapshot {snapshot_date} has ambiguous published champions"
        )
    row = rows[0]
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
    if metadata["quality_status"] not in {"valid", "stale"}:
        raise ValueError(f"Alpha snapshot {snapshot_date} has invalid quality status")
    if not str(metadata["published_at"]).strip():
        raise ValueError(f"Alpha snapshot {snapshot_date} has no publication time")
    return metadata


def fetch_rows(connection: sqlite3.Connection, snapshot_date: str) -> list[dict[str, Any]]:
    metadata = run_metadata(connection, snapshot_date)
    rows = connection.execute(
        """
        SELECT ticker, alpha_rank, payload_json
        FROM alpha_rows
        WHERE as_of = ? AND model_run_id = ?
        ORDER BY alpha_rank ASC, ticker ASC
        """,
        (snapshot_date, metadata["model_run_id"]),
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
    for field in ("candidate_pool", "deep_research_priority"):
        if not isinstance(payload[field], bool):
            raise ValueError(f"Alpha {field} must be Boolean for {ticker}")
    if not isinstance(payload["factor_attribution"], dict) or not payload[
        "factor_attribution"
    ]:
        raise ValueError(f"Alpha factor_attribution must be a non-empty object for {ticker}")
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
    metadata = run_metadata(connection, snapshot_date)
    lines = [
        "# 多因子 Alpha 榜",
        "",
        f"- 数据日期: `{snapshot_date}`",
        f"- Champion run: `{run_metadata(connection, snapshot_date)['model_run_id']}`",
        f"- Freshness: `{metadata['quality_status']}` (published `{metadata['published_at']}`)",
        "- 说明: 严格保留脚本生成的 Alpha Rank；仅用于研究优先级，不是买入名单。",
        "- 概率成熟度: `Experimental`；必须同时读取预测不确定性。",
        "",
        "| Alpha Rank | Ticker | Alpha Score | 历史分位 | P(20D超额>0) | 预测不确定性 | Rank vs S&P500 | 轨迹 | 连续Top10 | 近20日Top10 | 上次Top10 | Candidate | Deep research |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {rank} | `{ticker}` | {score:.4f} | {percentile} | {probability} | {uncertainty:.4f} | {rank_sp} | {trajectory} | {consecutive} | {recent} | {last_date} | {candidate} | {deep} |".format(
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
                candidate=yes_no(row.get("candidate_pool")),
                deep=yes_no(row.get("deep_research_priority")),
            )
        )
    return "\n".join(lines)


def render_query(
    connection: sqlite3.Connection, snapshot_date: str, ticker: str
) -> str:
    ticker = ticker.upper()
    metadata = run_metadata(connection, snapshot_date)
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
            f"- Freshness: `{metadata['quality_status']}` (published `{metadata['published_at']}`)",
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
    metadata = run_metadata(connection, snapshot_date)
    previous_metadata = (
        None if previous is None else run_metadata(connection, previous)
    )
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
            f"- 当前 Freshness: `{metadata['quality_status']}` (published `{metadata['published_at']}`)",
            "- 上次 Freshness: `{}`".format(
                "-"
                if previous_metadata is None
                else f"{previous_metadata['quality_status']} (published {previous_metadata['published_at']})"
            ),
            f"- 新进入 Top{top}: {ticker_list(entered)}",
            f"- 滑出 Top{top}: {ticker_list(dropped)}",
            f"- 继续留在 Top{top}: {ticker_list(continued)}",
            "- 变化字段不改变原始 Alpha Rank。",
            "- 研究优先级，不是买入名单。",
        ]
    )


def render_decision_card(
    connection: sqlite3.Connection,
    snapshot_date: str,
    ticker: str,
    analysis_db: Path,
    primary_timeframe: str,
    strategy_horizon: str,
) -> str:
    ticker = ticker.upper()
    metadata = run_metadata(connection, snapshot_date)
    alpha_row = next(
        (
            item
            for item in fetch_rows(connection, snapshot_date)
            if str(item["ticker"]).upper() == ticker
        ),
        None,
    )
    if alpha_row is None:
        raise ValueError(f"{ticker} not found in Alpha snapshot {snapshot_date}")
    key = analysis_delta_adapter.stable_key(
        ticker, "decision_card", primary_timeframe, strategy_horizon
    )
    with analysis_delta_adapter.connect_read_only(analysis_db) as analysis_connection:
        analysis = analysis_delta_adapter.fetch_latest(analysis_connection, key)
    if str(analysis["as_of"])[:10] != snapshot_date:
        raise ValueError(
            f"Decision Card analysis date does not match Alpha snapshot {snapshot_date}"
        )
    snapshot = analysis["snapshot"]
    missing = sorted(REQUIRED_DECISION_FIELDS - snapshot.keys())
    if missing:
        raise ValueError(f"Decision Card analysis missing fields: {missing}")
    empty = sorted(field for field in REQUIRED_DECISION_FIELDS if not snapshot[field])
    if empty:
        raise ValueError(f"Decision Card analysis has empty fields: {empty}")
    changed = [
        f"{field}={status}"
        for field, status in sorted(analysis["delta"].items())
        if status != "unchanged"
    ]
    delta = "; ".join(changed) or "unchanged"
    probability = percent(alpha_row["probability_positive"])
    uncertainty = float(alpha_row["predictive_std"])
    rows = (
        ("上次运行增量", f"{analysis['comparison_mode']}: {delta}"),
        ("决策状态", snapshot["decision_state"]),
        (
            "Alpha Rank / trajectory",
            f"{int(alpha_row['alpha_rank'])} / {alpha_row.get('trajectory_state') or '-'}; "
            f"run={metadata['model_run_id']}; as_of={snapshot_date}",
        ),
        (
            "P(20D超额>0) / predictive uncertainty",
            f"Experimental: {probability} / {uncertainty:.4f}",
        ),
        ("因子归因", alpha_row["factor_attribution"]),
        ("主分析时间框架", snapshot["primary_regime"]),
        ("执行观察时间框架", snapshot["execution_context"]),
        ("PA + EMA", snapshot["pa_ema"]),
        ("走势强弱参考点位", snapshot["levels"]),
        ("加仓区 / TP或再平衡区", snapshot["zones"]),
        ("当周事件与新闻", snapshot["events"]),
        (
            "失效与下一次检查",
            f"{render_cell(snapshot['invalidation'])}; {render_cell(snapshot['next_check'])}",
        ),
        ("比例式仓位语言", snapshot["sizing_language"]),
    )
    lines = [
        f"## {ticker} 决策卡",
        "",
        "| 模块 | 当前读数 |",
        "| --- | --- |",
    ]
    lines.extend(f"| {label} | {render_cell(value)} |" for label, value in rows)
    lines.extend(
        [
            "",
            "- 模型字段来自 published champion，不得由分析层改写。",
            "- 概率为 Experimental，必须与 predictive uncertainty 相邻解释。",
            "- 研究优先级，不是买入名单；不创建或批准订单。",
        ]
    )
    return "\n".join(lines)


def render_cell(value: Any) -> str:
    if isinstance(value, dict):
        text = "; ".join(f"{key}={value[key]}" for key in sorted(value))
    elif isinstance(value, list):
        text = "; ".join(str(item) for item in value)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


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


def yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def main() -> int:
    args = parse_args()
    try:
        with connect_read_only(Path(args.db)) as connection:
            snapshot_date = resolve_date(connection, args.date)
            if args.command == "show":
                output = render_show(connection, snapshot_date, args.top)
            elif args.command == "query":
                output = render_query(connection, snapshot_date, args.ticker)
            elif args.command == "decision-card":
                output = render_decision_card(
                    connection,
                    snapshot_date,
                    args.ticker,
                    Path(args.analysis_db),
                    args.primary_timeframe,
                    args.strategy_horizon,
                )
            else:
                output = render_changes(connection, snapshot_date, args.top)
    except (ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"alpha leaderboard error: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
