#!/usr/bin/env python3
"""Behavior checks for the stateless Macro Event Brief and Board delivery."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from macro_fixture import (
    DEFAULT_RESEARCH_AS_OF,
    DEFAULT_XNYS_CALENDAR,
    DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
    MACRO_FIELDS,
    XNYS_SESSIONS,
    XNYS_SESSIONS_WITH_PREVIOUS,
    StaticXNYSCalendar,
    complete_raw_macro_values,
    fixture_field_value,
)
from macro_fixture_board import write_representative_macro_board
from stateless_research_run import (
    FieldValue,
    LongbridgeAvailability,
    ResearchRequest,
    run_stateless_research,
)


class RecordingProvider:
    def __init__(self, values: dict[str, FieldValue]) -> None:
        self.values = values
        self.requests: list[tuple[str, ...]] = []

    def fetch_many(self, fields: tuple[str, ...]) -> dict[str, FieldValue]:
        self.requests.append(fields)
        return {name: self.values[name] for name in fields if name in self.values}


def run_macro(
    provider: RecordingProvider,
    session_calendar: StaticXNYSCalendar = DEFAULT_XNYS_CALENDAR,
):
    return run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
        session_calendar=session_calendar,
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
    )


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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "xnys_calendar_missing" in result.markdown


def assert_complete_macro_delivers_brief_then_self_contained_board() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_macro(provider)

    assert result.status == "complete"
    assert result.markdown is not None and result.markdown.startswith("## 宏观事件简报")
    assert "US CPI" in result.markdown
    assert result.board_html is not None and "<html" in result.board_html
    for label in ("2Y", "10Y", "30Y", "VIX", "VIX3M", "DXY", "WTI", "Gold", "HYG/LQD", "NDX/RUT"):
        assert label in result.board_html
    assert "VIX/VIX3M" not in result.board_html
    assert "manifest" not in result.board_html.lower()
    assert "来源：treasury · 截至：2026-07-24" in result.board_html
    assert "来源：yfinance · 截至：2026-07-24" in result.board_html
    assert "US CPI" in result.board_html
    assert "来源：https://www.bls.gov/cpi/ · 截至：2026-07-24T20:00:00Z" in result.board_html
    assert "宏观环境研究简报" in result.board_html
    assert "30 日" in result.board_html
    assert "即将发生" in result.board_html
    assert '<header class="masthead">' in result.board_html
    assert 'class="market-strip"' in result.board_html
    assert 'class="evidence-rail"' in result.board_html
    for view in ("trend", "current", "events", "scenarios"):
        assert f'data-view="{view}"' in result.board_html
        assert f'data-panel="{view}"' in result.board_html
    assert 'data-series="HYG/LQD"' in result.board_html
    assert 'data-series="NDX/RUT"' in result.board_html
    assert 'data-exposure-select' in result.board_html
    assert "宏观因子暴露" in result.board_html
    assert "不代表持仓" in result.board_html
    assert "条件框架，不是预测" in result.board_html
    assert '"PingFang SC"' in result.board_html
    assert "font-synthesis:none" in result.board_html
    assert "font-variant-numeric:tabular-nums" in result.board_html
    assert provider.requests == [MACRO_FIELDS]


def assert_primary_event_evidence_is_visible_in_the_brief_and_board() -> None:
    result = run_macro(RecordingProvider(complete_raw_macro_values()))

    assert result.status == "complete"
    assert result.markdown is not None
    assert "证据类型：official_calendar" in result.markdown
    assert "已确认一手来源：true" in result.markdown
    assert result.board_html is not None
    assert "证据类型：official_calendar" in result.board_html
    assert "已确认一手来源：true" in result.board_html


def assert_each_event_keeps_its_own_source_time() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events.append(
        {
            "title": "US PPI",
            "category": "PPI",
            "time": "2026-07-30T12:30:00Z",
            "as_of": "2026-07-24T18:00:00Z",
            "status": "upcoming",
            "transmission": "rates and risk assets",
            "original_source": "https://www.bls.gov/ppi/",
            "evidence_kind": "official_calendar",
            "primary_source_confirmed": True,
        }
    )

    result = run_macro(RecordingProvider(values))

    assert result.status == "complete"
    assert result.markdown is not None
    assert "US PPI" in result.markdown
    assert "来源：https://www.bls.gov/ppi/ · 截至：2026-07-24T18:00:00Z" in result.markdown
    assert result.board_html is not None
    assert "US PPI" in result.board_html
    assert "来源：https://www.bls.gov/ppi/ · 截至：2026-07-24T18:00:00Z" in result.board_html


def assert_mismatched_event_source_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["title"] = "US PPI"
    events[0]["category"] = "PPI"

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_original_source_unverified" in result.markdown


def assert_unregistered_event_identity_blocks_the_board() -> None:
    for mutation in (
        {"time": "2026-07-30T12:30:00Z"},
        {"evidence_kind": "government_or_regulatory_filing"},
    ):
        values = complete_raw_macro_values()
        events = values["macro_events"].value
        assert isinstance(events, list)
        events[0].update(mutation)

        result = run_macro(RecordingProvider(values))

        assert result.status == "blocked"
        assert result.board_html is None
        assert result.markdown is not None
        assert "data_gap: macro_events_original_source_unverified" in result.markdown


def assert_missing_event_source_time_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    del events[0]["as_of"]

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_as_of_missing" in result.markdown


def assert_invalid_event_source_time_blocks_the_board() -> None:
    for source_time in ("not-a-time", "2026-07-24T20:00:00"):
        values = complete_raw_macro_values()
        events = values["macro_events"].value
        assert isinstance(events, list)
        events[0]["as_of"] = source_time

        result = run_macro(RecordingProvider(values))

        assert result.status == "blocked"
        assert result.board_html is None
        assert result.markdown is not None
        assert "data_gap: macro_events_as_of_invalid" in result.markdown


def assert_missing_event_evidence_kind_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    del events[0]["evidence_kind"]

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_evidence_kind_missing" in result.markdown


def assert_unconfirmed_primary_event_source_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["primary_source_confirmed"] = False

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_primary_source_unconfirmed" in result.markdown


def assert_aggregated_event_evidence_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["original_source"] = "https://news.example.com/cpi"
    events[0]["evidence_kind"] = "aggregated_news"

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_evidence_kind_invalid" in result.markdown


def assert_mislabeled_aggregated_event_url_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["original_source"] = "https://aggregated.example.com/cpi"

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_original_source_unverified" in result.markdown


def assert_missing_primary_source_registry_blocks_the_board() -> None:
    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": RecordingProvider(complete_raw_macro_values())},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_primary_source_registry_missing" in result.markdown


def assert_invalid_event_time_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["time"] = "not-a-time"

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_time_invalid" in result.markdown


def assert_timezone_less_event_time_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    events = values["macro_events"].value
    assert isinstance(events, list)
    events[0]["time"] = "2026-07-25T08:30:00"

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: macro_events_time_invalid" in result.markdown


def assert_representative_fixture_board_is_written_to_the_caller_temp_directory() -> None:
    with TemporaryDirectory() as temporary_directory:
        output = write_representative_macro_board(Path(temporary_directory))

        assert output == Path(temporary_directory) / "research-brief.html"
        html = output.read_text(encoding="utf-8")
        assert html.startswith("<!doctype html>")
        assert "宏观环境" in html
        assert "证据类型：official_calendar" in html
        assert "合成视觉样本" in html
        assert "非市场数据" in html


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
                "as_of": "2026-07-24T20:00:00Z",
                "status": "occurred",
                "transmission": "stale observation",
                "original_source": "https://www.bls.gov/cpi/",
                "evidence_kind": "official_calendar",
                "primary_source_confirmed": True,
            },
            {
                "title": "Late CPI",
                "category": "CPI",
                "time": "2026-08-02T12:30:00Z",
                "as_of": "2026-07-24T20:00:00Z",
                "status": "upcoming",
                "transmission": "outside planning horizon",
                "original_source": "https://www.bls.gov/cpi/",
                "evidence_kind": "official_calendar",
                "primary_source_confirmed": True,
            },
            {
                "title": "Single-name earnings",
                "category": "earnings",
                "time": "2026-07-25T12:30:00Z",
                "as_of": "2026-07-24T20:00:00Z",
                "status": "upcoming",
                "transmission": "not macro policy evidence",
                "original_source": "https://example.com/events",
                "evidence_kind": "official_announcement",
                "primary_source_confirmed": True,
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
    values["treasury_10y"] = fixture_field_value(
        "treasury_10y", {"value": 4.4, "unit": "%"}, "yfinance"
    )
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
    values["wti"] = fixture_field_value(
        "wti",
        {"value": 68.4, "symbol": "CL=F", "completed": False},
        "yfinance",
    )
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "wti_not_completed" in result.markdown


def assert_non_xnys_observation_blocks_the_board_with_a_precise_reason() -> None:
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
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_leg_observations_invalid" in result.markdown


def assert_duplicate_observation_date_blocks_the_board_with_a_precise_reason() -> None:
    values = complete_raw_macro_values()
    legs = values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    observations = legs["HYG"]["observations"]
    assert isinstance(observations, list)
    observations[1]["date"] = observations[0]["date"]

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_leg_observations_invalid" in result.markdown


def assert_unordered_observations_block_the_board_with_a_precise_reason() -> None:
    values = complete_raw_macro_values()
    legs = values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    observations = legs["HYG"]["observations"]
    assert isinstance(observations, list)
    observations[1], observations[2] = observations[2], observations[1]

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_leg_observations_invalid" in result.markdown


def assert_fewer_than_30_common_sessions_blocks_the_board_with_a_precise_reason() -> None:
    values = complete_raw_macro_values()
    legs = values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    observations = legs["HYG"]["observations"]
    assert isinstance(observations, list)
    observations.pop()

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_fewer_than_30_common_sessions" in result.markdown


def assert_missing_ratio_constituent_blocks_the_board_with_a_precise_reason() -> None:
    values = complete_raw_macro_values()
    legs = values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    del legs["LQD"]

    result = run_macro(RecordingProvider(values))

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_legs_invalid" in result.markdown


def assert_missing_latest_session_blocks_the_board_with_a_precise_reason() -> None:
    values = complete_raw_macro_values(sessions=XNYS_SESSIONS_WITH_PREVIOUS)
    legs = values["hyg_lqd_history"].value["legs"]
    assert isinstance(legs, dict)
    observations = legs["HYG"]["observations"]
    assert isinstance(observations, list)
    observations.pop()

    result = run_macro(
        RecordingProvider(values),
        StaticXNYSCalendar(XNYS_SESSIONS_WITH_PREVIOUS),
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: hyg_lqd_history_latest_session_missing" in result.markdown


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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "research_as_of_invalid" in result.markdown


def assert_timezone_less_research_as_of_blocks_the_board() -> None:
    provider = RecordingProvider(complete_raw_macro_values())

    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of="2026-07-25T12:00:00",
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": provider},
        session_calendar=DEFAULT_XNYS_CALENDAR,
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
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
        primary_event_source_registry=DEFAULT_PRIMARY_EVENT_SOURCE_REGISTRY,
    )

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None
    assert "data_gap: ndx_rut_history_leg_source_mismatch" in result.markdown


def assert_unparseable_market_as_of_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    for name in ("vix", "vix3m", "dxy", "wti", "gold", "hyg_lqd_history", "ndx_rut_history"):
        original = values[name]
        values[name] = fixture_field_value(
            name, original.value, original.source, "not-a-time"
        )
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "vix_as_of_invalid" in result.markdown


def assert_proxy_market_source_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    original = values["hyg_lqd_history"]
    values["hyg_lqd_history"] = fixture_field_value(
        "hyg_lqd_history", original.value, "proxy_vendor", original.as_of
    )
    provider = RecordingProvider(values)

    result = run_macro(provider)

    assert result.status == "blocked"
    assert result.board_html is None
    assert result.markdown is not None and "data_gap: hyg_lqd_history" in result.markdown


def assert_stale_ratio_window_blocks_the_board() -> None:
    values = complete_raw_macro_values()
    for name in ("vix", "vix3m", "dxy", "wti", "gold", "hyg_lqd_history", "ndx_rut_history"):
        original = values[name]
        values[name] = fixture_field_value(
            name, original.value, original.source, "2026-06-29"
        )
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
    assert_primary_event_evidence_is_visible_in_the_brief_and_board()
    assert_each_event_keeps_its_own_source_time()
    assert_mismatched_event_source_blocks_the_board()
    assert_unregistered_event_identity_blocks_the_board()
    assert_missing_event_source_time_blocks_the_board()
    assert_invalid_event_source_time_blocks_the_board()
    assert_missing_event_evidence_kind_blocks_the_board()
    assert_unconfirmed_primary_event_source_blocks_the_board()
    assert_aggregated_event_evidence_blocks_the_board()
    assert_mislabeled_aggregated_event_url_blocks_the_board()
    assert_missing_primary_source_registry_blocks_the_board()
    assert_invalid_event_time_blocks_the_board()
    assert_timezone_less_event_time_blocks_the_board()
    assert_representative_fixture_board_is_written_to_the_caller_temp_directory()
    assert_event_brief_keeps_only_major_events_in_its_time_windows()
    assert_non_official_treasury_field_blocks_the_board()
    assert_unclassified_macro_event_blocks_the_board()
    assert_missing_frozen_field_keeps_brief_and_suppresses_board()
    assert_uncompleted_market_snapshot_blocks_the_board()
    assert_non_xnys_observation_blocks_the_board_with_a_precise_reason()
    assert_duplicate_observation_date_blocks_the_board_with_a_precise_reason()
    assert_unordered_observations_block_the_board_with_a_precise_reason()
    assert_fewer_than_30_common_sessions_blocks_the_board_with_a_precise_reason()
    assert_missing_ratio_constituent_blocks_the_board_with_a_precise_reason()
    assert_missing_latest_session_blocks_the_board_with_a_precise_reason()
    assert_invalid_research_as_of_blocks_the_board()
    assert_timezone_less_research_as_of_blocks_the_board()
    assert_cross_source_ratio_legs_do_not_form_a_board()
    assert_unparseable_market_as_of_blocks_the_board()
    assert_proxy_market_source_blocks_the_board()
    assert_stale_ratio_window_blocks_the_board()
    print("macro research run selftest passed")


if __name__ == "__main__":
    main()
