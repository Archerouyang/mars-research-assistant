#!/usr/bin/env python3
"""Build the only Mars Macro ResearchResult from normalized direct observations."""

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
            "source": "White House Presidential Actions",
        }
        for record in observations["policy.us_executive_actions"]["value"]
    ]
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
            "question": "直接来源的金融条件快照是否支持改变风险判断？",
            "decision": "本面板仅使用最近共同完成收盘与最新官方流动性数据；未建立直接来源合同的字段不会以代理补入。",
            "chart_series": [
                {"label": label, "value": float(resolved_values[field_id])}
                for label, field_id in chart_fields.items()
            ],
            "trend_series": trend_series,
            "policy_watch": policy_watch,
            "views": [
                "Overview",
                "Rates & Liquidity",
                "Cross-Asset Impact",
                "Policy Watch",
            ],
            "modules": [
                _module("plan_context", "complete", as_of, "mars_direct_contract", {
                    "active_plan_id": "mars-direct-macro-v1",
                    "applicable_horizon": "current",
                    "applicable_session": as_of,
                    "assumptions": "只使用本轮验证的直接来源字段。",
                    "constraints": "未验证字段不得以代理进入 Board。",
                    "current_posture": "直接来源快照。",
                    "decision_rules": "字段或共同收盘日不完整时拒绝生成 Board。",
                }, "Mars 直接来源字段合同已启用。"),
                _module("rates_liquidity", "complete", as_of, "us_treasury_daily_rates", {
                    "rule": "2Y、10Y、30Y 使用同一共同完成收盘；流动性使用最新官方发布值。",
                    "scope": "美国国债收益率曲线和三项官方流动性字段。",
                }, "收益率与流动性字段均来自直接来源。"),
                _module("cross_asset", "complete", as_of, "cboe_vix_history", {
                    "rule": "VIX/VIX3M 与 NDX/RUT 均由同一共同完成收盘日的直接历史计算。",
                    "scope": "波动期限结构与成长/小盘相对强弱。",
                }, "波动与相对强弱字段均来自直接来源。"),
                _module("policy_watch", "complete", as_of, "white_house_presidential_actions", {
                    "rule": "特朗普及美国行政政策只显示白宫 Presidential Actions 的直接、限字段摘要。",
                    "scope": "标题、发布时间和官方页面链接；不写入原始页面正文。",
                }, "白宫行政政策字段已按直接来源合同验证。"),
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
                    "impact": "Conditional on a separate reconciled portfolio read.",
                    "plan_rule": "不从本面板产生交易指令。",
                },
                {
                    "id": "relative-strength",
                    "kind": "theme",
                    "label": "成长/小盘相对强弱",
                    "sensitivity": "NDX/RUT 的水平、变化率和二十日标准化读数。",
                    "impact": "Conditional on a separate reconciled portfolio read.",
                    "plan_rule": "只作为后续研究的交叉确认。",
                },
            ],
            "evidence": [
                _evidence("rate-actual", "直接利率与流动性", "rates_liquidity", "actual", "us_treasury_daily_rates", "rates-sensitive", as_of,
                          "收益率曲线和流动性字段通过直接来源合同验证。",
                          "期限结构与流动性需要和波动、相对强弱共同解读。"),
                _evidence("relative-actual", "波动与相对强弱", "cross_asset", "actual", "cboe_vix_history", "relative-strength", as_of,
                          "VIX/VIX3M 与 NDX/RUT 由同一完成收盘日的历史计算。",
                          "比值的变化率与标准化读数用于描述结构，不构成交易指令。"),
                _evidence("policy-actual", "白宫行政政策", "policy_watch", "actual", "white_house_presidential_actions", "rates-sensitive", as_of,
                          "特朗普及美国行政政策只来自白宫 Presidential Actions 的直接、限字段摘要。",
                          "缺失、过期或无法直开的白宫来源会阻断 Board。"),
            ],
            "posture": {
                "label": "直接来源快照",
                "consequence": "先以已验证字段确认结构；不对缺失字段作代理推断。",
                "derived_from": ["rate-actual", "relative-actual", "policy-actual"],
            },
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
        "state_reasons": ["未建立直接来源合同的字段不进入本面板。"],
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
                "source_refs": ["us_treasury_daily_rates"],
            }
        ],
        "risks": [
            {
                "label": "字段边界",
                "severity": "high",
                "detail": "缺少直接来源合同的字段不会用代理补齐。",
                "invalidation": "为该字段建立并验证精确公开来源合同。",
            }
        ],
        "scenarios": [
            {"name": row["name"], "condition": row["trigger"], "implication": row["posture"]}
            for row in snapshot["payload"]["scenarios"]
        ],
        "next_checks": ["下一次直接来源刷新时重新验证共同完成收盘和最新官方观测。"],
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
        "直接来源的共同完成收盘历史。",
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


SOURCE_ALIASES = {
    "us_treasury_daily_rates": "U.S. Treasury daily yield curve",
    "cboe_vix_history": "Cboe VIX daily history",
    "cboe_vix3m_history": "Cboe VIX3M daily history",
    "fred_nasdaq100_history": "FRED NASDAQ100 daily close",
    "cboe_rut_history": "Cboe Russell 2000 daily history",
    "federal_reserve_h41": "Federal Reserve H.4.1",
    "us_treasury_dts": "U.S. Treasury Daily Treasury Statement",
    "new_york_fed_on_rrp": "New York Fed ON RRP results",
    "white_house_presidential_actions": "White House Presidential Actions",
    "mars_direct_contract": "Mars direct field contract",
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
            "id": "mars_direct_contract",
            "alias": SOURCE_ALIASES["mars_direct_contract"],
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
