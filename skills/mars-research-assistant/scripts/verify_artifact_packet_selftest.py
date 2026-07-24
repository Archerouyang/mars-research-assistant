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
        "json": (9365, "d0e9c9b93f8ab0cb355a8f0ed1e7e9a8eecfcc51e7c72aea4844d0695e17a2ac"),
        "html": (224197, "c3876d96a6140e0dcc0c743a9081bba2e87204dfbe9f65f64e606d510a2042c1"),
        "manifest": (851, "ffdca5c906585520c9ea632b62ecc8950192d6b24e032d2e8acb93d7b4b3b9c0"),
    },
    "macro-regime": {
        "board": "macro_regime",
        "json": (16504, "d3cf33d89ce1f93886e78d5a173ef0fb3c058ce4a6b10cbc39fc26f6af19c97f"),
        "html": (1148088, "d06b51bfd19c56846f4543b0ca83d8d783ee9965e7ebac6431e07cfd3618865e"),
        "manifest": (842, "987ac2bf5f9657dd16d9709d5734169ce98ccae93d5fbdc6b65da453a82fa9f7"),
    },
    "portfolio-risk": {
        "board": "portfolio_risk",
        "json": (19233, "f690292d79ed3e60afe1922025fd0fcadd124acb8eec603b0c47e0bc34b7f806"),
        "html": (1175902, "015337bc914d0c4212e1114ce66784c488103db36a69c7037745315e83c62fcc"),
        "manifest": (844, "bb07a6482a64ba2163b79ed0bf929eb7220fea16e77877e92fcb9e4049478b76"),
    },
}
SUPPORTED_PUBLIC_INTERFACE = {
    "ArtifactPacket",
    "ArtifactPacketError",
    "HTML_HARD_LIMIT_BYTES",
    "MANIFEST_HARD_LIMIT_BYTES",
    "SNAPSHOT_HARD_LIMIT_BYTES",
    "build_artifact_packet",
    "build_standalone_artifact_packet",
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

    _verify_standalone_safety_gate()

    print("ArtifactPacket facade contract ok")
    return 0


def _verify_standalone_safety_gate() -> None:
    snapshot = _standalone_snapshot("public_fixture")
    safe_html = b"<!doctype html><html><body>Board</body></html>"
    packet = artifact_packet.build_standalone_artifact_packet(
        snapshot,
        safe_html,
        privacy="public_fixture",
        visual_adapter="macro",
    )
    if packet != artifact_packet.build_standalone_artifact_packet(
        snapshot,
        safe_html,
        privacy="public_fixture",
        visual_adapter="macro",
    ):
        raise SystemExit("standalone_artifact_packet_not_deterministic")
    for unsafe_html in (
        b"<!doctype html><html><script>fetch('/private')</script></html>",
        b'<!doctype html><html><img src="https://example.com/a.png"></html>',
    ):
        try:
            artifact_packet.build_standalone_artifact_packet(
                snapshot,
                unsafe_html,
                privacy="public_fixture",
                visual_adapter="macro",
            )
        except artifact_packet.ArtifactPacketError as error:
            if str(error) != "html_safety_violation":
                raise SystemExit(f"standalone_safety_error_changed:{error}") from error
        else:
            raise SystemExit("standalone_unsafe_html_accepted")

    private_snapshot = _standalone_snapshot("private")
    artifact_packet.build_standalone_artifact_packet(
        private_snapshot,
        safe_html,
        privacy="private",
        visual_adapter="macro",
    )

    leaked_snapshot = _standalone_snapshot("public_fixture")
    leaked_snapshot["visual"]["label"] = "/Users/private/account"
    try:
        artifact_packet.build_standalone_artifact_packet(
            leaked_snapshot,
            safe_html,
            privacy="public_fixture",
            visual_adapter="macro",
        )
    except artifact_packet.ArtifactPacketError as error:
        if str(error) != "privacy_violation":
            raise SystemExit(f"standalone_privacy_error_changed:{error}") from error
    else:
        raise SystemExit("standalone_public_privacy_leak_accepted")


def _standalone_snapshot(privacy: str) -> dict[str, object]:
    return {
        "artifact_kind": "standalone_board",
        "artifact_lifecycle": "durable",
        "decision_cutoff": "2026-07-22T12:00:00Z",
        "default_view": "trend",
        "presentation_state": "ready",
        "privacy": privacy,
        "renderer_version": "1.0",
        "schema_version": "1.0",
        "snapshot_id": "research-result-macro-test",
        "views": ["trend", "current", "events", "scenarios"],
        "visual": {"adapter": "macro"},
    }


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
