#!/usr/bin/env python3
"""Build a compact Portfolio Risk Board payload from normalized snapshots.

Inputs must already use the standard ``portfolio_snapshot.csv`` schema. This
adapter never calls a broker and never performs order actions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from product_knowledge import effective_exposure, normalize_symbol, product_knowledge
from record_schemas import CSV_SCHEMAS
from repair_portfolio_snapshot import repair_row


SCHEMA_VERSION = "1.0"
PORTFOLIO_HEADER = list(CSV_SCHEMAS["portfolio_snapshot.csv"])
PRODUCT_LABELS = {
    "cash": "现金",
    "stock_common": "普通股",
    "etf_common": "普通 ETF",
    "sector_etf": "行业 ETF",
    "leveraged_etf": "每日杠杆 ETF",
    "option": "期权",
    "future": "期货",
}
THEME_LABELS = {
    "ai_hardware": "AI 硬件",
    "ai_hardware_leverage": "AI 硬件杠杆",
    "korea_equity_leverage": "韩国权益杠杆",
    "memory_storage": "存储",
    "memory_storage_leverage": "存储杠杆",
    "semiconductor": "半导体",
    "semiconductor_leverage": "半导体杠杆",
    "tech_beta": "科技 Beta",
    "tech_beta_leverage": "科技 Beta 杠杆",
    "tech_inverse_leverage": "科技反向杠杆",
    "tesla_leverage": "Tesla 杠杆",
}


class PortfolioPanelError(ValueError):
    """Fail-closed panel input error with a stable public code."""


def _number(value: Any) -> float:
    try:
        return float(str(value or "0").replace(",", "").replace("$", ""))
    except ValueError:
        return 0.0


def _timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PortfolioPanelError("snapshot_as_of_invalid") from error


def load_snapshot(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or any(field not in reader.fieldnames for field in PORTFOLIO_HEADER):
            raise PortfolioPanelError("snapshot_schema_invalid")
        return [repair_row(row) for row in reader if str(row.get("symbol") or "").strip()]


def _effective_exposures(row: Mapping[str, str]) -> tuple[float, float, float]:
    market_value = abs(_number(row.get("market_value")))
    raw_delta = row.get("delta_exposure")
    raw_notional = row.get("notional_exposure")
    supplied_delta = None if raw_delta is None or not str(raw_delta).strip() else _number(raw_delta)
    supplied_notional = (
        None if raw_notional is None or not str(raw_notional).strip() else _number(raw_notional)
    )
    symbol = str(row.get("symbol") or "")
    row_direction = str(row.get("direction") or "long")
    delta = effective_exposure(
        symbol,
        market_value,
        supplied_delta,
        position_direction=row_direction,
    )
    notional = effective_exposure(
        symbol,
        market_value,
        supplied_notional,
        position_direction=row_direction,
    )
    return market_value, delta, notional


def _positions(rows: Iterable[Mapping[str, str]], excluded: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    positions: list[dict[str, Any]] = []
    exclusions: list[str] = []
    for raw in rows:
        raw = repair_row(raw)
        symbol = normalize_symbol(str(raw.get("symbol") or ""))
        if symbol in excluded:
            exclusions.append(symbol)
            continue
        market_value, delta, notional = _effective_exposures(raw)
        instrument = str(raw.get("instrument_type") or "unspecified")
        product = product_knowledge(symbol)
        underlying = product.underlying if product.known else normalize_symbol(str(raw.get("underlying") or symbol))
        positions.append(
            {
                "symbol": symbol,
                "underlying": underlying,
                "underlying_kind": product.underlying_kind,
                "broker": str(raw.get("broker") or "Unknown"),
                "instrument_type": instrument,
                "product": PRODUCT_LABELS.get(instrument, instrument.replace("_", " ")),
                "theme": str(raw.get("theme_id") or "unmapped"),
                "currency": str(raw.get("currency") or "USD").upper(),
                "is_cash": instrument == "cash" or symbol == "CASH",
                "market_value": market_value,
                "delta_exposure": 0.0 if instrument == "cash" or symbol == "CASH" else delta,
                "notional_exposure": 0.0 if instrument == "cash" or symbol == "CASH" else notional,
            }
        )
    return positions, sorted(set(exclusions))


def _aggregate(
    positions: list[Mapping[str, Any]],
    key: str,
    total_delta: float,
    plan_limit: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "direct_market_value": 0.0,
            "delta_exposure": 0.0,
            "notional_exposure": 0.0,
            "affected_holdings": [],
        }
    )
    for row in positions:
        if row["is_cash"]:
            continue
        label = str(row[key] or "unmapped")
        group = grouped[label]
        group["direct_market_value"] += float(row["market_value"])
        group["delta_exposure"] += float(row["delta_exposure"])
        group["notional_exposure"] += float(row["notional_exposure"])
        if row["symbol"] not in group["affected_holdings"]:
            group["affected_holdings"].append(row["symbol"])
    output = []
    for label, values in grouped.items():
        output.append(
            {
                "label": label,
                **values,
                "weight_pct": abs(values["delta_exposure"]) / total_delta * 100 if total_delta else 0.0,
                "plan_limit": plan_limit,
            }
        )
    return sorted(output, key=lambda item: abs(item["delta_exposure"]), reverse=True)


def _stress_scenarios(
    positions: list[Mapping[str, Any]],
    by_theme: list[Mapping[str, Any]],
    capital: float,
) -> list[dict[str, Any]]:
    non_cash = [row for row in positions if not row["is_cash"]]
    net_delta = sum(float(row["delta_exposure"]) for row in non_cash)
    rows = [
        {
            "name": "全组合风险偏好 -10%",
            "family": "risk_off",
            "estimated_impact": -0.10 * net_delta,
            "confidence": "情景假设",
            "assumptions": ["所有已确认等效方向敞口同步下跌 10%", "不计分散化收益"],
            "plan_constraint": "用于比较风险承受力，不是价格预测。",
        }
    ]
    if by_theme:
        top = by_theme[0]
        rows.append(
            {
                "name": f"最大主题 {top['label']} -15%",
                "family": "theme_shock",
                "estimated_impact": -0.15 * float(top["delta_exposure"]),
                "confidence": "情景假设",
                "assumptions": [f"{top['label']} 相关等效方向敞口下跌 15%"],
                "plan_constraint": "检验最大共同因子，而非逐股目标价。",
            }
        )
    leveraged_delta = sum(
        abs(float(row["delta_exposure"]))
        for row in non_cash
        if row["instrument_type"] == "leveraged_etf"
    )
    if leveraged_delta:
        rows.append(
            {
                "name": "杠杆产品隔夜缺口 -12%",
                "family": "leveraged_gap",
                "estimated_impact": -0.12 * leveraged_delta,
                "confidence": "情景假设",
                "assumptions": ["每日杠杆 ETF 的等效方向敞口发生 12% 不利跳空"],
                "plan_constraint": "单独观察路径依赖和事件跳空。",
            }
        )
    for row in rows:
        row["weight_pct"] = abs(float(row["estimated_impact"])) / capital * 100 if capital else 0.0
    return sorted(rows, key=lambda item: item["estimated_impact"])


def _risk_ledger(
    by_symbol: list[Mapping[str, Any]],
    by_theme: list[Mapping[str, Any]],
    by_product: list[Mapping[str, Any]],
    reconciliation: str,
    unmapped_count: int,
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    if by_symbol and float(by_symbol[0]["weight_pct"]) >= 40:
        top = by_symbol[0]
        risks.append({"exposure": top["label"], "risk_issue": f"等效方向权重 {top['weight_pct']:.1f}%", "plan_constraint": "先判断是否为同一底层因子的重复表达。", "severity": "high", "status": "active"})
    if by_theme and float(by_theme[0]["weight_pct"]) >= 50:
        top = by_theme[0]
        risks.append({"exposure": top["label"], "risk_issue": f"最大主题等效方向权重 {top['weight_pct']:.1f}%", "plan_constraint": "主题冲击会同时作用于多只持仓。", "severity": "high", "status": "active"})
    leveraged = next((row for row in by_product if row["label"] == "每日杠杆 ETF"), None)
    if leveraged and float(leveraged["weight_pct"]) >= 20:
        risks.append({"exposure": "每日杠杆 ETF", "risk_issue": f"等效方向权重 {leveraged['weight_pct']:.1f}%", "plan_constraint": "路径依赖和隔夜跳空需独立管理。", "severity": "high", "status": "active"})
    if reconciliation != "reconciled":
        risks.append({"exposure": "跨券商对账", "risk_issue": "当前为工作视图，来源尚未确认合并。", "plan_constraint": "不得把缺失来源解释为空仓。", "severity": "medium", "status": "watch"})
    if unmapped_count:
        risks.append({"exposure": "主题映射", "risk_issue": f"{unmapped_count} 个持仓尚未完成主题映射。", "plan_constraint": "主题集中度可能被低估。", "severity": "medium", "status": "watch"})
    return risks[:4]


def build_portfolio_panel(
    rows: Iterable[Mapping[str, str]],
    *,
    as_of: str,
    reconciliation: str = "unreconciled",
    excluded_symbols: Iterable[str] = (),
    fundamentals: Mapping[str, Any] | None = None,
    privacy: str = "private",
) -> dict[str, Any]:
    if reconciliation not in {"reconciled", "unreconciled"}:
        raise PortfolioPanelError("reconciliation_invalid")
    _timestamp(as_of)
    positions, exclusions = _positions(rows, {normalize_symbol(item) for item in excluded_symbols})
    currencies = {str(row["currency"]).upper() for row in positions}
    if len(currencies) > 1:
        raise PortfolioPanelError("snapshot_currency_mixed")
    if currencies and currencies != {"USD"}:
        raise PortfolioPanelError("snapshot_currency_unsupported")
    non_cash = [row for row in positions if not row["is_cash"]]
    cash = sum(float(row["market_value"]) for row in positions if row["is_cash"])
    market = sum(float(row["market_value"]) for row in non_cash)
    net_delta = sum(float(row["delta_exposure"]) for row in non_cash)
    gross_delta = sum(abs(float(row["delta_exposure"])) for row in non_cash)
    gross_notional = sum(abs(float(row["notional_exposure"])) for row in non_cash)
    capital = market + cash
    by_symbol = _aggregate(non_cash, "underlying", gross_delta, "比较直接市值与杠杆调整后的等效方向敞口。")
    by_theme = _aggregate(non_cash, "theme", gross_delta, "观察共同主题因子。")
    for row in by_theme:
        row["label"] = THEME_LABELS.get(str(row["label"]), str(row["label"]).replace("_", " "))
    by_product = _aggregate(non_cash, "product", gross_delta, "区分现金产品与路径依赖产品。")
    by_broker = _aggregate(non_cash, "broker", gross_delta, "仅显示来源覆盖，不显示账户标识。")
    brokers = sorted({str(row["broker"]) for row in positions})
    if reconciliation == "reconciled" and len(brokers) == 1:
        scope_label = f"{brokers[0]} 单一来源视图"
    elif reconciliation == "reconciled":
        scope_label = "已对账的跨券商视图"
    else:
        scope_label = "未对账的跨券商工作视图"
    unmapped_count = sum(1 for row in non_cash if row["theme"] == "unmapped")
    risk_ledger = _risk_ledger(by_symbol, by_theme, by_product, reconciliation, unmapped_count)
    stresses = _stress_scenarios(non_cash, by_theme, capital)
    high_risks = [row["exposure"] for row in risk_ledger if row["severity"] == "high"]
    posture = "集中风险偏高" if high_risks else "风险结构暂未触发高等级提示"
    decision = "；".join(high_risks) if high_risks else "继续观察来源完整性与集中度变化"
    complete = 4 - int(reconciliation != "reconciled") - int(unmapped_count > 0)
    fundamental_items: list[dict[str, Any]] = []
    source = "not_provided"
    fundamentals_as_of = ""
    if isinstance(fundamentals, Mapping):
        source = str(fundamentals.get("source") or "not_provided")
        fundamentals_as_of = str(fundamentals.get("as_of") or "")
        exposure_by_underlying = {str(row["label"]): row for row in by_symbol}
        for raw_item in fundamentals.get("items", []):
            if not isinstance(raw_item, Mapping):
                continue
            symbol = str(raw_item.get("symbol") or "").upper()
            exposure = exposure_by_underlying.get(symbol)
            if not exposure:
                continue
            item = dict(raw_item)
            item["source_holdings"] = list(exposure.get("affected_holdings") or [])
            fundamental_items.append(item)
    panel = {
        "schema_version": SCHEMA_VERSION,
        "decision_cutoff": as_of,
        "privacy": privacy,
        "coverage": {"required_complete": complete, "required_total": 4},
        "payload": {
            "totals": {
                "gross_market_value": market,
                "gross_delta_exposure": gross_delta,
                "net_delta_exposure": net_delta,
                "gross_notional_exposure": gross_notional,
                "cash_context": cash,
                "currency": "USD",
                "scope_label": scope_label,
            },
            "aggregations": {"by_symbol": by_symbol, "by_theme": by_theme, "by_product": by_product, "by_broker": by_broker},
            "stress_scenarios": stresses,
            "source_coverage": [
                {"source_alias": broker, "reconciliation_status": reconciliation, "as_of": as_of}
                for broker in brokers
            ],
            "exclusions": [{"symbol": symbol} for symbol in exclusions],
            "risk_ledger": risk_ledger,
            "fundamentals": {
                "source": source,
                "as_of": fundamentals_as_of,
                "items": fundamental_items,
            },
            "posture": {"label": posture},
            "decision": decision,
        },
    }
    validate_portfolio_panel(panel)
    return panel


def validate_portfolio_panel(panel: Mapping[str, Any]) -> None:
    if panel.get("schema_version") != SCHEMA_VERSION or panel.get("privacy") not in {"private", "public_fixture"}:
        raise PortfolioPanelError("panel_schema_invalid")
    _timestamp(str(panel.get("decision_cutoff") or ""))
    payload = panel.get("payload")
    if not isinstance(payload, Mapping):
        raise PortfolioPanelError("panel_payload_invalid")
    required = {"totals", "aggregations", "stress_scenarios", "source_coverage", "exclusions", "risk_ledger", "fundamentals", "posture", "decision"}
    if set(payload) != required:
        raise PortfolioPanelError("panel_payload_invalid")
    fundamentals = payload.get("fundamentals")
    if not isinstance(fundamentals, Mapping) or not isinstance(fundamentals.get("items"), list):
        raise PortfolioPanelError("panel_fundamentals_invalid")
    serialized = json.dumps(panel, ensure_ascii=False).lower()
    if "account_id" in serialized or "account_number" in serialized:
        raise PortfolioPanelError("panel_privacy_invalid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="append", required=True, help="Standard portfolio_snapshot.csv; repeat for each source")
    parser.add_argument("--output", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--reconciliation", choices=("reconciled", "unreconciled"), default="unreconciled")
    parser.add_argument("--exclude-symbol", action="append", default=[])
    parser.add_argument("--fundamentals", help="Saved output from portfolio_fundamentals_adapter.py")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = [row for path in args.snapshot for row in load_snapshot(Path(path).expanduser())]
    fundamentals = None
    if args.fundamentals:
        try:
            fundamentals = json.loads(Path(args.fundamentals).expanduser().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PortfolioPanelError("panel_fundamentals_invalid") from error
    panel = build_portfolio_panel(
        rows,
        as_of=args.as_of,
        reconciliation=args.reconciliation,
        excluded_symbols=args.exclude_symbol,
        fundamentals=fundamentals,
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(panel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Portfolio panel payload written: {output}")
    print("No live broker reads; consumed normalized portfolio snapshots only.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
