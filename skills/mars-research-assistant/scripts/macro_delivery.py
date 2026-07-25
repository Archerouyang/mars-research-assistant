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


def ratio_pair_validation_problems(
    field: Any,
    *,
    research_as_of: str | None,
    session_calendar: Any | None,
) -> tuple[str, ...]:
    """Report a malformed ratio pair so the normal lazy fallback can retry it."""

    if getattr(field, "name", None) not in {"hyg_lqd_history", "ndx_rut_history"}:
        return ()
    sessions, session_problems = _completed_xnys_sessions(research_as_of, session_calendar)
    if session_problems:
        return ()
    ratio = "HYG/LQD" if field.name == "hyg_lqd_history" else "NDX/RUT"
    _, pair_problems = _derive_ratio_pair(field, ratio, sessions)
    return pair_problems


def build_macro_delivery(
    fields: Mapping[str, Any],
    *,
    research_as_of: str | None,
    session_calendar: Any | None,
) -> MacroDelivery:
    """Return the Event Brief first and a Board only after all frozen gates pass."""

    event_field = fields.get("macro_events")
    events, event_problems = _validated_events(event_field, research_as_of)
    markdown = (
        _render_event_brief(events, event_field)
        if not event_problems
        else "## Macro Event Brief\n- data_gap: macro_events"
    )
    blockers = list(event_problems)
    field_problems, trend_series = _validate_macro_fields(
        fields,
        research_as_of=research_as_of,
        session_calendar=session_calendar,
    )
    blockers.extend(field_problems)
    if blockers:
        rendered = markdown + "\n\n## Macro Regime Blocker\n" + "\n".join(
            f"- data_gap: {problem}" for problem in blockers
        )
        return MacroDelivery(rendered, None, tuple(blockers))
    return MacroDelivery(markdown, render_macro_board(_board_payload(fields, events, trend_series)), ())


def _validated_events(
    field: Any, research_as_of: str | None
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    if field is None:
        return (), ("macro_events",)
    events = getattr(field, "value", None)
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return (), ("macro_events_invalid",)
    if research_as_of is None:
        return (), ("research_as_of_missing",)
    reference_time = _parse_research_as_of(research_as_of)
    if reference_time is None:
        return (), ("research_as_of_invalid",)
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


def _parse_research_as_of(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _is_major_event(category: str) -> bool:
    normalized = category.casefold().replace("_", " ").replace("-", " ")
    return any(term in normalized for term in _MAJOR_EVENT_TERMS)


def _is_in_event_window(event_time: datetime, status: str, reference_time: datetime) -> bool:
    if status == "upcoming":
        return reference_time <= event_time <= reference_time + timedelta(days=7)
    if status == "occurred":
        return reference_time - timedelta(hours=24) <= event_time <= reference_time
    return False


def _validate_macro_fields(
    fields: Mapping[str, Any],
    *,
    research_as_of: str | None,
    session_calendar: Any | None,
) -> tuple[tuple[str, ...], Mapping[str, list[dict[str, Any]]]]:
    problems = [name for name in MACRO_REQUIRED_FIELDS if name not in fields]
    treasury_names = ("treasury_2y", "treasury_10y", "treasury_30y")
    if all(name in fields for name in treasury_names):
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
    sessions, session_problems = _completed_xnys_sessions(research_as_of, session_calendar)
    problems.extend(session_problems)
    present_market_fields = tuple(name for name in _MARKET_FIELDS if name in fields)
    market_dates = _field_dates(fields, present_market_fields, problems)
    if sessions:
        latest_session = sessions[-1]
        for name, market_date in market_dates.items():
            if market_date != latest_session:
                problems.append(f"{name}_as_of_not_latest_completed_session")
    for name in present_market_fields:
        if str(fields[name].source).casefold() not in _MARKET_SOURCES:
            problems.append(f"{name}_source_invalid")
    for name in _SCALAR_FIELDS:
        if name not in fields:
            continue
        value = fields[name].value
        if not isinstance(value, Mapping) or not isinstance(value.get("value"), (int, float)):
            problems.append(f"{name}_invalid")
    for name in ("vix", "vix3m", "dxy", "wti", "gold"):
        if name not in fields:
            continue
        value = fields[name].value
        if not isinstance(value, Mapping) or value.get("completed") is not True:
            problems.append(f"{name}_not_completed")
    for name, symbol in _EXPECTED_SYMBOLS.items():
        if name not in fields:
            continue
        value = fields[name].value
        if not isinstance(value, Mapping) or value.get("symbol") != symbol:
            problems.append(f"{name}_semantic_invalid")
    trend_series: dict[str, list[dict[str, Any]]] = {}
    if sessions:
        for field_name, ratio in (("hyg_lqd_history", "HYG/LQD"), ("ndx_rut_history", "NDX/RUT")):
            if field_name not in fields:
                continue
            pair_points, pair_problems = _derive_ratio_pair(
                fields[field_name],
                ratio,
                sessions,
            )
            problems.extend(pair_problems)
            if not pair_problems:
                trend_series[ratio] = pair_points
    return tuple(dict.fromkeys(problems)), trend_series


def _completed_xnys_sessions(
    research_as_of: str | None, session_calendar: Any | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if research_as_of is None:
        return (), ("research_as_of_missing",)
    reference_time = _parse_research_as_of(research_as_of)
    if reference_time is None:
        return (), ("research_as_of_invalid",)
    if session_calendar is None:
        return (), ("xnys_calendar_missing",)
    try:
        raw_sessions = session_calendar.completed_sessions(research_as_of)
    except Exception:
        return (), ("xnys_calendar_unavailable",)
    if not isinstance(raw_sessions, Sequence) or isinstance(raw_sessions, (str, bytes)):
        return (), ("xnys_calendar_invalid",)
    sessions: list[str] = []
    for raw_session in raw_sessions:
        parsed = _parse_timestamp(raw_session)
        if parsed is None:
            return (), ("xnys_calendar_invalid",)
        session = parsed.date().isoformat()
        if session > reference_time.date().isoformat():
            return (), ("xnys_calendar_invalid",)
        sessions.append(session)
    if not sessions or len(set(sessions)) != len(sessions) or sessions != sorted(sessions):
        return (), ("xnys_calendar_invalid",)
    return tuple(sessions), ()


def _derive_ratio_pair(
    field: Any,
    ratio: str,
    sessions: Sequence[str],
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    expected_symbols = _EXPECTED_RATIO_SYMBOLS[ratio]
    value = getattr(field, "value", None)
    if not isinstance(value, Mapping) or value.get("ratio") != ratio:
        return [], (f"{field.name}_pair_invalid",)
    legs = value.get("legs")
    if not isinstance(legs, Mapping) or set(legs) != set(expected_symbols):
        return [], (f"{field.name}_legs_invalid",)
    normalized_legs: list[dict[str, float]] = []
    for symbol in expected_symbols:
        normalized, leg_problems = _normalize_ratio_leg(
            legs[symbol],
            symbol=symbol,
            field=field,
            valid_sessions=set(sessions),
        )
        if leg_problems:
            return [], tuple(f"{field.name}_{problem}" for problem in leg_problems)
        normalized_legs.append(normalized)
    left, right = normalized_legs
    common_sessions = [session for session in sessions if session in left and session in right]
    if len(common_sessions) < 30:
        return [], (f"{field.name}_fewer_than_30_common_sessions",)
    selected_sessions = common_sessions[-30:]
    if selected_sessions[-1] != sessions[-1]:
        return [], (f"{field.name}_latest_session_missing",)
    points = []
    for session in selected_sessions:
        denominator = right[session]
        if denominator == 0:
            return [], (f"{field.name}_zero_denominator",)
        points.append({"date": session, "value": left[session] / denominator, "completed": True})
    return points, ()


def _normalize_ratio_leg(
    raw_leg: Any,
    *,
    symbol: str,
    field: Any,
    valid_sessions: set[str],
) -> tuple[dict[str, float], tuple[str, ...]]:
    if not isinstance(raw_leg, Mapping):
        return {}, ("leg_invalid",)
    if raw_leg.get("symbol") != symbol:
        return {}, ("leg_symbol_invalid",)
    if raw_leg.get("source") != field.source or raw_leg.get("as_of") != field.as_of:
        return {}, ("leg_source_mismatch",)
    observations = raw_leg.get("observations")
    if not isinstance(observations, list) or not observations:
        return {}, ("leg_observations_missing",)
    values: dict[str, float] = {}
    ordered_dates: list[str] = []
    for observation in observations:
        if not isinstance(observation, Mapping):
            return {}, ("leg_observations_invalid",)
        parsed = _parse_timestamp(observation.get("date"))
        if parsed is None:
            return {}, ("leg_observations_invalid",)
        date = parsed.date().isoformat()
        close = observation.get("close")
        if (
            date not in valid_sessions
            or not isinstance(close, (int, float))
            or observation.get("completed") is not True
            or observation.get("source") != field.source
            or observation.get("as_of") != field.as_of
        ):
            return {}, ("leg_observations_invalid",)
        if date in values:
            return {}, ("leg_observations_invalid",)
        values[date] = float(close)
        ordered_dates.append(date)
    if ordered_dates != sorted(ordered_dates):
        return {}, ("leg_observations_invalid",)
    return values, ()


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


def _board_payload(
    fields: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    trend_series: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    scalars = {name: fields[name] for name in _SCALAR_FIELDS}
    return {
        "as_of": scalars["vix"].as_of,
        "treasury_as_of": fields["treasury_2y"].as_of,
        "values": {name: scalars[name].value["value"] for name in _SCALAR_FIELDS},
        "sources": {name: fields[name].source for name in MACRO_REQUIRED_FIELDS},
        "as_ofs": {name: fields[name].as_of for name in MACRO_REQUIRED_FIELDS},
        "trend_series": dict(trend_series),
        "events": [{**event, "as_of": fields["macro_events"].as_of} for event in events[:5]],
    }
