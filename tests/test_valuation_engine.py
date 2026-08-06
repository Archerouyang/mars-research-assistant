from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "mars-research-assistant"
VALUATION_ENGINE = (
    RUNTIME / "skills" / "deep-equity-research" / "scripts" / "dcf.py"
)
FIXTURES = ROOT / "tests" / "fixtures"
FULL_FIXTURE = FIXTURES / "valuation-full.json"
MISSING_FIXTURE = FIXTURES / "valuation-missing-inputs.json"
INVALID_PROBABILITY_FIXTURE = FIXTURES / "valuation-invalid-probability.json"
NOT_APPLICABLE_FIXTURE = FIXTURES / "valuation-not-applicable.json"


def scenario_per_share(
    cash_flows: list[float],
    wacc: float,
    terminal_growth: float,
    net_debt: float,
    shares: float,
) -> float:
    discounted = sum(
        cash_flow / (1 + wacc) ** year
        for year, cash_flow in enumerate(cash_flows, 1)
    )
    terminal = cash_flows[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    enterprise = discounted + terminal / (1 + wacc) ** len(cash_flows)
    return (enterprise - net_debt) / shares


class ValuationEngineTests(unittest.TestCase):
    def _run(self, fixture: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALUATION_ENGINE), "--input", str(fixture), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_full_fixture_recomputes_all_models_deterministically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            first_output = Path(temporary) / "mars-research" / "valuation-1.json"
            second_output = Path(temporary) / "mars-research" / "valuation-2.json"
            first = self._run(FULL_FIXTURE, first_output)
            second = self._run(FULL_FIXTURE, second_output)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            artifact = json.loads(first_output.read_text(encoding="utf-8"))
            rerun = json.loads(second_output.read_text(encoding="utf-8"))
        self.assertEqual(artifact, rerun)
        self.assertEqual(artifact["engine_version"], "1.0.0")
        self.assertEqual(artifact["model_version"], "v1.0.3-valuation-1")
        self.assertEqual(artifact["market_scope"], "us")
        self.assertEqual(artifact["currency"], "USD")
        for field in ("issuer_id", "listing_id", "case_id", "artifact_version", "schema_version"):
            self.assertIn(field, artifact["identity"])

        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        dcf_input = fixture["models"]["dcf"]
        wacc = dcf_input["wacc"]["value"]
        growth = dcf_input["terminal_growth"]["value"]
        net_debt = dcf_input["net_debt"]["value"]
        shares = dcf_input["shares_outstanding"]["value"]
        input_scenarios = {
            item["name"]: item for item in dcf_input["scenarios"]
        }
        results = artifact["results"]
        for model in ("dcf", "reverse_dcf", "pvgo", "epv", "eva", "sotp", "monte_carlo"):
            with self.subTest(model=model):
                self.assertEqual(results[model]["status"], "computed")

        dcf = results["dcf"]
        self.assertEqual(
            [entry["name"] for entry in dcf["scenarios"]], ["bear", "base", "bull"]
        )
        weighted = 0.0
        per_share_by_name: dict[str, float] = {}
        for entry in dcf["scenarios"]:
            source = input_scenarios[entry["name"]]
            expected = scenario_per_share(
                source["free_cash_flows"], wacc, growth, net_debt, shares
            )
            per_share_by_name[entry["name"]] = expected
            self.assertAlmostEqual(entry["per_share"], expected, delta=1e-6)
            self.assertAlmostEqual(
                entry["probability"], source["probability"]["value"], delta=1e-12
            )
            weighted += source["probability"]["value"] * expected
        self.assertAlmostEqual(
            dcf["probability_weighted_per_share"], weighted, delta=1e-6
        )
        checks = dcf["terminal_value_checks"]
        for key in ("long_run_growth", "mature_margin", "reinvestment_roic_consistency"):
            with self.subTest(check=key):
                self.assertIn(key, checks)
                self.assertIn(checks[key]["status"], {"pass", "warn", "fail"})
                self.assertIsInstance(checks[key]["detail"], str)
        self.assertEqual(checks["long_run_growth"]["status"], "pass")
        self.assertEqual(checks["mature_margin"]["status"], "pass")
        self.assertEqual(checks["reinvestment_roic_consistency"]["status"], "pass")
        self.assertAlmostEqual(
            dcf["value_zone"]["low"], per_share_by_name["bear"], delta=1e-6
        )
        self.assertAlmostEqual(dcf["value_zone"]["high"], weighted, delta=1e-6)

        monte_carlo = results["monte_carlo"]
        self.assertEqual(monte_carlo["seed"], 42)
        self.assertEqual(monte_carlo["trials"], 500)
        self.assertEqual(
            monte_carlo, rerun["results"]["monte_carlo"],
            "seeded Monte Carlo must be byte-identical across runs",
        )
        for key in ("p10", "p50", "p90"):
            self.assertIn(key, monte_carlo["percentiles"])
        self.assertLessEqual(
            monte_carlo["percentiles"]["p10"], monte_carlo["percentiles"]["p50"]
        )
        self.assertLessEqual(
            monte_carlo["percentiles"]["p50"], monte_carlo["percentiles"]["p90"]
        )
        self.assertEqual(results["reverse_dcf"]["horizon_years"], 10)

    def test_missing_inputs_fail_closed_without_fair_value_numbers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            output = Path(temporary) / "mars-research" / "valuation.json"
            result = self._run(MISSING_FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
        dcf = artifact["results"]["dcf"]
        self.assertEqual(dcf["status"], "missing_inputs")
        self.assertIn("wacc", dcf["missing"])
        self.assertNotIn("per_share", json.dumps(dcf, ensure_ascii=False))
        self.assertTrue(artifact["data_gaps"])

    def test_probabilities_not_summing_to_one_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            output = Path(temporary) / "mars-research" / "valuation.json"
            result = self._run(INVALID_PROBABILITY_FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
        dcf = artifact["results"]["dcf"]
        self.assertEqual(dcf["status"], "invalid_inputs")
        self.assertNotIn("probability_weighted_per_share", dcf)
        self.assertTrue(
            any("概率" in gap for gap in artifact["data_gaps"]),
            artifact["data_gaps"],
        )

    def test_not_applicable_models_keep_their_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            output = Path(temporary) / "mars-research" / "valuation.json"
            result = self._run(NOT_APPLICABLE_FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
        fixture = json.loads(NOT_APPLICABLE_FIXTURE.read_text(encoding="utf-8"))
        for model in ("pvgo", "epv"):
            with self.subTest(model=model):
                entry = artifact["results"][model]
                self.assertEqual(entry["status"], "not_applicable")
                self.assertEqual(entry["reason"], fixture["models"][model]["reason"])
        self.assertEqual(artifact["results"]["dcf"]["status"], "computed")

    def test_reverse_dcf_reports_no_solution_for_extreme_price(self) -> None:
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        fixture["models"]["dcf"]["price"]["value"] = 10_000_000.0
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            temporary_path = Path(temporary)
            extreme = temporary_path / "extreme-price.json"
            extreme.write_text(
                json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
            )
            output = temporary_path / "mars-research" / "valuation.json"
            result = self._run(extreme, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
        reverse = artifact["results"]["reverse_dcf"]
        self.assertEqual(reverse["status"], "no_solution")
        self.assertNotIn("implied_fcf_cagr", reverse)
        self.assertIn("-95.00%", reverse["detail"])
        self.assertIn("300.00%", reverse["detail"])

    def test_output_path_inside_runtime_package_is_refused(self) -> None:
        output = RUNTIME / "blocked-valuation.json"
        try:
            result = self._run(FULL_FIXTURE, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Skill runtime package", result.stderr)
            self.assertFalse(output.exists())
        finally:
            output.unlink(missing_ok=True)

    def test_output_never_overwrites_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            output = Path(temporary) / "mars-research" / "valuation.json"
            first = self._run(FULL_FIXTURE, output)
            second = self._run(FULL_FIXTURE, output)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("File exists", second.stderr)

    def _run_modified_fixture(
        self, mutate: Callable[[dict], None]
    ) -> dict:
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        mutate(fixture)
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            temporary_path = Path(temporary)
            modified = temporary_path / "modified.json"
            modified.write_text(
                json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
            )
            output = temporary_path / "mars-research" / "valuation.json"
            result = self._run(modified, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(output.read_text(encoding="utf-8"))

    def test_provenance_retains_source_derivation_currency_and_period(self) -> None:
        def mutate(fixture: dict) -> None:
            fixture["models"]["dcf"]["net_debt"]["currency"] = "USD"
            fixture["models"]["dcf"]["net_debt"]["accounting_period"] = "FY2025"
            fixture["models"]["monte_carlo"]["distributions"]["wacc"]["source"] = {
                "name": "Example distribution assumption",
                "kind": "valuation_assumption",
                "as_of": "2026-07-30T00:00:00Z",
                "url": "https://example.com/distribution",
            }

        artifact = self._run_modified_fixture(mutate)
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        dcf = artifact["results"]["dcf"]
        self.assertEqual(dcf["status"], "computed")
        self.assertNotIn("source_gaps", dcf)
        provenance = dcf["inputs_provenance"]
        for name in (
            "price",
            "shares_outstanding",
            "net_debt",
            "wacc",
            "terminal_growth",
            "long_run_growth_cap",
            "mature_margin_benchmark",
        ):
            with self.subTest(field=name):
                record = provenance[name]
                self.assertEqual(
                    record["value"], fixture["models"]["dcf"][name]["value"]
                )
                self.assertEqual(
                    record["source"], fixture["models"]["dcf"][name]["source"]
                )
        self.assertEqual(
            provenance["wacc"]["derivation"],
            fixture["models"]["dcf"]["wacc"]["derivation"],
        )
        self.assertEqual(provenance["net_debt"]["currency"], "USD")
        self.assertEqual(provenance["net_debt"]["accounting_period"], "FY2025")
        self.assertIsNone(provenance["price"]["currency"])
        self.assertIsNone(provenance["price"]["derivation"])
        monte_carlo = artifact["results"]["monte_carlo"]["inputs_provenance"]
        self.assertEqual(
            monte_carlo["distributions"]["wacc"]["source"]["name"],
            "Example distribution assumption",
        )
        self.assertIsNone(
            monte_carlo["distributions"]["terminal_growth"]["source"]
        )
        eva_nopat = artifact["results"]["eva"]["inputs_provenance"]["nopat_path"]
        self.assertEqual(eva_nopat["value"], fixture["models"]["eva"]["nopat_path"])
        self.assertIsNone(eva_nopat["source"])
        self.assertNotIn("source_inherited_from", eva_nopat)
        self.assertEqual(artifact["data_gaps"], [])

    def test_scenario_and_segment_source_inheritance(self) -> None:
        artifact = self._run_modified_fixture(lambda fixture: None)
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        scenarios = artifact["results"]["dcf"]["inputs_provenance"]["scenarios"]
        for name in ("bear", "base", "bull"):
            with self.subTest(scenario=name):
                scenario_source = next(
                    item["source"]
                    for item in fixture["models"]["dcf"]["scenarios"]
                    if item["name"] == name
                )
                record = scenarios[name]
                for field in (
                    "probability",
                    "free_cash_flows",
                    "margins",
                    "reinvestment_rate",
                    "roic",
                ):
                    self.assertEqual(record[field]["source"], scenario_source)
                    self.assertEqual(
                        record[field]["source_inherited_from"], "scenario"
                    )
        segments = artifact["results"]["sotp"]["inputs_provenance"]["segments"]
        self.assertEqual(
            [segment["name"] for segment in segments],
            ["core", "services", "investments"],
        )
        core = segments[0]["inputs"]
        self.assertEqual(
            core["wacc"]["source"],
            fixture["models"]["sotp"]["segments"][0]["source"],
        )
        self.assertEqual(core["wacc"]["source_inherited_from"], "segment")
        self.assertEqual(
            core["free_cash_flows"]["source_inherited_from"], "segment"
        )

        def mutate(fixture: dict) -> None:
            fixture["models"]["sotp"]["segments"][0]["inputs"]["wacc"]["source"] = {
                "name": "Segment-specific wacc note",
                "kind": "issuer_ir",
                "as_of": "2026-07-29T00:00:00Z",
                "url": "https://example.com/segment-wacc",
            }

        overridden = self._run_modified_fixture(mutate)
        core_wacc = overridden["results"]["sotp"]["inputs_provenance"]["segments"][0][
            "inputs"
        ]["wacc"]
        self.assertEqual(core_wacc["source"]["name"], "Segment-specific wacc note")
        self.assertNotIn("source_inherited_from", core_wacc)

    def test_missing_key_source_is_annotated_not_silent(self) -> None:
        def mutate(fixture: dict) -> None:
            del fixture["models"]["dcf"]["wacc"]["source"]
            del fixture["models"]["dcf"]["scenarios"][0]["source"]

        artifact = self._run_modified_fixture(mutate)
        dcf = artifact["results"]["dcf"]
        self.assertEqual(dcf["status"], "computed")
        self.assertIn("probability_weighted_per_share", dcf)
        self.assertEqual(
            dcf["source_gaps"], ["wacc", "scenarios[0].probability"]
        )
        self.assertIsNone(
            dcf["inputs_provenance"]["wacc"]["source"]
        )
        self.assertIsNone(
            dcf["inputs_provenance"]["scenarios"]["bear"]["probability"]["source"]
        )
        self.assertTrue(
            any("wacc" in gap and "缺少来源" in gap for gap in artifact["data_gaps"]),
            artifact["data_gaps"],
        )
        self.assertTrue(
            any(
                "scenarios[0].probability" in gap for gap in artifact["data_gaps"]
            ),
            artifact["data_gaps"],
        )

    def test_malformed_source_fails_closed(self) -> None:
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        fixture["models"]["dcf"]["price"]["source"]["kind"] = "search_summary"
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            temporary_path = Path(temporary)
            modified = temporary_path / "bad-source.json"
            modified.write_text(
                json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
            )
            output = temporary_path / "mars-research" / "valuation.json"
            result = self._run(modified, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("kind", result.stderr)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        self.assertFalse(output.exists())

    def _run_mutated_fixture(
        self, mutate: Callable[[dict], None]
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
        mutate(fixture)
        temporary = tempfile.TemporaryDirectory(prefix="mars-v103-valuation-")
        self.addCleanup(temporary.cleanup)
        temporary_path = Path(temporary.name)
        modified = temporary_path / "modified.json"
        modified.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        output = temporary_path / "mars-research" / "valuation.json"
        return self._run(modified, output), output

    def test_identity_versions_must_be_one(self) -> None:
        for field in ("artifact_version", "schema_version"):
            with self.subTest(field=field):
                result, output = self._run_mutated_fixture(
                    lambda fixture: fixture["identity"].update({field: 2})
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"identity {field} must be 1", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(output.exists())

    def test_scenario_probability_out_of_range_is_rejected(self) -> None:
        # 概率之和仍为 1，但单情景概率越界 [0, 1] 必须拒绝。
        def mutate(fixture: dict) -> None:
            scenarios = fixture["models"]["dcf"]["scenarios"]
            scenarios[0]["probability"]["value"] = -0.25
            scenarios[1]["probability"]["value"] = 1.0

        result, output = self._run_mutated_fixture(mutate)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact = json.loads(output.read_text(encoding="utf-8"))
        dcf = artifact["results"]["dcf"]
        self.assertEqual(dcf["status"], "invalid_inputs")
        self.assertIn("[0, 1]", dcf["detail"])
        self.assertNotIn("probability_weighted_per_share", dcf)

    def test_ah_compare_and_vie_adr_blocks_pass_through(self) -> None:
        def mutate(fixture: dict) -> None:
            fixture["ah_compare"] = {
                "pair": {"a_share_listing_id": "TP.SS", "hk_listing_id": "TP.HK"},
                "fx_pair": "CNY/HKD",
                "fx_rate": 1.09,
                "share_right_ratio": 1.0,
                "liquidity_diff": "离线验收示例：流动性差异。",
                "trading_day_diff": "离线验收示例：交易日历差异。",
                "premium_discount": 0.12,
            }
            fixture["vie_adr"] = {"us_listed_chinese_issuer": False}

        artifact = self._run_modified_fixture(mutate)
        self.assertEqual(artifact["ah_compare"]["fx_pair"], "CNY/HKD")
        self.assertEqual(artifact["ah_compare"]["fx_rate"], 1.09)
        self.assertEqual(artifact["vie_adr"], {"us_listed_chinese_issuer": False})

    def test_malformed_ah_compare_block_fails_closed(self) -> None:
        result, output = self._run_mutated_fixture(
            lambda fixture: fixture.update({"ah_compare": "not-an-object"})
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ah_compare requires an object", result.stderr)
        self.assertFalse(output.exists())

    def test_top_level_schema_version_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mars-v103-valuation-") as temporary:
            output = Path(temporary) / "mars-research" / "valuation.json"
            result = self._run(FULL_FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(artifact["schema_version"], 1)
        for field in ("issuer_id", "listing_id", "case_id", "artifact_version", "schema_version"):
            self.assertIn(field, artifact["identity"])
        self.assertEqual(artifact["identity"]["schema_version"], 1)

    def test_source_missing_url_fails_closed(self) -> None:
        def strip_dcf_url(fixture: dict) -> None:
            del fixture["models"]["dcf"]["price"]["source"]["url"]

        def strip_reverse_dcf_url(fixture: dict) -> None:
            del fixture["models"]["reverse_dcf"]["current_free_cash_flow"]["source"]["url"]

        def strip_monte_carlo_url(fixture: dict) -> None:
            fixture["models"]["monte_carlo"]["distributions"]["wacc"]["source"] = {
                "name": "Distribution assumption without url",
                "kind": "valuation_assumption",
                "as_of": "2026-07-30T00:00:00Z",
            }

        cases = {
            "dcf": strip_dcf_url,
            "reverse_dcf": strip_reverse_dcf_url,
            "monte_carlo": strip_monte_carlo_url,
        }
        for label, mutate in cases.items():
            with self.subTest(model=label):
                fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
                mutate(fixture)
                with tempfile.TemporaryDirectory(
                    prefix="mars-v103-valuation-"
                ) as temporary:
                    temporary_path = Path(temporary)
                    modified = temporary_path / "missing-url.json"
                    modified.write_text(
                        json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
                    )
                    output = temporary_path / "mars-research" / "valuation.json"
                    result = self._run(modified, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("url", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(output.exists())


    def test_source_as_of_after_computed_as_of_fails_closed(self) -> None:
        cases = {
            "dcf price source": lambda fixture: fixture["models"]["dcf"]["price"][
                "source"
            ].update(as_of="2026-07-31T00:00:00Z"),
            "scenario source": lambda fixture: fixture["models"]["dcf"]["scenarios"][
                0
            ]["source"].update(as_of="2026-08-01T00:00:00Z"),
            "monte_carlo distribution source": lambda fixture: fixture["models"][
                "monte_carlo"
            ]["distributions"]["wacc"].update(
                source={
                    "name": "Late distribution assumption",
                    "kind": "valuation_assumption",
                    "as_of": "2026-07-30T12:00:01Z",
                    "url": "https://example.com/late-distribution",
                }
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                result, output = self._run_mutated_fixture(mutate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("after fixture computed_as_of", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(output.exists())

    def test_bool_top_level_schema_version_fails_closed(self) -> None:
        result, output = self._run_mutated_fixture(
            lambda fixture: fixture.update(schema_version=True)
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture schema_version must be 1", result.stderr)
        self.assertFalse(output.exists())

    def test_unknown_market_scope_and_currency_fail_closed(self) -> None:
        for field, value in (("market_scope", "moon"), ("currency", "JPY")):
            with self.subTest(field=field):
                result, output = self._run_mutated_fixture(
                    lambda fixture, f=field, v=value: fixture.update({f: v})
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("not supported", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1)
                self.assertFalse(output.exists())

    def test_short_selling_advice_in_guarded_text_fails_closed(self) -> None:
        cases = {
            "derivation 做空": lambda fixture: fixture["models"]["dcf"]["wacc"].update(
                derivation="建议做空对冲。"
            ),
            "derivation short": lambda fixture: fixture["models"]["dcf"]["wacc"].update(
                derivation="pair with a short leg"
            ),
            "rationale 沽空": lambda fixture: fixture["models"]["dcf"]["scenarios"][
                0
            ]["probability"].update(rationale="可沽空相关 ETF 对冲。"),
            "not_applicable reason 卖空": lambda fixture: fixture["models"][
                "pvgo"
            ].update(status="not_applicable", reason="建议卖空。"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                result, output = self._run_mutated_fixture(mutate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("trade directive", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
