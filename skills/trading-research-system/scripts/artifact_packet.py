#!/usr/bin/env python3
"""Public Artifact Packet facade over a shared core and static Board registry."""

from __future__ import annotations

from typing import Any, Mapping

from artifact_packet_board_adapters import resolve_board_adapter
from artifact_packet_core import (
    ArtifactPacket,
    ArtifactPacketError,
    BoardAdapter as _BoardAdapter,
    HTML_HARD_LIMIT_BYTES,
    MANIFEST_HARD_LIMIT_BYTES,
    SCHEMA_VERSION as _SCHEMA_VERSION,
    SNAPSHOT_HARD_LIMIT_BYTES,
    build_artifact_packet as _build_artifact_packet,
    canonical_json_bytes,
    sha256_hex,
    write_artifact_packet,
)


__all__ = (
    "ArtifactPacket",
    "ArtifactPacketError",
    "HTML_HARD_LIMIT_BYTES",
    "MANIFEST_HARD_LIMIT_BYTES",
    "SNAPSHOT_HARD_LIMIT_BYTES",
    "build_artifact_packet",
    "canonical_json_bytes",
    "sha256_hex",
    "write_artifact_packet",
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


def _resolve_valid_schema_adapter(snapshot: Mapping[str, Any]) -> _BoardAdapter:
    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    if snapshot.get("schema_version") != _SCHEMA_VERSION:
        raise ArtifactPacketError("schema_version_invalid")
    return resolve_board_adapter(snapshot)
