#!/usr/bin/env python3
"""Behavior checks for the stateless research-run seam."""

from __future__ import annotations

import subprocess

from stateless_research_run import (
    FieldValue,
    LongbridgeAvailability,
    ResearchRequest,
    SourceUnavailable,
    preflight_longbridge,
    run_stateless_research,
)


class RecordingProvider:
    def __init__(self, values: dict[str, FieldValue]) -> None:
        self.values = values
        self.requests: list[tuple[str, ...]] = []

    def fetch_many(self, fields: tuple[str, ...]) -> dict[str, FieldValue]:
        self.requests.append(fields)
        return {field: self.values[field] for field in fields if field in self.values}


class UnavailableProvider:
    def __init__(self) -> None:
        self.requests: list[tuple[str, ...]] = []

    def fetch_many(self, fields: tuple[str, ...]) -> dict[str, FieldValue]:
        self.requests.append(fields)
        raise SourceUnavailable("timeout")


def field(name: str, source: str = "longbridge") -> FieldValue:
    return FieldValue(
        name=name,
        status="available",
        value=f"{name}-value",
        source=source,
        as_of="2026-07-25T20:00:00Z",
    )


def assert_source_choice_is_required_even_when_longbridge_is_authorized() -> None:
    result = run_stateless_research(
        ResearchRequest(required_fields=("market_quote",)),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={
            "longbridge": RecordingProvider({"market_quote": field("market_quote")})
        },
    )

    assert result.status == "source_choice_required"
    assert result.profile is None
    assert result.longbridge == {"cli_present": True, "authorized": True}


def assert_authorized_longbridge_uses_one_primary_batch_without_fallback() -> None:
    longbridge = RecordingProvider(
        {
            "market_quote": field("market_quote"),
            "finance_calendar": field("finance_calendar"),
        }
    )
    portable = RecordingProvider({"market_quote": field("market_quote", "yfinance")})

    result = run_stateless_research(
        ResearchRequest(
            required_fields=("market_quote", "finance_calendar"),
            source_choice="longbridge",
        ),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={"longbridge": longbridge, "portable": portable},
    )

    assert result.status == "complete"
    assert result.profile == "longbridge"
    assert longbridge.requests == [("market_quote", "finance_calendar")]
    assert portable.requests == []
    assert {value.source for value in result.fields} == {"longbridge"}


def assert_preflight_fails_closed_when_cli_disappears_after_detection() -> None:
    def missing_runner(_command: tuple[str, ...]) -> tuple[int, str]:
        raise FileNotFoundError("longbridge")

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=missing_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_fails_closed_when_cli_status_times_out() -> None:
    def timeout_runner(command: tuple[str, ...]) -> tuple[int, str]:
        raise subprocess.TimeoutExpired(command, 5)

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=timeout_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_accepts_active_nested_token_status() -> None:
    def active_token_runner(_command: tuple[str, ...]) -> tuple[int, str]:
        return 0, '{"token": {"status": "active"}}'

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=active_token_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": True}


def assert_preflight_rejects_unknown_nested_token_status() -> None:
    def unknown_token_runner(_command: tuple[str, ...]) -> tuple[int, str]:
        return 0, '{"token": {"status": "unknown"}}'

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=unknown_token_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_ignores_active_account_status() -> None:
    def active_account_runner(_command: tuple[str, ...]) -> tuple[int, str]:
        return 0, '{"account": {"status": "active"}}'

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=active_account_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_rejects_active_top_level_status() -> None:
    def active_status_runner(_command: tuple[str, ...]) -> tuple[int, str]:
        return 0, '{"status": "active"}'

    availability = preflight_longbridge(
        which=lambda _name: "/usr/local/bin/longbridge",
        command_runner=active_status_runner,
    )

    assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_rejects_active_token_after_explicit_root_denial() -> None:
    for key in ("authorized", "authenticated", "token_valid", "valid"):
        def contradictory_status_runner(_command: tuple[str, ...], key: str = key) -> tuple[int, str]:
            return 0, f'{{"{key}": false, "token": {{"status": "active"}}}}'

        availability = preflight_longbridge(
            which=lambda _name: "/usr/local/bin/longbridge",
            command_runner=contradictory_status_runner,
        )

        assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_preflight_fails_closed_for_missing_or_malformed_token_status() -> None:
    for output in ("not-json", "{}", '{"token": {}}'):
        def incomplete_status_runner(
            _command: tuple[str, ...], output: str = output
        ) -> tuple[int, str]:
            return 0, output

        availability = preflight_longbridge(
            which=lambda _name: "/usr/local/bin/longbridge",
            command_runner=incomplete_status_runner,
        )

        assert availability.as_dict() == {"cli_present": True, "authorized": False}


def assert_source_error_falls_back_once_for_all_unresolved_fields() -> None:
    longbridge = UnavailableProvider()
    portable = RecordingProvider(
        {
            "market_quote": field("market_quote", "yfinance"),
            "finance_calendar": field("finance_calendar", "yfinance"),
        }
    )

    result = run_stateless_research(
        ResearchRequest(
            required_fields=("market_quote", "finance_calendar"),
            source_choice="longbridge",
        ),
        availability=LongbridgeAvailability(cli_present=True, authorized=True),
        providers={"longbridge": longbridge, "portable": portable},
    )

    assert result.status == "complete"
    assert longbridge.requests == [("market_quote", "finance_calendar")]
    assert portable.requests == [("market_quote", "finance_calendar")]
    assert {value.source for value in result.fields} == {"yfinance"}


def assert_unavailable_longbridge_enters_portable_without_a_choice() -> None:
    portable = RecordingProvider({"market_quote": field("market_quote", "yfinance")})

    result = run_stateless_research(
        ResearchRequest(required_fields=("market_quote",)),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": portable},
    )

    assert result.status == "complete"
    assert result.profile == "portable"
    assert portable.requests == [("market_quote",)]


def assert_private_broker_fields_are_rejected_before_provider_access() -> None:
    for private_field in ("account", "holdings", "orders"):
        try:
            ResearchRequest(required_fields=(private_field,))
        except ValueError as error:
            assert str(error) == "private_field_not_allowed"
        else:
            raise AssertionError(f"private field was accepted: {private_field}")


def main() -> None:
    assert_source_choice_is_required_even_when_longbridge_is_authorized()
    assert_authorized_longbridge_uses_one_primary_batch_without_fallback()
    assert_preflight_fails_closed_when_cli_disappears_after_detection()
    assert_preflight_fails_closed_when_cli_status_times_out()
    assert_preflight_accepts_active_nested_token_status()
    assert_preflight_rejects_unknown_nested_token_status()
    assert_preflight_ignores_active_account_status()
    assert_preflight_rejects_active_top_level_status()
    assert_preflight_rejects_active_token_after_explicit_root_denial()
    assert_preflight_fails_closed_for_missing_or_malformed_token_status()
    assert_source_error_falls_back_once_for_all_unresolved_fields()
    assert_unavailable_longbridge_enters_portable_without_a_choice()
    assert_private_broker_fields_are_rejected_before_provider_access()
    print("stateless research run selftest passed")


if __name__ == "__main__":
    main()
