#!/usr/bin/env python3
"""Contract tests for the public Instrument artifact-packet tracer seam."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from artifact_packet import ArtifactPacketError, build_artifact_packet, write_artifact_packet


# These are independently captured known-good bytes for the public fixture.
EXPECTED_CONTENT_HASH = "e81d14d85094d5d9c068ec85101f428c33967481b3d8bf4ec81b819190e952bd"
EXPECTED_JSON_SHA256 = "809841d66fd759af82710108bf97718c10b597e96b5947881cd6e53ff0857366"
EXPECTED_HTML_SHA256 = "f9cbbb7a603a3b77e2ce24712626c7e2019497e8251628fa9a53ec61d8b5eacf"


class ArtifactPacketSelftest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = root / "assets" / "fixtures" / "input" / "instrument-overview-tracer.json"
        cls.snapshot = json.loads(fixture.read_text(encoding="utf-8"))

    def build(self, snapshot: dict | None = None, **kwargs: str):
        return build_artifact_packet(copy.deepcopy(snapshot or self.snapshot), **kwargs)

    def assert_error(self, code: str, snapshot: dict) -> None:
        with self.assertRaisesRegex(ArtifactPacketError, f"^{code}$"):
            self.build(snapshot)

    def test_builds_known_good_deterministic_packet(self) -> None:
        first = self.build()
        second = self.build()

        self.assertEqual(first.canonical_json, second.canonical_json)
        self.assertEqual(first.html, second.html)
        self.assertEqual(first.manifest, second.manifest)
        self.assertEqual(hashlib.sha256(first.canonical_json).hexdigest(), EXPECTED_JSON_SHA256)
        self.assertEqual(hashlib.sha256(first.html).hexdigest(), EXPECTED_HTML_SHA256)

        canonical_snapshot = json.loads(first.canonical_json)
        manifest = json.loads(first.manifest)
        self.assertEqual(canonical_snapshot["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertEqual(manifest["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertEqual(manifest["html_sha256"], EXPECTED_HTML_SHA256)
        self.assertEqual(manifest["board"], "instrument_research")
        self.assertEqual(manifest["default_view"], "Overview")
        self.assertEqual(manifest["presentation_state"], "ready")

    def test_html_is_semantic_self_contained_and_has_no_action_surface(self) -> None:
        html = self.build().html.decode("utf-8")
        for literal in (
            "Instrument Research",
            "Provenance",
            "Current decision",
            "Coverage",
            "Evidence rail",
            "Safety boundary",
            "Synthetic fixture. Not investment advice.",
            "Synthetic demand, capacity, and peer context are complete.",
        ):
            self.assertIn(literal, html)
        for forbidden in (
            "<script",
            "fetch(",
            "xmlhttprequest",
            "websocket",
            "http://",
            "https://",
            "cdn",
            "telemetry",
            "broker",
            "runtime",
            "order action",
        ):
            self.assertNotIn(forbidden, html.lower())

    def test_rejects_forbidden_network_and_action_references(self) -> None:
        for injected in (
            "https://example.invalid",
            "fetch(",
            "telemetry",
            "broker",
            "runtime",
            "order action",
        ):
            unsafe = copy.deepcopy(self.snapshot)
            unsafe["payload"]["modules"][0]["summary"] = injected
            unsafe["content_hash"] = _content_hash(unsafe)
            self.assert_error("html_safety_violation", unsafe)

    def test_rejects_invalid_versions_board_content_and_privacy(self) -> None:
        invalid_payload = copy.deepcopy(self.snapshot)
        invalid_payload["payload"].pop("decision")
        self.assert_error("payload_invalid", invalid_payload)

        invalid_schema = copy.deepcopy(self.snapshot)
        invalid_schema["schema_version"] = "2.0"
        self.assert_error("schema_version_invalid", invalid_schema)

        invalid_payload_version = copy.deepcopy(self.snapshot)
        invalid_payload_version["payload_version"] = "2.0"
        self.assert_error("payload_version_invalid", invalid_payload_version)

        board_mismatch = copy.deepcopy(self.snapshot)
        board_mismatch["payload"]["board"] = "macro_regime"
        self.assert_error("board_mismatch", board_mismatch)

        content_mismatch = copy.deepcopy(self.snapshot)
        content_mismatch["content_hash"] = "0" * 64
        self.assert_error("content_hash_mismatch", content_mismatch)

        privacy_violation = copy.deepcopy(self.snapshot)
        privacy_violation["payload"]["question"] = "private path: /Users/example/secret"
        self.assert_error("privacy_violation", privacy_violation)

    def test_rejects_unsafe_diagnostics_and_size_overages(self) -> None:
        unsafe_diagnostic = copy.deepcopy(self.snapshot)
        unsafe_diagnostic["diagnostics"] = [{"code": "E1", "message": "Traceback: secret"}]
        self.assert_error("diagnostic_unsafe", unsafe_diagnostic)

        oversized = copy.deepcopy(self.snapshot)
        oversized["payload"]["padding"] = "x" * (1536 * 1024)
        oversized["content_hash"] = _content_hash(oversized)
        self.assert_error("snapshot_size_exceeded", oversized)

    def test_rejects_invalid_source_freshness(self) -> None:
        future_source = copy.deepcopy(self.snapshot)
        future_source["source_registry"][-1]["as_of"] = "2026-07-16T09:01:00Z"
        self.assert_error("source_freshness_invalid", future_source)

    def test_rejects_incomplete_sources_and_invalid_source_references(self) -> None:
        source_without_alias = copy.deepcopy(self.snapshot)
        source_without_alias["source_registry"][0].pop("alias")
        self.assert_error("source_registry_invalid", source_without_alias)

        invalid_reference = copy.deepcopy(self.snapshot)
        invalid_reference["payload"]["modules"][0]["source_refs"] = [{}]
        self.assert_error("modules_invalid", invalid_reference)

    def test_evidence_and_presentation_states_are_independent(self) -> None:
        packet = self.build(presentation_state="invalid_artifact")
        snapshot = json.loads(packet.canonical_json)
        manifest = json.loads(packet.manifest)
        self.assertEqual(snapshot["evidence_state"], "complete")
        self.assertEqual(manifest["presentation_state"], "invalid_artifact")

    def test_writes_immutable_packet_files_within_hard_limits(self) -> None:
        packet = self.build()
        self.assertLessEqual(len(packet.canonical_json), 1536 * 1024)
        self.assertLessEqual(len(packet.html), 4 * 1024 * 1024)
        self.assertLessEqual(len(packet.manifest), 64 * 1024)

        with tempfile.TemporaryDirectory() as raw_tmp:
            output = Path(raw_tmp)
            paths = write_artifact_packet(packet, output)
            self.assertEqual(paths["json"].read_bytes(), packet.canonical_json)
            self.assertEqual(paths["html"].read_bytes(), packet.html)
            self.assertEqual(paths["manifest"].read_bytes(), packet.manifest)
            write_artifact_packet(packet, output)

            paths["html"].write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ArtifactPacketError, "^immutable_output_conflict$"):
                write_artifact_packet(packet, output)

    def test_documented_generator_command_writes_complete_packet(self) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = root / "assets" / "fixtures" / "input" / "instrument-overview-tracer.json"
        generator = root / "scripts" / "instrument_overview_artifact.py"
        with tempfile.TemporaryDirectory() as raw_tmp:
            result = subprocess.run(
                [sys.executable, str(generator), str(fixture), "--output-dir", raw_tmp],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("artifact packet written:", result.stdout)
            self.assertEqual(
                sorted(path.name for path in Path(raw_tmp).iterdir()),
                ["artifact.manifest.json", "research-brief.html", "snapshot.canonical.json"],
            )


def _content_hash(snapshot: dict) -> str:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    return hashlib.sha256(
        json.dumps(content, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    unittest.main()
