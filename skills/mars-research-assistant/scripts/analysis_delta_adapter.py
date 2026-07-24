#!/usr/bin/env python3
"""Read the latest full analysis snapshot and stored delta by stable key."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

from runtime_state import default_runtime_dir


def default_db_path() -> Path:
    return default_runtime_dir() / "knowledge" / "analysis.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read prior analysis state without relying on chat history."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    latest = subparsers.add_parser("latest")
    latest.add_argument("--db", default=str(default_db_path()))
    latest.add_argument("--symbol", required=True)
    latest.add_argument("--analysis-type", default="decision_card")
    latest.add_argument("--primary-timeframe", default="1D")
    latest.add_argument("--strategy-horizon", default="swing")
    latest.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser.parse_args()


def connect_read_only(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"analysis store not found: {resolved}")
    connection = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'analysis_runs'"
    ).fetchone()
    if exists is None:
        connection.close()
        raise ValueError("analysis store missing analysis_runs table")
    columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(analysis_runs)").fetchall()
    }
    if "status" not in columns:
        connection.close()
        raise ValueError("analysis store missing success status metadata")
    return connection


def stable_key(
    symbol: str, analysis_type: str, primary_timeframe: str, strategy_horizon: str
) -> str:
    return "|".join(
        (symbol.upper(), analysis_type, primary_timeframe, strategy_horizon)
    )


def fetch_latest(connection: sqlite3.Connection, key: str) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT run_id, stable_key, symbol_or_scope, analysis_type,
               primary_timeframe, strategy_horizon, as_of, model_version,
               rule_version, input_fingerprint, payload_json, delta_json,
               comparison_mode
        FROM analysis_runs
        WHERE stable_key = ? AND status = 'success'
        ORDER BY as_of DESC, sequence_id DESC
        LIMIT 1
        """,
        (key,),
    ).fetchone()
    if row is None:
        raise ValueError(f"no prior analysis found for {key}")
    snapshot = json.loads(row["payload_json"])
    delta = json.loads(row["delta_json"])
    if not isinstance(snapshot, dict) or not isinstance(delta, dict):
        raise ValueError(f"invalid analysis payload for {key}")
    comparison_mode = str(row["comparison_mode"])
    if comparison_mode not in {"baseline", "incremental", "full_recompute"}:
        raise ValueError(f"invalid analysis comparison mode for {key}")
    predecessor = connection.execute(
        """
        SELECT model_version, rule_version
        FROM analysis_runs
        WHERE stable_key = ? AND status = 'success' AND run_id != ?
          AND (as_of < ? OR (as_of = ? AND sequence_id < (
              SELECT sequence_id FROM analysis_runs WHERE run_id = ?
          )))
        ORDER BY as_of DESC, sequence_id DESC
        LIMIT 1
        """,
        (key, row["run_id"], row["as_of"], row["as_of"], row["run_id"]),
    ).fetchone()
    if predecessor is not None and (
        predecessor["model_version"] != row["model_version"]
        or predecessor["rule_version"] != row["rule_version"]
    ):
        comparison_mode = "full_recompute"
        delta = {field: "updated" for field in sorted(snapshot)}
    return {
        "run_id": row["run_id"],
        "stable_key": row["stable_key"],
        "symbol_or_scope": row["symbol_or_scope"],
        "analysis_type": row["analysis_type"],
        "primary_timeframe": row["primary_timeframe"],
        "strategy_horizon": row["strategy_horizon"],
        "as_of": row["as_of"],
        "model_version": row["model_version"],
        "rule_version": row["rule_version"],
        "input_fingerprint": row["input_fingerprint"],
        "comparison_mode": comparison_mode,
        "snapshot": snapshot,
        "delta": delta,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 上次分析对照",
        "",
        f"- Stable key: `{payload['stable_key']}`",
        f"- As of: `{payload['as_of']}`",
        f"- Comparison mode: `{payload['comparison_mode']}`",
        f"- Model / rule: `{payload['model_version']}` / `{payload['rule_version']}`",
        "",
        "| 字段 | 变化 | 最新值 |",
        "| --- | --- | --- |",
    ]
    snapshot = payload["snapshot"]
    delta = payload["delta"]
    for field in sorted(delta):
        value = snapshot.get(field, "-")
        lines.append(
            f"| {field} | {delta[field]} | `{json.dumps(value, ensure_ascii=False, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "- 默认只向用户解释 updated / added / invalidated；unchanged 用于确认继承。",
            "- 模型或规则版本变化时，按 full_recompute 重新生成完整 Decision Card。",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    key = stable_key(
        args.symbol,
        args.analysis_type,
        args.primary_timeframe,
        args.strategy_horizon,
    )
    try:
        with connect_read_only(Path(args.db)) as connection:
            payload = fetch_latest(connection, key)
    except (ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(f"analysis delta error: {error}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
