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
EXPECTED_MANIFEST_SHA256 = "bcae87b490d241907d5bbf4caa392409f3989ee3779352d688a89662b23cb0d3"


class ArtifactPacketSelftest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = root / "assets" / "fixtures" / "input" / "instrument-overview-tracer.json"
        cls.snapshot = json.loads(fixture.read_text(encoding="utf-8"))

    def build(self, snapshot: dict | None = None, **kwargs: str):
        return build_artifact_packet(copy.deepcopy(snapshot or self.snapshot), **kwargs)

    def assert_error(self, code: str, snapshot: dict, secret: str | None = None) -> None:
        with self.assertRaises(ArtifactPacketError) as raised:
            self.build(snapshot)
        self.assertEqual(str(raised.exception), code)
        if secret is not None:
            self.assertNotIn(secret, str(raised.exception))

    def test_builds_known_good_deterministic_packet(self) -> None:
        first = self.build()
        second = self.build()

        self.assertEqual(first.canonical_json, second.canonical_json)
        self.assertEqual(first.html, second.html)
        self.assertEqual(first.manifest, second.manifest)
        self.assertEqual(hashlib.sha256(first.canonical_json).hexdigest(), EXPECTED_JSON_SHA256)
        self.assertEqual(hashlib.sha256(first.html).hexdigest(), EXPECTED_HTML_SHA256)
        self.assertEqual(hashlib.sha256(first.manifest).hexdigest(), EXPECTED_MANIFEST_SHA256)

        canonical_snapshot = json.loads(first.canonical_json)
        manifest = json.loads(first.manifest)
        self.assertEqual(canonical_snapshot["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertEqual(manifest["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertEqual(manifest["html_sha256"], EXPECTED_HTML_SHA256)
        self.assertEqual(manifest["board"], "instrument_research")
        self.assertEqual(manifest["default_view"], "Overview")
        self.assertEqual(manifest["presentation_state"], "ready")
        self.assertEqual(manifest["snapshot_contract_version"], "1.0")

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
        unsafe_diagnostic["diagnostics"] = [_valid_diagnostic(message="Traceback: secret")]
        self.assert_error("diagnostic_unsafe", unsafe_diagnostic)

        oversized = copy.deepcopy(self.snapshot)
        oversized["payload"]["padding"] = "x" * (1536 * 1024)
        oversized["content_hash"] = _content_hash(oversized)
        self.assert_error("snapshot_size_exceeded", oversized)

    def test_rejects_invalid_source_freshness(self) -> None:
        future_source = copy.deepcopy(self.snapshot)
        future_source["source_registry"][-1]["as_of"] = "2026-07-16T09:01:00Z"
        self.assert_error("source_freshness_invalid", future_source)

    def test_rejects_stale_modules_and_insufficient_source_support(self) -> None:
        stale_module = copy.deepcopy(self.snapshot)
        stale_module["payload"]["modules"][-1]["as_of"] = "2026-07-16T08:20:00Z"
        self.assert_error("module_freshness_invalid", stale_module)

        future_module = copy.deepcopy(self.snapshot)
        future_module["payload"]["modules"][-1]["as_of"] = "2026-07-16T09:01:00Z"
        self.assert_error("module_freshness_invalid", future_module)

        s4_only = copy.deepcopy(self.snapshot)
        s4_only["source_registry"][-1]["priority"] = "S4"
        self.assert_error("module_source_support_invalid", s4_only)

        all_stale_refs = copy.deepcopy(self.snapshot)
        all_stale_refs["source_registry"][-1]["as_of"] = "2026-07-16T08:00:00Z"
        all_stale_refs["source_registry"][-1]["freshness_status"] = "stale"
        self.assert_error("module_source_support_invalid", all_stale_refs)

    def test_rejects_incomplete_sources_and_invalid_source_references(self) -> None:
        source_without_alias = copy.deepcopy(self.snapshot)
        source_without_alias["source_registry"][0].pop("alias")
        self.assert_error("source_registry_invalid", source_without_alias)

        invalid_reference = copy.deepcopy(self.snapshot)
        invalid_reference["payload"]["modules"][0]["source_refs"] = [{}]
        self.assert_error("modules_invalid", invalid_reference)

        unsafe_alias = copy.deepcopy(self.snapshot)
        unsafe_alias["source_registry"][0]["alias"] = "Account 123456789"
        self.assert_error("source_registry_invalid", unsafe_alias)

    def test_validates_all_diagnostic_fields_without_leaking_input(self) -> None:
        valid = copy.deepcopy(self.snapshot)
        valid["diagnostics"] = [_valid_diagnostic()]
        valid["content_hash"] = _content_hash(valid)
        self.build(valid)

        invalid_severity = copy.deepcopy(self.snapshot)
        invalid_severity["diagnostics"] = [_valid_diagnostic(severity="fatal")]
        self.assert_error("diagnostics_invalid", invalid_severity)

        invalid_retryable = copy.deepcopy(self.snapshot)
        invalid_retryable["diagnostics"] = [_valid_diagnostic(retryable="yes")]
        self.assert_error("diagnostics_invalid", invalid_retryable)

        invalid_code_type = copy.deepcopy(self.snapshot)
        invalid_code_type["diagnostics"] = [_valid_diagnostic(code=7)]
        self.assert_error("diagnostics_invalid", invalid_code_type)

        for field in ("severity", "module", "source_alias"):
            invalid_type = copy.deepcopy(self.snapshot)
            invalid_type["diagnostics"] = [_valid_diagnostic(**{field: 7})]
            self.assert_error("diagnostics_invalid", invalid_type)

        invalid_unhashable_severity = copy.deepcopy(self.snapshot)
        invalid_unhashable_severity["diagnostics"] = [_valid_diagnostic(severity=[])]
        self.assert_error("diagnostics_invalid", invalid_unhashable_severity)

        unknown_alias = copy.deepcopy(self.snapshot)
        unknown_alias["diagnostics"] = [_valid_diagnostic(source_alias="Unknown source")]
        self.assert_error("diagnostic_reference_invalid", unknown_alias)

        for field, injected in (
            ("source_alias", "123456789"),
            ("code", "API_KEY"),
            ("module", "/Users/example/private"),
            ("message", "raw response at /Users/example/private"),
            ("message", "full account id 123456789"),
            ("message", "reference 1234-5678-90"),
        ):
            unsafe = copy.deepcopy(self.snapshot)
            diagnostic = _valid_diagnostic()
            diagnostic[field] = injected
            unsafe["diagnostics"] = [diagnostic]
            self.assert_error("diagnostic_unsafe", unsafe, secret=injected)

        private_runtime = copy.deepcopy(self.snapshot)
        private_runtime["privacy"] = "private_runtime"
        private_runtime["diagnostics"] = [_valid_diagnostic(message="raw response account 123456789")]
        self.assert_error("diagnostic_unsafe", private_runtime, secret="123456789")

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


def _valid_diagnostic(**overrides: object) -> dict[str, object]:
    diagnostic: dict[str, object] = {
        "code": "SOURCE_DELAY",
        "severity": "warning",
        "module": "market_instrument",
        "source_alias": "Synthetic market data",
        "message": "Synthetic source delay.",
        "retryable": True,
    }
    diagnostic.update(overrides)
    return diagnostic


def _content_hash(snapshot: dict) -> str:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    return hashlib.sha256(
        json.dumps(content, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    unittest.main()
