#!/usr/bin/env python3
"""Validate and directly deliver one stateless Macro research result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

from macro_board_visual import render_macro_board


MACRO_REQUIRED_FIELDS = (
    "macro_events",
    "treasury_2y",
    "treasury_10y",
    "treasury_30y",
    "vix",
    "vix3m",
    "dxy",
    "wti",
    "gold",
    "hyg_lqd_history",
    "ndx_rut_history",
)
_SCALAR_FIELDS = ("treasury_2y", "treasury_10y", "treasury_30y", "vix", "vix3m", "dxy", "wti", "gold")
_EXPECTED_SYMBOLS = {
    "vix": "^VIX",
    "vix3m": "^VIX3M",
    "dxy": "DX-Y.NYB",
    "wti": "CL=F",
    "gold": "GC=F",
}
_EXPECTED_RATIO_SYMBOLS = {"HYG/LQD": ("HYG", "LQD"), "NDX/RUT": ("^NDX", "^RUT")}
_OFFICIAL_TREASURY_SOURCES = frozenset({"treasury", "official_treasury", "treasury.gov"})
_MARKET_FIELDS = ("vix", "vix3m", "dxy", "wti", "gold", "hyg_lqd_history", "ndx_rut_history")
_MARKET_SOURCES = frozenset({"longbridge", "yfinance"})
_MAJOR_EVENT_TERMS = (
    "central bank",
    "fed",
    "ecb",
    "boj",
    "cpi",
    "pce",
    "ppi",
    "employment",
    "payroll",
    "gdp",
    "pmi",
    "fiscal",
    "tariff",
    "treasury auction",
    "long treasury auction",
)


@dataclass(frozen=True)
class MacroDelivery:
    markdown: str
    board_html: str | None
    blockers: tuple[str, ...]


def build_macro_delivery(fields: Mapping[str, Any]) -> MacroDelivery:
    """Return the Event Brief first and a Board only after all frozen gates pass."""

    event_field = fields.get("macro_events")
    events, event_problems = _validated_events(event_field)
    markdown = (
        _render_event_brief(events, event_field)
        if not event_problems
        else "## Macro Event Brief\n- data_gap: macro_events"
    )
    blockers = list(event_problems)
    blockers.extend(_field_blockers(fields))
    if blockers:
        rendered = markdown + "\n\n## Macro Regime Blocker\n" + "\n".join(
            f"- data_gap: {problem}" for problem in blockers
        )
        return MacroDelivery(rendered, None, tuple(blockers))
    return MacroDelivery(markdown, render_macro_board(_board_payload(fields, events)), ())


def _validated_events(field: Any) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    if field is None:
        return (), ("macro_events",)
    events = getattr(field, "value", None)
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return (), ("macro_events_invalid",)
    reference_time = _parse_timestamp(getattr(field, "as_of", None))
    if reference_time is None:
        return (), ("macro_events_as_of_invalid",)
    selected: list[Mapping[str, Any]] = []
    for event in events:
        if not isinstance(event, Mapping):
            return (), ("macro_events_invalid",)
        required = ("title", "category", "time", "status", "transmission", "original_source")
        if any(not str(event.get(key) or "").strip() for key in required):
            return (), ("macro_events_invalid",)
        if not str(event["original_source"]).startswith(("https://", "http://")):
            return (), ("macro_events_original_source_invalid",)
        event_time = _parse_timestamp(event["time"])
        if event_time is None:
            return (), ("macro_events_time_invalid",)
        status = str(event["status"])
        if status not in {"upcoming", "occurred"}:
            return (), ("macro_events_status_invalid",)
        if not _is_major_event(str(event["category"])) or not _is_in_event_window(
            event_time, status, reference_time
        ):
            continue
        selected.append(event)
    return tuple(selected), ()


def _render_event_brief(events: Sequence[Mapping[str, Any]], field: Any) -> str:
    rendered = []
    for event in events:
        rendered.append(
            f"- {event['time']} · {event['category']} · {event['title']} ({event['status']})"
            f"\n  传导：{event['transmission']}"
            f"\n  source: {event['original_source']} · as_of: {field.as_of}"
        )
    if not rendered:
        rendered.append("- none_found: 当前事件窗口未发现符合范围的重大事件")
    return "## Macro Event Brief\n" + "\n".join(rendered)


def _parse_timestamp(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_major_event(category: str) -> bool:
    normalized = category.casefold().replace("_", " ").replace("-", " ")
    return any(term in normalized for term in _MAJOR_EVENT_TERMS)


def _is_in_event_window(event_time: datetime, status: str, reference_time: datetime) -> bool:
    if status == "upcoming":
        return reference_time <= event_time <= reference_time + timedelta(days=7)
    if status == "occurred":
        return reference_time - timedelta(hours=24) <= event_time <= reference_time
    return False


def _field_blockers(fields: Mapping[str, Any]) -> tuple[str, ...]:
    problems = [name for name in MACRO_REQUIRED_FIELDS if name not in fields]
    if problems:
        return tuple(problems)
    treasury_names = ("treasury_2y", "treasury_10y", "treasury_30y")
    treasury_dates = _field_dates(fields, treasury_names, problems)
    if len(treasury_dates) == len(treasury_names) and len(set(treasury_dates.values())) != 1:
        problems.append("treasury_curve_date_mismatch")
    treasury_sources = {
        str(fields[name].source).casefold() for name in treasury_names
    }
    for name in treasury_names:
        if str(fields[name].source).casefold() not in _OFFICIAL_TREASURY_SOURCES:
            problems.append(f"{name}_source_invalid")
    if len(treasury_sources) != 1:
        problems.append("treasury_curve_source_mismatch")
    market_dates = _field_dates(fields, _MARKET_FIELDS, problems)
    if len(market_dates) == len(_MARKET_FIELDS) and len(set(market_dates.values())) != 1:
        problems.append("market_completed_session_mismatch")
    for name in _MARKET_FIELDS:
        if str(fields[name].source).casefold() not in _MARKET_SOURCES:
            problems.append(f"{name}_source_invalid")
    for name in _SCALAR_FIELDS:
        value = fields[name].value
        if not isinstance(value, Mapping) or not isinstance(value.get("value"), (int, float)):
            problems.append(f"{name}_invalid")
    for name in ("vix", "vix3m", "dxy", "wti", "gold"):
        value = fields[name].value
        if not isinstance(value, Mapping) or value.get("completed") is not True:
            problems.append(f"{name}_not_completed")
    for name, symbol in _EXPECTED_SYMBOLS.items():
        value = fields[name].value
        if not isinstance(value, Mapping) or value.get("symbol") != symbol:
            problems.append(f"{name}_semantic_invalid")
    histories = (fields["hyg_lqd_history"], fields["ndx_rut_history"])
    point_dates: list[tuple[str, ...]] = []
    for field, ratio in zip(histories, ("HYG/LQD", "NDX/RUT")):
        value = field.value
        points = value.get("points") if isinstance(value, Mapping) else None
        if not isinstance(value, Mapping) or value.get("ratio") != ratio or not isinstance(points, list) or len(points) != 30:
            problems.append(f"{field.name}_invalid")
            continue
        if tuple(value.get("symbols") or ()) != _EXPECTED_RATIO_SYMBOLS[ratio]:
            problems.append(f"{field.name}_semantic_invalid")
        dates = []
        for point in points:
            if not isinstance(point, Mapping) or not isinstance(point.get("value"), (int, float)) or not point.get("completed"):
                problems.append(f"{field.name}_points_invalid")
                break
            date = _parse_timestamp(point.get("date"))
            if date is None:
                problems.append(f"{field.name}_points_invalid")
                break
            dates.append(date.date().isoformat())
        if len(dates) != 30 or len(set(dates)) != 30 or dates != sorted(dates):
            problems.append(f"{field.name}_points_invalid")
        expected_as_of = market_dates.get(field.name)
        if len(dates) == 30 and expected_as_of is not None and dates[-1] != expected_as_of:
            problems.append(f"{field.name}_as_of_mismatch")
        point_dates.append(tuple(dates))
    if len(point_dates) == 2 and point_dates[0] != point_dates[1]:
        problems.append("ratio_common_sessions_mismatch")
    return tuple(dict.fromkeys(problems))


def _field_dates(
    fields: Mapping[str, Any], names: Sequence[str], problems: list[str]
) -> dict[str, str]:
    dates: dict[str, str] = {}
    for name in names:
        parsed = _parse_timestamp(fields[name].as_of)
        if parsed is None:
            problems.append(f"{name}_as_of_invalid")
            continue
        dates[name] = parsed.date().isoformat()
    return dates


def _board_payload(fields: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scalars = {name: fields[name] for name in _SCALAR_FIELDS}
    return {
        "as_of": scalars["vix"].as_of,
        "treasury_as_of": fields["treasury_2y"].as_of,
        "values": {name: scalars[name].value["value"] for name in _SCALAR_FIELDS},
        "sources": {name: fields[name].source for name in MACRO_REQUIRED_FIELDS},
        "as_ofs": {name: fields[name].as_of for name in MACRO_REQUIRED_FIELDS},
        "trend_series": {
            "HYG/LQD": fields["hyg_lqd_history"].value["points"],
            "NDX/RUT": fields["ndx_rut_history"].value["points"],
        },
        "events": [{**event, "as_of": fields["macro_events"].as_of} for event in events[:5]],
    }
