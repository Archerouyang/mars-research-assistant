#!/usr/bin/env python3
"""Host-side boundary for direct public-web Macro observations.

The portable Skill cannot call Codex's web-search tool itself.  It therefore
accepts only this ephemeral capture object, which the host creates after it
has searched for and directly opened every exact source in the Mars contract.
Raw responses stay outside the result and are never persisted by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from mars_observation_adapter import ObservationAdapterError, load_mars_source_contract


DIRECT_WEB_OPEN_METHOD = "web_search_then_direct_open"


class MarsWebCaptureError(ValueError):
    """Raised when the host has not provided a complete direct-web capture."""


@dataclass(frozen=True)
class MarsWebCapture:
    """Ephemeral direct-web capture; only Macro Preflight may consume it."""

    _source_payloads: Mapping[str, Any]
    acquired_at: str


def capture_mars_direct_web_observations(
    source_payloads: Mapping[str, Any],
    direct_open_receipts: Mapping[str, Any],
    *,
    acquired_at: str,
) -> MarsWebCapture:
    """Bind source payloads to direct-open receipts before Macro Preflight.

    `source_payloads` is intentionally not accepted by the public Macro Board
    runner.  It exists only at the host acquisition boundary, immediately after
    a web search and direct page open.  The returned capture is in-memory only.
    """

    if not isinstance(source_payloads, Mapping) or not isinstance(direct_open_receipts, Mapping):
        raise MarsWebCaptureError("direct_web_capture_invalid")
    acquired_timestamp = _parse_timestamp(acquired_at, "capture_acquired_at")
    contract = load_mars_source_contract()
    fields = contract["fields"]
    market_session = contract["market_session"]
    expected_urls = {
        str(field["source_id"]): str(field["source_url"])
        for field in fields
    }
    expected_urls[str(market_session["source_id"])] = str(market_session["source_url"])
    for source in contract.get("event_sources", []):
        if not isinstance(source, Mapping):
            raise MarsWebCaptureError("direct_web_capture_contract_invalid")
        expected_urls[str(source["source_id"])] = str(source["source_url"])
    if set(direct_open_receipts) != set(expected_urls):
        raise MarsWebCaptureError("direct_web_capture_receipts_incomplete")
    if set(source_payloads) - set(expected_urls) - {"fixture_kind"}:
        raise MarsWebCaptureError("direct_web_capture_source_not_supported")
    for source_id, expected_url in expected_urls.items():
        payload = source_payloads.get(source_id)
        receipt = direct_open_receipts.get(source_id)
        if not isinstance(receipt, Mapping):
            raise MarsWebCaptureError(f"{source_id}:direct_web_capture_missing")
        if set(receipt) != {"source_url", "opened_at", "method"}:
            raise MarsWebCaptureError(f"{source_id}:direct_web_receipt_invalid")
        if receipt.get("source_url") != expected_url:
            raise MarsWebCaptureError(f"{source_id}:direct_web_source_url_mismatch")
        if receipt.get("method") != DIRECT_WEB_OPEN_METHOD:
            raise MarsWebCaptureError(f"{source_id}:direct_web_method_invalid")
        opened_at = _parse_timestamp(receipt.get("opened_at"), f"{source_id}:direct_web_opened_at")
        if opened_at > acquired_timestamp:
            raise MarsWebCaptureError(f"{source_id}:direct_web_opened_after_capture")
        if payload is not None:
            if not isinstance(payload, Mapping):
                raise MarsWebCaptureError(f"{source_id}:direct_web_payload_invalid")
            if payload.get("source_url") != expected_url:
                raise MarsWebCaptureError(f"{source_id}:direct_web_source_url_mismatch")
            payload_retrieved_at = _parse_timestamp(
                payload.get("retrieved_at"), f"{source_id}:direct_web_payload_retrieved_at"
            )
            if opened_at != payload_retrieved_at:
                raise MarsWebCaptureError(f"{source_id}:direct_web_time_mismatch")
    return MarsWebCapture(
        _source_payloads=source_payloads,
        acquired_at=acquired_at,
    )


def normalize_captured_mars_observations(
    capture: MarsWebCapture,
    as_of: str,
) -> tuple[dict[str, Any], ...]:
    """Normalize only a typed direct-web capture; reject generic payloads."""

    if not isinstance(capture, MarsWebCapture):
        raise MarsWebCaptureError("direct_web_capture_required")
    try:
        from mars_observation_adapter import normalize_mars_observation_run

        run = normalize_mars_observation_run(capture._source_payloads, as_of)
    except ObservationAdapterError as error:
        raise MarsWebCaptureError(str(error)) from error
    return run.observations


def _parse_timestamp(value: Any, context: str) -> datetime:
    if not isinstance(value, str):
        raise MarsWebCaptureError(f"{context}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise MarsWebCaptureError(f"{context}_invalid") from error
    if parsed.tzinfo is None:
        raise MarsWebCaptureError(f"{context}_invalid")
    return parsed
