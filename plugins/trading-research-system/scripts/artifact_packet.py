#!/usr/bin/env python3
"""Public Artifact Packet facade over a shared core and static Board registry."""

from __future__ import annotations

from typing import Any, Mapping

from artifact_packet_board_adapters import BOARD_ADAPTERS, resolve_board_adapter
from artifact_packet_core import (
    ArtifactPacket,
    ArtifactPacketError,
    BoardAdapter,
    SCHEMA_VERSION,
    build_artifact_packet as _build_artifact_packet,
    canonical_json_bytes,
    sha256_hex,
    validate_snapshot,
    write_artifact_packet,
)


def build_artifact_packet(
    snapshot: Mapping[str, Any],
    *,
    default_view: str = "Overview",
    presentation_state: str = "ready",
) -> ArtifactPacket:
    """Validate one Board snapshot and return its canonical artifact packet."""

    return _build_artifact_packet(
        snapshot,
        _resolve_valid_schema_adapter(snapshot),
        default_view=default_view,
        presentation_state=presentation_state,
    )


def validate_board_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Dispatch a versioned Board snapshot through the static adapter registry."""

    adapter = _resolve_valid_schema_adapter(snapshot)
    return validate_snapshot(snapshot, adapter)


def validate_instrument_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible Instrument validation entrypoint."""

    return validate_snapshot(snapshot, BOARD_ADAPTERS[("instrument_research", "1")])


def validate_macro_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible Macro validation entrypoint."""

    return validate_snapshot(snapshot, BOARD_ADAPTERS[("macro_regime", "1")])


def validate_portfolio_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible Portfolio validation entrypoint."""

    return validate_snapshot(snapshot, BOARD_ADAPTERS[("portfolio_risk", "1")])


def render_research_brief(
    snapshot: Mapping[str, Any],
    default_view: str,
    presentation_state: str,
) -> bytes:
    """Render one Board through its purpose-specific renderer."""

    return resolve_board_adapter(snapshot).render(snapshot, default_view, presentation_state)


def render_instrument_research_brief(
    snapshot: Mapping[str, Any],
    default_view: str,
    presentation_state: str,
) -> bytes:
    """Backward-compatible Instrument-only render entrypoint."""

    return BOARD_ADAPTERS[("instrument_research", "1")].render(
        snapshot,
        default_view,
        presentation_state,
    )


def _resolve_valid_schema_adapter(snapshot: Mapping[str, Any]) -> BoardAdapter:
    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    return resolve_board_adapter(snapshot)
