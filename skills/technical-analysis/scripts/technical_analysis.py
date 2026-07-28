#!/usr/bin/env python3
"""Build deterministic technical-analysis artifacts from an offline OHLCV fixture."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from html import escape
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
from xml.etree import ElementTree
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


VISIBLE_BARS = 120
SMA_WINDOWS = (20, 50, 200)
MINIMUM_HISTORY_BARS = VISIBLE_BARS + max(SMA_WINDOWS) - 1
SWING_RADIUS = 2
ATR_WINDOW = 14
ATR_CLUSTER_RATIO = 0.5
ADJUSTED_METHODS = {
    "adjusted",
    "dividend-adjusted",
    "split-adjusted",
    "total-return-adjusted",
}


class TechnicalAnalysisError(ValueError):
    """Reject an invalid request or artifact operation."""


class DataQualityError(ValueError):
    """Describe a blocking data gap without producing technical evidence."""


@dataclass(frozen=True)
class Source:
    as_of: str
    status: str

    @property
    def label(self) -> str:
        return "yfinance EOD（非官方 best-effort）"


@dataclass(frozen=True)
class QualifiedHistory:
    timeframe: str
    timezone: str
    adjustment: str
    bars: list[dict[str, int | float | str]]
    stripped_incomplete_bar: bool


@dataclass(frozen=True)
class Swing:
    side: str
    price: float
    anchor_date: str
    confirmed_index: int


def _required_text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TechnicalAnalysisError(f"{context} requires text")
    return value.strip()


def _data_text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataQualityError(f"{context} requires text")
    return value.strip()


def _timestamp(value: object, context: str) -> datetime:
    text = _required_text(value, context)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise DataQualityError(f"{context} requires an ISO 8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataQualityError(f"{context} requires a timezone-aware timestamp")
    return parsed


def _source(value: object) -> Source:
    if not isinstance(value, dict):
        raise TechnicalAnalysisError("provider requires an object")
    if _required_text(value.get("name"), "provider") != "yfinance EOD":
        raise TechnicalAnalysisError("provider must be yfinance EOD")
    if _required_text(value.get("kind"), "provider") != "public_best_effort":
        raise TechnicalAnalysisError("provider must be yfinance public best-effort")
    status = _required_text(value.get("status", "available"), "provider")
    if status not in {"available", "rate_limited", "unavailable"}:
        raise TechnicalAnalysisError(
            "provider status must be available, rate_limited, or unavailable"
        )
    as_of = _required_text(value.get("as_of"), "provider")
    _timestamp(as_of, "provider as_of")
    return Source(as_of=as_of, status=status)


def _number(value: object, field: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataQualityError(f"OHLCV bar requires numeric {field}")
    if not math.isfinite(value):
        raise DataQualityError(f"OHLCV bar requires finite {field}")
    return value


def _normalize_bar(value: object) -> dict[str, int | float | str]:
    if not isinstance(value, dict):
        raise DataQualityError("OHLCV bar must be an object")
    timestamp = _data_text(value.get("timestamp"), "OHLCV bar")
    _timestamp(timestamp, "OHLCV bar")
    open_price = _number(value.get("open"), "open")
    high_price = _number(value.get("high"), "high")
    low_price = _number(value.get("low"), "low")
    close_price = _number(value.get("close"), "close")
    volume = _number(value.get("volume"), "volume")
    if volume <= 0:
        raise DataQualityError("OHLCV bar requires positive volume")
    if not low_price <= min(open_price, close_price) <= max(
        open_price, close_price
    ) <= high_price:
        raise DataQualityError("OHLCV bar has inconsistent price bounds")
    return {
        "timestamp": timestamp,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume,
    }


def _qualified_history(value: object, requested_timeframe: str) -> QualifiedHistory:
    if not isinstance(value, dict):
        raise DataQualityError("OHLCV requires an object")
    timeframe = _data_text(value.get("timeframe"), "OHLCV")
    if timeframe != requested_timeframe:
        raise DataQualityError("OHLCV timeframe does not match requested timeframe")
    if timeframe != "1D":
        raise DataQualityError("technical analysis currently requires 1D OHLCV")
    if value.get("time_range_suitable") is not True:
        raise DataQualityError(
            "OHLCV time range is not suitable for the requested analysis"
        )
    _data_text(value.get("time_range"), "OHLCV")
    timezone = _data_text(value.get("timezone"), "OHLCV")
    adjustment = _data_text(value.get("adjustment"), "OHLCV")
    if adjustment not in ADJUSTED_METHODS:
        raise DataQualityError("OHLCV adjustment must be adjusted")
    raw_bars = value.get("bars")
    if not isinstance(raw_bars, list):
        raise DataQualityError("OHLCV bars require a list")

    stripped_incomplete_bar = False
    if any(
        isinstance(bar, dict) and bar.get("complete") is False
        for bar in raw_bars[:-1]
    ):
        raise DataQualityError("only the latest OHLCV bar may be incomplete")
    if (
        raw_bars
        and isinstance(raw_bars[-1], dict)
        and raw_bars[-1].get("complete") is False
    ):
        raw_bars = raw_bars[:-1]
        stripped_incomplete_bar = True

    bars = [_normalize_bar(bar) for bar in raw_bars]
    timestamps = [str(bar["timestamp"]) for bar in bars]
    parsed_timestamps = [
        _timestamp(timestamp, "OHLCV bar") for timestamp in timestamps
    ]
    if any(
        previous >= current
        for previous, current in zip(parsed_timestamps, parsed_timestamps[1:])
    ):
        raise DataQualityError("OHLCV timestamps must be strictly increasing")

    coverage_start = _data_text(value.get("coverage_start"), "OHLCV")
    coverage_end = _data_text(value.get("coverage_end"), "OHLCV")
    try:
        coverage_start_date = date.fromisoformat(coverage_start)
        coverage_end_date = date.fromisoformat(coverage_end)
    except ValueError as error:
        raise DataQualityError("OHLCV coverage requires ISO 8601 dates") from error
    if coverage_start_date > coverage_end_date:
        raise DataQualityError("OHLCV coverage start must not follow coverage end")
    if bars and (
        timestamps[0][:10] != coverage_start
        or timestamps[-1][:10] != coverage_end
    ):
        raise DataQualityError("OHLCV coverage must exactly match actual bars")
    if len(bars) < MINIMUM_HISTORY_BARS:
        missing = MINIMUM_HISTORY_BARS - len(bars)
        raise DataQualityError(
            f"日线 OHLCV 缺少 {missing} 根已完成日线"
            f"（需要至少 {MINIMUM_HISTORY_BARS} 根，实际 {len(bars)} 根）。"
        )
    return QualifiedHistory(
        timeframe=timeframe,
        timezone=timezone,
        adjustment=adjustment,
        bars=bars,
        stripped_incomplete_bar=stripped_incomplete_bar,
    )


def _moving_average(values: list[float], window: int) -> list[float | None]:
    averages: list[float | None] = []
    rolling_total = 0.0
    for index, value in enumerate(values):
        rolling_total += value
        if index >= window:
            rolling_total -= values[index - window]
        average = rolling_total / window if index >= window - 1 else None
        averages.append(round(average, 6) if average is not None else None)
    return averages


def _true_ranges(bars: list[dict[str, int | float | str]]) -> list[float]:
    ranges: list[float] = []
    for index, bar in enumerate(bars):
        high = float(bar["high"])
        low = float(bar["low"])
        if index == 0:
            value = high - low
        else:
            previous_close = float(bars[index - 1]["close"])
            value = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
        ranges.append(round(value, 6))
    return ranges


def _atr14(bars: list[dict[str, int | float | str]]) -> list[float | None]:
    return _moving_average(_true_ranges(bars), ATR_WINDOW)


def _confirmed_swings(
    bars: list[dict[str, int | float | str]],
) -> list[Swing]:
    swings: list[Swing] = []
    start = max(SWING_RADIUS, len(bars) - VISIBLE_BARS)
    stop = len(bars) - SWING_RADIUS
    for index in range(start, stop):
        low = float(bars[index]["low"])
        high = float(bars[index]["high"])
        neighbors = bars[index - SWING_RADIUS : index] + bars[
            index + 1 : index + SWING_RADIUS + 1
        ]
        anchor_date = str(bars[index]["timestamp"])[:10]
        confirmed_index = index + SWING_RADIUS
        if all(low < float(neighbor["low"]) for neighbor in neighbors):
            swings.append(
                Swing("support", low, anchor_date, confirmed_index)
            )
        if all(high > float(neighbor["high"]) for neighbor in neighbors):
            swings.append(
                Swing("resistance", high, anchor_date, confirmed_index)
            )
    return swings


def _cluster_levels(
    swings: list[Swing],
    side: str,
    latest_close: float,
    latest_atr: float,
) -> list[dict[str, Any]]:
    candidates = [
        swing
        for swing in swings
        if swing.side == side
        and (
            (side == "support" and swing.price <= latest_close)
            or (side == "resistance" and swing.price >= latest_close)
        )
    ]
    tolerance = round(latest_atr * ATR_CLUSTER_RATIO, 6)
    clusters: list[list[Swing]] = []
    for candidate in sorted(candidates, key=lambda item: (item.price, item.anchor_date)):
        matching = next(
            (
                cluster
                for cluster in clusters
                if abs(
                    candidate.price
                    - sum(item.price for item in cluster) / len(cluster)
                )
                <= tolerance
            ),
            None,
        )
        if matching is None:
            clusters.append([candidate])
        else:
            matching.append(candidate)

    levels: list[dict[str, Any]] = []
    for cluster in clusters:
        price = round(sum(item.price for item in cluster) / len(cluster), 6)
        levels.append(
            {
                "side": side,
                "method": "confirmed_swing_atr14_cluster",
                "lookback": VISIBLE_BARS,
                "anchor_dates": sorted(item.anchor_date for item in cluster),
                "touches": len(cluster),
                "price": price,
                "_confirmed_index": max(item.confirmed_index for item in cluster),
                "_distance": round(abs(price - latest_close), 6),
            }
        )
    levels.sort(
        key=lambda level: (
            -int(level["touches"]),
            -int(level["_confirmed_index"]),
            float(level["_distance"]),
            float(level["price"]),
        )
    )
    return levels[:2]


def _fallback_level(
    bars: list[dict[str, int | float | str]], side: str
) -> dict[str, Any]:
    visible = bars[-VISIBLE_BARS:]
    field = "low" if side == "support" else "high"
    selected = (
        min(visible, key=lambda bar: (float(bar[field]), str(bar["timestamp"])))
        if side == "support"
        else max(visible, key=lambda bar: (float(bar[field]), str(bar["timestamp"])))
    )
    return {
        "side": side,
        "method": "120d_extreme_fallback",
        "lookback": VISIBLE_BARS,
        "anchor_dates": [str(selected["timestamp"])[:10]],
        "touches": 1,
        "price": round(float(selected[field]), 6),
    }


def _key_levels(
    bars: list[dict[str, int | float | str]], latest_atr: float
) -> list[dict[str, Any]]:
    latest_close = float(bars[-1]["close"])
    swings = _confirmed_swings(bars)
    levels: list[dict[str, Any]] = []
    for side in ("support", "resistance"):
        ranked = _cluster_levels(swings, side, latest_close, latest_atr)
        if not ranked:
            ranked = [_fallback_level(bars, side)]
        for level in ranked:
            level.pop("_confirmed_index", None)
            level.pop("_distance", None)
        levels.extend(ranked)
    return levels


def _market_context(
    value: object, research_as_of: str, target_timezone: str
) -> dict[str, Any]:
    if value is None:
        return {"status": "not_provided"}
    if not isinstance(value, dict):
        return {"status": "invalid", "reason": "市场背景不是标准工件。"}
    try:
        status = _required_text(value.get("status", "available"), "market context")
    except TechnicalAnalysisError as error:
        return {"status": "invalid", "reason": str(error)}
    if status != "available":
        reason = value.get("reason")
        return {
            "status": "unavailable",
            "reason": (
                reason.strip()
                if isinstance(reason, str) and reason.strip()
                else f"市场背景状态：{status}"
            ),
        }
    try:
        as_of = _required_text(value.get("as_of"), "market context")
        source = _required_text(value.get("source"), "market context")
        timezone_name = _required_text(
            value.get("timezone"), "market context"
        )
        regime = _required_text(value.get("regime"), "market context")
        summary = _required_text(value.get("summary"), "market context")
        context_time = _timestamp(as_of, "market context as_of")
        research_time = _timestamp(research_as_of, "research as_of")
        target_zone = ZoneInfo(target_timezone)
    except (
        TechnicalAnalysisError,
        DataQualityError,
        ZoneInfoNotFoundError,
    ) as error:
        return {"status": "invalid", "reason": str(error)}
    if timezone_name != target_timezone:
        return {
            "status": "invalid",
            "reason": "市场背景时区与目标市场时区不一致。",
        }
    same_run = value.get("same_run") is True
    age_hours = round(
        (
            research_time.astimezone(target_zone)
            - context_time.astimezone(target_zone)
        ).total_seconds()
        / 3600,
        3,
    )
    if not same_run and (age_hours < 0 or age_hours > 24):
        return {
            "status": "stale",
            "as_of": as_of,
            "source": source,
            "timezone": timezone_name,
            "regime": regime,
            "age_hours": age_hours,
        }
    return {
        "status": "valid",
        "as_of": as_of,
        "source": source,
        "timezone": timezone_name,
        "regime": regime,
        "summary": summary,
        "same_run": same_run,
        "age_hours": max(age_hours, 0),
    }


def _technical_regime(latest: dict[str, float]) -> str:
    close = latest["close"]
    sma20 = latest["sma20"]
    sma50 = latest["sma50"]
    sma200 = latest["sma200"]
    if close > sma20 > sma50 > sma200:
        return "多头"
    if close < sma20 < sma50 < sma200:
        return "空头"
    return "震荡"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _source_attempt_metadata(
    fixture: dict[str, Any], default_attempts: int
) -> tuple[int, bool]:
    attempts = fixture.get("source_attempts", default_attempts)
    if isinstance(attempts, bool) or not isinstance(attempts, int):
        raise TechnicalAnalysisError("source_attempts must be an integer")
    if attempts not in {1, 2}:
        raise TechnicalAnalysisError("source_attempts must be one or two")
    expanded = fixture.get("expanded_window_retry_used", attempts == 2)
    if not isinstance(expanded, bool):
        raise TechnicalAnalysisError(
            "expanded_window_retry_used must be boolean"
        )
    if expanded != (attempts == 2):
        raise TechnicalAnalysisError(
            "expanded_window_retry_used contradicts source_attempts"
        )
    return attempts, expanded


def _build_evidence(
    fixture: dict[str, Any],
    source: Source,
    history: QualifiedHistory,
    retry_count: int,
) -> dict[str, Any]:
    bars = history.bars
    closes = [float(bar["close"]) for bar in bars]
    volumes = [float(bar["volume"]) for bar in bars]
    moving_averages = {
        str(window): _moving_average(closes, window) for window in SMA_WINDOWS
    }
    atr14 = _atr14(bars)
    latest_atr = atr14[-1]
    if latest_atr is None or latest_atr <= 0:
        raise DataQualityError("ATR14 requires positive price ranges")
    latest_sma20 = moving_averages["20"][-1]
    latest_sma50 = moving_averages["50"][-1]
    latest_sma200 = moving_averages["200"][-1]
    if latest_sma20 is None or latest_sma50 is None or latest_sma200 is None:
        raise DataQualityError("latest moving averages require complete values")
    latest: dict[str, float] = {
        "close": round(closes[-1], 6),
        "sma20": latest_sma20,
        "sma50": latest_sma50,
        "sma200": latest_sma200,
        "volume": round(volumes[-1], 6),
        "volume20_average": round(sum(volumes[-20:]) / 20, 6),
        "atr14": round(latest_atr, 6),
    }
    source_attempts, expanded_window_retry_used = _source_attempt_metadata(
        fixture, retry_count + 1
    )
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "status": "qualified",
        "symbol": _required_text(fixture.get("instrument"), "fixture"),
        "source": {
            "provider": "yfinance",
            "label": source.label,
            "classification": "non_official_best_effort",
            "as_of": source.as_of,
            "attempts": source_attempts,
            "expanded_window_retry_used": expanded_window_retry_used,
        },
        "timeframe": history.timeframe,
        "timezone": history.timezone,
        "as_of": source.as_of,
        "research_as_of": _required_text(
            fixture.get("research_as_of"), "fixture"
        ),
        "adjustment": history.adjustment,
        "bars_used": len(bars),
        "visible_bars": VISIBLE_BARS,
        "stripped_incomplete_latest_bar": history.stripped_incomplete_bar,
        "ohlcv": bars,
        "indicators": {
            "sma": moving_averages,
            "atr14": atr14,
            "latest": latest,
        },
        "key_levels": _key_levels(bars, latest_atr),
        "market_context": _market_context(
            fixture.get("market_context"),
            _required_text(fixture.get("research_as_of"), "fixture"),
            history.timezone,
        ),
    }
    evidence["regime"] = _technical_regime(latest)
    technical_identity = {
        key: value for key, value in evidence.items() if key != "market_context"
    }
    digest = sha256(_canonical_json(technical_identity).encode("utf-8")).hexdigest()
    evidence["evidence_id"] = f"sha256:{digest}"
    return evidence


def _format_number(value: float | int) -> str:
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def _nearest_level(
    evidence: dict[str, Any], side: str
) -> dict[str, Any]:
    close = float(evidence["indicators"]["latest"]["close"])
    levels = [
        level for level in evidence["key_levels"] if level["side"] == side
    ]
    return min(levels, key=lambda level: abs(float(level["price"]) - close))


def _analysis_markdown(evidence: dict[str, Any]) -> str:
    latest = evidence["indicators"]["latest"]
    support = _nearest_level(evidence, "support")
    resistance = _nearest_level(evidence, "resistance")
    context = evidence["market_context"]
    lines = [
        f"# 技术面分析：{evidence['symbol']}",
        "",
        f"证据标识：`{evidence['evidence_id']}`",
        f"研究截至：{evidence['research_as_of']}",
        "",
        "## 数据状态",
        "- 状态：合格。",
        "- 数据源：yfinance（非官方、best-effort，唯一官方内置来源）。",
        (
            f"- 来源：{evidence['source']['label']}（as_of："
            f"{evidence['source']['as_of']}）"
        ),
        (
            f"- 已完成日线：{evidence['bars_used']} 根；时区："
            f"{evidence['timezone']}；复权：{evidence['adjustment']}。"
        ),
        (
            "- 同源扩大窗口重试："
            + ("已使用一次。" if evidence["source"]["expanded_window_retry_used"] else "未使用。")
        ),
        "",
        "## 技术结构",
        (
            f"- 当前分类：**{evidence['regime']}**。最新收盘 "
            f"{_format_number(latest['close'])}，SMA20 "
            f"{_format_number(latest['sma20'])}，SMA50 "
            f"{_format_number(latest['sma50'])}，SMA200 "
            f"{_format_number(latest['sma200'])}。"
        ),
        "- 该分类只基于已完成日线与确定性均线次序，不包含基本面或交易指令。",
        "",
        "## 均线与成交量",
        (
            f"- 最新成交量 {_format_number(latest['volume'])}；20 日均量 "
            f"{_format_number(latest['volume20_average'])}；ATR14 "
            f"{_format_number(latest['atr14'])}。"
        ),
        "",
        "## 关键位",
    ]
    for level in evidence["key_levels"]:
        side_label = "支撑" if level["side"] == "support" else "阻力"
        lines.append(
            f"- **{side_label} {_format_number(level['price'])}**："
            f"method={level['method']}；lookback={level['lookback']}；"
            f"anchor_dates={','.join(level['anchor_dates'])}；"
            f"touches={level['touches']}。"
        )
    lines.extend(
        [
            "",
            "## 条件情景与失效",
            (
                f"- **多头情景**：已完成日线收盘站上阻力 "
                f"{_format_number(resistance['price'])}，并维持 SMA20 "
                f"{_format_number(latest['sma20'])} 上方；失效条件为收盘跌破支撑 "
                f"{_format_number(support['price'])}。"
            ),
            (
                f"- **震荡情景**：收盘维持在支撑 "
                f"{_format_number(support['price'])} 与阻力 "
                f"{_format_number(resistance['price'])} 之间；任一侧已完成日线"
                "收盘有效突破后，该情景失效。"
            ),
            (
                f"- **空头情景**：已完成日线收盘跌破支撑 "
                f"{_format_number(support['price'])}，并位于 SMA20 "
                f"{_format_number(latest['sma20'])} 下方；失效条件为收盘重新站上阻力 "
                f"{_format_number(resistance['price'])}。"
            ),
            "",
            "## 市场背景",
        ]
    )
    if context["status"] == "valid":
        lines.append(
            f"- 已纳入背景：{context['summary']}（regime：{context['regime']}；"
            f"来源：{context['source']}；as_of：{context['as_of']}）。"
            "背景只用于解释共振或冲突，"
            "不改变图表、指标或关键位。"
        )
    else:
        reason = {
            "not_provided": "未提供市场背景",
            "stale": "市场背景已超过 24 小时有效期",
            "unavailable": context.get("reason", "市场背景不可用"),
            "invalid": context.get("reason", "市场背景无效"),
        }.get(context["status"], "市场背景不可用")
        lines.append(f"- {reason}；本报告仅基于技术面证据。")
    lines.extend(
        [
            "",
            "## 数据限制",
            "- yfinance 为非官方、best-effort 数据源；本工件不构成实时行情或交易建议。",
        ]
    )
    if evidence["stripped_incomplete_latest_bar"]:
        lines.append("- 已安全剔除一根未完成的最新日线。")
    return "\n".join(lines).rstrip() + "\n"


def _svg_text(value: object) -> str:
    return escape(str(value), quote=True)


def _svg_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _price_y(value: float, lower: float, upper: float, top: float, height: float) -> float:
    return top + (upper - value) * height / (upper - lower)


def _chart_svg(evidence: dict[str, Any]) -> str:
    bars = evidence["ohlcv"]
    visible = bars[-VISIBLE_BARS:]
    first_visible_index = len(bars) - VISIBLE_BARS
    levels = evidence["key_levels"]
    width = 960.0
    chart_left = 66.0
    chart_end = 938.0
    chart_width = chart_end - chart_left
    price_top = 48.0
    price_height = 314.0
    volume_top = 422.0
    volume_height = 88.0
    step = chart_width / VISIBLE_BARS
    body_width = max(2.0, min(5.4, step * 0.62))
    prices = [
        float(bar[field]) for bar in visible for field in ("low", "high")
    ] + [float(level["price"]) for level in levels]
    for window in SMA_WINDOWS:
        prices.extend(
            float(value)
            for value in evidence["indicators"]["sma"][str(window)][
                first_visible_index:
            ]
            if value is not None
        )
    lower = min(prices)
    upper = max(prices)
    padding = max((upper - lower) * 0.06, 1.0)
    lower -= padding
    upper += padding
    maximum_volume = max(float(bar["volume"]) for bar in visible)
    evidence_id = evidence["evidence_id"]

    parts = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560" '
            'width="100%" role="img" aria-label="{} 日线技术面分析图" '
            'data-evidence-id="{}">'
        ).format(_svg_text(evidence["symbol"]), _svg_text(evidence_id)),
        f"<title>{_svg_text(evidence['symbol'])} 日线技术面分析图</title>",
        (
            "<desc>最近 120 根已完成日线、成交量、SMA20、SMA50、SMA200 与"
            f"可追溯关键位；证据标识：{_svg_text(evidence_id)}；"
            f"数据来源：{_svg_text(evidence['source']['label'])}；"
            f"timezone：{_svg_text(evidence['timezone'])}；"
            f"as_of：{_svg_text(evidence['as_of'])}；"
            f"adjustment：{_svg_text(evidence['adjustment'])}；"
            f"bars_used：{evidence['bars_used']}。</desc>"
        ),
        '<rect width="960" height="560" fill="#ffffff"/>',
        (
            '<text x="66" y="22" fill="#111827" font-family="system-ui, sans-serif" '
            f'font-size="14" font-weight="700">{_svg_text(evidence["symbol"])}'
            " · 日线技术面分析</text>"
        ),
        (
            '<text x="938" y="22" text-anchor="end" fill="#374151" '
            'font-family="system-ui, sans-serif" font-size="10">'
            f"{_svg_text(evidence_id)}</text>"
        ),
    ]
    for fraction in range(5):
        y = price_top + price_height * fraction / 4
        price = upper - (upper - lower) * fraction / 4
        parts.extend(
            [
                (
                    f'<line x1="66" y1="{_svg_number(y)}" x2="938" '
                    f'y2="{_svg_number(y)}" stroke="#cbd5e1" stroke-width="1"/>'
                ),
                (
                    f'<text x="58" y="{_svg_number(y)}" text-anchor="end" '
                    'dominant-baseline="middle" fill="#374151" '
                    'font-family="system-ui, sans-serif" font-size="11">'
                    f"{_svg_number(price)}</text>"
                ),
            ]
        )
    for level in levels:
        y = _price_y(float(level["price"]), lower, upper, price_top, price_height)
        label = "支撑" if level["side"] == "support" else "阻力"
        color = "#166534" if level["side"] == "support" else "#9f1239"
        parts.extend(
            [
                (
                    f'<line data-key-level="{label}" '
                    f'data-level-side="{level["side"]}" '
                    f'data-level-method="{level["method"]}" '
                    f'data-level-lookback="{level["lookback"]}" '
                    f'data-level-anchor-dates="{_svg_text(",".join(level["anchor_dates"]))}" '
                    f'data-level-touches="{level["touches"]}" '
                    f'data-level-price="{_svg_number(float(level["price"]))}" '
                    f'x1="66" y1="{_svg_number(y)}" x2="938" y2="{_svg_number(y)}" '
                    f'stroke="{color}" stroke-width="1.4" stroke-dasharray="6 4"/>'
                ),
                (
                    f'<text x="934" y="{_svg_number(y - 3)}" text-anchor="end" '
                    f'fill="{color}" font-family="system-ui, sans-serif" '
                    f'font-size="11">{label} {_svg_number(float(level["price"]))}'
                    f" · {level['method']} · {level['touches']} touches</text>"
                ),
            ]
        )
    styles = {20: "#0057b8", 50: "#6d28d9", 200: "#b91c1c"}
    for legend_index, window in enumerate(SMA_WINDOWS):
        legend_x = 660 + legend_index * 92
        parts.append(
            f'<g data-legend="sma-{window}"><line x1="{legend_x}" y1="397" '
            f'x2="{legend_x + 16}" y2="397" stroke="{styles[window]}" stroke-width="2"/>'
            f'<text x="{legend_x + 20}" y="401" fill="#374151" '
            f'font-family="system-ui, sans-serif" font-size="11">SMA{window}</text></g>'
        )
        points = []
        series = evidence["indicators"]["sma"][str(window)]
        for index in range(first_visible_index, len(bars)):
            average = series[index]
            if average is None:
                continue
            x_point = chart_left + (index - first_visible_index + 0.5) * step
            y_point = _price_y(
                float(average), lower, upper, price_top, price_height
            )
            points.append(f"{_svg_number(x_point)},{_svg_number(y_point)}")
        parts.append(
            f'<polyline data-series="sma-{window}" fill="none" '
            f'stroke="{styles[window]}" stroke-width="1.6" '
            f'points="{" ".join(points)}"/>'
        )
    for index, bar in enumerate(visible, start=1):
        candle_x = chart_left + (index - 0.5) * step
        open_price = float(bar["open"])
        close_price = float(bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])
        color = "#047857" if close_price >= open_price else "#be123c"
        wick_top = _price_y(high, lower, upper, price_top, price_height)
        wick_bottom = _price_y(low, lower, upper, price_top, price_height)
        body_top = _price_y(
            max(open_price, close_price), lower, upper, price_top, price_height
        )
        body_bottom = _price_y(
            min(open_price, close_price), lower, upper, price_top, price_height
        )
        bar_volume_height = float(bar["volume"]) * volume_height / maximum_volume
        parts.extend(
            [
                (
                    f'<line x1="{_svg_number(candle_x)}" y1="{_svg_number(wick_top)}" '
                    f'x2="{_svg_number(candle_x)}" y2="{_svg_number(wick_bottom)}" '
                    f'stroke="{color}" stroke-width="1"/>'
                ),
                (
                    f'<rect data-candle="{index}" x="{_svg_number(candle_x - body_width / 2)}" '
                    f'y="{_svg_number(body_top)}" width="{_svg_number(body_width)}" '
                    f'height="{_svg_number(max(body_bottom - body_top, 1.2))}" '
                    f'fill="{color}" rx="0.6"/>'
                ),
                (
                    f'<rect data-volume="{index}" x="{_svg_number(candle_x - body_width / 2)}" '
                    f'y="{_svg_number(volume_top + volume_height - bar_volume_height)}" '
                    f'width="{_svg_number(body_width)}" '
                    f'height="{_svg_number(bar_volume_height)}" fill="{color}" '
                    'fill-opacity="0.42"/>'
                ),
            ]
        )
    parts.extend(
        [
            '<text x="66" y="402" fill="#374151" font-family="system-ui, sans-serif" '
            'font-size="11">成交量</text>',
            (
                '<text x="66" y="536" fill="#374151" font-family="system-ui, sans-serif" '
                f'font-size="11">{_svg_text(str(visible[0]["timestamp"])[:10])}</text>'
            ),
            (
                '<text x="938" y="536" text-anchor="end" fill="#374151" '
                f'font-family="system-ui, sans-serif" font-size="11">'
                f'{_svg_text(str(visible[-1]["timestamp"])[:10])}</text>'
            ),
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def _failure_markdown(
    symbol: str,
    research_as_of: str,
    source: Source,
    reason: str,
    attempts: int,
) -> str:
    return "\n".join(
        [
            f"# 技术面分析：{symbol}",
            "",
            f"研究截至：{research_as_of}",
            "",
            "## 数据状态",
            "- 状态：不合格，技术结论整体关闭。",
            "- 数据源：yfinance（非官方、best-effort，唯一官方内置来源）。",
            f"- 来源：{source.label}（as_of：{source.as_of}）",
            f"- 同源取数尝试：{attempts} 次（最多一次扩大历史窗口重试）。",
            "",
            "## 数据缺口",
            f"- {reason}",
        ]
    ) + "\n"


def _verify_artifacts(files: dict[str, str], evidence_id: str | None) -> None:
    if evidence_id is None:
        if set(files) != {"analysis.md"}:
            raise TechnicalAnalysisError("failed analysis may only contain analysis.md")
        return
    if set(files) != {"analysis.md", "chart.svg", "evidence.json"}:
        raise TechnicalAnalysisError("qualified analysis requires three artifacts")
    parsed = json.loads(files["evidence.json"])
    ElementTree.fromstring(files["chart.svg"])
    if parsed.get("evidence_id") != evidence_id:
        raise TechnicalAnalysisError("evidence JSON identity mismatch")
    if evidence_id not in files["analysis.md"] or evidence_id not in files["chart.svg"]:
        raise TechnicalAnalysisError("artifact evidence identities do not match")


def _atomic_write(output_dir: Path, files: dict[str, str]) -> None:
    if output_dir.exists():
        raise TechnicalAnalysisError("output_dir must not already exist")
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=parent)
    )
    try:
        for name, content in files.items():
            (temporary / name).write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _write_failure_package(
    output_dir: Path,
    symbol: str,
    research_as_of: str,
    source: Source,
    reason: str,
    attempts: int,
) -> None:
    files = {
        "analysis.md": _failure_markdown(
            symbol,
            research_as_of,
            source,
            reason,
            attempts,
        )
    }
    _verify_artifacts(files, None)
    _atomic_write(output_dir, files)


def render_fixture(fixture: dict[str, Any], output_dir: Path) -> None:
    symbol = _required_text(fixture.get("instrument"), "fixture")
    timeframe = _required_text(fixture.get("timeframe"), "fixture")
    research_as_of = _required_text(fixture.get("research_as_of"), "fixture")
    _timestamp(research_as_of, "research as_of")
    source = _source(fixture.get("provider"))
    if source.status != "available":
        source_attempts, _ = _source_attempt_metadata(fixture, 1)
        source_error = fixture.get("source_error")
        reason = f"yfinance 暂不可用：{source.status}"
        if isinstance(source_error, str) and source_error.strip():
            reason += f"（{source_error.strip()}）"
        reason += "。"
        _write_failure_package(
            output_dir,
            symbol,
            research_as_of,
            source,
            reason,
            source_attempts,
        )
        return

    raw_attempts = fixture.get("attempts")
    if raw_attempts is None:
        attempts = [fixture.get("ohlcv")]
    elif isinstance(raw_attempts, list) and 1 <= len(raw_attempts) <= 2:
        attempts = raw_attempts
    else:
        raise TechnicalAnalysisError("attempts must contain one or two OHLCV payloads")
    history: QualifiedHistory | None = None
    last_error: DataQualityError | None = None
    retry_count = 0
    for index, payload in enumerate(attempts):
        try:
            history = _qualified_history(payload, timeframe)
            retry_count = index
            break
        except DataQualityError as error:
            last_error = error
    if history is None:
        reason = str(last_error or DataQualityError("OHLCV unavailable"))
        source_error = fixture.get("source_error")
        if isinstance(source_error, str) and source_error.strip():
            reason += f"；同源请求错误：{source_error.strip()}"
        source_attempts, _ = _source_attempt_metadata(
            fixture, len(attempts)
        )
        _write_failure_package(
            output_dir,
            symbol,
            research_as_of,
            source,
            reason,
            source_attempts,
        )
        return

    try:
        evidence = _build_evidence(fixture, source, history, retry_count)
    except DataQualityError as error:
        source_attempts, _ = _source_attempt_metadata(
            fixture, retry_count + 1
        )
        _write_failure_package(
            output_dir,
            symbol,
            research_as_of,
            source,
            str(error),
            source_attempts,
        )
        return
    evidence_json = json.dumps(
        evidence, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    ) + "\n"
    files = {
        "analysis.md": _analysis_markdown(evidence),
        "chart.svg": _chart_svg(evidence),
        "evidence.json": evidence_json,
    }
    _verify_artifacts(files, evidence["evidence_id"])
    _atomic_write(output_dir, files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise TechnicalAnalysisError("fixture must be a JSON object")
        render_fixture(fixture, arguments.output_dir)
    except (
        OSError,
        json.JSONDecodeError,
        TechnicalAnalysisError,
        DataQualityError,
    ) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
