#!/usr/bin/env python3
"""Artifact-boundary tests for the canonical Macro Regime Board."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from artifact_packet import ArtifactPacketError, build_artifact_packet
from macro_regime_board import render_macro_regime_board


class MacroRegimeBoardSelftest(unittest.TestCase):
    """Exercise the public immutable packet seam, not renderer helpers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.fixture_dir = cls.root / "assets" / "fixtures" / "input"
        cls.complete = _fixture(cls.fixture_dir / "macro-regime-complete.json")

    def test_complete_snapshot_renders_all_views_and_local_echarts(self) -> None:
        packet = build_artifact_packet(copy.deepcopy(self.complete))
        html = packet.html.decode("utf-8")

        for literal in (
            'data-view="overview"',
            'data-view="rates-liquidity"',
            'data-view="inflation-growth"',
            'data-view="cross-asset-impact"',
            'data-view="event-scenarios"',
            "Evidence to Transmission to Exposure to Plan Decision",
            "Holding-first Exposure Lens",
            "Trigger to Cross-Asset to Exposure to Posture",
            'data-library="Apache ECharts" data-version="6.1.0"',
            "renderer: 'svg'",
            "animation: false",
            "aria: { enabled: true }",
            "Semantic cross-asset fallback",
            'data-research-brief-shell="v1"',
        ):
            self.assertIn(literal, html)

        for forbidden in ("fetch(", "xmlhttprequest", "websocket", 'src="http', 'href="http'):
            self.assertNotIn(forbidden, html.lower())

        manifest = json.loads(packet.manifest)
        self.assertEqual(manifest["board"], "macro_regime")
        self.assertEqual(
            manifest["views"],
            ["Overview", "Rates & Liquidity", "Inflation & Growth", "Cross-Asset Impact", "Event Scenarios"],
        )

    def test_public_state_fixtures_drive_status_and_visible_gaps(self) -> None:
        expected_states = {
            "macro-regime-complete.json": "complete",
            "macro-regime-partial.json": "partial",
            "macro-regime-stale.json": "stale",
            "macro-regime-source-error.json": "source_error",
        }
        for filename, expected_state in expected_states.items():
            with self.subTest(filename=filename):
                packet = build_artifact_packet(_fixture(self.fixture_dir / filename))
                canonical = json.loads(packet.canonical_json)
                html = packet.html.decode("utf-8")
                self.assertEqual(canonical["evidence_state"], expected_state)
                self.assertIn("Visible gaps", html)
                self.assertIn("Decision cutoff", html)
                if expected_state == "source_error":
                    self.assertIn("Plan-linked Macro decision unavailable", html)
                    self.assertNotIn("Risk-on regime", html)

    def test_missing_or_stale_plan_is_source_error_without_a_regime_label(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        plan = _module(snapshot, "plan_context")
        plan["evidence_state"] = "stale"
        plan["gap_reason"] = "Synthetic plan is stale at the decision cutoff."
        snapshot["evidence_state"] = "source_error"
        snapshot["coverage"]["required_complete"] = 5
        snapshot["state_reasons"] = ["Active plan is stale."]
        snapshot["payload"]["posture"]["label"] = "Plan context unavailable"
        snapshot["payload"]["decision"] = "No plan-linked Macro decision is available until plan context is complete."
        snapshot["content_hash"] = _content_hash(snapshot)

        packet = build_artifact_packet(snapshot)
        self.assertEqual(json.loads(packet.canonical_json)["evidence_state"], "source_error")
        self.assertNotIn("Risk-on regime", packet.html.decode("utf-8"))

    def test_unavailable_plan_redacts_plan_derived_consequences_from_html(self) -> None:
        snapshot = _fixture(self.fixture_dir / "macro-regime-source-error.json")
        payload = snapshot["payload"]
        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Plan-linked Macro decision unavailable", html)
        self.assertEqual(html.count('data-view-target="'), 5)
        self.assertIn("Evidence rail", html)
        for value in (
            payload["posture"]["label"],
            payload["posture"]["consequence"],
            *(item["plan_effect"] for item in payload["evidence"]),
            *(
                value
                for item in payload["evidence"]
                if item["category"] == "thesis"
                for value in (item["label"], item["reading"], item["transmission"])
            ),
            *(item["plan_rule"] for item in payload["exposure_lens"]),
            *(item["impact"] for item in payload["exposure_lens"]),
            *(item["posture"] for item in payload["scenarios"]),
        ):
            self.assertNotIn(value, html)

    def test_plan_context_requires_identity_session_posture_and_rules(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        plan = _module(snapshot, "plan_context")
        plan["data"] = {
            "active_plan_id": "synthetic-macro-plan-2026-07-17",
            "applicable_horizon": "weekly",
            "applicable_session": "2026-07-16T00:00:00Z",
            "assumptions": "Synthetic inflation and growth assumptions.",
            "constraints": "Cross-asset confirmation is required.",
            "current_posture": "Mixed evidence-gated posture.",
            "decision_rules": "Retain constraints until confirmation persists.",
        }
        snapshot["content_hash"] = _content_hash(snapshot)
        with self.assertRaisesRegex(ArtifactPacketError, "^plan_context_invalid$"):
            build_artifact_packet(snapshot)

    def test_evidence_rows_include_auditable_source_provenance(self) -> None:
        html = build_artifact_packet(copy.deepcopy(self.complete)).html.decode("utf-8")
        for literal in (
            "Source: Authorized Macro values (market-values) · S1 · fresh · 2026-07-17T09:50:00Z",
            "Source: Forecast consensus (forecast-consensus) · S1 · fresh · 2026-07-17T09:00:00Z",
            "Source: Media context (media-context) · S2 · fresh · 2026-07-17T09:30:00Z",
            "Source: Synthetic Macro plan (plan-fixture) · S3 · fresh · 2026-07-17T08:30:00Z",
        ):
            self.assertIn(literal, html)

    def test_macro_renderer_uses_injected_asset_without_filesystem_read(self) -> None:
        with patch.object(Path, "read_text", side_effect=AssertionError("renderer filesystem read")):
            html = render_macro_regime_board(
                self.complete,
                "Overview",
                "ready",
                echarts_source="window.echarts={init(){return {setOption(){},resize(){}}}};",
            ).decode("utf-8")
        self.assertIn("window.echarts", html)

    def test_unreconciled_holdings_require_conditional_portfolio_impact(self) -> None:
        snapshot = _fixture(self.fixture_dir / "macro-regime-partial.json")
        self.assertTrue(snapshot["payload"]["holdings_context"]["conditional"])
        html = build_artifact_packet(snapshot).html.decode("utf-8")
        self.assertIn("Conditional portfolio impact", html)

    def test_rejects_unconditional_exposure_when_holdings_are_incomplete(self) -> None:
        snapshot = _fixture(self.fixture_dir / "macro-regime-partial.json")
        snapshot["payload"]["holdings_context"]["conditional"] = False
        snapshot["content_hash"] = _content_hash(snapshot)
        with self.assertRaisesRegex(ArtifactPacketError, "^holdings_conditional_required$"):
            build_artifact_packet(snapshot)

        impact = _fixture(self.fixture_dir / "macro-regime-partial.json")
        impact["payload"]["exposure_lens"][0]["impact"] = "Confirmed portfolio impact."
        impact["content_hash"] = _content_hash(impact)
        with self.assertRaisesRegex(ArtifactPacketError, "^holdings_conditional_required$"):
            build_artifact_packet(impact)

    def test_rejects_free_floating_posture_and_mixed_source_categories(self) -> None:
        posture = copy.deepcopy(self.complete)
        posture["payload"]["posture"]["derived_from"] = []
        posture["content_hash"] = _content_hash(posture)
        with self.assertRaisesRegex(ArtifactPacketError, "^posture_derivation_invalid$"):
            build_artifact_packet(posture)

        source_mix = copy.deepcopy(self.complete)
        source_mix["payload"]["evidence"][0]["category"] = "thesis"
        source_mix["content_hash"] = _content_hash(source_mix)
        with self.assertRaisesRegex(ArtifactPacketError, "^evidence_invalid$"):
            build_artifact_packet(source_mix)

    def test_macro_cli_rejects_another_board_snapshot(self) -> None:
        generator = self.root / "scripts" / "macro_regime_board_artifact.py"
        instrument = self.fixture_dir / "instrument-research-complete.json"
        with tempfile.TemporaryDirectory() as raw_tmp:
            result = subprocess.run(
                [sys.executable, str(generator), str(instrument), "--output-dir", raw_tmp],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("board_invalid", result.stderr)


def _fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(snapshot: dict, module_id: str) -> dict:
    return next(item for item in snapshot["payload"]["modules"] if item["id"] == module_id)


def _content_hash(snapshot: dict) -> str:
    content = copy.deepcopy(snapshot)
    content.pop("content_hash", None)
    return hashlib.sha256(
        json.dumps(content, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    unittest.main()
