#!/usr/bin/env python3
"""Utilities for writing actual trade records into local daily files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from record_schemas import CSV_SCHEMAS


TRADE_FIELDS = CSV_SCHEMAS["trades.csv"]
TRADE_FIELD_SET = set(TRADE_FIELDS)
VALID_STAGES = {"post-order", "post-exit"}
UNKNOWNABLE_EXECUTION_FIELDS = ("quantity", "fees", "risk_amount")
POST_ORDER_REQUIRED_FIELDS = (
    "entry_date",
    "symbol",
    "underlying",
    "direction",
    "trade_type",
    "product",
    "instrument_type",
    "analysis_timeframe",
    "trigger_timeframe",
    "setup_tag",
    "signal_quality",
    "confidence",
    "entry_price",
    "stop_price",
    "target_price",
    "quantity",
    "cost",
    "fees",
    "risk_amount",
    "planned_R",
    "setup_review",
    "entry_review",
    "review_raw",
)
POST_EXIT_REQUIRED_FIELDS = (
    "exit_date",
    "pnl",
    "realized_R",
    "outcome",
    "mistake_tag",
    "exit_review",
    "lesson",
    "review_raw",
)


@dataclass(frozen=True)
class TradeRecordUpdate:
    stage: str
    trade_id: str
    fields: Mapping[str, str]
    review_text: str = ""
    allow_unknown_execution_fields: bool = False


def apply_trade_update(
    trades_path: Path,
    reviews_path: Path,
    update: TradeRecordUpdate,
) -> str:
    """Create or update one trade row and append the corresponding review."""

    stage = _normalize_stage(update.stage)
    fields = _normalized_fields(
        update.trade_id,
        stage,
        update.fields,
        update.allow_unknown_execution_fields,
    )
    rows = load_trade_rows(trades_path)
    row, created = _upsert_trade_row(rows, update.trade_id, stage, fields)
    write_trade_rows(trades_path, rows)
    append_review_section(reviews_path, stage, row, update.review_text)
    action = "created" if created else "updated"
    return f"{action} {update.trade_id} in {trades_path}"


def load_trade_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        if tuple(reader.fieldnames) != TRADE_FIELDS:
            raise ValueError(
                f"{path}: trades.csv header mismatch; expected {list(TRADE_FIELDS)!r}; actual {reader.fieldnames!r}"
            )
        return [_schema_row(row) for row in reader]


def write_trade_rows(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADE_FIELDS, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow(_schema_row(row))


def append_review_section(
    reviews_path: Path,
    stage: str,
    row: Mapping[str, str],
    review_text: str,
) -> None:
    reviews_path.parent.mkdir(parents=True, exist_ok=True)
    if not reviews_path.exists():
        reviews_path.write_text("# Daily Review\n\n## Trade Reviews\n", encoding="utf-8")

    section = render_review_section(stage, row, review_text)
    with reviews_path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n")
        handle.write(section)
        handle.write("\n")


def render_review_section(stage: str, row: Mapping[str, str], review_text: str) -> str:
    symbol = row.get("symbol") or row.get("underlying") or "N/A"
    lines = [
        f"### {row['trade_id']} - {symbol}",
        "",
        f"- 阶段：{stage.replace('-', '_')}",
        f"- 产品/方向：{row.get('product', '') or '-'} / {row.get('direction', '') or '-'}",
        f"- 分析时间框架：{row.get('analysis_timeframe', '') or '-'}",
        f"- 触发时间框架：{row.get('trigger_timeframe', '') or '-'}",
        f"- 盘面背景：{row.get('setup_review', '') or '-'}",
        f"- 入场理由：{row.get('entry_review', '') or '-'}",
        f"- 信号 K：{row.get('signal_quality', '') or '-'}",
        "- 辅助信号：-",
        f"- 入场信心：{row.get('confidence', '') or '-'}",
        f"- 风险计划：risk={row.get('risk_amount', '') or '-'}; planned_R={row.get('planned_R', '') or '-'}",
        f"- 出场与结果：{row.get('exit_review', '') or '-'}; outcome={row.get('outcome', '') or '-'}; realized_R={row.get('realized_R', '') or '-'}",
        "- 计划 vs 实际：-",
        f"- 错误标签：{row.get('mistake_tag', '') or '-'}",
        f"- 经验：{row.get('lesson', '') or '-'}",
        f"- 下次规则：{row.get('lesson', '') or '-'}",
    ]
    if review_text.strip():
        lines.extend(["", review_text.strip()])
    return "\n".join(lines)


def _upsert_trade_row(
    rows: list[dict[str, str]],
    trade_id: str,
    stage: str,
    fields: Mapping[str, str],
) -> tuple[dict[str, str], bool]:
    for row in rows:
        if row["trade_id"] == trade_id:
            fields = _merge_stage_fields(row, fields, stage)
            row.update(fields)
            return row, False

    if stage == "post-exit":
        raise ValueError(f"post-exit update requires an existing trade_id: {trade_id}")

    row = _schema_row({"trade_id": trade_id, **_merge_stage_fields({}, fields, stage)})
    rows.append(row)
    return row, True


def _normalized_fields(
    trade_id: str,
    stage: str,
    fields: Mapping[str, str],
    allow_unknown_execution_fields: bool,
) -> dict[str, str]:
    unknown = sorted(set(fields) - TRADE_FIELD_SET)
    if unknown:
        raise ValueError(f"unknown trades.csv fields for {trade_id}: {', '.join(unknown)}")

    normalized = {key: str(value) for key, value in fields.items() if value is not None}
    normalized["trade_id"] = trade_id
    if stage == "post-order":
        normalized.setdefault("status", "open")
        normalized.setdefault("outcome", "open")
        if allow_unknown_execution_fields:
            for field in UNKNOWNABLE_EXECUTION_FIELDS:
                if not normalized.get(field):
                    normalized[field] = "unknown"
        _require_fields(trade_id, stage, normalized, POST_ORDER_REQUIRED_FIELDS)
    elif stage == "post-exit":
        normalized.setdefault("status", "closed")
        _require_fields(trade_id, stage, normalized, POST_EXIT_REQUIRED_FIELDS)
    return normalized


def _normalize_stage(stage: str) -> str:
    normalized = stage.strip().lower().replace("_", "-")
    if normalized not in VALID_STAGES:
        raise ValueError(f"stage must be one of {sorted(VALID_STAGES)!r}; got {stage!r}")
    return normalized


def _schema_row(row: Mapping[str, str]) -> dict[str, str]:
    return {field: str(row.get(field) or "") for field in TRADE_FIELDS}


def _require_fields(
    trade_id: str,
    stage: str,
    fields: Mapping[str, str],
    required_fields: Sequence[str],
) -> None:
    missing = [field for field in required_fields if not str(fields.get(field) or "").strip()]
    if missing:
        raise ValueError(f"{stage} update for {trade_id} is missing required fields: {', '.join(missing)}")


def _merge_stage_fields(
    existing: Mapping[str, str],
    incoming: Mapping[str, str],
    stage: str,
) -> dict[str, str]:
    merged = dict(incoming)
    new_raw = incoming.get("review_raw", "")
    if new_raw:
        existing_raw = existing.get("review_raw", "")
        labeled_raw = f"[{stage}] {new_raw}"
        merged["review_raw"] = f"{existing_raw}\n{labeled_raw}".strip() if existing_raw else labeled_raw
    return merged
