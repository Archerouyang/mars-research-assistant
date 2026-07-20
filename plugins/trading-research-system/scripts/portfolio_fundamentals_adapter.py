#!/usr/bin/env python3
"""Build underlying fundamentals for a Portfolio Risk panel.

The adapter consumes JSON already saved from read-only Longbridge CLI commands.
It never invokes Longbridge and never performs broker or order actions.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"


class PortfolioFundamentalsError(ValueError):
    """Fail-closed fundamentals input error with a stable public code."""


def _number(value: Any) -> float | None:
    try:
        cleaned = str(value or "").strip().replace(",", "").replace("$", "").replace("%", "")
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _epoch(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PortfolioFundamentalsError("fundamentals_source_invalid") from error


def _forecast_intervals(payload: Any) -> list[dict[str, float | int]]:
    items = payload.get("items", []) if isinstance(payload, Mapping) else []
    intervals: list[dict[str, float | int]] = []
    for row in items if isinstance(items, list) else []:
        if not isinstance(row, Mapping):
            continue
        eps = _number(row.get("forecast_eps_mean"))
        start = _epoch(row.get("forecast_start_date"))
        end = _epoch(row.get("forecast_end_date"))
        if eps is not None and eps > 0 and start:
            intervals.append({"start": start, "end": end, "eps": eps})
    return sorted(intervals, key=lambda row: int(row["start"]))


def _eps_at(intervals: list[Mapping[str, float | int]], timestamp: int) -> float | None:
    selected: float | None = None
    for row in intervals:
        start = int(row["start"])
        end = int(row["end"])
        if start <= timestamp and (end == 0 or timestamp <= end):
            selected = float(row["eps"])
    return selected


def _downsample(points: list[dict[str, Any]], maximum: int = 28) -> list[dict[str, Any]]:
    if len(points) <= maximum:
        return points
    step = (len(points) - 1) / (maximum - 1)
    indexes = sorted({round(index * step) for index in range(maximum)})
    return [points[index] for index in indexes]


def _forward_pe_history(kline: Any, forecasts: Any) -> list[dict[str, Any]]:
    intervals = _forecast_intervals(forecasts)
    bars = kline if isinstance(kline, list) else []
    points: list[dict[str, Any]] = []
    for bar in bars:
        if not isinstance(bar, Mapping):
            continue
        timestamp = _epoch(bar.get("time") or bar.get("timestamp"))
        close = _number(bar.get("close"))
        eps = _eps_at(intervals, timestamp)
        if timestamp and close is not None and close > 0 and eps is not None and eps > 0:
            points.append(
                {
                    "date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
                    "value": round(close / eps, 2),
                }
            )
    return _downsample(points)


def _latest_metric(valuation: Any) -> float | None:
    metrics = valuation.get("metrics", {}) if isinstance(valuation, Mapping) else {}
    pe = metrics.get("pe", {}) if isinstance(metrics, Mapping) else {}
    rows = pe.get("list", []) if isinstance(pe, Mapping) else []
    values = [_number(row.get("value")) for row in rows if isinstance(row, Mapping)]
    clean = [value for value in values if value is not None]
    return clean[-1] if clean else None


def _financial_metrics(payload: Any) -> dict[str, float | str | None]:
    rows = payload.get("indicators", []) if isinstance(payload, Mapping) else []
    indexed = {
        str(row.get("field_name")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("field_name")
    }

    def yoy(field: str) -> float | None:
        value = _number(indexed.get(field, {}).get("yoy"))
        return value * 100 if value is not None else None

    def value(field: str) -> float | None:
        return _number(indexed.get(field, {}).get("indicator_value"))

    return {
        "report": str(payload.get("report") or "") if isinstance(payload, Mapping) else "",
        "revenue_yoy_pct": yoy("operating_revenue"),
        "net_income_yoy_pct": yoy("net_profit"),
        "net_margin_pct": value("net_profit_margin"),
        "roe_pct": value("roe"),
    }


def _statement_metrics(payload: Any) -> dict[str, Any]:
    rows = payload.get("list", []) if isinstance(payload, Mapping) else []
    reports = [row for row in rows if isinstance(row, Mapping)]
    if not reports:
        return {
            "report": "",
            "report_date": "",
            "revenue_yoy_pct": None,
            "net_income_yoy_pct": None,
            "gross_margin_pct": None,
            "net_margin_pct": None,
            "margin_history": [],
        }
    latest = max(reports, key=lambda row: (str(row.get("rpt_date") or ""), str(row.get("fp_end") or "")))
    fields = {
        str(row.get("field")): row
        for row in latest.get("fields", [])
        if isinstance(row, Mapping) and row.get("field")
    }

    def field(*names: str) -> Mapping[str, Any]:
        return next((fields[name] for name in names if name in fields), {})

    def yoy(*names: str) -> float | None:
        value = _number(field(*names).get("yoy"))
        return value * 100 if value is not None else None

    revenue = _number(field("total_rev", "rev").get("value"))
    gross_profit = _number(field("gp").get("value"))
    net_income = _number(field("ni_company", "ni", "earning_co").get("value"))
    history: list[dict[str, Any]] = []
    for report in sorted(reports, key=lambda row: str(row.get("fp_end") or "")):
        report_fields = {
            str(row.get("field")): row
            for row in report.get("fields", [])
            if isinstance(row, Mapping) and row.get("field")
        }
        report_revenue = _number((report_fields.get("total_rev") or report_fields.get("rev") or {}).get("value"))
        report_gross = _number((report_fields.get("gp") or {}).get("value"))
        report_net = _number(
            (
                report_fields.get("ni_company")
                or report_fields.get("ni")
                or report_fields.get("earning_co")
                or {}
            ).get("value")
        )
        if report_revenue:
            history.append(
                {
                    "date": str(report.get("fp_end") or report.get("rpt_date") or ""),
                    "gross_margin_pct": round(report_gross / report_revenue * 100, 2) if report_gross is not None else None,
                    "net_margin_pct": round(report_net / report_revenue * 100, 2) if report_net is not None else None,
                }
            )
    return {
        "report": str(latest.get("report_txt") or latest.get("fp_end") or ""),
        "report_date": str(latest.get("rpt_date") or ""),
        "revenue_yoy_pct": yoy("total_rev", "rev"),
        "net_income_yoy_pct": yoy("ni_company", "ni", "earning_co"),
        "gross_margin_pct": gross_profit / revenue * 100 if gross_profit is not None and revenue else None,
        "net_margin_pct": net_income / revenue * 100 if net_income is not None and revenue else None,
        "margin_history": history[-8:],
    }


def _short_interest_metrics(payload: Any, as_of: str, maximum_age_days: int = 45) -> dict[str, Any]:
    rows = payload.get("data", []) if isinstance(payload, Mapping) else []
    records = [row for row in rows if isinstance(row, Mapping) and _epoch(row.get("timestamp"))]
    if not records:
        return {
            "short_interest_pct": None,
            "short_days_to_cover": None,
            "short_interest_as_of": "",
            "short_interest_status": "missing",
            "short_interest_history": [],
        }
    latest = max(records, key=lambda row: _epoch(row.get("timestamp")))
    timestamp = _epoch(latest.get("timestamp"))
    cutoff = _epoch(as_of)
    age_days = (cutoff - timestamp) / 86400 if cutoff and timestamp else maximum_age_days + 1
    fresh = -1 <= age_days <= maximum_age_days
    return {
        "short_interest_pct": (_number(latest.get("rate")) or 0) * 100 if fresh else None,
        "short_days_to_cover": _number(latest.get("days_to_cover")) if fresh else None,
        "short_interest_as_of": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
        "short_interest_status": "available" if fresh else "stale",
        "short_interest_history": [
            {
                "date": datetime.fromtimestamp(_epoch(row.get("timestamp")), timezone.utc).date().isoformat(),
                "value": round((_number(row.get("rate")) or 0) * 100, 2),
            }
            for row in sorted(records, key=lambda row: _epoch(row.get("timestamp")))[-12:]
        ] if fresh else [],
    }


def _short_trade_metrics(payload: Any) -> dict[str, Any]:
    rows = payload.get("data", []) if isinstance(payload, Mapping) else payload if isinstance(payload, list) else []
    records = sorted(
        [row for row in rows if isinstance(row, Mapping) and _epoch(row.get("timestamp"))],
        key=lambda row: _epoch(row.get("timestamp")),
    )
    if not records:
        return {
            "short_volume_pct": None,
            "short_volume_5d_avg_pct": None,
            "short_volume_as_of": "",
            "short_volume_history": [],
        }
    latest = records[-1]
    recent = records[-5:]
    recent_rates = [(_number(row.get("rate")) or 0) * 100 for row in recent]
    return {
        "short_volume_pct": (_number(latest.get("rate")) or 0) * 100,
        "short_volume_5d_avg_pct": statistics.fmean(recent_rates) if recent_rates else None,
        "short_volume_as_of": datetime.fromtimestamp(_epoch(latest.get("timestamp")), timezone.utc).date().isoformat(),
        "short_volume_history": _downsample(
            [
                {
                    "date": datetime.fromtimestamp(_epoch(row.get("timestamp")), timezone.utc).date().isoformat(),
                    "value": round((_number(row.get("rate")) or 0) * 100, 2),
                }
                for row in records
            ],
            maximum=30,
        ),
    }


def _option_positioning_metrics(payload: Any) -> dict[str, Any]:
    rows = payload.get("stats", []) if isinstance(payload, Mapping) else payload if isinstance(payload, list) else []
    records = sorted(
        [row for row in rows if isinstance(row, Mapping) and _epoch(row.get("timestamp"))],
        key=lambda row: _epoch(row.get("timestamp")),
    )
    if not records:
        return {
            "put_call_volume_ratio": None,
            "put_call_open_interest_ratio": None,
            "put_call_volume_20d_avg": None,
            "option_positioning_as_of": "",
            "put_call_volume_history": [],
        }
    latest = records[-1]
    recent_values = [
        value
        for value in (_number(row.get("put_call_volume_ratio")) for row in records[-20:])
        if value is not None
    ]
    return {
        "put_call_volume_ratio": _number(latest.get("put_call_volume_ratio")),
        "put_call_open_interest_ratio": _number(latest.get("put_call_open_interest_ratio")),
        "put_call_volume_20d_avg": statistics.fmean(recent_values) if recent_values else None,
        "option_positioning_as_of": datetime.fromtimestamp(_epoch(latest.get("timestamp")), timezone.utc).date().isoformat(),
        "put_call_volume_history": _downsample(
            [
                {
                    "date": datetime.fromtimestamp(_epoch(row.get("timestamp")), timezone.utc).date().isoformat(),
                    "value": round(value, 3),
                }
                for row in records
                if (value := _number(row.get("put_call_volume_ratio"))) is not None
            ],
            maximum=30,
        ),
    }


def _realized_volatility_metrics(kline: Any, iv30_pct: float | None) -> dict[str, float | None]:
    bars = kline if isinstance(kline, list) else []
    closes = [value for value in (_number(row.get("close")) for row in bars if isinstance(row, Mapping)) if value and value > 0]
    returns = [math.log(current / prior) for prior, current in zip(closes[-22:-1], closes[-21:]) if prior > 0]
    hv20 = statistics.stdev(returns) * math.sqrt(252) * 100 if len(returns) >= 20 else None
    return {
        "hv20_pct": hv20,
        "iv_hv_ratio": iv30_pct / hv20 if iv30_pct is not None and hv20 else None,
        "iv_hv_spread_pct": iv30_pct - hv20 if iv30_pct is not None and hv20 is not None else None,
        "implied_move_30d_pct": iv30_pct * math.sqrt(30 / 365) if iv30_pct is not None else None,
    }


def _implied_volatility_metrics(payload: Any, as_of: str, maximum_age_days: int = 7) -> dict[str, float | str | None]:
    data = payload.get("data", {}) if isinstance(payload, Mapping) else {}
    timestamp_text = str(payload.get("timestamp") or "") if isinstance(payload, Mapping) else ""
    timestamp = _epoch(timestamp_text)
    cutoff = _epoch(as_of)
    age_days = (cutoff - timestamp) / 86400 if cutoff and timestamp else maximum_age_days + 1
    iv30 = _number(data.get("iv30")) if isinstance(data, Mapping) else None
    fresh = iv30 is not None and -1 <= age_days <= maximum_age_days
    return {
        "iv30_pct": iv30 if fresh else None,
        "iv30_as_of": timestamp_text,
        "iv30_status": "available" if fresh else ("stale" if iv30 is not None else "missing"),
    }


def _revision(intervals: list[Mapping[str, float | int]], latest_timestamp: int, days: int = 30) -> float | None:
    latest = _eps_at(intervals, latest_timestamp)
    prior = _eps_at(intervals, latest_timestamp - days * 86400)
    if latest is None or prior is None or prior == 0:
        return None
    return (latest / prior - 1) * 100


def build_item(config: Mapping[str, Any], *, as_of: str = "") -> dict[str, Any]:
    symbol = str(config.get("symbol") or "").upper()
    if not symbol:
        raise PortfolioFundamentalsError("fundamentals_symbol_missing")
    entity_type = str(config.get("entity_type") or "company")
    kline = _read_json(str(config["kline_json"]))
    forecasts = _read_json(str(config["forecast_json"])) if config.get("forecast_json") else {"items": []}
    valuation = _read_json(str(config["valuation_json"])) if config.get("valuation_json") else {}
    financial = _read_json(str(config["financial_json"])) if config.get("financial_json") else {}
    statement = _read_json(str(config["income_statement_json"])) if config.get("income_statement_json") else {}
    short_interest = _read_json(str(config["short_interest_json"])) if config.get("short_interest_json") else {}
    short_trades = _read_json(str(config["short_trades_json"])) if config.get("short_trades_json") else {}
    option_volume = _read_json(str(config["option_volume_json"])) if config.get("option_volume_json") else {}
    implied_volatility = _read_json(str(config["implied_volatility_json"])) if config.get("implied_volatility_json") else {}
    bars = kline if isinstance(kline, list) else []
    last_bar = bars[-1] if bars and isinstance(bars[-1], Mapping) else {}
    latest_timestamp = _epoch(last_bar.get("time") or last_bar.get("timestamp"))
    price = _number(last_bar.get("close"))
    intervals = _forecast_intervals(forecasts)
    forward_eps = _eps_at(intervals, latest_timestamp)
    history = _forward_pe_history(kline, forecasts)
    status = "available" if entity_type == "company" and history else "partial"
    if entity_type != "company":
        status = "proxy"
    mapping_note = str(config.get("mapping_note") or "直接持有底层")
    metrics = _financial_metrics(financial) if entity_type == "company" else {
        "report": "",
        "revenue_yoy_pct": None,
        "net_income_yoy_pct": None,
        "net_margin_pct": None,
        "roe_pct": None,
    }
    metrics["roe_report"] = metrics["report"]
    statement_metrics = _statement_metrics(statement) if entity_type == "company" else _statement_metrics({})
    if statement_metrics["report"]:
        metrics.update(
            {
                "report": statement_metrics["report"],
                "report_date": statement_metrics["report_date"],
                "revenue_yoy_pct": statement_metrics["revenue_yoy_pct"],
                "net_income_yoy_pct": statement_metrics["net_income_yoy_pct"],
                "gross_margin_pct": statement_metrics["gross_margin_pct"],
                "net_margin_pct": statement_metrics["net_margin_pct"],
                "margin_history": statement_metrics["margin_history"],
            }
        )
    else:
        metrics.update({"report_date": "", "gross_margin_pct": None, "margin_history": []})
    metrics.update(_short_interest_metrics(short_interest, as_of))
    metrics.update(_short_trade_metrics(short_trades))
    metrics.update(_option_positioning_metrics(option_volume))
    volatility_metrics = _implied_volatility_metrics(implied_volatility, as_of)
    metrics.update(volatility_metrics)
    metrics.update(_realized_volatility_metrics(kline, volatility_metrics.get("iv30_pct")))
    metrics.update(
        {
            "price": price,
            "current_pe": _latest_metric(valuation),
            "forward_pe": price / forward_eps if price is not None and forward_eps else None,
            "forward_eps": forward_eps,
            "eps_revision_30d_pct": _revision(intervals, latest_timestamp),
        }
    )
    return {
        "symbol": symbol,
        "display_name": str(config.get("display_name") or symbol),
        "entity_type": entity_type,
        "source_holdings": [str(item).upper() for item in config.get("source_holdings", [])],
        "mapping_note": mapping_note,
        "status": status,
        "metrics": metrics,
        "forward_pe_history": history,
        "note": (
            "Forward P/E 由同期复权收盘价除以当时 Longbridge 一致预期 EPS 推导。"
            if history
            else "缺少可匹配的一致预期 EPS，未生成 Forward P/E 曲线。"
        ),
    }


def build_fundamentals(manifest: Mapping[str, Any]) -> dict[str, Any]:
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise PortfolioFundamentalsError("fundamentals_items_missing")
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": str(manifest.get("as_of") or ""),
        "source": str(manifest.get("source") or "Longbridge CLI"),
        "items": [build_item(item, as_of=str(manifest.get("as_of") or "")) for item in items if isinstance(item, Mapping)],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = _read_json(args.manifest)
    if not isinstance(manifest, Mapping):
        raise PortfolioFundamentalsError("fundamentals_manifest_invalid")
    payload = build_fundamentals(manifest)
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Portfolio fundamentals written: {output}")
    print("No live broker reads; consumed saved Longbridge CLI JSON only.")
    print("No order actions; this adapter never creates, modifies, cancels, or submits orders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
