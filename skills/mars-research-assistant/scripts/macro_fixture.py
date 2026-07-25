#!/usr/bin/env python3
"""Synthetic, complete Macro inputs for fixture-only checks and visual review."""

from __future__ import annotations

from stateless_research_run import FieldValue


MACRO_FIELDS = (
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
XNYS_SESSIONS = (
    "2026-06-12",
    "2026-06-15",
    "2026-06-16",
    "2026-06-17",
    "2026-06-18",
    "2026-06-19",
    "2026-06-22",
    "2026-06-23",
    "2026-06-24",
    "2026-06-25",
    "2026-06-26",
    "2026-06-29",
    "2026-06-30",
    "2026-07-01",
    "2026-07-02",
    "2026-07-06",
    "2026-07-07",
    "2026-07-08",
    "2026-07-09",
    "2026-07-10",
    "2026-07-13",
    "2026-07-14",
    "2026-07-15",
    "2026-07-16",
    "2026-07-17",
    "2026-07-20",
    "2026-07-21",
    "2026-07-22",
    "2026-07-23",
    "2026-07-24",
)
XNYS_SESSIONS_WITH_PREVIOUS = ("2026-06-11", *XNYS_SESSIONS)
DEFAULT_RESEARCH_AS_OF = "2026-07-25T12:00:00Z"


class StaticXNYSCalendar:
    """Fixture calendar that accepts the one documented reference timestamp."""

    def __init__(self, sessions: tuple[str, ...]) -> None:
        self.sessions = sessions

    def completed_sessions(self, research_as_of: str) -> tuple[str, ...]:
        assert research_as_of == DEFAULT_RESEARCH_AS_OF
        return self.sessions


DEFAULT_XNYS_CALENDAR = StaticXNYSCalendar(XNYS_SESSIONS)


class StaticPrimaryEventSourceRegistry:
    """Fixture-only authoritative binding of evidence kind to exact primary URL."""

    def __init__(self, approved_sources: frozenset[tuple[str, str]]) -> None:
        self.approved_sources = approved_sources

    def approves(self, evidence_kind: str, original_source: str) -> bool:
        return (evidence_kind, original_source) in self.approved_sources


DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY = StaticPrimaryEventSourceRegistry(
    frozenset(
        {
            ("official_calendar", "https://www.bls.gov/cpi/"),
            ("official_announcement", "https://example.com/events"),
        }
    )
)


def fixture_field_value(
    name: str,
    value: object,
    source: str = "official",
    as_of: str = "2026-07-24",
) -> FieldValue:
    return FieldValue(
        name=name,
        status="available",
        value=value,
        source=source,
        as_of=as_of,
    )


def raw_leg(
    symbol: str,
    start: float,
    source: str,
    sessions: tuple[str, ...] = XNYS_SESSIONS,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "source": source,
        "as_of": "2026-07-24",
        "observations": [
            {
                "date": date,
                "close": start + index,
                "completed": True,
                "source": source,
                "as_of": "2026-07-24",
            }
            for index, date in enumerate(sessions)
        ],
    }


def raw_ratio_pair(
    ratio: str,
    left: str,
    right: str,
    left_start: float,
    right_start: float,
    source: str,
    sessions: tuple[str, ...] = XNYS_SESSIONS,
) -> dict[str, object]:
    return {
        "ratio": ratio,
        "legs": {
            left: raw_leg(left, left_start, source, sessions),
            right: raw_leg(right, right_start, source, sessions),
        },
    }


def complete_raw_macro_values(
    market_source: str = "yfinance",
    sessions: tuple[str, ...] = XNYS_SESSIONS,
) -> dict[str, FieldValue]:
    """Return a complete, source-labelled Macro delivery fixture."""

    return {
        "macro_events": fixture_field_value(
            "macro_events",
            [
                {
                    "title": "US CPI",
                    "category": "CPI",
                    "time": "2026-07-29T12:30:00Z",
                    "as_of": "2026-07-24T20:00:00Z",
                    "status": "upcoming",
                    "transmission": "rates and risk assets",
                    "original_source": "https://www.bls.gov/cpi/",
                    "evidence_kind": "official_calendar",
                    "primary_source_confirmed": True,
                }
            ],
            "official_calendar",
            "2026-07-24T20:00:00Z",
        ),
        "treasury_2y": fixture_field_value(
            "treasury_2y", {"value": 4.2, "unit": "%"}, "treasury"
        ),
        "treasury_10y": fixture_field_value(
            "treasury_10y", {"value": 4.4, "unit": "%"}, "treasury"
        ),
        "treasury_30y": fixture_field_value(
            "treasury_30y", {"value": 4.7, "unit": "%"}, "treasury"
        ),
        "vix": fixture_field_value(
            "vix",
            {"value": 16.2, "symbol": "^VIX", "completed": True},
            market_source,
        ),
        "vix3m": fixture_field_value(
            "vix3m",
            {"value": 19.4, "symbol": "^VIX3M", "completed": True},
            market_source,
        ),
        "dxy": fixture_field_value(
            "dxy",
            {"value": 101.1, "symbol": "DX-Y.NYB", "completed": True},
            market_source,
        ),
        "wti": fixture_field_value(
            "wti",
            {"value": 68.4, "symbol": "CL=F", "completed": True},
            market_source,
        ),
        "gold": fixture_field_value(
            "gold",
            {"value": 3342.0, "symbol": "GC=F", "completed": True},
            market_source,
        ),
        "hyg_lqd_history": fixture_field_value(
            "hyg_lqd_history",
            raw_ratio_pair(
                "HYG/LQD", "HYG", "LQD", 100.0, 50.0, market_source, sessions
            ),
            market_source,
        ),
        "ndx_rut_history": fixture_field_value(
            "ndx_rut_history",
            raw_ratio_pair(
                "NDX/RUT", "^NDX", "^RUT", 200.0, 100.0, market_source, sessions
            ),
            market_source,
        ),
    }
