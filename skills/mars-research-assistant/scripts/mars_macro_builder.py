#!/usr/bin/env python3
"""Build the only Mars Macro ResearchResult from normalized field-contract observations."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping

from artifact_packet_core import canonical_json_bytes, sha256_hex


DERIVED_CHANGE_IDS = (
    "equity.ndx_rut_ratio.change_1d",
    "equity.ndx_rut_ratio.change_5d",
    "equity.ndx_rut_ratio.change_20d",
)


def build_mars_macro_research_result(
    observations: Mapping[str, Mapping[str, Any]],
    resolved_values: Mapping[str, Any],
    *,
    as_of: str,
    field_ids: list[str],
) -> dict[str, Any]:
    """Create a bounded Macro result without accepting caller narrative or charts."""

    market_date = str(observations["equity.ndx_close"]["market_reference_date"])
    rates_source = str(observations["rates.us_10y_yield"]["source_id"])
    relative_source = str(observations["volatility.vix_close"]["source_id"])
    rate_series = [
        _trend(observations["rates.us_2y_yield"], "2Y", "percent"),
        _trend(observations["rates.us_10y_yield"], "10Y", "percent"),
        _trend(observations["rates.us_30y_yield"], "30Y", "percent"),
    ]
    vix_ratio_history = _ratio_history(
        observations["volatility.vix_close"], observations["volatility.vix3m_close"]
    )
    ndx_rut_history = _ratio_history(
        observations["equity.ndx_close"], observations["equity.rut_close"]
    )
    policy_watch = [
        {
            "id": str(record["id"]),
            "title": str(record["title"]),
            "published_at": str(record["published_at"]),
            "policy_status": str(record["policy_status"]),
            "posture_effect": str(record["posture_effect"]),
            "source": "White House Presidential Actions",
        }
        for record in observations["policy.us_executive_actions"]["value"]
    ]
    event_watch = [
        {
            key: record[key]
            for key in (
                "id", "title", "category", "time", "timezone", "reference_period",
                "consensus", "previous", "revised_previous", "actual", "source",
            )
        }
        for record in observations["events.seven_day_allowlist"]["value"]
    ]
    evidence_groups = _evidence_groups(observations, resolved_values)
    posture = _posture(evidence_groups)
    trend_series = [
        *rate_series,
        _trend_from_points(
            "VIX/VIX3M",
            "ratio",
            vix_ratio_history,
            "短端与三个月隐含波动率的直接来源比值。",
        ),
        _trend_from_points(
            "NDX/RUT",
            "ratio",
            ndx_rut_history,
            "纳指 100 与 Russell 2000 的直接来源比值。",
        ),
    ]
    chart_fields = {
        "2Y": "rates.us_2y_yield",
        "10Y": "rates.us_10y_yield",
        "30Y": "rates.us_30y_yield",
        "VIX/VIX3M": "volatility.vix_vix3m_ratio",
        "NDX/RUT": "equity.ndx_rut_ratio",
        "NDX/RUT 5D": "equity.ndx_rut_ratio.change_5d",
        "NDX/RUT 20D": "equity.ndx_rut_ratio.change_20d",
        "准备金": "liquidity.reserve_balances",
        "TGA": "liquidity.tga_balance",
        "ON RRP": "liquidity.on_rrp_usage",
    }
    trend_fields = {
        "2Y": "rates.us_2y_yield",
        "10Y": "rates.us_10y_yield",
        "30Y": "rates.us_30y_yield",
        "VIX/VIX3M": "volatility.vix_vix3m_ratio",
        "NDX/RUT": "equity.ndx_rut_ratio",
    }
    snapshot = {
        "artifact_lifecycle": "transient",
        "board": "macro_regime",
        "builder": {"generated_at": as_of, "id": "mars-macro-builder"},
        "coverage": {"required_complete": 4, "required_total": 4},
        "decision_cutoff": as_of,
        "diagnostics": [],
        "evidence_state": "complete",
        "locale": "zh-CN",
        "payload": {
            "board": "macro_regime",
            "macro_profile": "mars_direct_v1",
            "payload_version": "1.0",
            "question": "当前金融条件是否支持增加高 Beta 风险，以及未来一周哪些事件可能改变这个判断？",
            "decision": _decision(posture),
            "chart_series": [
                {"label": label, "value": float(resolved_values[field_id])}
                for label, field_id in chart_fields.items()
            ],
            "trend_series": trend_series,
            "policy_watch": policy_watch,
            "event_watch": event_watch,
            "evidence_groups": evidence_groups,
            "market_timing": {
                "market_reference_date": market_date,
                "intraday_excluded": True,
                "news_policy_cutoff": as_of,
                "lag_reason": "所有市场字段对齐至最近共同完成收盘；流动性保留各自最新官方发布期。",
            },
            "views": [
                "Overview",
                "Rates & Liquidity",
                "Cross-Asset Impact",
                "Policy Watch",
            ],
            "modules": [
                _module("plan_context", "complete", as_of, "mars_field_contract", {
                    "active_plan_id": "mars-field-contract-v1",
                    "applicable_horizon": "current",
                    "applicable_session": as_of,
                    "assumptions": "只使用本轮验证的精确字段来源。",
                    "constraints": "未验证字段不得以代理进入 Board。",
                    "current_posture": "字段合同快照。",
                    "decision_rules": "字段或共同收盘日不完整时拒绝生成 Board。",
                }, "Mars 精确字段合同已启用。"),
                _module("rates_liquidity", "complete", as_of, rates_source, {
                    "rule": "2Y、10Y、30Y 使用同一共同完成收盘；流动性使用最新官方发布值。",
                    "scope": "美国国债收益率曲线和三项官方流动性字段。",
                }, "收益率与流动性字段均来自精确字段来源。"),
                _module("cross_asset", "complete", as_of, relative_source, {
                    "rule": "VIX/VIX3M 与 NDX/RUT 均由同一共同完成收盘日的直接历史计算。",
                    "scope": "波动期限结构与成长/小盘相对强弱。",
                }, "波动与相对强弱字段均来自精确字段来源。"),
                _module("policy_watch", "complete", as_of, "white_house_presidential_actions", {
                    "rule": "未来七日事件与特朗普政策均使用直接来源的限字段摘要。",
                    "scope": "事件保留时间、时区、参考期、共识和前值；政策不写入原始正文。",
                }, "事件和行政政策字段已按公开一手来源合同验证。"),
            ],
            "holdings_context": {
                "conditional": True,
                "status": "not_loaded",
                "summary": "没有读取账户或持仓；组合传导保持条件性表述。",
            },
            "exposure_lens": [
                {
                    "id": "rates-sensitive",
                    "kind": "theme",
                    "label": "利率敏感资产",
                    "sensitivity": "长期收益率与波动期限结构变化。",
                    "impact": "Conditional on a separate consented holdings read.",
                    "plan_rule": "不从本面板产生交易指令。",
                },
                {
                    "id": "relative-strength",
                    "kind": "theme",
                    "label": "成长/小盘相对强弱",
                    "sensitivity": "NDX/RUT 的水平、变化率和二十日标准化读数。",
                    "impact": "Conditional on a separate consented holdings read.",
                    "plan_rule": "只作为后续研究的交叉确认。",
                },
            ],
            "evidence": [
                _evidence("rate-actual", "利率与流动性", "rates_liquidity", "actual", rates_source, "rates-sensitive", as_of,
                          "收益率曲线和流动性字段通过精确字段合同验证。",
                          "期限结构与流动性需要和波动、相对强弱共同解读。"),
                _evidence("relative-actual", "波动与相对强弱", "cross_asset", "actual", relative_source, "relative-strength", as_of,
                          "VIX/VIX3M 与 NDX/RUT 由同一完成收盘日的合同历史计算。",
                          "比值的变化率与标准化读数用于描述结构，不构成交易指令。"),
                _evidence("event-actual", "未来七日高影响事件", "policy_watch", "actual", "official_macro_event_allowlist", "rates-sensitive", as_of,
                          "未来七日事件来自直接、限字段摘要。",
                          "缺失、过期或无法直开的日历来源会阻断 Board。"),
                _evidence("policy-actual", "美国行政政策", "policy_watch", "actual", "white_house_presidential_actions", "rates-sensitive", as_of,
                          "特朗普及美国行政政策来自白宫 Presidential Actions 的直接、限字段摘要。",
                          "仅已确认或直接归属的状态可影响 posture。"),
            ],
            "posture": posture,
            "scenarios": [],
            "preflight": {
                "field_contract_version": "macro-v1",
                "market_reference_date": market_date,
                "validated_field_ids": sorted(field_ids),
                "chart_field_ids": chart_fields,
                "trend_field_ids": trend_fields,
            },
        },
        "payload_version": "1.0",
        "privacy": "private_runtime",
        "renderer_version": "1.0",
        "schema_version": "1.0",
        "snapshot_id": f"mars-macro-{market_date}",
        "source_registry": _source_registry(observations),
        "state_reasons": [
            "未建立精确字段来源合同的字段不进入本面板。",
            "不支持盘中 Macro Board；市场字段只使用最近共同完成收盘。",
        ],
        "timezone": "UTC",
    }
    _refresh_snapshot_hash(snapshot)
    sources = [
        {
            "id": row["id"],
            "label": row["alias"],
            "priority": row["priority"],
            "as_of": row["as_of"],
        }
        for row in snapshot["source_registry"]
    ]
    return {
        "schema_version": "1.0",
        "result_kind": "macro",
        "as_of": as_of,
        "decision": snapshot["payload"]["decision"],
        "key_evidence": [
            {
                "label": "共同完成收盘",
                "value": market_date,
                "evidence_type": "fact",
                "status": "complete",
                "as_of": as_of,
                "source_refs": [rates_source],
            }
        ],
        "risks": [
            {
                "label": "字段边界",
                "severity": "high",
                "detail": "缺少精确字段来源合同的字段不会用代理补齐。",
                "invalidation": "为该字段建立并验证精确来源合同。",
            }
        ],
        "scenarios": [
            {"name": row["name"], "condition": row["trigger"], "implication": row["posture"]}
            for row in snapshot["payload"]["scenarios"]
        ],
        "next_checks": [
            "下一次字段刷新时重新验证共同完成收盘、事件时间和最新官方观测。"
        ],
        "data_gaps": [],
        "sources": sources,
        "privacy": "private",
        "locale": "zh-CN",
        "visual": {"adapter": "macro", "snapshot": snapshot, "default_view": "Overview"},
    }


def _trend(row: Mapping[str, Any], label: str, unit: str) -> dict[str, Any]:
    return _trend_from_points(
        label,
        unit,
        row["history"],
        "通过字段合同验证的共同完成收盘历史。",
    )


def _trend_from_points(
    label: str, unit: str, points: list[Mapping[str, Any]], implication: str
) -> dict[str, Any]:
    return {
        "label": label,
        "unit": unit,
        "points": [
            {"time": f"{point['date']}T20:00:00Z", "value": float(point["value"])}
            for point in points
        ],
        "implication": implication,
    }


def _ratio_history(
    numerator: Mapping[str, Any], denominator: Mapping[str, Any]
) -> list[dict[str, Any]]:
    return [
        {"date": left["date"], "value": float(left["value"]) / float(right["value"])}
        for left, right in zip(numerator["history"], denominator["history"])
    ]


def _module(
    module_id: str, state: str, as_of: str, source_ref: str, data: Mapping[str, str], summary: str
) -> dict[str, Any]:
    return {
        "id": module_id,
        "requirement": "required",
        "evidence_state": state,
        "summary": summary,
        "as_of": as_of,
        "freshness_policy_id": "official-current-v1",
        "source_refs": [source_ref],
        "gap_reason": "" if state == "complete" else summary,
        "data": dict(data),
    }


def _evidence(
    evidence_id: str, label: str, family: str, category: str, source_ref: str,
    exposure_id: str, as_of: str, reading: str, transmission: str,
) -> dict[str, str]:
    return {
        "id": evidence_id,
        "label": label,
        "family": family,
        "category": category,
        "source_ref": source_ref,
        "exposure_id": exposure_id,
        "as_of": as_of,
        "reading": reading,
        "transmission": transmission,
        "plan_effect": "不创建交易指令。",
        "status": {
            "actual": "verified", "forecast": "needs_check", "media": "lead", "thesis": "plan_rule",
        }[category],
    }


def _evidence_groups(
    observations: Mapping[str, Mapping[str, Any]],
    resolved_values: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return qualitative, auditable groups without a numeric risk score."""

    ten_year_history = observations["rates.us_10y_yield"]["history"]
    rate_status = _direction_status(
        float(ten_year_history[-1]["value"]),
        float(ten_year_history[-2]["value"]),
        rising="pressures",
        falling="supports",
    )
    volatility_status = _direction_status(
        float(resolved_values["volatility.vix_vix3m_ratio"]),
        1.0,
        rising="pressures",
        falling="supports",
    )
    style_status = _direction_status(
        float(resolved_values["equity.ndx_rut_ratio.change_20d"]),
        0.0,
        rising="pressures",
        falling="supports",
    )
    policy_records = observations["policy.us_executive_actions"]["value"]
    active_effects = [
        record["posture_effect"]
        for record in policy_records
        if record["policy_status"] in {"confirmed", "stated_not_enacted"}
    ]
    policy_status = (
        "pressures" if "pressures" in active_effects
        else "supports" if "supports" in active_effects
        else "neutral"
    )
    return [
        {
            "id": "rates",
            "label": "利率",
            "status": rate_status,
            "field_ids": ["rates.us_2y_yield", "rates.us_10y_yield", "rates.us_30y_yield"],
            "reason": "10Y 相对前一完成收盘的方向用于描述折现率压力。",
        },
        {
            "id": "credit_volatility",
            "label": "信用与波动率",
            "status": volatility_status,
            "field_ids": ["volatility.vix_close", "volatility.vix3m_close", "volatility.vix_vix3m_ratio"],
            "reason": "1 以下为期限结构正常化，1 以上为短端波动压力。",
        },
        {
            "id": "large_small_relative_strength",
            "label": "大盘成长/小盘相对强弱",
            "status": style_status,
            "field_ids": ["equity.ndx_rut_ratio", "equity.ndx_rut_ratio.change_20d"],
            "reason": "NDX/RUT 上升代表大盘成长相对拥挤，小盘参与度较弱。",
        },
        {
            "id": "liquidity_policy_events",
            "label": "流动性、政策与事件",
            "status": policy_status,
            "field_ids": [
                "liquidity.reserve_balances",
                "liquidity.tga_balance",
                "liquidity.on_rrp_usage",
                "events.seven_day_allowlist",
                "policy.us_executive_actions",
            ],
            "reason": "流动性字段保持分列，不发明净流动性；仅已确认或直接归属政策可改变该组状态。",
        },
    ]


def _direction_status(
    current: float, baseline: float, *, rising: str, falling: str
) -> str:
    if current > baseline:
        return rising
    if current < baseline:
        return falling
    return "neutral"


def _posture(evidence_groups: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_id = {str(group["id"]): str(group["status"]) for group in evidence_groups}
    rates = by_id["rates"]
    volatility = by_id["credit_volatility"]
    style = by_id["large_small_relative_strength"]
    liquidity_policy = by_id["liquidity_policy_events"]
    if rates == "pressures" and (
        volatility == "pressures" or style == "pressures" or liquidity_policy == "pressures"
    ):
        label = "risk_reduction_required"
        consequence = "利率压力与至少一个交叉证据组同步承压；优先降低高 Beta 风险。"
    elif all(status == "supports" for status in (rates, volatility, style, liquidity_policy)):
        label = "risk_expansion_allowed"
        consequence = "四个证据组均支持；仍需在独立标的研究中确认。"
    else:
        label = "hold_current_risk"
        consequence = "证据未形成一致的扩张或收缩条件，维持现有风险预算。"
    return {
        "label": label,
        "consequence": consequence,
        "derived_from": ["rate-actual", "relative-actual", "event-actual", "policy-actual"],
    }


def _decision(posture: Mapping[str, str]) -> str:
    return (
        f"当前 posture：{posture['label']}。{posture['consequence']} "
        "本面板仅使用最近共同完成收盘与最新官方发布；不包含盘中数据或代理字段。"
    )


SOURCE_ALIASES = {
    "us_treasury_daily_rates": "U.S. Treasury daily yield curve",
    "cboe_vix_history": "Cboe VIX daily history",
    "cboe_vix3m_history": "Cboe VIX3M daily history",
    "fred_nasdaq100_history": "FRED NASDAQ100 daily close",
    "cboe_rut_history": "Cboe Russell 2000 daily history",
    "federal_reserve_h41": "Federal Reserve H.4.1",
    "us_treasury_dts": "U.S. Treasury Daily Treasury Statement",
    "new_york_fed_on_rrp": "New York Fed ON RRP results",
    "official_macro_event_allowlist": "Official seven-day macro event sources",
    "white_house_presidential_actions": "White House Presidential Actions",
    "ibkr_market_data": "Interactive Brokers market data",
    "mars_field_contract": "Mars field contract",
}


def _source_registry(
    observations: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Expose exact, observed source identities instead of generic source buckets."""

    observed_at: dict[str, str] = {}
    for observation in observations.values():
        source_id = observation.get("source_id")
        data_as_of = observation.get("data_as_of")
        if isinstance(source_id, str) and isinstance(data_as_of, str):
            previous = observed_at.get(source_id)
            if previous is None or data_as_of > previous:
                observed_at[source_id] = data_as_of
    if not observed_at:
        raise ValueError("observed_source_registry_missing")
    rows = [
        {
            "id": source_id,
            "alias": SOURCE_ALIASES.get(source_id, source_id),
            "priority": "S0",
            "as_of": observed_at[source_id],
            "freshness_policy_id": "official-current-v1",
            "freshness_status": "fresh",
        }
        for source_id in sorted(observed_at)
    ]
    rows.append(
        {
            "id": "mars_field_contract",
            "alias": SOURCE_ALIASES["mars_field_contract"],
            "priority": "S3",
            "as_of": max(observed_at.values()),
            "freshness_policy_id": "official-current-v1",
            "freshness_status": "fresh",
        }
    )
    return rows


def _refresh_snapshot_hash(snapshot: dict[str, Any]) -> None:
    hashable = copy.deepcopy(snapshot)
    hashable.pop("content_hash", None)
    snapshot["content_hash"] = sha256_hex(canonical_json_bytes(hashable))
