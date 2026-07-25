#!/usr/bin/env python3
"""Behavior checks for the stateless Macro Event Brief and Board delivery."""

from __future__ import annotations

from stateless_research_run import (
    FieldValue,
    LongbridgeAvailability,
    ResearchRequest,
    run_stateless_research,
)


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


class RecordingProvider:
    def __init__(self, values: dict[str, FieldValue]) -> None:
        self.values = values
        self.requests: list[tuple[str, ...]] = []

    def fetch_many(self, fields: tuple[str, ...]) -> dict[str, FieldValue]:
        self.requests.append(fields)
        return {name: self.values[name] for name in fields if name in self.values}


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


class StaticXNYSCalendar:
    def __init__(self, sessions: tuple[str, ...]) -> None:
        self.sessions = sessions

    def completed_sessions(self, research_as_of: str) -> tuple[str, ...]:
        assert research_as_of == "2026-07-25T12:00:00Z"
        return self.sessions


DEFAULT_RESEARCH_AS_OF = "2026-07-25T12:00:00Z"
DEFAULT_XNYS_CALENDAR = StaticXNYSCalendar(XNYS_SESSIONS)


def run_macro(provider: RecordingProvider):
    return run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )


def field(name: str, value: object, source: str = "official", as_of: str = "2026-07-24") -> FieldValue:
    return FieldValue(name=name, status="available", value=value, source=source, as_of=as_of)


def aligned_points(start: float) -> list[dict[str, object]]:
    return [
        {"date": f"2026-06-{index:02d}", "value": start + index, "completed": True}
        for index in range(1, 31)
    ]


def complete_macro_values() -> dict[str, FieldValue]:
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
                }
            ],
            "official_calendar",
            "2026-07-24T20:00:00Z",
        ),
        "treasury_2y": field("treasury_2y", {"value": 4.2, "unit": "%"}, "treasury"),
        "treasury_10y": field("treasury_10y", {"value": 4.4, "unit": "%"}, "treasury"),
        "treasury_30y": field("treasury_30y", {"value": 4.7, "unit": "%"}, "treasury"),
        "vix": field("vix", {"value": 16.2, "symbol": "^VIX", "completed": True}, "yfinance", "2026-06-30"),
        "vix3m": field("vix3m", {"value": 19.4, "symbol": "^VIX3M", "completed": True}, "yfinance", "2026-06-30"),
        "dxy": field("dxy", {"value": 101.1, "symbol": "DX-Y.NYB", "completed": True}, "yfinance", "2026-06-30"),
        "wti": field("wti", {"value": 68.4, "symbol": "CL=F", "completed": True}, "yfinance", "2026-06-30"),
        "gold": field("gold", {"value": 3342.0, "symbol": "GC=F", "completed": True}, "yfinance", "2026-06-30"),
        "hyg_lqd_history": field(
            "hyg_lqd_history",
            {"points": aligned_points(0.81), "ratio": "HYG/LQD", "symbols": ["HYG", "LQD"]},
            "yfinance",
            "2026-06-30",
        ),
        "ndx_rut_history": field(
            "ndx_rut_history",
            {"points": aligned_points(5.1), "ratio": "NDX/RUT", "symbols": ["^NDX", "^RUT"]},
            "yfinance",
            "2026-06-30",
        ),
    }


def raw_leg(symbol: str, start: float, source: str) -> dict[str, object]:
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
            for index, date in enumerate(XNYS_SESSIONS)
        ],
    }


def raw_ratio_pair(
    ratio: str,
    left: str,
    right: str,
    left_start: float,
    right_start: float,
    source: str,
) -> dict[str, object]:
    return {
        "ratio": ratio,
        "legs": {
            left: raw_leg(left, left_start, source),
            right: raw_leg(right, right_start, source),
        },
    }


def complete_raw_macro_values(market_source: str = "yfinance") -> dict[str, FieldValue]:
    values = complete_macro_values()
    values["hyg_lqd_history"] = field(
        "hyg_lqd_history",
        raw_ratio_pair("HYG/LQD", "HYG", "LQD", 100.0, 50.0, market_source),
        market_source,
    )
    values["ndx_rut_history"] = field(
        "ndx_rut_history",
        raw_ratio_pair("NDX/RUT", "^NDX", "^RUT", 200.0, 100.0, market_source),
        market_source,
    )
    for name in ("vix", "vix3m", "dxy", "wti", "gold"):
        original = values[name]
        values[name] = field(name, original.value, market_source, "2026-07-24")
    return values


def assert_macro_board_derives_ratio_pairs_at_latest_completed_session() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of="2026-07-25T12:00:00Z",
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
        session_calendar=StaticXNYSCalendar(XNYS_SESSIONS),
    )

    assert result.status == "complete"
    assert result.board_html is not None
    assert '"HYG/LQD"' in result.board_html
    assert '"value": 2.0' in result.board_html
    assert '"NDX/RUT"' in result.board_html
    assert '"value": 2.0' in result.board_html


def assert_incomplete_longbridge_pair_lazily_falls_back_as_one_field() -> None:
    longbridge_values = complete_raw_macro_values("longbridge")
    legs = longbridge_values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    hyg_observations = legs["HYG"]["observations"]
    assert isinstance(hyg_observations, list)
    hyg_observations.pop()
    longbridge = RecordingProvider(longbridge_values)
    portable = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="longbridge",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={"longbridge": longbridge, "portable": portable},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )

    assert result.status == "complete"
    assert longbridge.requests == [MACRO_FIELDS]
    assert portable.requests == [("hyg_lqd_history",)]
    assert next(field for field in result.fields if field.name == "hyg_lqd_history").source == "yfinance"


def assert_complete_longbridge_pairs_do_not_trigger_portable_fallback() -> None:
    longbridge = RecordingProvider(complete_raw_macro_values("longbridge"))
    portable = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="longbridge",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={"longbridge": longbridge, "portable": portable},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )

    assert result.status == "complete"
    assert longbridge.requests == [MACRO_FIELDS]
    assert portable.requests == []


def assert_missing_xnys_calendar_blocks_the_board() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "xnys_calendar_missing" in result.markdown


def assert_complete_macro_delivers_brief_then_self_contained_board() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_macro(provider)

    assert result.status == "complete"
    assert result.markdown is not None and result.markdown.startswith("## Macro Event Brief")
    assert "US CPI" in result.markdown
    assert result.board_html is not None and "<html" in result.board_html
    for label in ("2Y", "10Y", "30Y", "VIX", "VIX3M", "DXY", "WTI", "Gold", "HYG/LQD", "NDX/RUT"):
        assert label in result.board_html
    assert "VIX/VIX3M" not in result.board_html
    assert "manifest" not in result.board_html.lower()
    assert "source: treasury · as_of: 2026-07-24" in result.board_html
    assert "source: yfinance · as_of: 2026-07-24" in result.board_html
    assert "US CPI" in result.board_html
    assert "source: https://www.bls.gov/cpi/ · as_of: 2026-07-24T20:00:00Z" in result.board_html
    assert provider.requests == [MACRO_FIELDS]


def assert_event_brief_keeps_only_major_events_in_its_time_windows() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events.extend(
        [
            {
                "title": "Old CPI",
                "category": "CPI",
                "time": "2026-07-22T12:30:00Z",
                "status": "occurred",
                "transmission": "stale observation",
                "original_source": "https://www.bls.gov/cpi/",
            },
            {
                "title": "Late CPI",
                "category": "CPI",
                "time": "2026-08-02T12:30:00Z",
                "status": "upcoming",
                "transmission": "outside planning horizon",
                "original_source": "https://www.bls.gov/cpi/",
            },
            {
                "title": "Single-name earnings",
                "category": "earnings",
                "time": "2026-07-25T12:30:00Z",
                "status": "upcoming",
                "transmission": "not macro policy evidence",
                "original_source": "https://example.com/events",
            },
        ]
    )
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "complete"
    assert result.markdown is not None
    assert "US CPI" in result.markdown
    assert "Old CPI" not in result.markdown
    assert "Late CPI" not in result.markdown
    assert "Single-name earnings" not in result.markdown


def assert_non_official_treasury_field_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    values["treasury_10y"] = field("treasury_10y", {"value": 4.4, "unit": "%"}, "yfinance")
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "treasury_10y_source_invalid" in result.markdown


def assert_unclassified_macro_event_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["status"] = "tentative"
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "macro_events_status_invalid" in result.markdown


def assert_missing_frozen_field_keeps_brief_and_suppresses_board() -> None:
    values = complete_raw_macro_values()
    del values["gold"]
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.missing_fields == ("gold",)
    assert result.board_html is None
    assert result.markdown is not None
    assert "US CPI" in result.markdown
    assert "data_gap: gold" in result.markdown


def assert_uncompleted_market_snapshot_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    values["wti"] = field("wti", {"value": 68.4, "symbol": "CL=F", "completed": False}, "yfinance")
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "wti_not_completed" in result.markdown


def assert_invalid_or_duplicate_common_session_dates_block_the_board() -> None:
    values = complete_raw_macro_values()
    for name in ("hyg_lqd_history", "ndx_rut_history"):
        legs = values[name].value["legs"]
        assert isinstance(legs, dict)
        for leg in legs.values():
            observations = leg["observations"]
            assert isinstance(observations, list)
            observations[1]["date"] = "2026-07-04"
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "data_gap: hyg_lqd_history" in result.markdown


def assert_invalid_research_as_of_blocks_the_board() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of="not-a-time",
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "research_as_of_invalid" in result.markdown


def assert_cross_source_ratio_legs_do_not_form_a_board() -> None:
    values = complete_raw_macro_values("longbridge")
    legs = values["ndx_rut_history"].value["legs"]
    assert isinstance(legs, dict)
    right_leg = legs["^RUT"]
    right_leg["source"] = "yfinance"
    observations = right_leg["observations"]
    assert isinstance(observations, list)
    for observation in observations:
        observation["source"] = "yfinance"
    provider = RecordingProvider(values)

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="longbridge",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={"longbridge": provider},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "data_gap: ndx_rut_history" in result.markdown


def assert_unparseable_market_as_of_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    for name in ("vix", "vix3m", "dxy", "wti", "gold", "hyg_lqd_history", "ndx_rut_history"):
        original = values[name]
        values[name] = field(name, original.value, original.source, "not-a-time")
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "vix_as_of_invalid" in result.markdown


def assert_proxy_market_source_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    original = values["hyg_lqd_history"]
    values["hyg_lqd_history"] = field("hyg_lqd_history", original.value, "proxy_vendor", original.as_of)
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "data_gap: hyg_lqd_history" in result.markdown


def assert_stale_ratio_window_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    for name in ("vix", "vix3m", "dxy", "wti", "gold", "hyg_lqd_history", "ndx_rut_history"):
        original = values[name]
        values[name] = field(name, original.value, original.source, "2026-06-29")
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "vix_as_of_not_latest_completed_session" in result.markdown


def main() -> None:
    assert_macro_board_derives_ratio_pairs_at_latest_completed_session()
    assert_incomplete_longbridge_pair_lazily_falls_back_as_one_field()
    assert_complete_longbridge_pairs_do_not_trigger_portable_fallback()
    assert_missing_xnys_calendar_blocks_the_board()
    assert_complete_macro_delivers_brief_then_self_contained_board()
    assert_event_brief_keeps_only_major_events_in_its_time_windows()
    assert_non_official_treasury_field_blocks_the_board()
    assert_unclassified_macro_event_blocks_the_board()
    assert_missing_frozen_field_keeps_brief_and_suppresses_board()
    assert_uncompleted_market_snapshot_blocks_the_board()
    assert_invalid_or_duplicate_common_session_dates_block_the_board()
    assert_invalid_research_as_of_blocks_the_board()
    assert_cross_source_ratio_legs_do_not_form_a_board()
    assert_unparseable_market_as_of_blocks_the_board()
    assert_proxy_market_source_blocks_the_board()
    assert_stale_ratio_window_blocks_the_board()
    print("macro research run selftest passed")


if __name__ == "__main__":
    main()
