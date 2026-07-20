#!/usr/bin/env python3
"""Focused contract checks for the supported Artifact Packet facade."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

import artifact_packet


REFERENCE_PACKETS = {
    "instrument-research": {
        "board": "instrument_research",
        "json": (9353, "bfdaa9d9b4b9920cbe8fd41146198093159c769ab9458a305a6fbd979ef7268f"),
        "html": (224175, "8bb59a93baf860b5a23137df127066f0fb42efc347ab707205ea3e5ae7d4909a"),
        "manifest": (851, "245bc13ae957cc09e7be7e2372dab900a955f5c0d724b5bac1e0179deb167bd2"),
    },
    "macro-regime": {
        "board": "macro_regime",
        "json": (16492, "712c4c14f256505a36ec5c1c7cb798543ec0f512bb20a12b53fc72335f367ae8"),
        "html": (1148066, "dbec6fb0de7556624fdaf4e33f0919be2c0d812c88d29e6dd2b893da044410fc"),
        "manifest": (842, "5f889e17fd70583f9dd6675092a2daff08acadfea715cab8c580ce81ce6ece45"),
    },
    "portfolio-risk": {
        "board": "portfolio_risk",
        "json": (19221, "17bcae8005789b307b038620b7f1d55a4bf03b2b9b8ea02da463d6e1fce863de"),
        "html": (1175892, "e529e1ea246539e22ddace15f12c276226e6b577b9df8aace81a7d3aabb5f144"),
        "manifest": (844, "08d6f88d5dc72744b258f92b77425dacbf251150023afb35b89807d16f94d899"),
    },
}
SUPPORTED_PUBLIC_INTERFACE = {
    "ArtifactPacket",
    "ArtifactPacketError",
    "HTML_HARD_LIMIT_BYTES",
    "MANIFEST_HARD_LIMIT_BYTES",
    "SNAPSHOT_HARD_LIMIT_BYTES",
    "build_artifact_packet",
    "canonical_json_bytes",
    "sha256_hex",
    "write_artifact_packet",
}
REMOVED_COMPATIBILITY_ENTRIES = {
    "render_instrument_research_brief",
    "render_research_brief",
    "validate_board_snapshot",
    "validate_instrument_snapshot",
    "validate_macro_snapshot",
    "validate_portfolio_snapshot",
}


def main() -> int:
    _verify_public_interface()
    root = Path(__file__).resolve().parents[1]
    fixtures = root / "assets" / "fixtures" / "input"

    for fixture_name, reference in REFERENCE_PACKETS.items():
        snapshot = json.loads(
            (fixtures / f"{fixture_name}-complete.json").read_text(encoding="utf-8")
        )
        packet = artifact_packet.build_artifact_packet(snapshot)
        if packet != artifact_packet.build_artifact_packet(snapshot):
            raise SystemExit(f"artifact_packet_not_deterministic:{fixture_name}")
        _verify_reference_bytes(fixture_name, packet, reference)
        _verify_manifest_identity(fixture_name, snapshot, packet, reference)
        _verify_safe_html(fixture_name, packet.html)
        _verify_immutable_write(fixture_name, packet)

    print("ArtifactPacket facade contract ok")
    return 0


def _verify_public_interface() -> None:
    actual = set(getattr(artifact_packet, "__all__", ()))
    if actual != SUPPORTED_PUBLIC_INTERFACE:
        raise SystemExit(
            "artifact_packet_public_interface_mismatch:"
            f"missing={sorted(SUPPORTED_PUBLIC_INTERFACE - actual)}:"
            f"extra={sorted(actual - SUPPORTED_PUBLIC_INTERFACE)}"
        )
    leaked = sorted(name for name in REMOVED_COMPATIBILITY_ENTRIES if hasattr(artifact_packet, name))
    if leaked:
        raise SystemExit(f"artifact_packet_compatibility_entry_retained:{','.join(leaked)}")


def _verify_reference_bytes(
    fixture_name: str,
    packet: artifact_packet.ArtifactPacket,
    reference: dict[str, object],
) -> None:
    for key, data in (
        ("json", packet.canonical_json),
        ("html", packet.html),
        ("manifest", packet.manifest),
    ):
        expected_length, expected_hash = reference[key]
        if len(data) != expected_length or hashlib.sha256(data).hexdigest() != expected_hash:
            raise SystemExit(f"artifact_packet_reference_bytes_changed:{fixture_name}:{key}")


def _verify_manifest_identity(
    fixture_name: str,
    snapshot: dict[str, object],
    packet: artifact_packet.ArtifactPacket,
    reference: dict[str, object],
) -> None:
    manifest = json.loads(packet.manifest)
    expected = {
        "artifact_identity": f"{snapshot['snapshot_id']}:{reference['board']}",
        "board": reference["board"],
        "canonical_json_sha256": hashlib.sha256(packet.canonical_json).hexdigest(),
        "content_hash": snapshot["content_hash"],
        "html_sha256": hashlib.sha256(packet.html).hexdigest(),
        "privacy": snapshot["privacy"],
        "snapshot_id": snapshot["snapshot_id"],
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise SystemExit(f"artifact_packet_manifest_identity_changed:{fixture_name}")


def _verify_safe_html(fixture_name: str, html_bytes: bytes) -> None:
    html = html_bytes.decode("utf-8").lower()
    for forbidden in ("fetch(", "websocket", "broker write", "place order"):
        if forbidden in html:
            raise SystemExit(f"artifact_packet_forbidden_surface:{fixture_name}:{forbidden}")


def _verify_immutable_write(fixture_name: str, packet: artifact_packet.ArtifactPacket) -> None:
    with tempfile.TemporaryDirectory(prefix="artifact-packet-selftest-") as temporary:
        output = Path(temporary) / fixture_name
        first = artifact_packet.write_artifact_packet(packet, output)
        second = artifact_packet.write_artifact_packet(packet, output)
        if first != second:
            raise SystemExit(f"artifact_packet_idempotent_write_changed:{fixture_name}")
        first["html"].write_bytes(packet.html + b"conflict")
        try:
            artifact_packet.write_artifact_packet(packet, output)
        except artifact_packet.ArtifactPacketError as error:
            if str(error) != "immutable_output_conflict":
                raise SystemExit(f"artifact_packet_immutable_error_changed:{fixture_name}") from error
        else:
            raise SystemExit(f"artifact_packet_immutable_write_not_enforced:{fixture_name}")


if __name__ == "__main__":
    raise SystemExit(main())
