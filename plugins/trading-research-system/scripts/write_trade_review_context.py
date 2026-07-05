#!/usr/bin/env python3
"""Append a two-stage trade review context section without writing trades.csv."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys


STAGE_CHOICES = ("post-order", "post-exit", "post_order", "post_exit")

POST_ORDER_FIELDS = (
    ("产品/方向", ("product", "direction")),
    ("Broker facts", ("broker", "account_id", "execution_id", "order_id")),
    ("Plan link", ("setup_id", "parent_trade_id", "theme_id")),
    ("分析时间框架", ("analysis_timeframe",)),
    ("触发时间框架", ("trigger_timeframe",)),
    ("盘面背景", ("market_background", "setup_review")),
    ("入场理由", ("entry_reason", "entry_review")),
    ("信号 K", ("signal_bar", "signal_quality")),
    ("辅助信号", ("auxiliary_evidence",)),
    ("入场信心", ("confidence",)),
    ("风险计划", ("risk_plan", "stop_price", "target_price", "planned_R")),
    ("计划 vs 实际", ("plan_vs_actual",)),
    ("错误标签", ("mistake_tag",)),
    ("经验", ("lesson",)),
    ("下次规则", ("next_rule",)),
)

POST_EXIT_FIELDS = (
    ("产品/方向", ("product", "direction")),
    ("Broker facts", ("broker", "account_id", "execution_id", "order_id")),
    ("Plan link", ("setup_id", "parent_trade_id", "theme_id")),
    ("分析时间框架", ("analysis_timeframe",)),
    ("触发时间框架", ("trigger_timeframe",)),
    ("出场与结果", ("exit_reason", "exit_result", "pnl", "realized_R", "outcome")),
    ("计划 vs 实际", ("plan_vs_actual",)),
    ("执行质量", ("execution_quality",)),
    ("错误标签", ("mistake_tag",)),
    ("经验", ("lesson",)),
    ("下次规则", ("next_rule",)),
)


def default_runtime_dir() -> Path:
    configured = os.environ.get("TRADING_RESEARCH_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Documents" / "dailytrades-runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a post-order or post-exit review context section to reviews.md."
    )
    parser.add_argument("--stage", required=True, choices=STAGE_CHOICES)
    parser.add_argument("--trade-id", required=True)
    parser.add_argument("--fields-json", required=True, help="JSON object containing review-context fields")
    parser.add_argument("--review-file", default=None, help="Markdown/text review note to preserve")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trading date, YYYY-MM-DD")
    parser.add_argument(
        "--runtime-dir",
        default=str(default_runtime_dir()),
        help="Private runtime directory; defaults to TRADING_RESEARCH_RUNTIME_DIR or ~/Documents/dailytrades-runtime",
    )
    parser.add_argument("--root", default=None, help="Daily data root override. Defaults to <runtime-dir>/daily")
    parser.add_argument("--daily-dir", default=None, help="Daily directory override. Defaults to <root>/<date>")
    parser.add_argument("--reviews-md", default=None, help="reviews.md override")
    return parser.parse_args()


def normalize_stage(stage: str) -> str:
    return stage.replace("_", "-")


def load_fields(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"fields JSON must contain an object: {path}")
    return {str(key): "" if value is None else str(value) for key, value in raw.items()}


def load_review_text(path: str | None) -> str:
    if not path:
        return ""
    review_path = Path(path).expanduser()
    if not review_path.is_file():
        raise ValueError(f"review file does not exist: {review_path}")
    return review_path.read_text(encoding="utf-8").strip()


def resolve_daily_dir(args: argparse.Namespace) -> Path:
    if args.daily_dir:
        return Path(args.daily_dir).expanduser()
    root = Path(args.root).expanduser() if args.root else Path(args.runtime_dir).expanduser() / "daily"
    return root / args.date


def compact_values(fields: dict[str, str], keys: tuple[str, ...]) -> str:
    values = [fields[key].strip() for key in keys if fields.get(key, "").strip()]
    return " / ".join(values) if values else "unknown"


def render_section(stage: str, trade_id: str, fields: dict[str, str], review_text: str) -> str:
    symbol = fields.get("symbol") or fields.get("underlying") or "unknown"
    field_groups = POST_ORDER_FIELDS if stage == "post-order" else POST_EXIT_FIELDS

    lines = [
        f"### {trade_id} - {symbol}",
        "",
        f"- 阶段：{stage.replace('-', '_')}",
    ]
    for label, keys in field_groups:
        lines.append(f"- {label}：{compact_values(fields, keys)}")

    if review_text:
        lines.extend(["", "#### 原始复盘文字", "", review_text])

    return "\n".join(lines).rstrip() + "\n"


def append_review(path: Path, section: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Daily Review\n"
    separator = "\n" if existing.endswith("\n") else "\n\n"
    path.write_text(existing + separator + section, encoding="utf-8")


def main() -> int:
    args = parse_args()
    stage = normalize_stage(args.stage)
    daily_dir = resolve_daily_dir(args)
    reviews_path = Path(args.reviews_md).expanduser() if args.reviews_md else daily_dir / "reviews.md"

    try:
        fields = load_fields(Path(args.fields_json).expanduser())
        review_text = load_review_text(args.review_file)
        section = render_section(stage, args.trade_id, fields, review_text)
        append_review(reviews_path, section)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"write trade review context failed: {error}", file=sys.stderr)
        return 1

    print(f"review context appended to {reviews_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
