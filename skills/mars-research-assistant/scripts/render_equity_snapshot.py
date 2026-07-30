#!/usr/bin/env python3
"""Render a deterministic, non-overwriting equity-snapshot Markdown artifact."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


class EquitySnapshotError(ValueError):
    """Report an invalid or insufficient evidence fixture without inventing facts."""


PRIMARY_IDENTITY_KINDS = {"sec_filing", "regulatory_filing", "issuer_ir", "exchange"}
KEY_DATA_SOURCE_KINDS = {
    "price": {"public_quote"},
    "market_scale_or_valuation_anchor": {"public_quote"},
    "latest_financial_summary": PRIMARY_IDENTITY_KINDS,
}
UPDATE_SOURCE_KINDS = {"issuer_announcement", "credible_media"}
TRADE_DIRECTIVE = re.compile(
    r"建议(?:买入|卖出|增持|减持|加仓|减仓|建仓|平仓)|"
    r"(?:买入|卖出|增持|减持)该(?:股|股票)|加仓|减仓|建仓|平仓|下单|持仓比例|"
    r"\bbuy\b|\bsell\b|\bposition size\b|\bplace (?:an )?order\b",
    re.IGNORECASE,
)
RUNTIME_ROOT = Path(__file__).resolve().parents[1]


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EquitySnapshotError(f"{context} requires text")
    return value.strip()


def _date(value: object, context: str) -> date:
    text = _text(value, context)
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise EquitySnapshotError(f"{context} requires an ISO-8601 date") from error


def _as_of_moment(value: object, context: str) -> tuple[str, datetime]:
    text = _text(value, context)
    if "T" not in text:
        raise EquitySnapshotError(
            f"{context} requires a complete timestamp with timezone"
        )
    try:
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text
        )
    except ValueError as error:
        raise EquitySnapshotError(f"{context} requires an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EquitySnapshotError(f"{context} timestamp requires a timezone")
    return text, parsed.astimezone(timezone.utc)


def _as_of(value: object, context: str) -> str:
    return _as_of_moment(value, context)[0]


def _validate_source_times(value: object, research_as_of: datetime) -> None:
    if isinstance(value, dict):
        if {"name", "as_of", "url"}.issubset(value):
            _, source_as_of = _as_of_moment(value["as_of"], "source")
            if source_as_of > research_as_of:
                raise EquitySnapshotError("source as_of is after research as_of")
        for nested in value.values():
            _validate_source_times(nested, research_as_of)
    elif isinstance(value, list):
        for nested in value:
            _validate_source_times(nested, research_as_of)


def _statement(value: object, context: str) -> str:
    statement = _text(value, context)
    if TRADE_DIRECTIVE.search(statement):
        raise EquitySnapshotError(f"{context} contains a trade directive")
    return statement


def _source(source: object, context: str, allowed_kinds: set[str]) -> str:
    if not isinstance(source, dict):
        raise EquitySnapshotError(f"{context} requires a source")
    name = _text(source.get("name"), f"{context} source")
    kind = _text(source.get("kind"), f"{context} source")
    if kind not in allowed_kinds:
        raise EquitySnapshotError(f"{context} source kind is not allowed: {kind}")
    as_of = _as_of(source.get("as_of"), f"{context} source")
    url = _text(source.get("url"), f"{context} source")
    return f"[{name}]({url})（as_of：{as_of}）"


def _identity_record(
    value: object, context: str, required: tuple[str, ...]
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EquitySnapshotError(f"{context} requires an object")
    return {field: _text(value.get(field), f"{context} {field}") for field in required}


def _identity(identity: object, instrument: str) -> tuple[dict[str, str], str]:
    if not isinstance(identity, dict):
        raise EquitySnapshotError("identity requires an object")
    if identity.get("status") != "verified":
        reason = _text(identity.get("reason"), "unverified identity")
        raise EquitySnapshotError(f"issuer identity is not uniquely verified: {reason}")
    requested = _identity_record(
        identity.get("request"), "identity request", ("company_name", "ticker", "exchange")
    )
    verified = _identity_record(
        identity.get("verified"),
        "verified identity",
        ("company_name", "ticker", "exchange", "issuer"),
    )
    if requested["ticker"] != instrument:
        raise EquitySnapshotError("identity request ticker does not match instrument")
    for field in ("company_name", "ticker", "exchange"):
        if requested[field] != verified[field]:
            raise EquitySnapshotError(f"verified identity {field} does not match request")
    source = _source(identity.get("source"), "identity", PRIMARY_IDENTITY_KINDS)
    return verified, source


def _key_data(items: object) -> list[str]:
    if not isinstance(items, list) or len(items) != 3:
        raise EquitySnapshotError("key public data requires exactly three items")
    required = set(KEY_DATA_SOURCE_KINDS)
    rendered = ["## 关键公开数据"]
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise EquitySnapshotError("key public data item must be an object")
        kind = _text(item.get("kind"), "key public data item")
        if kind not in required or kind in seen:
            raise EquitySnapshotError("key public data kinds must be unique and complete")
        seen.add(kind)
        label = _statement(item.get("label"), "key public data label")
        value = _statement(item.get("value"), f"{label} value")
        source = _source(item.get("source"), label, KEY_DATA_SOURCE_KINDS[kind])
        rendered.append(f"- **{label}**：{value}（来源：{source}）")
    if seen != required:
        raise EquitySnapshotError("key public data kinds are incomplete")
    rendered.append("")
    return rendered


def _updates(items: object, research_as_of: date, issuer: str) -> list[str]:
    if not isinstance(items, list) or not 3 <= len(items) <= 5:
        raise EquitySnapshotError("recent company updates require three to five items")
    rendered = ["## 最近 30 天公司相关公告或新闻"]
    for item in items:
        if not isinstance(item, dict):
            raise EquitySnapshotError("recent company update must be an object")
        title = _statement(item.get("title"), "recent company update")
        update_issuer = _text(item.get("issuer"), f"{title} issuer")
        if update_issuer != issuer:
            raise EquitySnapshotError(f"{title} is not directly related to the verified issuer")
        summary = _statement(item.get("summary"), f"{title} summary")
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
    research_as_of_text, research_as_of_moment = _as_of_moment(
        fixture.get("research_as_of"), "fixture"
    )
    research_as_of = date.fromisoformat(research_as_of_text[:10])
    _validate_source_times(fixture, research_as_of_moment)
    identity, issuer_source = _identity(fixture.get("identity"), instrument)
    gaps = fixture.get("data_gaps", [])
    if not isinstance(gaps, list):
        raise EquitySnapshotError("data gaps must be a list")
    lines = [
        f"# 个股快览：{instrument}",
        "",
        f"研究截至：{research_as_of_text}",
        "",
        "## 发行人身份",
        f"- 公司：{identity['company_name']}；Ticker：{identity['ticker']}；交易所：{identity['exchange']}",
        f"- 发行人：{identity['issuer']}（来源：{issuer_source}）",
        "",
        *_key_data(fixture.get("key_public_data")),
        *_updates(fixture.get("recent_company_updates"), research_as_of, identity["issuer"]),
        "## 数据缺口",
    ]
    if gaps:
        lines.extend(f"- {_statement(gap, 'data gap')}" for gap in gaps)
    else:
        lines.append("- 本次未记录额外数据缺口。")
    return "\n".join(lines).rstrip() + "\n"


def _write_new(path: Path, content: str) -> None:
    resolved = path.resolve()
    if RUNTIME_ROOT == resolved or RUNTIME_ROOT in resolved.parents:
        raise EquitySnapshotError("output path must not be inside the Skill runtime package")
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
