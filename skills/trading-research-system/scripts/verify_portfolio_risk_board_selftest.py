#!/usr/bin/env python3
"""Behavior tests for the canonical Portfolio Risk Board artifact seam."""

from __future__ import annotations

import json
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from artifact_packet import ArtifactPacketError, build_artifact_packet


class PortfolioRiskBoardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-complete.json"
        self.complete = json.loads(fixture.read_text(encoding="utf-8"))

    def test_complete_snapshot_builds_all_six_portfolio_views(self) -> None:
        packet = build_artifact_packet(self.complete)
        manifest = json.loads(packet.manifest)
        html = packet.html.decode("utf-8")

        self.assertEqual(manifest["board"], "portfolio_risk")
        self.assertEqual(
            manifest["views"],
            [
                "Overview",
                "By Symbol",
                "By Theme / Industry",
                "By Product",
                "By Broker",
                "Stress Tests",
            ],
        )
        for literal in (
            "Risk Decision Ledger",
            "Exposure Spine",
            "By Symbol",
            "By Theme / Industry",
            "By Product",
            "By Broker",
            "Stress-to-Decision Lab",
            "Long-end rates -75 bps",
            "symbol → theme → industry → product → broker",
            "Impact contributions",
        ):
            self.assertIn(literal, html)
        self.assertIn("Broker exposure", html)
        self.assertIn("<dt>Liquidity</dt>", html)
        self.assertIn("Industry decomposition", html)
        self.assertIn("Cash / collateral context", html)
        self.assertIn("3,000", html)

    def test_partial_snapshot_scopes_totals_and_discloses_nav_only_and_exclusions(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Confirmed position-detail sources only", html)
        self.assertIn("nav_only", html)
        self.assertIn("Gamma retirement", html)
        self.assertIn("EXCL2X", html)
        self.assertIn("Broker-reported positions remain disclosed", html)
        self.assertIn("User requested analytical exclusion", html)
        self.assertIn("Analytical Board calculations only", html)
        self.assertIn("user_requested", html)
        self.assertIn("Reported exposure:</strong> 2,000", html)
        self.assertNotIn('<article class="product-detail"><h3>EXCL2X', html)

    def test_stale_snapshot_preserves_existing_exposure_but_marks_the_board_stale(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-stale.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("stale", html)
        self.assertIn("Product terms must be refreshed", html)
        self.assertIn("SAMP2X", html)

    def test_source_error_snapshot_refuses_calculated_exposure_without_position_detail(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-source-error.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("No confirmed position-detail source", html)
        self.assertIn("Calculated exposure unavailable", html)
        self.assertNotIn("SAMP2X", html)

    def test_portfolio_cli_writes_all_four_evidence_state_packets(self) -> None:
        generator = self.root / "scripts" / "portfolio_risk_board_artifact.py"
        fixture_dir = self.root / "assets" / "fixtures" / "input"
        for state in ("complete", "partial", "stale", "source-error"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as raw_tmp:
                fixture = fixture_dir / f"portfolio-risk-{state}.json"
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

    def test_rejects_nav_only_source_in_confirmed_totals(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        snapshot["payload"]["totals"]["confirmed_source_refs"].append("nav-context")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_duplicate_confirmed_source_references(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["totals"]["confirmed_source_refs"].append("broker-alpha")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_position_account_alias_that_disagrees_with_source_coverage(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["account_alias"] = "Fabricated account"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_excluded_holding_in_an_aggregation(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        snapshot["payload"]["aggregations"]["by_symbol"][0]["affected_holdings"].append("EXCL2X")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^aggregations_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_totals_that_do_not_reconcile_to_included_positions(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["totals"]["gross_market_value"] += 100.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_position_currency_that_is_not_normalized_to_totals_currency(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["currency"] = "EUR"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^position_currency_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_aggregation_that_does_not_reconcile_to_position_detail(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        row = snapshot["payload"]["aggregations"]["by_symbol"][0]
        row["affected_holdings"] = ["FAKE"]
        row["direct_market_value"] = 999999.0
        row["delta_exposure"] = 999999.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^aggregations_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_duplicate_position_identity_inside_an_aggregation_row(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        row = snapshot["payload"]["aggregations"]["by_symbol"][1]
        row["affected_position_ids"].append("pos-mem")
        row["direct_market_value"] *= 2
        row["delta_exposure"] *= 2
        row["notional_exposure"] *= 2
        row["weight_pct"] = 35.0
        row["label"] = "MEM look-through"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^aggregations_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_unusable_stress_assumptions_and_coverage(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        scenario = snapshot["payload"]["stress_scenarios"][0]
        scenario["assumptions"] = []
        scenario["affected_holdings"] = []
        scenario["missing_exposure"] = -1.0
        scenario["covered_exposure"] = 999999.0
        scenario["confidence"] = "certain"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_stress_impact_that_does_not_reconcile_to_position_contributions(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["stress_scenarios"][0]["impact_contributions"][0]["estimated_impact"] += 1.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_option_greeks_on_a_non_option_product(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["option_greeks"] = {
            "delta": 1.0,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
        }
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_missing_delta_on_a_non_option_product(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["delta_exposure"] = None
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_incomplete_risk_ledger_before_rendering(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["risk_ledger"][0].pop("severity")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^risk_ledger_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_incomplete_exposure_spine_before_rendering(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["exposure_spine"][0].pop("plan_constraint")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^exposure_spine_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_exposure_spine_without_industry_decomposition(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["exposure_spine"][0]["decompositions"].remove("industry")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^exposure_spine_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_exclusion_that_does_not_match_broker_reported_exposure(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        snapshot["payload"]["exclusions"][0]["reported_exposure"] += 1.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^exclusions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_incomplete_exclusion_impact_disclosure(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        snapshot["payload"]["exclusions"][0]["affected_scenarios"].pop()
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^exclusions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_position_detail_module_state_that_conflicts_with_source_coverage(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        module = next(item for item in snapshot["payload"]["modules"] if item["id"] == "position_detail")
        module["evidence_state"] = "source_error"
        module["gap_reason"] = "Contradictory source error."
        snapshot["coverage"]["required_complete"] -= 1
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^position_detail_state_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_non_finite_and_boolean_financial_values(self) -> None:
        for field, value, error in (
            ("quantity", float("nan"), "positions_invalid"),
            ("market_value", True, "positions_invalid"),
        ):
            with self.subTest(field=field):
                snapshot = copy.deepcopy(self.complete)
                snapshot["payload"]["positions"][0][field] = value
                self._rehash(snapshot)
                with self.assertRaisesRegex(ArtifactPacketError, f"^{error}$"):
                    build_artifact_packet(snapshot)

    def test_rejects_invalid_position_and_source_domains(self) -> None:
        mutations = (
            (lambda snapshot: snapshot["payload"]["positions"][0].__setitem__("direction", "banana"), "positions_invalid"),
            (lambda snapshot: snapshot["payload"]["positions"][0].__setitem__("leverage_multiple", -5.0), "positions_invalid"),
            (lambda snapshot: snapshot["payload"]["positions"][0].__setitem__("liquidity_status", "excellent maybe"), "positions_invalid"),
            (lambda snapshot: snapshot["payload"]["source_coverage"][0].__setitem__("nav_context", -1.0), "source_coverage_invalid"),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                snapshot = copy.deepcopy(self.complete)
                mutate(snapshot)
                self._rehash(snapshot)
                with self.assertRaisesRegex(ArtifactPacketError, f"^{error}$"):
                    build_artifact_packet(snapshot)

    def test_rejects_aggregation_label_that_does_not_match_group_identity(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["aggregations"]["by_broker"][0]["label"] = "WRONG BROKER"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^aggregations_invalid$"):
            build_artifact_packet(snapshot)

    def test_aggregation_identity_supports_the_same_symbol_across_brokers(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][2]["symbol"] = "SAMP"
        for rows in snapshot["payload"]["aggregations"].values():
            for row in rows:
                row["affected_holdings"] = list(dict.fromkeys("SAMP" if symbol == "MEM" else symbol for symbol in row["affected_holdings"]))
        for item in snapshot["payload"]["risk_ledger"] + snapshot["payload"]["stress_scenarios"]:
            item["affected_holdings"] = list(dict.fromkeys("SAMP" if symbol == "MEM" else symbol for symbol in item["affected_holdings"]))
        self._rehash(snapshot)

        packet = build_artifact_packet(snapshot)

        self.assertIn("Synthetic Broker Beta / Beta IRA", packet.html.decode("utf-8"))

    def test_rejects_global_source_error_when_confirmed_position_detail_exists(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        module = next(item for item in snapshot["payload"]["modules"] if item["id"] == "product_risk")
        module["evidence_state"] = "source_error"
        module["gap_reason"] = "Product details unavailable."
        snapshot["coverage"]["required_complete"] -= 1
        snapshot["evidence_state"] = "source_error"
        snapshot["payload"]["posture"]["label"] = "Calculated exposure unavailable"
        snapshot["payload"]["decision"] = "No portfolio risk calculation is available until confirmed position detail is restored."
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^evidence_state_mismatch$"):
            build_artifact_packet(snapshot)

    def test_missing_option_greeks_degrades_only_options_and_related_stress_to_partial(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        option = next(position for position in snapshot["payload"]["positions"] if position["product_type"] == "option")
        option["option_greeks"] = None
        option["delta_exposure"] = None
        totals = snapshot["payload"]["totals"]
        totals["gross_delta_exposure"] -= 3200.0
        totals["net_delta_exposure"] -= 3200.0
        totals["options_delta_included"] = False
        for rows in snapshot["payload"]["aggregations"].values():
            for row in rows:
                if option["id"] in row["affected_position_ids"]:
                    row["delta_exposure"] -= 3200.0
                selected = [
                    position
                    for position in snapshot["payload"]["positions"]
                    if position["id"] in row["affected_position_ids"]
                ]
                row["weight_pct"] = round(
                    100.0 * sum(abs(position["delta_exposure"] or 0.0) for position in selected) / totals["gross_delta_exposure"],
                    1,
                )
        for module_id in ("product_risk", "stress_inputs"):
            module = next(item for item in snapshot["payload"]["modules"] if item["id"] == module_id)
            module["evidence_state"] = "partial"
            module["gap_reason"] = "Option Greeks unavailable; option delta, convexity, and related stress are incomplete."
        for scenario in snapshot["payload"]["stress_scenarios"]:
            if option["id"] in scenario["affected_position_ids"]:
                scenario["affected_position_ids"].remove(option["id"])
                scenario["affected_holdings"].remove(option["symbol"])
                scenario["covered_exposure"] -= option["direct_exposure"]
                scenario["missing_exposure"] += option["direct_exposure"]
                scenario["impact_contributions"] = [
                    contribution
                    for contribution in scenario["impact_contributions"]
                    if contribution["position_id"] != option["id"]
                ]
                scenario["estimated_impact"] = sum(
                    contribution["estimated_impact"]
                    for contribution in scenario["impact_contributions"]
                )
                scenario["status"] = "partial"
                scenario["confidence"] = "low"
        snapshot["coverage"]["required_complete"] -= 2
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Greeks unavailable", html)
        self.assertIn("Cash equities", html)

    @staticmethod
    def _rehash(snapshot: dict) -> None:
        snapshot.pop("content_hash", None)
        canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        snapshot["content_hash"] = hashlib.sha256(canonical).hexdigest()


if __name__ == "__main__":
    unittest.main()
