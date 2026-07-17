#!/usr/bin/env python3
"""Static private registry for Artifact Packet Board adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, Mapping

from artifact_packet import ArtifactPacketError
import artifact_packet_instrument_adapter as instrument
import artifact_packet_macro_adapter as macro


RenderBoard = Callable[[Mapping[str, Any], str, str], bytes]
ValidateBoard = Callable[[Mapping[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class BoardAdapter:
    """One statically registered Board payload policy and renderer."""

    board_id: str
    payload_major: str
    payload_version: str
    validate_snapshot: ValidateBoard
    render: RenderBoard
    freshness_policies: Mapping[str, timedelta | None]


BOARD_ADAPTERS: Mapping[tuple[str, str], BoardAdapter] = {
    (instrument.BOARD_ID, "1"): BoardAdapter(
        board_id=instrument.BOARD_ID,
        payload_major="1",
        payload_version=instrument.PAYLOAD_VERSION,
        validate_snapshot=instrument.validate_instrument_snapshot,
        render=instrument.render_board,
        freshness_policies=instrument.FRESHNESS_POLICIES,
    ),
    (macro.BOARD_ID, "1"): BoardAdapter(
        board_id=macro.BOARD_ID,
        payload_major="1",
        payload_version=macro.PAYLOAD_VERSION,
        validate_snapshot=macro.validate_macro_snapshot,
        render=macro.render_board,
        freshness_policies=macro.FRESHNESS_POLICIES,
    ),
}


def resolve_board_adapter(snapshot: Mapping[str, Any]) -> BoardAdapter:
    """Resolve a known Board and payload major without dynamic discovery."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    board_id = snapshot.get("board")
    known_boards = {adapter.board_id for adapter in BOARD_ADAPTERS.values()}
    if board_id not in known_boards:
        raise ArtifactPacketError("board_invalid")
    payload_version = snapshot.get("payload_version")
    if not isinstance(payload_version, str):
        raise ArtifactPacketError("payload_version_invalid")
    adapter = BOARD_ADAPTERS.get((board_id, payload_version.partition(".")[0]))
    if adapter is None or payload_version != adapter.payload_version:
        raise ArtifactPacketError("payload_version_invalid")
    return adapter


validate_instrument_snapshot = instrument.validate_instrument_snapshot
validate_macro_snapshot = macro.validate_macro_snapshot

