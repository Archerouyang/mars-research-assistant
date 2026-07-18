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
            "Coverage basis",
            "Covered delta exposure",
            "Unscoped derivative notional",
            "Unscoped NAV context",
            "position_delta_times_shock_v1",
            "Currency conversion",
            "identity conversion",
        ):
            self.assertIn(literal, html)
        self.assertIn("Broker exposure", html)
        self.assertIn("<dt>Liquidity</dt>", html)
        self.assertIn("Industry decomposition", html)
        self.assertIn("Cash / collateral context", html)
        self.assertIn("6,000", html)

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

    def test_rejects_actionable_broker_language_outside_structural_fields(self) -> None:
        mutations = (
            ("question", "Use the broker to buy SAMP now."),
            ("question", "Buy SAMP now."),
            ("question", "Please buy SAMP now."),
            ("question", "Increase SAMP now."),
            ("question", "Can you sell SAMP now?"),
            ("question", "Cancel the order now."),
            ("question", "Modify the open order now."),
            ("question", "Place a limit order for SAMP now."),
            ("question", "Order approved for SAMP"),
            ("question", "Go long SAMP now"),
            ("question", "Fill the order now"),
            ("question", "Close 100 shares of SAMP."),
            ("question", "Exit 100 shares of SAMP."),
            ("question", "Reduce SAMP by 50 shares."),
            ("question", "Open a 100 share position."),
            ("question", "Trim 50 shares of SAMP."),
            ("question", "Flatten the SAMP position."),
            ("question", "Cut SAMP by 50 shares."),
            ("question", "Scale out 50 shares of SAMP."),
            ("question", "Scale out of SAMP."),
            ("question", "Scale out."),
            ("question", "Take profits."),
            ("question", "Close half."),
            ("question", "Offload SAMP."),
            ("question", "Dispose of SAMP."),
            ("question", "Close half the exposure."),
            ("question", "Reduce exposure by half."),
            ("question", "Scale down SAMP."),
            ("question", "Dump 50 shares of SAMP."),
            ("question", "Take profit on 50 shares of SAMP."),
            ("question", "Halve the SAMP position."),
            ("question", "Pare 50 shares from SAMP."),
            ("posture", "Broker liquidation approved for SAMP"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                snapshot = copy.deepcopy(self.complete)
                if field == "question":
                    snapshot["payload"]["question"] = value
                else:
                    snapshot["payload"]["posture"]["label"] = value
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^html_safety_violation$"):
                    build_artifact_packet(snapshot)

    def test_no_javascript_fallback_starts_on_overview_for_non_overview_default(self) -> None:
        packet = build_artifact_packet(self.complete, default_view="Stress Tests")
        manifest = json.loads(packet.manifest)
        html = packet.html.decode("utf-8")

        self.assertEqual(manifest["default_view"], "Stress Tests")
        self.assertRegex(
            html,
            r'id="view-overview"[^>]*aria-labelledby="tab-overview">',
        )
        self.assertRegex(
            html,
            r'id="view-stress-tests"[^>]*aria-labelledby="tab-stress-tests" hidden>',
        )
        self.assertIn(
            'selectPortfolioView(portfolioTabs.find((button)=>button.dataset.viewTarget==="stress-tests")||portfolioTabs[0]);',
            html,
        )

    def test_rejects_actionable_broker_alias_even_when_references_reconcile(self) -> None:
        for alias in ("Ask broker to purchase SAMP now", "Unload Broker SAMP"):
            with self.subTest(alias=alias):
                snapshot = copy.deepcopy(self.complete)
                source = next(
                    item for item in snapshot["source_registry"] if item["id"] == "broker-alpha"
                )
                source["alias"] = alias
                snapshot["payload"]["source_coverage"][0]["source_alias"] = alias
                snapshot["payload"]["aggregations"]["by_broker"][0]["label"] = (
                    f"{alias} / Alpha taxable"
                )
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^html_safety_violation$"):
                    build_artifact_packet(snapshot)

    def test_reconciled_partial_position_detail_remains_usable_but_degrades_board(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        source = snapshot["payload"]["source_coverage"][0]
        source["evidence_state"] = "partial"
        source["gap_reason"] = "One position field remains incomplete."
        module = next(
            item for item in snapshot["payload"]["modules"] if item["id"] == "position_detail"
        )
        module["evidence_state"] = "partial"
        module["gap_reason"] = "One reconciled source has incomplete position evidence."
        snapshot["coverage"]["required_complete"] -= 1
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        packet = build_artifact_packet(snapshot)

        self.assertIn("SAMP2X", packet.html.decode("utf-8"))

    def test_rejects_source_error_claim_when_partial_position_detail_is_usable(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-source-error.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        source = snapshot["payload"]["source_coverage"][0]
        source["detail_status"] = "position_detail"
        source["evidence_state"] = "partial"
        source["reconciliation_status"] = "reconciled"
        source["gap_reason"] = "Some reconciled position detail is usable but incomplete."
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_partial_totals_scope_without_omission_boundaries(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        snapshot["payload"]["totals"]["scope_label"] = "Reconciled sources"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_partial_totals_scope_that_denies_required_omissions(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        invalid_labels = (
            "Confirmed position-detail sources only; NAV-only context not omitted; "
            "excluded holding not omitted",
            "Position-detail sources only are not confirmed; NAV-only and excluded "
            "positions are not omitted",
            "Confirmed position-detail sources only; NAV-only context omitted; "
            "NAV-only context included; excluded holding omitted",
        )
        for label in invalid_labels:
            with self.subTest(label=label):
                snapshot = json.loads(fixture.read_text(encoding="utf-8"))
                snapshot["payload"]["totals"]["scope_label"] = label
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
                    build_artifact_packet(snapshot)

    def test_rejects_position_account_alias_that_disagrees_with_source_coverage(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["account_alias"] = "Fabricated account"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_position_detail_claim_that_ignores_stale_source_registry(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        source = next(
            item for item in snapshot["source_registry"] if item["id"] == "broker-alpha"
        )
        source["as_of"] = "2026-07-17T08:00:00Z"
        source["freshness_status"] = "stale"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^module_freshness_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_complete_coverage_whose_own_timestamp_is_stale(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["source_coverage"][0]["as_of"] = "2020-01-01T00:00:00Z"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_broker_source_that_downgrades_its_freshness_policy(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        source = next(
            item for item in snapshot["source_registry"] if item["id"] == "broker-alpha"
        )
        source["freshness_policy_id"] = "official-current-v1"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_module_timestamp_ahead_of_its_evidence(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        module = next(
            item
            for item in snapshot["payload"]["modules"]
            if item["id"] == "position_detail"
        )
        module["as_of"] = "2026-07-17T09:56:00Z"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^module_freshness_invalid$"):
            build_artifact_packet(snapshot)

    def test_reconciled_stale_position_detail_remains_usable_and_stale(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        broker_refs = {"broker-alpha", "broker-beta"}
        for source in snapshot["source_registry"]:
            if source["id"] in broker_refs:
                source["as_of"] = "2026-07-17T09:00:00Z"
                source["freshness_status"] = "stale"
        for row in snapshot["payload"]["source_coverage"]:
            row["as_of"] = "2026-07-17T09:00:00Z"
            row["fx_as_of"] = "2026-07-17T09:00:00Z"
            row["evidence_state"] = "stale"
            row["gap_reason"] = "Position detail is outside the live-risk freshness window."
        for position in snapshot["payload"]["positions"]:
            position["fx_as_of"] = "2026-07-17T09:00:00Z"
        for balance in snapshot["payload"]["cash_collateral"]:
            balance["as_of"] = "2026-07-17T09:00:00Z"
            balance["fx_as_of"] = "2026-07-17T09:00:00Z"
        stale_module_count = 0
        for module in snapshot["payload"]["modules"]:
            if broker_refs.intersection(module["source_refs"]):
                module["as_of"] = "2026-07-17T09:00:00Z"
                module["evidence_state"] = "stale"
                module["gap_reason"] = "Position detail is outside the live-risk freshness window."
                stale_module_count += 1
        snapshot["coverage"]["required_complete"] -= stale_module_count
        snapshot["evidence_state"] = "stale"
        snapshot["state_reasons"] = ["Position detail is stale but remains reconciled."]
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("stale", html)
        self.assertIn("SAMP2X", html)

    def test_rejects_direct_exposure_that_diverges_from_market_value(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["direct_exposure"] -= 100.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_position_fields_that_conflict_with_product_semantics(self) -> None:
        mutations = (
            lambda snapshot: snapshot["payload"]["positions"][0].__setitem__(
                "direction", "short"
            ),
            lambda snapshot: (
                snapshot["payload"]["positions"][0].__setitem__("notional_exposure", 16000.0),
                snapshot["payload"]["positions"][0].__setitem__("source_notional_exposure", 16000.0),
            ),
            lambda snapshot: snapshot["payload"]["positions"][1].__setitem__(
                "leverage_multiple", 3.0
            ),
            lambda snapshot: (
                snapshot["payload"]["positions"][1].__setitem__("delta_exposure", 5000.0),
                snapshot["payload"]["positions"][1].__setitem__("source_delta_exposure", 5000.0),
            ),
            lambda snapshot: snapshot["payload"]["positions"][3][
                "option_greeks"
            ].__setitem__("delta", 0.5),
            lambda snapshot: (
                snapshot["payload"]["positions"][3].__setitem__("notional_exposure", -10000.0),
                snapshot["payload"]["positions"][3].__setitem__("source_notional_exposure", -10000.0),
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                snapshot = copy.deepcopy(self.complete)
                mutate(snapshot)
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
                    build_artifact_packet(snapshot)

    def test_rejects_option_delta_outside_the_valid_domain(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        option = snapshot["payload"]["positions"][3]
        option["option_greeks"]["delta"] = 1.5
        option["delta_exposure"] = 15000.0
        option["source_delta_exposure"] = 15000.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^option_greeks_required$"):
            build_artifact_packet(snapshot)

    def test_accepts_one_x_inverse_etf_with_directional_exposure(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        position = snapshot["payload"]["positions"][1]
        position["product_type"] = "inverse_etf"
        position["leverage_multiple"] = 1.0
        position["notional_exposure"] = -5000.0
        position["delta_exposure"] = -5000.0
        position["source_notional_exposure"] = -5000.0
        position["source_delta_exposure"] = -5000.0
        totals = snapshot["payload"]["totals"]
        totals["gross_delta_exposure"] -= 5000.0
        totals["net_delta_exposure"] -= 15000.0
        for rows in snapshot["payload"]["aggregations"].values():
            for row in rows:
                if position["id"] in row["affected_position_ids"]:
                    row["delta_exposure"] -= 15000.0
                    row["notional_exposure"] -= 15000.0
                    if rows is snapshot["payload"]["aggregations"]["by_product"]:
                        row["label"] = "Inverse ETF"
                selected = [
                    item
                    for item in snapshot["payload"]["positions"]
                    if item["id"] in row["affected_position_ids"]
                ]
                row["weight_pct"] = round(
                    100.0
                    * sum(abs(item["delta_exposure"] or 0.0) for item in selected)
                    / totals["gross_delta_exposure"],
                    1,
                )
        for scenario in snapshot["payload"]["stress_scenarios"]:
            if position["id"] in scenario["affected_position_ids"]:
                scenario["covered_exposure"] -= 5000.0
                contribution = next(
                    item
                    for item in scenario["impact_contributions"]
                    if item["position_id"] == position["id"]
                )
                contribution["estimated_impact"] = (
                    position["delta_exposure"] * contribution["shock_pct"]
                )
                scenario["estimated_impact"] = sum(
                    item["estimated_impact"]
                    for item in scenario["impact_contributions"]
                )
        self._rehash(snapshot)

        packet = build_artifact_packet(snapshot)

        self.assertIn(
            '<article class="product-detail"><h3>SAMP2X',
            packet.html.decode("utf-8"),
        )

    def test_rejects_cash_context_that_does_not_reconcile_to_confirmed_nav(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["totals"]["cash_context"] = 999999.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^portfolio_totals_invalid$"):
            build_artifact_packet(snapshot)

    def test_complete_snapshot_exposes_explicit_cash_and_collateral_provenance(self) -> None:
        rows = self.complete["payload"]["cash_collateral"]

        self.assertEqual(
            {row["source_ref"] for row in rows},
            set(self.complete["payload"]["totals"]["confirmed_source_refs"]),
        )
        html = build_artifact_packet(self.complete).html.decode("utf-8")
        self.assertIn("Cash and collateral balances", html)
        self.assertIn("Cash balance", html)
        self.assertIn("Collateral value", html)
        self.assertIn("Balance source / as of", html)

    def test_product_view_exposes_risk_horizon_and_option_expiry(self) -> None:
        option = next(
            position
            for position in self.complete["payload"]["positions"]
            if position["product_type"] == "option"
        )

        self.assertEqual(option["risk_horizon"], "medium_term")
        self.assertIsNotNone(option["expiry_at"])
        html = build_artifact_packet(self.complete).html.decode("utf-8")
        self.assertIn("Risk horizon", html)
        self.assertIn("Expiry", html)

    def test_rejects_cash_balance_that_breaks_source_nav_reconciliation(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["cash_collateral"][0]["cash_balance"] += 1.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^cash_collateral_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_missing_or_invalid_product_horizon_fields(self) -> None:
        mutations = (
            lambda position: position.__setitem__("risk_horizon", "unknown"),
            lambda position: position.__setitem__("expiry_at", "2026-08-01T00:00:00Z"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                snapshot = copy.deepcopy(self.complete)
                mutate(snapshot["payload"]["positions"][0])
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
                    build_artifact_packet(snapshot)

        snapshot = copy.deepcopy(self.complete)
        option = next(
            position
            for position in snapshot["payload"]["positions"]
            if position["product_type"] == "option"
        )
        option["expiry_at"] = None
        self._rehash(snapshot)
        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_complete_module_rejects_an_unresolved_gap(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["modules"][0]["gap_reason"] = "Unresolved evidence gap."
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^modules_invalid$"):
            build_artifact_packet(snapshot)

    def test_degraded_module_requires_an_explicit_gap(self) -> None:
        for evidence_state in ("partial", "stale", "source_error"):
            with self.subTest(evidence_state=evidence_state):
                snapshot = copy.deepcopy(self.complete)
                snapshot["payload"]["modules"][0]["evidence_state"] = evidence_state
                snapshot["coverage"]["required_complete"] -= 1
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^modules_invalid$"):
                    build_artifact_packet(snapshot)

    def test_complete_source_rejects_an_unresolved_gap(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["source_coverage"][0]["gap_reason"] = (
            "Unresolved reconciliation gap."
        )
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
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

    def test_rejects_invalid_identity_currency_conversion_metadata(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["source_coverage"][0]["fx_rate_to_base"] = 1.01
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
            build_artifact_packet(snapshot)

    def test_cross_currency_positions_are_auditable_in_base_currency(self) -> None:
        snapshot = self._cross_currency_snapshot()
        fx_ref = "fx-krw-usd"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("KRW → USD", html)
        self.assertIn(fx_ref, html)
        self.assertIn("8,700,000 → 8,700", html)

    def test_rejects_fx_source_that_downgrades_its_freshness_policy(self) -> None:
        snapshot = self._cross_currency_snapshot()
        fx_source = next(
            item for item in snapshot["source_registry"] if item["id"] == "fx-krw-usd"
        )
        fx_source["freshness_policy_id"] = "official-current-v1"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_s4_as_the_sole_cross_currency_fx_authority(self) -> None:
        snapshot = self._cross_currency_snapshot()
        fx_source = next(
            item for item in snapshot["source_registry"] if item["id"] == "fx-krw-usd"
        )
        fx_source["priority"] = "S4"
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^source_coverage_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_unconverted_nav_only_context_outside_base_currency(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        nav_only = next(
            row
            for row in snapshot["payload"]["source_coverage"]
            if row["detail_status"] == "nav_only"
        )
        nav_only.update(
            {
                "source_currency": "EUR",
                "source_nav_context": nav_only["nav_context"],
                "currency": "EUR",
                "fx_rate_to_base": 1.0,
                "fx_source_ref": None,
            }
        )
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^position_currency_invalid$"):
            build_artifact_packet(snapshot)

    def test_stress_disclosure_labels_normalized_nav_context_currency(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Unscoped NAV context (USD)", html)

    def test_cross_currency_nav_only_context_uses_fresh_s1_fx(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        fx_ref = "fx-eur-usd-nav"
        fx_as_of = "2026-07-17T09:50:00Z"
        rate = 6000.0 / 5400.0
        snapshot["source_registry"].append(
            {
                "id": fx_ref,
                "alias": "Synthetic EUR USD NAV rate",
                "priority": "S1",
                "as_of": fx_as_of,
                "freshness_policy_id": "intraday-market-v1",
                "freshness_status": "fresh",
            }
        )
        nav_only = next(
            row
            for row in snapshot["payload"]["source_coverage"]
            if row["detail_status"] == "nav_only"
        )
        nav_only.update(
            {
                "source_currency": "EUR",
                "source_nav_context": 5400.0,
                "fx_rate_to_base": rate,
                "fx_as_of": fx_as_of,
                "fx_source_ref": fx_ref,
            }
        )
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("EUR → USD", html)
        self.assertIn(fx_ref, html)
        self.assertIn("Unscoped NAV context (USD)", html)

    def test_partial_scenario_degrades_a_complete_snapshot(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        for scenario in snapshot["payload"]["stress_scenarios"]:
            scenario["status"] = "partial"
            scenario["gap_reason"] = "Scenario coverage is incomplete."
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^evidence_state_mismatch$"):
            build_artifact_packet(snapshot)

    def test_complete_scenario_rejects_an_unresolved_gap(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["stress_scenarios"][0]["gap_reason"] = (
            "Unresolved scenario gap."
        )
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
            build_artifact_packet(snapshot)

    def test_partial_scenario_status_and_gap_are_visible(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn(">partial · low confidence<", html)
        self.assertIn("Scenario gap:", html)

    def test_scenario_only_partial_gap_is_visible_in_static_evidence_rail(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        for scenario in snapshot["payload"]["stress_scenarios"]:
            scenario["status"] = "partial"
            scenario["gap_reason"] = "Scenario coverage is incomplete."
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("<strong>stress:Rates +75 bps</strong>", html)
        self.assertIn("partial · Scenario coverage is incomplete.", html)
        self.assertNotIn("No evidence gaps in this snapshot.", html)

    def test_scenario_only_stale_gap_is_visible_in_static_evidence_rail(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        for scenario in snapshot["payload"]["stress_scenarios"]:
            scenario["status"] = "stale"
            scenario["gap_reason"] = "Scenario inputs are stale."
        snapshot["evidence_state"] = "stale"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("<strong>stress:Rates +75 bps</strong>", html)
        self.assertIn("stale · Scenario inputs are stale.", html)
        self.assertNotIn("No evidence gaps in this snapshot.", html)

    def test_rejects_position_value_that_does_not_match_its_fx_conversion(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["positions"][0]["source_market_value"] += 1.0
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

    def test_rejects_stress_coverage_that_uses_market_value_or_hides_nav_context(self) -> None:
        for field, value in (
            ("covered_exposure", 18700.0),
            ("coverage_basis", "direct_market_value"),
            ("unscoped_nav_context", 999.0),
        ):
            with self.subTest(field=field):
                snapshot = copy.deepcopy(self.complete)
                snapshot["payload"]["stress_scenarios"][0][field] = value
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
                    build_artifact_packet(snapshot)

    def test_rejects_complete_scenarios_when_stress_inputs_are_unavailable(self) -> None:
        for scenario_state in ("complete", "partial"):
            with self.subTest(scenario_state=scenario_state):
                snapshot = copy.deepcopy(self.complete)
                module = next(
                    item
                    for item in snapshot["payload"]["modules"]
                    if item["id"] == "stress_inputs"
                )
                module["evidence_state"] = "source_error"
                module["gap_reason"] = "Stress assumptions are unavailable."
                for scenario in snapshot["payload"]["stress_scenarios"]:
                    scenario["status"] = scenario_state
                snapshot["coverage"]["required_complete"] -= 1
                snapshot["evidence_state"] = "partial"
                self._rehash(snapshot)

                with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
                    build_artifact_packet(snapshot)

    def test_source_error_stress_inputs_allow_an_empty_scenario_set(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        module = next(
            item
            for item in snapshot["payload"]["modules"]
            if item["id"] == "stress_inputs"
        )
        module["evidence_state"] = "source_error"
        module["gap_reason"] = "Stress assumptions are unavailable."
        snapshot["payload"]["stress_scenarios"] = []
        snapshot["coverage"]["required_complete"] -= 1
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Stress assumptions are unavailable", html)
        self.assertIn("SAMP2X", html)

    def test_rejects_stress_impact_that_does_not_reconcile_to_position_contributions(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["payload"]["stress_scenarios"][0]["impact_contributions"][0]["estimated_impact"] += 1.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
            build_artifact_packet(snapshot)

    def test_rejects_offsetting_stress_contributions_without_position_shock_support(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        contributions = snapshot["payload"]["stress_scenarios"][0]["impact_contributions"]
        contributions[0]["estimated_impact"] += 5000.0
        contributions[1]["estimated_impact"] -= 5000.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^stress_scenarios_invalid$"):
            build_artifact_packet(snapshot)

    def test_source_error_stress_with_exclusion_keeps_disclosure_and_no_scenarios(self) -> None:
        fixture = self.root / "assets" / "fixtures" / "input" / "portfolio-risk-partial.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        module = next(
            item
            for item in snapshot["payload"]["modules"]
            if item["id"] == "stress_inputs"
        )
        if module["evidence_state"] == "complete":
            snapshot["coverage"]["required_complete"] -= 1
        module["evidence_state"] = "source_error"
        module["gap_reason"] = "Stress assumptions are unavailable."
        snapshot["payload"]["stress_scenarios"] = []
        for exclusion in snapshot["payload"]["exclusions"]:
            exclusion["affected_scenarios"] = []
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Stress assumptions are unavailable", html)
        self.assertIn("EXCL2X", html)

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
        snapshot["payload"]["positions"][0]["source_delta_exposure"] = None
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
        snapshot["payload"]["aggregations"]["by_broker"][0]["label"] = "WRONG SOURCE"
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
        option["source_delta_exposure"] = None
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
            scenario["unscoped_derivative_notional"] = abs(
                option["notional_exposure"]
            )
            if option["id"] in scenario["affected_position_ids"]:
                scenario["affected_position_ids"].remove(option["id"])
                scenario["affected_holdings"].remove(option["symbol"])
                scenario["covered_exposure"] -= 3200.0
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
                scenario["gap_reason"] = (
                    "Option Greeks unavailable; related stress coverage is incomplete."
                )
        snapshot["coverage"]["required_complete"] -= 2
        snapshot["evidence_state"] = "partial"
        self._rehash(snapshot)

        html = build_artifact_packet(snapshot).html.decode("utf-8")

        self.assertIn("Greeks unavailable", html)
        self.assertIn("Unscoped derivative notional</dt><dd>10,000", html)
        self.assertIn("Cash equities", html)

    def test_rejects_missing_greeks_option_with_wrong_notional_direction(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        option = snapshot["payload"]["positions"][3]
        option["option_greeks"] = None
        option["delta_exposure"] = None
        option["source_delta_exposure"] = None
        option["notional_exposure"] = -10000.0
        option["source_notional_exposure"] = -10000.0
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^positions_invalid$"):
            build_artifact_packet(snapshot)

    def test_complete_module_rejects_a_mixed_fresh_and_stale_source_set(self) -> None:
        snapshot = copy.deepcopy(self.complete)
        snapshot["source_registry"].append(
            {
                "id": "stale-support",
                "alias": "Synthetic stale support",
                "priority": "S1",
                "as_of": "2026-07-17T09:30:00Z",
                "freshness_policy_id": "intraday-market-v1",
                "freshness_status": "stale",
            }
        )
        snapshot["payload"]["modules"][0]["source_refs"].append("stale-support")
        self._rehash(snapshot)

        with self.assertRaisesRegex(ArtifactPacketError, "^module_source_support_invalid$"):
            build_artifact_packet(snapshot)

    def _cross_currency_snapshot(self) -> dict:
        snapshot = copy.deepcopy(self.complete)
        fx_ref = "fx-krw-usd"
        fx_as_of = "2026-07-17T09:55:00Z"
        rate = 0.001
        snapshot["source_registry"].append(
            {
                "id": fx_ref,
                "alias": "Synthetic KRW USD rate",
                "priority": "S1",
                "as_of": fx_as_of,
                "freshness_policy_id": "intraday-market-v1",
                "freshness_status": "fresh",
            }
        )
        coverage = next(
            row
            for row in snapshot["payload"]["source_coverage"]
            if row["source_ref"] == "broker-beta"
        )
        coverage.update(
            {
                "source_currency": "KRW",
                "source_nav_context": coverage["nav_context"] / rate,
                "fx_rate_to_base": rate,
                "fx_as_of": fx_as_of,
                "fx_source_ref": fx_ref,
            }
        )
        balance = next(
            row
            for row in snapshot["payload"]["cash_collateral"]
            if row["source_ref"] == "broker-beta"
        )
        balance.update(
            {
                "source_currency": "KRW",
                "source_cash_balance": balance["cash_balance"] / rate,
                "source_collateral_value": balance["collateral_value"] / rate,
                "fx_rate_to_base": rate,
                "fx_as_of": fx_as_of,
                "fx_source_ref": fx_ref,
            }
        )
        for position in snapshot["payload"]["positions"]:
            if position["source_ref"] != "broker-beta":
                continue
            position.update(
                {
                    "source_currency": "KRW",
                    "source_market_value": position["market_value"] / rate,
                    "source_direct_exposure": position["direct_exposure"] / rate,
                    "source_delta_exposure": (
                        None
                        if position["delta_exposure"] is None
                        else position["delta_exposure"] / rate
                    ),
                    "source_notional_exposure": position["notional_exposure"] / rate,
                    "fx_rate_to_base": rate,
                    "fx_as_of": fx_as_of,
                    "fx_source_ref": fx_ref,
                }
            )
        reconciliation = next(
            module
            for module in snapshot["payload"]["modules"]
            if module["id"] == "reconciliation"
        )
        reconciliation["source_refs"].append(fx_ref)
        return snapshot

    @staticmethod
    def _rehash(snapshot: dict) -> None:
        snapshot.pop("content_hash", None)
        canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        snapshot["content_hash"] = hashlib.sha256(canonical).hexdigest()


if __name__ == "__main__":
    unittest.main()
