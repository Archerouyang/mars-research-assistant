#!/usr/bin/env python3
"""Render a deterministic, non-overwriting equity-snapshot Markdown artifact."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any


class EquitySnapshotError(ValueError):
    """Report an invalid or insufficient evidence fixture without inventing facts."""


PRIMARY_IDENTITY_KINDS = {"sec_filing", "regulatory_filing", "issuer_ir", "exchange"}
DATA_SOURCE_KINDS = PRIMARY_IDENTITY_KINDS | {"public_quote"}
UPDATE_SOURCE_KINDS = {"issuer_announcement", "credible_media"}


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EquitySnapshotError(f"{context} requires text")
    return value.strip()


def _date(value: object, context: str) -> date:
    text = _text(value, context)
    try:
        return date.fromisoformat(text[:10])
    except ValueError as error:
        raise EquitySnapshotError(f"{context} requires an ISO-8601 date") from error


def _source(source: object, context: str, allowed_kinds: set[str]) -> str:
    if not isinstance(source, dict):
        raise EquitySnapshotError(f"{context} requires a source")
    name = _text(source.get("name"), f"{context} source")
    kind = _text(source.get("kind"), f"{context} source")
    if kind not in allowed_kinds:
        raise EquitySnapshotError(f"{context} source kind is not allowed: {kind}")
    as_of = _text(source.get("as_of"), f"{context} source")
    url = _text(source.get("url"), f"{context} source")
    return f"[{name}]({url})（as_of：{as_of}）"


def _identity(identity: object) -> tuple[str, str]:
    if not isinstance(identity, dict):
        raise EquitySnapshotError("identity requires an object")
    if identity.get("status") != "verified":
        reason = _text(identity.get("reason"), "unverified identity")
        raise EquitySnapshotError(f"issuer identity is not uniquely verified: {reason}")
    issuer = _text(identity.get("issuer"), "identity")
    source = _source(identity.get("source"), "identity", PRIMARY_IDENTITY_KINDS)
    return issuer, source


def _key_data(items: object) -> list[str]:
    if not isinstance(items, list) or len(items) != 3:
        raise EquitySnapshotError("key public data requires exactly three items")
    required = {"price", "market_scale_or_valuation_anchor", "latest_financial_summary"}
    rendered = ["## 关键公开数据"]
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise EquitySnapshotError("key public data item must be an object")
        kind = _text(item.get("kind"), "key public data item")
        if kind not in required or kind in seen:
            raise EquitySnapshotError("key public data kinds must be unique and complete")
        seen.add(kind)
        label = _text(item.get("label"), "key public data label")
        value = _text(item.get("value"), f"{label} value")
        source = _source(item.get("source"), label, DATA_SOURCE_KINDS)
        rendered.append(f"- **{label}**：{value}（来源：{source}）")
    if seen != required:
        raise EquitySnapshotError("key public data kinds are incomplete")
    rendered.append("")
    return rendered


def _updates(items: object, research_as_of: date) -> list[str]:
    if not isinstance(items, list) or not 3 <= len(items) <= 5:
        raise EquitySnapshotError("recent company updates require three to five items")
    rendered = ["## 最近 30 天公司相关公告或新闻"]
    for item in items:
        if not isinstance(item, dict):
            raise EquitySnapshotError("recent company update must be an object")
        title = _text(item.get("title"), "recent company update")
        summary = _text(item.get("summary"), f"{title} summary")
        published = _date(item.get("published_on"), f"{title} published date")
        age = (research_as_of - published).days
        if age < 0 or age > 30:
            raise EquitySnapshotError(f"{title} is outside the 30-day news window")
        source = _source(item.get("source"), title, UPDATE_SOURCE_KINDS)
        rendered.append(
            f"- **{title}**（{published.isoformat()}）：{summary}（来源：{source}）"
        )
    rendered.append("")
    return rendered


def render_snapshot(fixture: dict[str, Any]) -> str:
    instrument = _text(fixture.get("instrument"), "fixture")
    research_as_of_text = _text(fixture.get("research_as_of"), "fixture")
    research_as_of = _date(research_as_of_text, "research as_of")
    issuer, issuer_source = _identity(fixture.get("identity"))
    gaps = fixture.get("data_gaps", [])
    if not isinstance(gaps, list):
        raise EquitySnapshotError("data gaps must be a list")
    lines = [
        f"# 个股快览：{instrument}",
        "",
        f"研究截至：{research_as_of_text}",
        "",
        "## 发行人身份",
        f"- 发行人：{issuer}（来源：{issuer_source}）",
        "",
        *_key_data(fixture.get("key_public_data")),
        *_updates(fixture.get("recent_company_updates"), research_as_of),
        "## 数据缺口",
    ]
    if gaps:
        lines.extend(f"- {_text(gap, 'data gap')}" for gap in gaps)
    else:
        lines.append("- 本次未记录额外数据缺口。")
    return "\n".join(lines).rstrip() + "\n"


def _write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise EquitySnapshotError("fixture must be a JSON object")
        _write_new(arguments.output, render_snapshot(fixture))
    except (OSError, json.JSONDecodeError, EquitySnapshotError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
