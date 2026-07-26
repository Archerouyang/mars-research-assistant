#!/usr/bin/env python3
"""Render a deterministic Markdown Price Action fixture for offline checks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class PriceActionError(ValueError):
    """Report unusable OHLCV without producing a technical conclusion."""


PROVIDER_KINDS = {"public_best_effort", "fmp_eod", "user_supplied"}
PROVIDER_STATUSES = {"available", "not_configured", "unauthorized", "rate_limited"}
FMP_ENTITLEMENT_STATUSES = {"available", "not_entitled", "unavailable"}


@dataclass(frozen=True)
class Provider:
    name: str
    kind: str
    as_of: str
    status: str
    entitlement_status: str | None

    @property
    def label(self) -> str:
        if self.kind == "public_best_effort":
            return f"{self.name}（非官方 best-effort）"
        return self.name


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PriceActionError(f"{context} requires text")
    return value.strip()


def _provider(provider: object) -> Provider:
    if not isinstance(provider, dict):
        raise PriceActionError("provider requires an object")
    kind = _text(provider.get("kind"), "provider")
    if kind not in PROVIDER_KINDS:
        raise PriceActionError("provider kind must be supported")
    status = _text(provider.get("status", "available"), "provider")
    if status not in PROVIDER_STATUSES:
        raise PriceActionError(
            "provider status must be one of: available, not_configured, unauthorized, rate_limited"
        )
    entitlement_status = None
    if kind == "fmp_eod":
        entitlement_status = _text(provider.get("entitlement_status"), "FMP entitlement")
        if entitlement_status not in FMP_ENTITLEMENT_STATUSES:
            raise PriceActionError(
                "FMP entitlement must be one of: available, not_entitled, unavailable"
            )
    return Provider(
        name=_text(provider.get("name"), "provider"),
        kind=kind,
        as_of=_text(provider.get("as_of"), "provider"),
        status=status,
        entitlement_status=entitlement_status,
    )


def _valid_ohlcv(ohlcv: object, requested_timeframe: str) -> tuple[str, str, str]:
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
            if not isinstance(bar.get(field), (int, float)):
                raise PriceActionError(f"OHLCV bar requires numeric {field}")
    if timestamps[0][:10] > coverage_start[:10] or timestamps[-1][:10] < coverage_end[:10]:
        raise PriceActionError("OHLCV bars do not cover the declared time range")
    return time_range, timezone, adjustment


def _unavailable_report(
    instrument: str, research_as_of: str, provider: Provider, reason: str
) -> str:
    return "\n".join(
        (
            f"# Price Action：{instrument}",
            "",
            f"研究截至：{research_as_of}",
            "",
            "## 数据状态",
            f"- 来源：{provider.label}（as_of：{provider.as_of}）",
            f"- 数据不可用：{reason}",
            "",
            "## 数据缺口",
            f"- {reason}",
        )
    ) + "\n"


def _levels(levels: object) -> list[str]:
    if not isinstance(levels, list) or not levels:
        raise PriceActionError("key levels require at least one item")
    rendered = ["## 关键位"]
    for level in levels:
        if not isinstance(level, dict):
            raise PriceActionError("key level must be an object")
        rendered.append(
            "- **{}**：{}（观察：{}）".format(
                _text(level.get("label"), "key level"),
                _text(level.get("price"), "key level"),
                _text(level.get("condition"), "key level"),
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
            f"{provider.name} 暂不可用：{provider.status}。未回显任何凭据。",
        )
    if provider.kind == "fmp_eod" and provider.entitlement_status != "available":
        return _unavailable_report(
            instrument,
            research_as_of,
            provider,
            f"{provider.name} 暂不可用：{provider.entitlement_status}。未回显任何凭据。",
        )
    try:
        time_range, timezone, adjustment = _valid_ohlcv(fixture.get("ohlcv"), timeframe)
    except PriceActionError as error:
        return _unavailable_report(instrument, research_as_of, provider, str(error))
    structure = _text(fixture.get("structure"), "fixture")
    lines = [
        f"# Price Action：{instrument}",
        "",
        f"研究截至：{research_as_of}",
        "",
        "## 数据状态",
        f"- 时间框架：{timeframe}",
        f"- 来源：{provider.label}（as_of：{provider.as_of}）",
        f"- 覆盖范围：{time_range}；时区：{timezone}；复权：{adjustment}",
        "",
        "## 价格结构",
        structure,
        "",
        *_levels(fixture.get("key_levels")),
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
