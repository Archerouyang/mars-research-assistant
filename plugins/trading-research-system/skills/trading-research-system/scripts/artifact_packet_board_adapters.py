#!/usr/bin/env python3
"""Static private registry for Artifact Packet Board adapters."""

from __future__ import annotations

from typing import Any, Mapping

from artifact_packet_core import ArtifactPacketError, BoardAdapter
import artifact_packet_instrument_adapter as instrument
import artifact_packet_macro_adapter as macro
import artifact_packet_portfolio_adapter as portfolio


BOARD_ADAPTERS: Mapping[tuple[str, str], BoardAdapter] = {
    (instrument.BOARD_ID, "1"): BoardAdapter(
        board_id=instrument.BOARD_ID,
        payload_version=instrument.PAYLOAD_VERSION,
        validate_payload=instrument.validate_payload,
        render=instrument.render_board,
        allowed_modules=frozenset(instrument.ALL_INSTRUMENT_MODULES),
        freshness_policies=instrument.FRESHNESS_POLICIES,
    ),
    (macro.BOARD_ID, "1"): BoardAdapter(
        board_id=macro.BOARD_ID,
        payload_version=macro.PAYLOAD_VERSION,
        validate_payload=macro.validate_payload,
        render=macro.render_board,
        allowed_modules=frozenset(macro.REQUIRED_MACRO_MODULES),
        freshness_policies=macro.FRESHNESS_POLICIES,
    ),
    (portfolio.BOARD_ID, "1"): BoardAdapter(
        board_id=portfolio.BOARD_ID,
        payload_version=portfolio.PAYLOAD_VERSION,
        validate_payload=portfolio.validate_payload,
        render=portfolio.render_board,
        allowed_modules=frozenset(portfolio.REQUIRED_PORTFOLIO_MODULES),
        freshness_policies=portfolio.FRESHNESS_POLICIES,
        allowed_snapshot_action_terms=frozenset({"broker"}),
    ),
}


def resolve_board_adapter(snapshot: Mapping[str, Any]) -> BoardAdapter:
    """Resolve a known Board and payload major without dynamic discovery."""

    if not isinstance(snapshot, Mapping):
        raise ArtifactPacketError("schema_invalid")
    board_id = snapshot.get("board")
    known_boards = {adapter.board_id for adapter in BOARD_ADAPTERS.values()}
    if not isinstance(board_id, str) or board_id not in known_boards:
        raise ArtifactPacketError("board_invalid")
    payload_version = snapshot.get("payload_version")
    if not isinstance(payload_version, str):
        raise ArtifactPacketError("payload_version_invalid")
    adapter = BOARD_ADAPTERS.get((board_id, payload_version.partition(".")[0]))
    if adapter is None or payload_version != adapter.payload_version:
        raise ArtifactPacketError("payload_version_invalid")
    return adapter
