#!/usr/bin/env python3
"""Render a deterministic Markdown Price Action fixture for offline checks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
import json
import math
from pathlib import Path
import re
from typing import Any


class PriceActionError(ValueError):
    """Report unusable OHLCV without producing a technical conclusion."""


PROVIDER_KINDS = {"public_best_effort"}
PROVIDER_STATUSES = {"available", "rate_limited", "unavailable"}
CHART_VISIBLE_BARS = 120
SMA_WINDOWS = (20, 50, 200)
CHART_MINIMUM_HISTORY_BARS = CHART_VISIBLE_BARS + max(SMA_WINDOWS) - 1
ADJUSTED_OHLCV_METHODS = {
    "adjusted",
    "dividend-adjusted",
    "split-adjusted",
    "total-return-adjusted",
}


@dataclass(frozen=True)
class Provider:
    name: str
    kind: str
    as_of: str
    status: str

    @property
    def label(self) -> str:
        return "yfinance EOD（非官方 best-effort）"


@dataclass(frozen=True)
class KeyLevel:
    label: str
    display_price: str
    price: float
    condition: str


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PriceActionError(f"{context} requires text")
    return value.strip()


def _provider(provider: object) -> Provider:
    if not isinstance(provider, dict):
        raise PriceActionError("provider requires an object")
    kind = _text(provider.get("kind"), "provider")
    if kind not in PROVIDER_KINDS:
        raise PriceActionError("provider must be yfinance public best-effort")
    if _text(provider.get("name"), "provider") != "yfinance EOD":
        raise PriceActionError("provider must be yfinance EOD")
    status = _text(provider.get("status", "available"), "provider")
    if status not in PROVIDER_STATUSES:
        raise PriceActionError(
            "provider status must be one of: available, rate_limited, unavailable"
        )
    return Provider(
        name=_text(provider.get("name"), "provider"),
        kind=kind,
        as_of=_text(provider.get("as_of"), "provider"),
        status=status,
    )


def _valid_ohlcv(
    ohlcv: object, requested_timeframe: str
) -> tuple[str, str, str, list[dict[str, Any]]]:
    if not isinstance(ohlcv, dict):
        raise PriceActionError("OHLCV requires an object")
    if _text(ohlcv.get("timeframe"), "OHLCV") != requested_timeframe:
        raise PriceActionError("OHLCV timeframe does not match requested timeframe")
    if ohlcv.get("time_range_suitable") is not True:
        raise PriceActionError("OHLCV time range is not suitable for the requested analysis")
    time_range = _text(ohlcv.get("time_range"), "OHLCV")
    coverage_start = _text(ohlcv.get("coverage_start"), "OHLCV")
    coverage_end = _text(ohlcv.get("coverage_end"), "OHLCV")
    timezone = _text(ohlcv.get("timezone"), "OHLCV")
    adjustment = _text(ohlcv.get("adjustment"), "OHLCV")
    if adjustment not in ADJUSTED_OHLCV_METHODS:
        raise PriceActionError("OHLCV adjustment must be adjusted")
    bars = ohlcv.get("bars")
    if not isinstance(bars, list) or len(bars) < 2:
        raise PriceActionError("OHLCV requires at least two bars")
    timestamps: list[str] = []
    for bar in bars:
        if not isinstance(bar, dict):
            raise PriceActionError("OHLCV bar must be an object")
        timestamp = _text(bar.get("timestamp"), "OHLCV bar")
        timezone_offset = len(timestamp) >= 6 and timestamp[-6] in {"+", "-"}
        if "T" not in timestamp or not (timestamp.endswith("Z") or timezone_offset):
            raise PriceActionError("OHLCV bar requires a timezone-aware timestamp")
        timestamps.append(timestamp)
        for field in ("open", "high", "low", "close", "volume"):
            value = bar.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PriceActionError(f"OHLCV bar requires numeric {field}")
            if not math.isfinite(value):
                raise PriceActionError(f"OHLCV bar requires finite {field}")
        if float(bar["volume"]) <= 0:
            raise PriceActionError("OHLCV bar requires positive volume")
        low = float(bar["low"])
        high = float(bar["high"])
        open_price = float(bar["open"])
        close_price = float(bar["close"])
        if not low <= min(open_price, close_price) <= max(open_price, close_price) <= high:
            raise PriceActionError("OHLCV bar has inconsistent price bounds")
    if any(previous >= current for previous, current in zip(timestamps, timestamps[1:])):
        raise PriceActionError("OHLCV timestamps must be strictly increasing")
    if timestamps[0][:10] > coverage_start[:10] or timestamps[-1][:10] < coverage_end[:10]:
        raise PriceActionError("OHLCV bars do not cover the declared time range")
    return time_range, timezone, adjustment, bars


def _moving_average(values: list[float], window: int) -> list[float | None]:
    averages: list[float | None] = []
    rolling_total = 0.0
    for index, value in enumerate(values):
        rolling_total += value
        if index >= window:
            rolling_total -= values[index - window]
        averages.append(rolling_total / window if index >= window - 1 else None)
    return averages


def _level_price(price: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", price.replace(",", ""))
    return float(match.group()) if match else None


def _key_levels(levels: object) -> list[KeyLevel]:
    if not isinstance(levels, list) or not levels:
        raise PriceActionError("key levels require at least one item")
    parsed: list[KeyLevel] = []
    for level in levels:
        if not isinstance(level, dict):
            raise PriceActionError("key level must be an object")
        display_price = _text(level.get("price"), "key level")
        numeric_price = _level_price(display_price)
        if numeric_price is None or not math.isfinite(numeric_price):
            raise PriceActionError("key level price must contain a number")
        parsed.append(
            KeyLevel(
                label=_text(level.get("label"), "key level"),
                display_price=display_price,
                price=numeric_price,
                condition=_text(level.get("condition"), "key level"),
            )
        )
    return parsed


def _svg_text(value: object) -> str:
    return escape(str(value), quote=True)


def _format_svg_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _price_y(value: float, lower: float, upper: float, top: float, height: float) -> float:
    return top + (upper - value) * height / (upper - lower)


def _static_daily_svg(
    instrument: str,
    provider: Provider,
    bars: list[dict[str, Any]],
    key_levels: list[KeyLevel],
) -> str:
    if len(bars) < CHART_MINIMUM_HISTORY_BARS:
        raise PriceActionError(
            "日线 OHLCV 少于 319 根，无法为最近 120 根生成完整 SMA200。"
        )
    visible = bars[-CHART_VISIBLE_BARS:]
    closes = [float(bar["close"]) for bar in bars]
    moving_averages = {
        window: _moving_average(closes, window) for window in SMA_WINDOWS
    }
    first_visible_index = len(bars) - len(visible)

    width = 960.0
    chart_left = 66.0
    chart_right = 22.0
    chart_end = width - chart_right
    chart_width = chart_end - chart_left
    price_top = 36.0
    price_height = 326.0
    volume_top = 422.0
    volume_panel_height = 88.0
    legend_start_x = chart_end - 260.0
    legend_step = 84.0
    legend_line_y = 398.0
    legend_text_y = legend_line_y + 4.0
    step = chart_width / len(visible)
    body_width = max(2.0, min(5.4, step * 0.62))

    price_samples = [
        float(bar[field]) for bar in visible for field in ("low", "high")
    ] + [level.price for level in key_levels]
    lower = min(price_samples)
    upper = max(price_samples)
    padding = max((upper - lower) * 0.06, 1.0)
    lower -= padding
    upper += padding
    maximum_volume = max(float(bar["volume"]) for bar in visible)

    parts = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560" '
            'width="100%" role="img" aria-label="{} 日线 Price Action 图">'
        ).format(_svg_text(instrument)),
        "<title>{} 日线 Price Action 图</title>".format(_svg_text(instrument)),
        (
            "<desc>最近 {} 根日线 K 线、成交量、SMA20、SMA50、SMA200 与关键位；"
            "数据来源：{}，as_of：{}。</desc>"
        ).format(
            len(visible), _svg_text(provider.label), _svg_text(provider.as_of)
        ),
        '<rect width="960" height="560" fill="#ffffff"/>',
        (
            '<text x="{}" y="20" fill="#172033" font-family="system-ui, -apple-system, '
            'BlinkMacSystemFont, sans-serif" font-size="14" font-weight="700">'
            "{} · 日线 Price Action</text>"
        ).format(_format_svg_number(chart_left), _svg_text(instrument)),
        (
            '<text x="{}" y="20" text-anchor="end" fill="#667085" '
            'font-family="system-ui, -apple-system, BlinkMacSystemFont, sans-serif" '
            'font-size="11">数据：{} ｜ as_of：{}</text>'
        ).format(
            _format_svg_number(chart_end),
            _svg_text(provider.label),
            _svg_text(provider.as_of),
        ),
    ]
    for fraction in range(5):
        y = price_top + price_height * fraction / 4
        price = upper - (upper - lower) * fraction / 4
        parts.extend(
            (
                (
                    '<line x1="{}" y1="{}" x2="{}" y2="{}" '
                    'stroke="#d9e0ea" stroke-width="1"/>'
                ).format(
                    _format_svg_number(chart_left),
                    _format_svg_number(y),
                    _format_svg_number(chart_end),
                    _format_svg_number(y),
                ),
                (
                    '<text x="{}" y="{}" text-anchor="end" dominant-baseline="middle" '
                    'fill="#667085" font-family="system-ui, -apple-system, '
                    'BlinkMacSystemFont, sans-serif" font-size="11">{}</text>'
                ).format(
                    _format_svg_number(chart_left - 8),
                    _format_svg_number(y),
                    _format_svg_number(price),
                ),
            )
        )

    for level in key_levels:
        y = _price_y(level.price, lower, upper, price_top, price_height)
        parts.extend(
            (
                (
                    '<line data-key-level="{}" x1="{}" y1="{}" x2="{}" y2="{}" '
                    'stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="5 4"/>'
                ).format(
                    _svg_text(level.label),
                    _format_svg_number(chart_left),
                    _format_svg_number(y),
                    _format_svg_number(chart_end),
                    _format_svg_number(y),
                ),
                (
                    '<text x="{}" y="{}" text-anchor="end" dominant-baseline="ideographic" '
                    'fill="#a15c07" font-family="system-ui, -apple-system, '
                    'BlinkMacSystemFont, sans-serif" font-size="11">{} {}</text>'
                ).format(
                    _format_svg_number(chart_end - 4),
                    _format_svg_number(y),
                    _svg_text(level.label),
                    _format_svg_number(level.price),
                ),
            )
        )

    moving_average_styles = {
        20: "#2563eb",
        50: "#7c3aed",
        200: "#dc2626",
    }
    for index, window in enumerate(SMA_WINDOWS):
        legend_x = legend_start_x + index * legend_step
        parts.append(
            (
                '<g data-legend="sma-{}"><line x1="{}" y1="{}" x2="{}" y2="{}" '
                'stroke="{}" stroke-width="2"/>'
                '<text x="{}" y="{}" fill="#475467" font-family="system-ui, '
                '-apple-system, BlinkMacSystemFont, sans-serif" font-size="11">'
                'SMA{}</text></g>'
            ).format(
                window,
                _format_svg_number(legend_x),
                _format_svg_number(legend_line_y),
                _format_svg_number(legend_x + 14),
                _format_svg_number(legend_line_y),
                moving_average_styles[window],
                _format_svg_number(legend_x + 18),
                _format_svg_number(legend_text_y),
                window,
            )
        )
    for window in SMA_WINDOWS:
        points = []
        for index in range(first_visible_index, len(bars)):
            average = moving_averages[window][index]
            if average is not None:
                x = chart_left + (index - first_visible_index + 0.5) * step
                y = _price_y(average, lower, upper, price_top, price_height)
                points.append(
                    f"{_format_svg_number(x)},{_format_svg_number(y)}"
                )
        parts.append(
            (
                '<polyline data-series="sma-{}" fill="none" stroke="{}" '
                'stroke-width="1.5" points="{}"/>'
            ).format(window, moving_average_styles[window], " ".join(points))
        )

    for index, bar in enumerate(visible, start=1):
        x = chart_left + (index - 0.5) * step
        open_price = float(bar["open"])
        close_price = float(bar["close"])
        high_price = float(bar["high"])
        low_price = float(bar["low"])
        color = "#15806a" if close_price >= open_price else "#c2414b"
        wick_top = _price_y(high_price, lower, upper, price_top, price_height)
        wick_bottom = _price_y(low_price, lower, upper, price_top, price_height)
        body_top = _price_y(
            max(open_price, close_price), lower, upper, price_top, price_height
        )
        body_bottom = _price_y(
            min(open_price, close_price), lower, upper, price_top, price_height
        )
        bar_volume_height = float(bar["volume"]) * volume_panel_height / maximum_volume
        parts.extend(
            (
                (
                    '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" '
                    'stroke-width="1"/>'
                ).format(
                    _format_svg_number(x),
                    _format_svg_number(wick_top),
                    _format_svg_number(x),
                    _format_svg_number(wick_bottom),
                    color,
                ),
                (
                    '<rect data-candle="{}" x="{}" y="{}" width="{}" height="{}" '
                    'fill="{}" rx="0.8"/>'
                ).format(
                    index,
                    _format_svg_number(x - body_width / 2),
                    _format_svg_number(body_top),
                    _format_svg_number(body_width),
                    _format_svg_number(max(body_bottom - body_top, 1.2)),
                    color,
                ),
                (
                    '<rect data-volume="{}" x="{}" y="{}" width="{}" height="{}" '
                    'fill="{}" fill-opacity="0.35"/>'
                ).format(
                    index,
                    _format_svg_number(x - body_width / 2),
                    _format_svg_number(
                        volume_top + volume_panel_height - bar_volume_height
                    ),
                    _format_svg_number(body_width),
                    _format_svg_number(bar_volume_height),
                    color,
                ),
            )
        )
    parts.extend(
        (
            (
                '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#b8c2d1" '
                'stroke-width="1"/>'
            ).format(
                _format_svg_number(chart_left),
                _format_svg_number(volume_top + volume_panel_height),
                _format_svg_number(chart_end),
                _format_svg_number(volume_top + volume_panel_height),
            ),
            (
                '<text x="{}" y="536" fill="#667085" font-family="system-ui, '
                '-apple-system, BlinkMacSystemFont, sans-serif" font-size="11">{}</text>'
            ).format(
                _format_svg_number(chart_left),
                _svg_text(str(visible[0]["timestamp"])[:10]),
            ),
            (
                '<text x="{}" y="536" text-anchor="end" fill="#667085" '
                'font-family="system-ui, -apple-system, BlinkMacSystemFont, sans-serif" '
                'font-size="11">{}</text>'
            ).format(
                _format_svg_number(chart_end),
                _svg_text(str(visible[-1]["timestamp"])[:10]),
            ),
            (
                '<text x="{}" y="402" fill="#667085" font-family="system-ui, '
                '-apple-system, BlinkMacSystemFont, sans-serif" font-size="11">'
                '成交量</text>'
            ).format(_format_svg_number(chart_left)),
            "</svg>",
        )
    )
    return "\n".join(parts)


def _unavailable_report(
    instrument: str,
    research_as_of: str,
    provider: Provider,
    reason: str,
) -> str:
    return "\n".join(
        (
            f"# Price Action：{instrument}",
            "",
            f"研究截至：{research_as_of}",
            "",
            "## 数据状态",
            "- 数据源：yfinance（非官方 best-effort，唯一数据源）。",
            f"- 来源：{provider.label}（as_of：{provider.as_of}）",
            f"- 数据不可用：{reason}",
            "",
            "## 数据缺口",
            f"- {reason}",
        )
    ) + "\n"


def _levels(levels: list[KeyLevel]) -> list[str]:
    rendered = ["## 关键位"]
    for level in levels:
        rendered.append(
            "- **{}**：{}（观察：{}）".format(
                level.label,
                level.display_price,
                level.condition,
            )
        )
    rendered.append("")
    return rendered


def _scenarios(scenarios: object) -> list[str]:
    if not isinstance(scenarios, list) or not scenarios:
        raise PriceActionError("scenarios require at least one item")
    rendered = ["## 情景与失效"]
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise PriceActionError("scenario must be an object")
        rendered.append(
            "- **{}**：{}；失效条件：{}".format(
                _text(scenario.get("label"), "scenario"),
                _text(scenario.get("condition"), "scenario"),
                _text(scenario.get("invalidation"), "scenario"),
            )
        )
    rendered.append("")
    return rendered


def _daily_chart_approved(timeframe: str, provider: Provider) -> bool:
    return timeframe == "1D" and provider.kind == "public_best_effort"


def render_price_action(fixture: dict[str, Any]) -> str:
    instrument = _text(fixture.get("instrument"), "fixture")
    timeframe = _text(fixture.get("timeframe"), "fixture")
    research_as_of = _text(fixture.get("research_as_of"), "fixture")
    provider = _provider(fixture.get("provider"))
    if provider.status != "available":
        return _unavailable_report(
            instrument,
            research_as_of,
            provider,
            f"yfinance 暂不可用：{provider.status}。",
        )
    try:
        time_range, timezone, adjustment, bars = _valid_ohlcv(
            fixture.get("ohlcv"), timeframe
        )
        key_levels = _key_levels(fixture.get("key_levels"))
    except PriceActionError as error:
        return _unavailable_report(
            instrument, research_as_of, provider, str(error)
        )
    structure = _text(fixture.get("structure"), "fixture")
    chart: list[str] = []
    if _daily_chart_approved(timeframe, provider):
        try:
            chart = [
                "## 日线图",
                _static_daily_svg(instrument, provider, bars, key_levels),
                "",
            ]
        except PriceActionError as error:
            return _unavailable_report(
                instrument, research_as_of, provider, str(error)
            )
    lines = [
        f"# Price Action：{instrument}",
        "",
        f"研究截至：{research_as_of}",
        "",
        "## 数据状态",
        f"- 时间框架：{timeframe}",
        "- 数据源：yfinance（非官方 best-effort，唯一数据源）。",
        f"- 来源：{provider.label}（as_of：{provider.as_of}）",
        f"- 覆盖范围：{time_range}；时区：{timezone}；复权：{adjustment}",
        "",
        *chart,
        "## 价格结构",
        structure,
        "",
        *_levels(key_levels),
        *_scenarios(fixture.get("scenarios")),
        "## 数据缺口",
    ]
    gaps = fixture.get("data_gaps", [])
    if not isinstance(gaps, list):
        raise PriceActionError("data gaps must be a list")
    if gaps:
        lines.extend(f"- {_text(gap, 'data gap')}" for gap in gaps)
    else:
        lines.append("- 本次未记录额外数据缺口。")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        fixture = json.loads(arguments.input.read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise PriceActionError("fixture must be a JSON object")
        arguments.output.write_text(render_price_action(fixture), encoding="utf-8")
    except (OSError, json.JSONDecodeError, PriceActionError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
