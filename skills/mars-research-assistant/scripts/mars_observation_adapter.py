#!/usr/bin/env python3
"""Normalize direct Mars 1.0 source payloads without fetching or persisting them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping


RETAINED_RAW_FIELD_IDS = frozenset(
    {
        "rates.us_2y_yield",
        "rates.us_10y_yield",
        "rates.us_30y_yield",
        "volatility.vix_close",
        "volatility.vix3m_close",
        "equity.ndx_close",
        "equity.rut_close",
        "liquidity.reserve_balances",
        "liquidity.tga_balance",
        "liquidity.on_rrp_usage",
        "events.seven_day_allowlist",
        "policy.us_executive_actions",
    }
)
EXCLUDED_UNVERIFIED_FIELD_IDS = frozenset(
    {
        "credit.hyg_close",
        "credit.lqd_close",
        "equity.spx_close",
    }
)


class ObservationAdapterError(ValueError):
    """Raised when a supported raw observation cannot be admitted exactly."""


@dataclass(frozen=True)
class MarsRawObservationRun:
    """Validated raw observations and the freshness assertions that admitted them."""

    observations: tuple[dict[str, Any], ...]
    completed_market_session: dict[str, Any]
    latest_official_observations: tuple[dict[str, str], ...]


def load_mars_source_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = path or (
        Path(__file__).resolve().parents[1]
        / "references"
        / "mars-1-0-observation-source-contracts.json"
    )
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ObservationAdapterError(f"source_contract_invalid:{error}") from error
    if (
        not isinstance(contract, dict)
        or contract.get("contract_version") != "mars-observation-adapter-v1"
        or not isinstance(contract.get("fields"), list)
    ):
        raise ObservationAdapterError("source_contract_invalid")
    required = {
        "field_id",
        "source_id",
        "source_url",
        "source_timing",
        "unit",
        "collection_key",
        "date_key",
        "value_key",
        "raw_field_path",
    }
    safety = contract.get("safety")
    if not isinstance(safety, Mapping) or any(
        safety.get(key) is not False
        for key in (
            "adapter_may_call_network",
            "persist_raw_source_payloads",
            "caller_derived_values_allowed",
            "broker_runtime_assumptions_allowed",
            "partial_board_allowed",
        )
    ) or any(
        safety.get(key) is not True
        for key in (
            "actual_latest_completed_market_session_required",
            "actual_latest_official_observation_required",
        )
    ):
        raise ObservationAdapterError("source_contract_invalid")
    fields = contract["fields"]
    event_contract = contract.get("event_contract")
    event_sources = contract.get("event_sources")
    expected_standard_fields = RETAINED_RAW_FIELD_IDS - {"events.seven_day_allowlist"}
    if (
        not fields
        or any(not isinstance(field, dict) or not required.issubset(field) for field in fields)
        or len({field["field_id"] for field in fields}) != len(fields)
        or {field["field_id"] for field in fields} != expected_standard_fields
    ):
        raise ObservationAdapterError("source_contract_invalid")
    _validate_event_contract(event_contract, event_sources)
    excluded = contract.get("excluded_fields")
    if (
        not isinstance(excluded, list)
        or {item.get("field_id") for item in excluded if isinstance(item, Mapping)}
        != EXCLUDED_UNVERIFIED_FIELD_IDS
    ):
        raise ObservationAdapterError("source_contract_invalid")
    market_session = contract.get("market_session")
    required_market_session = {
        "source_id",
        "source_url",
        "source_timing",
        "latest_session_key",
        "status_key",
        "required_status",
        "raw_field_path",
    }
    if (
        not isinstance(market_session, Mapping)
        or not required_market_session.issubset(market_session)
        or market_session.get("source_timing") != "completed_market"
    ):
        raise ObservationAdapterError("source_contract_invalid")
    return contract


def _validate_event_contract(event_contract: Any, event_sources: Any) -> None:
    required_contract = {
        "field_id",
        "source_id",
        "source_url",
        "source_timing",
        "unit",
        "raw_field_path",
        "allowed_categories",
        "source_ids",
    }
    required_source = {"source_id", "source_url", "allowed_categories"}
    if (
        not isinstance(event_contract, Mapping)
        or set(event_contract) != required_contract
        or event_contract.get("field_id") != "events.seven_day_allowlist"
        or event_contract.get("source_id") != "official_macro_event_allowlist"
        or event_contract.get("source_url") != "multi_direct_sources"
        or event_contract.get("source_timing") != "event"
        or event_contract.get("unit") != "event_set"
        or not isinstance(event_contract.get("raw_field_path"), list)
        or not isinstance(event_contract.get("allowed_categories"), list)
        or not isinstance(event_contract.get("source_ids"), list)
        or not isinstance(event_sources, list)
        or any(not isinstance(item, Mapping) or set(item) != required_source for item in event_sources)
    ):
        raise ObservationAdapterError("source_contract_invalid")
    source_ids = [item["source_id"] for item in event_sources]
    if (
        len(source_ids) != len(set(source_ids))
        or source_ids != event_contract["source_ids"]
        or not all(isinstance(source_id, str) and source_id for source_id in source_ids)
        or not all(isinstance(item["source_url"], str) and item["source_url"].startswith("https://") for item in event_sources)
        or not all(
            isinstance(category, str) and category
            for category in event_contract["allowed_categories"]
        )
        or not all(
            isinstance(category, str) and category in event_contract["allowed_categories"]
            for item in event_sources
            for category in item["allowed_categories"]
        )
    ):
        raise ObservationAdapterError("source_contract_invalid")


def normalize_mars_observations(
    source_payloads: Mapping[str, Any],
    as_of: str,
) -> list[dict[str, Any]]:
    """Return the retained raw base observations with normalized histories only."""

    return list(normalize_mars_observation_run(source_payloads, as_of).observations)


def normalize_mars_observation_run(
    source_payloads: Mapping[str, Any],
    as_of: str,
) -> MarsRawObservationRun:
    """Validate a complete one-run raw-observation boundary for Mars Macro."""

    if not isinstance(source_payloads, Mapping):
        raise ObservationAdapterError("source_payloads_invalid")
    as_of_timestamp = _parse_timestamp(as_of, "as_of")
    contract = load_mars_source_contract()
    fields = contract.get("fields")
    if not isinstance(fields, list):
        raise ObservationAdapterError("source_contract_invalid")
    event_contract = contract.get("event_contract")
    event_sources = contract.get("event_sources")
    if not isinstance(event_contract, Mapping) or not isinstance(event_sources, list):
        raise ObservationAdapterError("source_contract_invalid")
    market_session = contract.get("market_session")
    if not isinstance(market_session, Mapping):
        raise ObservationAdapterError("source_contract_invalid")
    source_ids = {str(field["source_id"]) for field in fields if isinstance(field, Mapping)}
    source_ids.add(str(market_session["source_id"]))
    source_ids.update(str(item["source_id"]) for item in event_sources)
    extras = sorted(set(source_payloads) - source_ids - {"fixture_kind"})
    if extras:
        raise ObservationAdapterError(f"source_payload_not_supported:{extras[0]}")

    completed_market_session = _normalize_completed_market_session(
        market_session,
        source_payloads,
        as_of_timestamp,
    )
    rows = [_normalize_field(dict(field), source_payloads, as_of_timestamp) for field in fields]
    rows.append(_normalize_event_set(event_contract, event_sources, source_payloads, as_of_timestamp))
    _align_completed_market_histories(
        rows,
        as_of_timestamp.date(),
        completed_market_session["market_reference_date"],
    )
    latest_official_observations = _validate_latest_official_observations(
        rows,
        source_payloads,
        as_of_timestamp,
    )
    return MarsRawObservationRun(
        observations=tuple(sorted(rows, key=lambda row: str(row["field_id"]))),
        completed_market_session=completed_market_session,
        latest_official_observations=tuple(latest_official_observations),
    )


def _normalize_completed_market_session(
    market_session: Mapping[str, Any],
    source_payloads: Mapping[str, Any],
    as_of: datetime,
) -> dict[str, Any]:
    source_id = str(market_session["source_id"])
    payload = source_payloads.get(source_id)
    if not isinstance(payload, Mapping):
        raise ObservationAdapterError("completed_market_session:source_payload_missing")
    if payload.get("source_url") != market_session["source_url"]:
        raise ObservationAdapterError("completed_market_session:source_url_mismatch")
    retrieved_at = payload.get("retrieved_at")
    retrieved_timestamp = _parse_timestamp(retrieved_at, "completed_market_session:retrieved_at")
    if retrieved_timestamp > as_of:
        raise ObservationAdapterError("completed_market_session:retrieved_at_after_as_of")
    status_key = str(market_session["status_key"])
    if payload.get(status_key) != market_session["required_status"]:
        raise ObservationAdapterError("completed_market_session:not_completed")
    latest_key = str(market_session["latest_session_key"])
    latest_date = _parse_date(payload.get(latest_key), "completed_market_session:latest_date")
    # A source-declared completed session may share the UTC decision date after
    # the U.S. market closes. Only a future session is impossible here.
    if latest_date > as_of.date():
        raise ObservationAdapterError("completed_market_session:not_completed")
    return {
        "source_id": source_id,
        "source_url": str(market_session["source_url"]),
        "source_timing": "completed_market",
        "retrieval_method": "direct_web_capture",
        "data_as_of": str(retrieved_at),
        "market_reference_date": latest_date.isoformat(),
        "raw_field_path": list(market_session["raw_field_path"]),
    }


def _normalize_field(
    field: dict[str, Any],
    source_payloads: Mapping[str, Any],
    as_of: datetime,
) -> dict[str, Any]:
    field_id = str(field["field_id"])
    source_id = str(field["source_id"])
    payload = source_payloads.get(source_id)
    if not isinstance(payload, Mapping):
        raise ObservationAdapterError(f"{field_id}:source_payload_missing")
    if payload.get("source_url") != field["source_url"]:
        raise ObservationAdapterError(f"{field_id}:source_url_mismatch")
    retrieved_at = payload.get("retrieved_at")
    retrieved_timestamp = _parse_timestamp(retrieved_at, f"{field_id}:retrieved_at")
    if retrieved_timestamp > as_of:
        raise ObservationAdapterError(f"{field_id}:retrieved_at_after_as_of")
    collection = payload.get(field["collection_key"])
    if not isinstance(collection, list) or (
        not collection and field["unit"] != "policy_evidence_set"
    ):
        raise ObservationAdapterError(f"{field_id}:source_collection_missing")

    if field["unit"] == "policy_evidence_set":
        return _normalize_policy_evidence(field, collection, retrieved_at, as_of)

    filter_spec = field.get("filter")
    records = [
        item
        for item in collection
        if isinstance(item, Mapping) and _matches_filter(item, filter_spec)
    ]
    if not records:
        raise ObservationAdapterError(f"{field_id}:raw_field_missing")

    history: list[dict[str, Any]] = []
    previous_date: date | None = None
    for record in records:
        raw_date = record.get(field["date_key"])
        parsed_date = _parse_date(raw_date, f"{field_id}:history_date")
        if previous_date is not None and parsed_date <= previous_date:
            raise ObservationAdapterError(f"{field_id}:history_date_not_ascending")
        previous_date = parsed_date
        value = _parse_number(record.get(field["value_key"]), f"{field_id}:raw_value")
        value *= float(field.get("scale", 1.0))
        history.append({"date": parsed_date.isoformat(), "value": value})

    timing = str(field["source_timing"])
    latest = history[-1]
    if timing == "official_release" and _parse_date(latest["date"], field_id) > as_of.date():
        raise ObservationAdapterError(f"{field_id}:reference_period_after_as_of")
    row: dict[str, Any] = {
        "field_id": field_id,
        "value": latest["value"],
        "unit": str(field["unit"]),
        "status": "available",
        "data_as_of": str(retrieved_at),
        "source_id": source_id,
        "source_url": str(field["source_url"]),
        "source_timing": timing,
        "retrieval_method": "direct_web_capture",
        "raw_field_path": list(field["raw_field_path"]),
        "history": history,
    }
    if timing == "official_release":
        row["reference_period"] = latest["date"]
    return row


def _normalize_policy_evidence(
    field: Mapping[str, Any],
    records: list[Any],
    retrieved_at: Any,
    as_of: datetime,
) -> dict[str, Any]:
    """Admit only a bounded White House action summary, never raw page content."""

    retrieved = _parse_timestamp(retrieved_at, "policy:retrieved_at")
    if as_of - retrieved > timedelta(hours=24):
        raise ObservationAdapterError("policy.us_executive_actions:source_stale")
    normalized: list[dict[str, str]] = []
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {
            "id", "title", "published_at", "source_url", "policy_status", "posture_effect"
        }:
            raise ObservationAdapterError("policy.us_executive_actions:record_shape_invalid")
        if not all(
            isinstance(record[key], str) and record[key].strip()
            for key in (
                "id", "title", "published_at", "source_url", "policy_status", "posture_effect"
            )
        ):
            raise ObservationAdapterError("policy.us_executive_actions:record_shape_invalid")
        if record["policy_status"] not in {
            "confirmed", "stated_not_enacted", "unverified_lead"
        }:
            raise ObservationAdapterError("policy.us_executive_actions:policy_status_invalid")
        if record["posture_effect"] not in {"supports", "neutral", "pressures"}:
            raise ObservationAdapterError("policy.us_executive_actions:posture_effect_invalid")
        if record["policy_status"] == "unverified_lead" and record["posture_effect"] != "neutral":
            raise ObservationAdapterError("policy.us_executive_actions:unverified_lead_must_be_neutral")
        published = _parse_timestamp(
            record["published_at"], "policy.us_executive_actions:published_at"
        )
        if published > as_of:
            raise ObservationAdapterError(
                "policy.us_executive_actions:published_at_after_as_of"
            )
        if record["source_url"] != field["source_url"]:
            raise ObservationAdapterError("policy.us_executive_actions:record_source_url_mismatch")
        normalized.append(
            {
                "id": str(record["id"]),
                "title": str(record["title"]),
                "published_at": str(record["published_at"]),
                "source_url": str(record["source_url"]),
                "policy_status": str(record["policy_status"]),
                "posture_effect": str(record["posture_effect"]),
            }
        )
    normalized.sort(key=lambda item: (item["published_at"], item["id"]))
    return {
        "field_id": str(field["field_id"]),
        "value": normalized,
        "unit": "policy_evidence_set",
        "status": "available",
        "data_as_of": str(retrieved_at),
        "source_id": str(field["source_id"]),
        "source_url": str(field["source_url"]),
        "source_timing": "policy",
        "retrieval_method": "direct_web_capture",
        "raw_field_path": list(field["raw_field_path"]),
        "reference_period": retrieved.date().isoformat(),
    }


def _normalize_event_set(
    event_contract: Mapping[str, Any],
    event_sources: list[Mapping[str, Any]],
    source_payloads: Mapping[str, Any],
    as_of: datetime,
) -> dict[str, Any]:
    """Normalize bounded future events from every direct allowlist source."""

    normalized: list[dict[str, Any]] = []
    latest_retrieved: datetime | None = None
    for source in event_sources:
        source_id = str(source["source_id"])
        payload = source_payloads.get(source_id)
        if not isinstance(payload, Mapping):
            raise ObservationAdapterError("events.seven_day_allowlist:source_payload_missing")
        if payload.get("source_url") != source["source_url"]:
            raise ObservationAdapterError("events.seven_day_allowlist:source_url_mismatch")
        retrieved_at = payload.get("retrieved_at")
        retrieved = _parse_timestamp(retrieved_at, "events.seven_day_allowlist:retrieved_at")
        if retrieved > as_of:
            raise ObservationAdapterError("events.seven_day_allowlist:retrieved_at_after_as_of")
        if as_of - retrieved > timedelta(days=1):
            raise ObservationAdapterError("events.seven_day_allowlist:source_stale")
        records = payload.get("records")
        if not isinstance(records, list):
            raise ObservationAdapterError("events.seven_day_allowlist:source_collection_missing")
        allowed_categories = set(source["allowed_categories"])
        for record in records:
            if not isinstance(record, Mapping) or set(record) != {
                "id",
                "title",
                "category",
                "time",
                "timezone",
                "reference_period",
                "consensus",
                "previous",
                "revised_previous",
                "actual",
            }:
                raise ObservationAdapterError("events.seven_day_allowlist:record_shape_invalid")
            if not all(
                isinstance(record[key], str) and record[key].strip()
                for key in (
                    "id",
                    "title",
                    "category",
                    "time",
                    "timezone",
                    "reference_period",
                    "consensus",
                    "previous",
                )
            ) or record["category"] not in allowed_categories:
                raise ObservationAdapterError("events.seven_day_allowlist:record_shape_invalid")
            if record["revised_previous"] is not None and not isinstance(record["revised_previous"], str):
                raise ObservationAdapterError("events.seven_day_allowlist:record_shape_invalid")
            if record["actual"] is not None and not isinstance(record["actual"], str):
                raise ObservationAdapterError("events.seven_day_allowlist:record_shape_invalid")
            event_time = _parse_timestamp(record["time"], "events.seven_day_allowlist:time")
            if event_time < as_of or event_time > as_of + timedelta(days=7):
                raise ObservationAdapterError("events.seven_day_allowlist:event_outside_horizon")
            normalized.append(
                {
                    "id": str(record["id"]),
                    "title": str(record["title"]),
                    "category": str(record["category"]),
                    "time": str(record["time"]),
                    "timezone": str(record["timezone"]),
                    "reference_period": str(record["reference_period"]),
                    "consensus": str(record["consensus"]),
                    "previous": str(record["previous"]),
                    "revised_previous": record["revised_previous"],
                    "actual": record["actual"],
                    "source": source_id,
                }
            )
        latest_retrieved = max(latest_retrieved or retrieved, retrieved)
    if latest_retrieved is None:
        raise ObservationAdapterError("events.seven_day_allowlist:source_collection_missing")
    if not normalized:
        raise ObservationAdapterError("events.seven_day_allowlist:no_allowed_events_in_horizon")
    if len({item["id"] for item in normalized}) != len(normalized):
        raise ObservationAdapterError("events.seven_day_allowlist:duplicate_event_id")
    normalized.sort(key=lambda item: (item["time"], item["id"]))
    return {
        "field_id": str(event_contract["field_id"]),
        "value": normalized,
        "unit": "event_set",
        "status": "available",
        "data_as_of": _format_timestamp(latest_retrieved),
        "source_id": str(event_contract["source_id"]),
        "source_url": str(event_contract["source_url"]),
        "source_timing": "event",
        "retrieval_method": "direct_web_capture",
        "raw_field_path": list(event_contract["raw_field_path"]),
        "reference_period": "next_7_days",
    }


def _align_completed_market_histories(
    rows: list[dict[str, Any]],
    as_of_date: date,
    expected_session_date: str,
) -> None:
    market_rows = [row for row in rows if row["source_timing"] == "completed_market"]
    if not market_rows:
        return
    latest_dates = {row["history"][-1]["date"] for row in market_rows}
    if latest_dates != {expected_session_date}:
        raise ObservationAdapterError("completed_market_session_not_latest")
    selected_date = _parse_date(expected_session_date, "completed_market_date")
    if selected_date > as_of_date:
        raise ObservationAdapterError("completed_market_date_not_completed")
    common_dates = set.intersection(
        *({point["date"] for point in row["history"]} for row in market_rows)
    )
    if len(common_dates) < 21:
        raise ObservationAdapterError("completed_market_history_insufficient")
    aligned_dates = sorted(common_dates)[-21:]
    if aligned_dates[-1] != selected_date.isoformat():
        raise ObservationAdapterError("completed_market_date_not_common")
    for row in market_rows:
        values_by_date = {point["date"]: point["value"] for point in row["history"]}
        row["history"] = [
            {"date": item_date, "value": values_by_date[item_date]}
            for item_date in aligned_dates
        ]
        row["value"] = row["history"][-1]["value"]
        row["market_reference_date"] = aligned_dates[-1]


def _validate_latest_official_observations(
    rows: list[dict[str, Any]],
    source_payloads: Mapping[str, Any],
    as_of: datetime,
) -> list[dict[str, str]]:
    latest_official_observations: list[dict[str, str]] = []
    for row in rows:
        if row["source_timing"] != "official_release":
            continue
        field_id = str(row["field_id"])
        payload = source_payloads.get(row["source_id"])
        if not isinstance(payload, Mapping):
            raise ObservationAdapterError(f"{field_id}:source_payload_missing")
        if payload.get("publication_status") != "published":
            raise ObservationAdapterError(f"{field_id}:official_release_not_published")
        latest_date = _parse_date(
            payload.get("latest_official_observation"),
            f"{field_id}:latest_official_observation",
        )
        if latest_date > as_of.date():
            raise ObservationAdapterError(f"{field_id}:latest_official_observation_after_as_of")
        if row.get("reference_period") != latest_date.isoformat():
            raise ObservationAdapterError(f"{field_id}:latest_official_observation_mismatch")
        latest_official_observations.append(
            {"field_id": field_id, "reference_period": latest_date.isoformat()}
        )
    return sorted(latest_official_observations, key=lambda item: item["field_id"])


def _matches_filter(record: Mapping[str, Any], filter_spec: Any) -> bool:
    if filter_spec is None:
        return True
    if not isinstance(filter_spec, Mapping):
        return False
    return record.get(filter_spec.get("key")) == filter_spec.get("equals")


def _parse_timestamp(value: Any, context: str) -> datetime:
    if not isinstance(value, str):
        raise ObservationAdapterError(f"{context}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ObservationAdapterError(f"{context}_invalid") from error
    if parsed.tzinfo is None:
        raise ObservationAdapterError(f"{context}_invalid")
    return parsed


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_date(value: Any, context: str) -> date:
    if not isinstance(value, str):
        raise ObservationAdapterError(f"{context}_invalid")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ObservationAdapterError(f"{context}_invalid") from error


def _parse_number(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise ObservationAdapterError(f"{context}_invalid")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ObservationAdapterError(f"{context}_invalid") from error
    if not math.isfinite(parsed):
        raise ObservationAdapterError(f"{context}_invalid")
    return parsed
