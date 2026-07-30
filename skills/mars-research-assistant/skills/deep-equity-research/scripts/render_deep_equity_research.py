#!/usr/bin/env python3
"""Render a traceable nine-chapter deep-equity-research Markdown artifact."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from math import isfinite
from pathlib import Path
import re
from typing import Any


class DeepResearchError(ValueError):
    """Reject incomplete evidence rather than inventing a research conclusion."""


CHAPTERS = (
    ("研究范围与核心判断", "research_scope_and_core_view"),
    ("公司与商业模式", "company_and_business_model"),
    ("行业与竞争格局", "industry_and_competition"),
    ("管理层、治理与资本配置", "management_governance_and_capital_allocation"),
    ("财务表现与质量核查", "financial_performance_and_quality"),
    ("预期差、催化剂与关键跟踪项", "expectations_catalysts_and_tracking"),
    ("三情景 DCF/反向 DCF", "valuation"),
    ("风险、反方论点与可证伪条件", "risks_counter_thesis_and_falsification"),
)
QUALITY_CHECKS = (
    ("trend_consistency", "收入、利润与经营现金流的趋势一致性"),
    ("cash_conversion_and_accrual_quality", "现金转换与应计质量"),
    ("working_capital_signals", "应收账款及递延收入相对收入的异常变化"),
    ("dilution_audit_and_governance", "股本稀释/SBC、审计意见与治理红旗"),
)
PRIMARY_SOURCE_KINDS = {"sec_filing", "regulatory_filing", "issuer_ir", "exchange"}
RESEARCH_SOURCE_KINDS = PRIMARY_SOURCE_KINDS | {"issuer_announcement", "credible_media"}
VALUATION_ASSUMPTION_SOURCE_KINDS = {"valuation_assumption"}
VALUATION_SCENARIO_SOURCE_KINDS = PRIMARY_SOURCE_KINDS | VALUATION_ASSUMPTION_SOURCE_KINDS
ALL_SOURCE_KINDS = RESEARCH_SOURCE_KINDS | {"public_quote"} | VALUATION_ASSUMPTION_SOURCE_KINDS
TRADE_DIRECTIVE = re.compile(
    r"买入|卖出|增持|减持|加仓|减仓|建仓|平仓|下单|持仓比例|\bbuy\b|\bsell\b|"
    r"\bposition size\b|\bplace (?:an )?order\b",
    re.IGNORECASE,
)
RUNTIME_ROOT = Path(__file__).resolve().parents[3]


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DeepResearchError(f"{context} requires text")
    return value.strip()


def _number(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DeepResearchError(f"{context} requires a finite number")
    result = float(value)
    if not isfinite(result):
        raise DeepResearchError(f"{context} requires a finite number")
    return result


def _as_of_moment(value: object, context: str) -> tuple[str, datetime]:
    text = _text(value, context)
    if "T" not in text:
        raise DeepResearchError(
            f"{context} requires a complete timestamp with timezone"
        )
    try:
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text
        )
    except ValueError as error:
        raise DeepResearchError(f"{context} requires an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DeepResearchError(f"{context} timestamp requires a timezone")
    return text, parsed.astimezone(timezone.utc)


def _as_of(value: object, context: str) -> str:
    return _as_of_moment(value, context)[0]


def _validate_source_times(value: object, research_as_of: datetime) -> None:
    if isinstance(value, dict):
        if {"name", "as_of", "url"}.issubset(value):
            _, source_as_of = _as_of_moment(value["as_of"], "source")
            if source_as_of > research_as_of:
                raise DeepResearchError("source as_of is after research as_of")
        for nested in value.values():
            _validate_source_times(nested, research_as_of)
    elif isinstance(value, list):
        for nested in value:
            _validate_source_times(nested, research_as_of)


def _source(source: object, context: str, allowed_kinds: set[str]) -> str:
    if not isinstance(source, dict):
        raise DeepResearchError(f"{context} requires a source")
    name = _text(source.get("name"), f"{context} source")
    kind = _text(source.get("kind"), f"{context} source")
    if kind not in allowed_kinds:
        raise DeepResearchError(f"{context} source kind is not allowed: {kind}")
    as_of = _as_of(source.get("as_of"), f"{context} source")
    url = _text(source.get("url"), f"{context} source")
    return f"[{name}]({url})（as_of：{as_of}）"


def _identity_record(
    value: object, context: str, required: tuple[str, ...]
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise DeepResearchError(f"{context} requires an object")
    return {field: _text(value.get(field), f"{context} {field}") for field in required}


def _identity(identity: object, symbol: str) -> tuple[dict[str, str], str]:
    if not isinstance(identity, dict) or identity.get("status") != "verified":
        reason = _text(
            identity.get("reason") if isinstance(identity, dict) else None,
            "unverified identity",
        )
        raise DeepResearchError(f"issuer identity is not uniquely verified: {reason}")
    requested = _identity_record(
        identity.get("request"), "identity request", ("company_name", "ticker", "exchange")
    )
    verified = _identity_record(
        identity.get("verified"),
        "verified identity",
        ("company_name", "ticker", "exchange", "issuer"),
    )
    if requested["ticker"] != symbol:
        raise DeepResearchError("identity request ticker does not match symbol")
    for field in ("company_name", "ticker", "exchange"):
        if requested[field] != verified[field]:
            raise DeepResearchError(f"verified identity {field} does not match request")
    return verified, _source(identity.get("source"), "issuer identity", PRIMARY_SOURCE_KINDS)


def _statement(value: object, context: str) -> str:
    statement = _text(value, context)
    if TRADE_DIRECTIVE.search(statement):
        raise DeepResearchError(f"{context} contains a trade directive")
    return statement


def _evidence(title: str, items: object) -> list[str]:
    if items is None or items == []:
        return [f"数据不可用：未提供{title}的可核验证据。", ""]
    if not isinstance(items, list):
        raise DeepResearchError(f"{title} must be a list")
    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise DeepResearchError(f"{title} evidence item must be an object")
        label = _statement(item.get("label"), f"{title} evidence")
        statement = _statement(item.get("statement"), f"{label} statement")
        lines.append(
            f"- **{label}**：{statement}（来源：{_source(item.get('source'), label, RESEARCH_SOURCE_KINDS)}）"
        )
    lines.append("")
    return lines


def _quality_checks(items: object) -> list[str]:
    if not isinstance(items, list):
        raise DeepResearchError("financial quality checks must be a list")
    expected = {key for key, _ in QUALITY_CHECKS}
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise DeepResearchError("financial quality check must be an object")
        key = _text(item.get("check"), "financial quality check")
        if key not in expected or key in indexed:
            raise DeepResearchError("financial quality checks are invalid or duplicated")
        indexed[key] = item
    if set(indexed) != expected:
        raise DeepResearchError("all four financial quality checks are required")
    lines = ["### 四项最小财报质量检查"]
    for key, label in QUALITY_CHECKS:
        item = indexed[key]
        if item.get("status") == "unavailable":
            reason = _statement(item.get("reason"), f"{label} gap")
            lines.append(f"- **{label}**：数据不可用：{reason}")
            continue
        statement = _statement(item.get("statement"), label)
        lines.append(
            f"- **{label}**：{statement}（来源：{_source(item.get('source'), label, PRIMARY_SOURCE_KINDS)}）"
        )
    return lines + [""]


def _input(value: object, name: str, allowed_kinds: set[str]) -> tuple[float, str]:
    if not isinstance(value, dict):
        raise DeepResearchError(f"valuation input {name} requires an object")
    return _number(value.get("value"), f"valuation input {name}"), _source(
        value.get("source"), f"valuation input {name}", allowed_kinds
    )


def _scenario(item: object) -> tuple[str, list[float], str]:
    if not isinstance(item, dict):
        raise DeepResearchError("valuation scenario must be an object")
    name = _text(item.get("name"), "valuation scenario")
    cash_flows = item.get("free_cash_flows")
    if not isinstance(cash_flows, list) or len(cash_flows) < 2:
        raise DeepResearchError(f"{name} requires at least two annual free-cash-flow values")
    values = [_number(value, f"{name} free cash flow") for value in cash_flows]
    if name not in {"bear", "base", "bull"}:
        raise DeepResearchError("valuation scenarios must be bear, base, and bull")
    return name, values, _source(
        item.get("source"), f"{name} scenario", VALUATION_SCENARIO_SOURCE_KINDS
    )


def _dcf(value: dict[str, Any]) -> tuple[list[str], list[str]]:
    if not isinstance(value, dict):
        return ["数据不可用：未提供来源可追溯的估值假设集。", ""], ["未提供估值假设集。"]
    required = ("price", "shares_outstanding", "net_debt", "wacc", "terminal_growth", "scenarios")
    missing = [field for field in required if field not in value]
    if missing:
        message = f"估值未运行：缺少必要输入：{', '.join(missing)}。"
        return [message, ""], [message]
    try:
        price, price_source = _input(value["price"], "price", {"public_quote"})
        shares, shares_source = _input(
            value["shares_outstanding"], "shares_outstanding", PRIMARY_SOURCE_KINDS
        )
        net_debt, debt_source = _input(value["net_debt"], "net_debt", PRIMARY_SOURCE_KINDS)
        wacc, wacc_source = _input(
            value["wacc"], "wacc", VALUATION_ASSUMPTION_SOURCE_KINDS
        )
        growth, growth_source = _input(
            value["terminal_growth"], "terminal_growth", VALUATION_ASSUMPTION_SOURCE_KINDS
        )
        raw_scenarios = value["scenarios"]
        if not isinstance(raw_scenarios, list) or len(raw_scenarios) != 3:
            raise DeepResearchError("valuation requires exactly three scenarios")
        scenarios = [_scenario(item) for item in raw_scenarios]
        if len({name for name, _, _ in scenarios}) != 3:
            raise DeepResearchError("valuation scenario names must be unique")
        if price <= 0 or shares <= 0 or not 0 < growth < wacc < 1:
            raise DeepResearchError("valuation inputs require positive price/shares and 0 < growth < WACC < 1")
    except DeepResearchError as error:
        message = f"估值未运行：{error}"
        return [message, ""], [message]

    lines = [
        "### 估值假设",
        "| 输入 | 数值 | 来源 |",
        "| --- | ---: | --- |",
        f"| 当前价格 | {price:.2f} | {price_source} |",
        f"| 股本 | {shares:.2f} | {shares_source} |",
        f"| 净债务 | {net_debt:.2f} | {debt_source} |",
        f"| WACC | {wacc:.2%} | {wacc_source} |",
        f"| 永续增长率 | {growth:.2%} | {growth_source} |",
        "",
        "### 三情景 DCF",
        "| 情景 | 企业价值 | 股权价值 | 每股估值 | FCF 路径来源 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, cash_flows, source in scenarios:
        discounted = sum(cash_flow / (1 + wacc) ** year for year, cash_flow in enumerate(cash_flows, 1))
        terminal = cash_flows[-1] * (1 + growth) / (wacc - growth)
        enterprise_value = discounted + terminal / (1 + wacc) ** len(cash_flows)
        equity_value = enterprise_value - net_debt
        lines.append(
            f"| {name} | {enterprise_value:.2f} | {equity_value:.2f} | {equity_value / shares:.2f} | {source} |"
        )
    reverse_lines = _reverse_dcf(value.get("reverse_dcf"), price, shares, net_debt, wacc, growth)
    return lines + ["", *reverse_lines, ""], []


def _reverse_dcf(
    value: object, price: float, shares: float, net_debt: float, wacc: float, growth: float
) -> list[str]:
    if value is None:
        return ["### 反向 DCF", "数据不可用：未提供反向 DCF 的当前自由现金流和预测期。"]
    if not isinstance(value, dict):
        return ["### 反向 DCF", "数据不可用：反向 DCF 输入格式无效。"]
    try:
        current_fcf, source = _input(
            value.get("current_free_cash_flow"), "current_free_cash_flow", PRIMARY_SOURCE_KINDS
        )
        horizon_value, horizon_source = _input(
            value.get("horizon_years"),
            "horizon_years",
            VALUATION_ASSUMPTION_SOURCE_KINDS,
        )
        if not horizon_value.is_integer():
            raise DeepResearchError("reverse DCF horizon_years requires a whole number")
        horizon = int(horizon_value)
        if current_fcf <= 0 or not 1 <= horizon <= 20:
            raise DeepResearchError("reverse DCF requires positive FCF and a 1–20 year horizon")
    except DeepResearchError as error:
        return ["### 反向 DCF", f"数据不可用：{error}"]
    target_enterprise_value = price * shares + net_debt
    low, high = -0.95, 3.0
    low_value = _reverse_enterprise_value(
        current_fcf, horizon, low, wacc, growth
    )
    high_value = _reverse_enterprise_value(
        current_fcf, horizon, high, wacc, growth
    )
    if not min(low_value, high_value) <= target_enterprise_value <= max(low_value, high_value):
        return [
            "### 反向 DCF",
            "数据不可用：反向 DCF 无法在 -95.00% 至 300.00% 的增长区间内匹配当前企业价值。",
        ]
    for _ in range(120):
        implied_growth = (low + high) / 2
        enterprise_value = _reverse_enterprise_value(
            current_fcf, horizon, implied_growth, wacc, growth
        )
        if enterprise_value < target_enterprise_value:
            low = implied_growth
        else:
            high = implied_growth
    return [
        "### 反向 DCF",
        f"- 预测期：{horizon} 年（来源：{horizon_source}）",
        f"以当前股价隐含的 {horizon} 年自由现金流年化增长约为 **{(low + high) / 2:.2%}**"
        f"（当前自由现金流来源：{source}）。",
    ]


def _reverse_enterprise_value(
    current_fcf: float, horizon: int, growth_rate: float, wacc: float, terminal_growth: float
) -> float:
    cash_flows = [
        current_fcf * (1 + growth_rate) ** year for year in range(1, horizon + 1)
    ]
    return sum(
        cash_flow / (1 + wacc) ** year for year, cash_flow in enumerate(cash_flows, 1)
    ) + cash_flows[-1] * (1 + terminal_growth) / (wacc - terminal_growth) / (1 + wacc) ** horizon


def _source_registry(items: object) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["- 数据不可用：未提供独立来源索引。"]
    return [f"- {_source(item, 'source registry', ALL_SOURCE_KINDS)}" for item in items]


def render_research(fixture: dict[str, Any]) -> str:
    symbol = _text(fixture.get("symbol"), "fixture")
    research_as_of, research_as_of_moment = _as_of_moment(
        fixture.get("research_as_of"), "fixture"
    )
    _validate_source_times(fixture, research_as_of_moment)
    identity, issuer_source = _identity(fixture.get("identity"), symbol)
    sections = fixture.get("sections")
    if not isinstance(sections, dict):
        raise DeepResearchError("sections requires an object")
    assumptions = fixture.get("assumptions", [])
    gaps = fixture.get("data_gaps", [])
    if not isinstance(assumptions, list) or not isinstance(gaps, list):
        raise DeepResearchError("assumptions and data gaps must be lists")
    lines = [
        f"# 深度个股研究：{symbol}",
        "",
        f"研究截至：{research_as_of}",
        f"公司：{identity['company_name']}；Ticker：{identity['ticker']}；交易所：{identity['exchange']}",
        f"发行人：{identity['issuer']}（来源：{issuer_source}）",
        "",
    ]
    valuation_gaps: list[str] = []
    for number, (title, key) in enumerate(CHAPTERS, 1):
        lines.append(f"## {number}. {title}")
        if key == "financial_performance_and_quality":
            lines.extend(_evidence(title, sections.get(key)))
            lines.extend(_quality_checks(fixture.get("financial_quality_checks")))
        elif key == "valuation":
            valuation, valuation_gaps = _dcf(fixture.get("valuation"))
            lines.extend(valuation)
        else:
            lines.extend(_evidence(title, sections.get(key)))
    lines.extend(["## 9. 来源、时间戳、假设与数据缺口", "### 来源索引", *_source_registry(fixture.get("sources")), "", "### 假设"])
    if assumptions:
        lines.extend(f"- {_statement(item, 'assumption')}" for item in assumptions)
    else:
        lines.append("- 本次未记录额外假设。")
    lines.extend(["", "### 数据缺口"])
    combined_gaps = [*valuation_gaps, *(_statement(item, "data gap") for item in gaps)]
    if combined_gaps:
        lines.extend(f"- {gap}" for gap in combined_gaps)
    else:
        lines.append("- 本次未记录额外数据缺口。")
    return "\n".join(lines).rstrip() + "\n"


def _write_new(path: Path, content: str) -> None:
    resolved = path.resolve()
    if RUNTIME_ROOT == resolved or RUNTIME_ROOT in resolved.parents:
        raise DeepResearchError("output path must not be inside the Skill runtime package")
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
            raise DeepResearchError("fixture must be a JSON object")
        _write_new(arguments.output, render_research(fixture))
    except (OSError, json.JSONDecodeError, DeepResearchError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
