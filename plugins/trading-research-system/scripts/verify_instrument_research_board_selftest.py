#!/usr/bin/env python3
"""Artifact-boundary tests for the canonical Instrument Research Board."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from artifact_packet import ArtifactPacketError, build_artifact_packet


class InstrumentResearchBoardSelftest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.root = root
        fixture = root / "assets" / "fixtures" / "input" / "instrument-research-complete.json"
        cls.complete = json.loads(fixture.read_text(encoding="utf-8"))

    def test_complete_snapshot_renders_all_views_and_local_price_chart(self) -> None:
        packet = build_artifact_packet(copy.deepcopy(self.complete))
        html = packet.html.decode("utf-8")

        for literal in (
            'data-view="overview"',
            'data-view="price-setup"',
            'data-view="industry-peers"',
            'data-view="catalysts-flows"',
            "Four-evidence balance",
            "Claim Ledger",
            "Verification Queue",
            "Catalyst to Evidence to Decision",
            "Price Action is timing evidence, not the research thesis.",
            'data-library="TradingView Lightweight Charts"',
            "LightweightCharts.createChart",
            "Research gate: ready",
            "Daily reset can diverge from the underlying over multiple sessions.",
        ):
            self.assertIn(literal, html)

        for forbidden in (
            'src="http',
            'src="//',
            'href="http',
            "fetch(",
            "xmlhttprequest",
            "websocket",
        ):
            self.assertNotIn(forbidden, html.lower())

        manifest = json.loads(packet.manifest)
        self.assertEqual(manifest["views"], [
            "Overview",
            "Price & Setup",
            "Industry & Peers",
            "Catalysts & Flows",
        ])
        self.assertEqual(manifest["presentation_state"], "ready")

    def test_public_state_fixtures_preserve_gates_gaps_and_supporting_only_flows(self) -> None:
        expected_states = {
            "instrument-research-complete.json": "complete",
            "instrument-research-partial.json": "partial",
            "instrument-research-stale.json": "stale",
            "instrument-research-source-error.json": "source_error",
        }
        fixture_dir = self.root / "assets" / "fixtures" / "input"
        for filename, expected_state in expected_states.items():
            with self.subTest(filename=filename):
                snapshot = json.loads((fixture_dir / filename).read_text(encoding="utf-8"))
                packet = build_artifact_packet(snapshot)
                canonical = json.loads(packet.canonical_json)
                html = packet.html.decode("utf-8")
                self.assertEqual(canonical["evidence_state"], expected_state)
                self.assertIn("supporting-only", html)
                if expected_state == "complete":
                    self.assertIn("Research gate: ready", html)
                else:
                    self.assertIn("Research gate: blocked", html)
                    self.assertIn("Visible gaps", html)
                if expected_state == "source_error":
                    self.assertIn("Unavailable", html)

        partial = json.loads((fixture_dir / "instrument-research-partial.json").read_text(encoding="utf-8"))
        self.assertEqual(partial["payload"]["modules"][-1]["id"], "flows")
        self.assertEqual(partial["payload"]["modules"][-1]["evidence_state"], "complete")
        self.assertEqual(partial["coverage"], {"required_complete": 3, "required_total": 4})

        invalid_gate = copy.deepcopy(partial)
        invalid_gate["payload"]["price_setup"]["research_gate_status"] = "ready"
        invalid_gate["content_hash"] = _content_hash(invalid_gate)
        with self.assertRaisesRegex(ArtifactPacketError, "^research_gate_mismatch$"):
            build_artifact_packet(invalid_gate)

    def test_partial_requires_complete_industry_and_fundamentals(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["evidence_state"] = "source_error"
        snapshot["coverage"] = {"required_complete": 3, "required_total": 4}
        snapshot["state_reasons"] = ["Industry evidence is incomplete at the decision cutoff."]
        snapshot["payload"]["price_setup"]["research_gate_status"] = "blocked"
        for module in snapshot["payload"]["modules"]:
            if module["id"] == "industry":
                module["evidence_state"] = "partial"
                module["gap_reason"] = "Capacity evidence remains unverified."
        snapshot["content_hash"] = _content_hash(snapshot)

        packet = build_artifact_packet(snapshot)
        canonical = json.loads(packet.canonical_json)
        self.assertEqual(canonical["evidence_state"], "source_error")
        self.assertIn("Research gate: blocked", packet.html.decode("utf-8"))

    def test_rejects_invalid_price_level_and_zone_values(self) -> None:
        invalid_level = copy.deepcopy(self.complete)
        invalid_level["payload"]["price_setup"]["levels"][0]["price"] = "not-a-price"
        invalid_level["content_hash"] = _content_hash(invalid_level)
        with self.assertRaisesRegex(ArtifactPacketError, "^price_setup_invalid$"):
            build_artifact_packet(invalid_level)

        invalid_zone = copy.deepcopy(self.complete)
        invalid_zone["payload"]["price_setup"]["zones"][0].update({"low": 101.0, "high": 99.0})
        invalid_zone["content_hash"] = _content_hash(invalid_zone)
        with self.assertRaisesRegex(ArtifactPacketError, "^price_setup_invalid$"):
            build_artifact_packet(invalid_zone)

    def test_instrument_research_cli_writes_the_canonical_packet(self) -> None:
        generator = self.root / "scripts" / "instrument_research_artifact.py"
        fixture = self.root / "assets" / "fixtures" / "input" / "instrument-research-complete.json"
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
