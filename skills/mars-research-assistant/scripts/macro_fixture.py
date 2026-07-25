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


def field(
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
        "macro_events": field(
            "macro_events",
            [
                {
                    "title": "US CPI",
                    "category": "CPI",
                    "time": "2026-07-29T12:30:00Z",
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
        "treasury_2y": field(
            "treasury_2y", {"value": 4.2, "unit": "%"}, "treasury"
        ),
        "treasury_10y": field(
            "treasury_10y", {"value": 4.4, "unit": "%"}, "treasury"
        ),
        "treasury_30y": field(
            "treasury_30y", {"value": 4.7, "unit": "%"}, "treasury"
        ),
        "vix": field(
            "vix",
            {"value": 16.2, "symbol": "^VIX", "completed": True},
            market_source,
        ),
        "vix3m": field(
            "vix3m",
            {"value": 19.4, "symbol": "^VIX3M", "completed": True},
            market_source,
        ),
        "dxy": field(
            "dxy",
            {"value": 101.1, "symbol": "DX-Y.NYB", "completed": True},
            market_source,
        ),
        "wti": field(
            "wti",
            {"value": 68.4, "symbol": "CL=F", "completed": True},
            market_source,
        ),
        "gold": field(
            "gold",
            {"value": 3342.0, "symbol": "GC=F", "completed": True},
            market_source,
        ),
        "hyg_lqd_history": field(
            "hyg_lqd_history",
            raw_ratio_pair(
                "HYG/LQD", "HYG", "LQD", 100.0, 50.0, market_source, sessions
            ),
            market_source,
        ),
        "ndx_rut_history": field(
            "ndx_rut_history",
            raw_ratio_pair(
                "NDX/RUT", "^NDX", "^RUT", 200.0, 100.0, market_source, sessions
            ),
            market_source,
        ),
    }
