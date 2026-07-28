from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from typing import Callable
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
QUALIFIED_FIXTURE = ROOT / "tests" / "fixtures" / "technical-analysis-demo.json"
YFINANCE_RUNTIME = (
    ROOT
    / "skills"
    / "technical-analysis"
    / "scripts"
    / "run_yfinance_analysis.py"
)
DEMO_ARTIFACTS = ROOT / "examples" / "technical-analysis-demo"


class TechnicalAnalysisArtifactTests(unittest.TestCase):
    def _render(self, fixture: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "scripts/render_technical_analysis_fixture.py",
                "--input",
                str(fixture),
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )

    def _write_fixture(
        self, directory: Path, update: Callable[[dict[str, object]], None]
    ) -> Path:
        fixture = json.loads(QUALIFIED_FIXTURE.read_text(encoding="utf-8"))
        update(fixture)
        fixture_path = directory / "fixture.json"
        fixture_path.write_text(
            json.dumps(fixture, ensure_ascii=False, indent=2, allow_nan=True) + "\n",
            encoding="utf-8",
        )
        return fixture_path

    def test_qualified_daily_history_creates_one_consistent_artifact_package(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            output_dir = Path(temporary) / "artifacts"

            result = self._render(QUALIFIED_FIXTURE, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                ["analysis.md", "chart.svg", "evidence.json"],
            )
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")
            svg = (output_dir / "chart.svg").read_text(encoding="utf-8")

        evidence_id = evidence["evidence_id"]
        self.assertIn(evidence_id, markdown)
        self.assertIn(evidence_id, svg)
        self.assertEqual(evidence["source"]["provider"], "yfinance")
        self.assertEqual(evidence["bars_used"], 319)
        self.assertEqual(len(evidence["ohlcv"]), 319)
        self.assertEqual(svg.count('data-candle="'), 120)
        self.assertEqual(svg.count('data-volume="'), 120)
        for window in (20, 50, 200):
            self.assertIn(f'data-series="sma-{window}"', svg)
        svg_root = ElementTree.fromstring(svg)
        for element in svg_root.iter():
            if element.attrib.get("data-series", "").startswith("sma-"):
                self.assertTrue(
                    all(
                        48 <= float(point.split(",")[1]) <= 362
                        for point in element.attrib["points"].split()
                    )
                )
        for provenance in (
            evidence["symbol"],
            evidence["source"]["label"],
            evidence["timezone"],
            evidence["as_of"],
            evidence["adjustment"],
            str(evidence["bars_used"]),
        ):
            self.assertIn(provenance, svg)

    def test_short_history_fails_closed_with_an_exact_gap(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def shorten(fixture: dict[str, object]) -> None:
                ohlcv = fixture["ohlcv"]
                assert isinstance(ohlcv, dict)
                bars = ohlcv["bars"]
                assert isinstance(bars, list)
                ohlcv["bars"] = bars[-318:]
                first = ohlcv["bars"][0]
                assert isinstance(first, dict)
                ohlcv["coverage_start"] = str(first["timestamp"])[:10]

            fixture_path = self._write_fixture(directory, shorten)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                [path.name for path in output_dir.iterdir()],
                ["analysis.md"],
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")

        self.assertIn("缺少 1 根已完成日线", markdown)
        self.assertIn("## 数据状态", markdown)
        self.assertIn("## 数据缺口", markdown)
        self.assertNotIn("## 技术结构", markdown)
        self.assertNotIn("## 关键位", markdown)
        self.assertNotIn("## 条件情景与失效", markdown)
        self.assertNotIn("<svg", markdown)

    def test_one_expanded_window_retry_can_recover_short_history(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def add_retry(fixture: dict[str, object]) -> None:
                qualified = fixture["ohlcv"]
                assert isinstance(qualified, dict)
                short = json.loads(json.dumps(qualified))
                short["bars"] = short["bars"][-318:]
                short["coverage_start"] = short["bars"][0]["timestamp"][:10]
                fixture["attempts"] = [short, qualified]
                fixture.pop("ohlcv")

            fixture_path = self._write_fixture(directory, add_retry)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )

        self.assertEqual(evidence["source"]["attempts"], 2)
        self.assertTrue(evidence["source"]["expanded_window_retry_used"])
        self.assertEqual(evidence["bars_used"], 319)

    def test_more_than_one_retry_is_rejected_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def add_three_attempts(fixture: dict[str, object]) -> None:
                qualified = fixture["ohlcv"]
                fixture["attempts"] = [qualified, qualified, qualified]

            fixture_path = self._write_fixture(directory, add_three_attempts)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "attempts must contain one or two OHLCV payloads",
                result.stdout + result.stderr,
            )
            self.assertFalse(output_dir.exists())

    def test_key_levels_are_computed_with_replayable_provenance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def inject_untrusted_levels(fixture: dict[str, object]) -> None:
                fixture["key_levels"] = [
                    {
                        "label": "不得采用",
                        "price": "1.23",
                        "condition": "这是旧提示词提供的数字",
                    }
                ]

            fixture_path = self._write_fixture(directory, inject_untrusted_levels)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")
            svg = (output_dir / "chart.svg").read_text(encoding="utf-8")

        levels = evidence["key_levels"]
        self.assertLessEqual(
            len([level for level in levels if level["side"] == "support"]), 2
        )
        self.assertLessEqual(
            len([level for level in levels if level["side"] == "resistance"]), 2
        )
        self.assertNotIn(1.23, [level["price"] for level in levels])
        for level in levels:
            self.assertIn(
                level["method"],
                {"confirmed_swing_atr14_cluster", "120d_extreme_fallback"},
            )
            self.assertEqual(level["lookback"], 120)
            self.assertTrue(level["anchor_dates"])
            self.assertGreaterEqual(level["touches"], 1)
            self.assertIsInstance(level["price"], (int, float))
            self.assertIn(f"method={level['method']}", markdown)
            self.assertIn(f"lookback={level['lookback']}", markdown)
            self.assertIn(f"touches={level['touches']}", markdown)
            self.assertIn(f'data-level-method="{level["method"]}"', svg)
            self.assertIn(f'data-level-touches="{level["touches"]}"', svg)

    def test_artifact_package_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)
            first = directory / "first"
            second = directory / "second"

            first_result = self._render(QUALIFIED_FIXTURE, first)
            second_result = self._render(QUALIFIED_FIXTURE, second)

            self.assertEqual(
                first_result.returncode, 0, first_result.stdout + first_result.stderr
            )
            self.assertEqual(
                second_result.returncode, 0, second_result.stdout + second_result.stderr
            )
            for artifact in ("analysis.md", "chart.svg", "evidence.json"):
                self.assertEqual(
                    (first / artifact).read_bytes(),
                    (second / artifact).read_bytes(),
                    artifact,
                )

    def test_existing_output_directory_is_preserved_on_atomic_write_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            output_dir = Path(temporary) / "artifacts"
            output_dir.mkdir()
            sentinel = output_dir / "sentinel.txt"
            sentinel.write_text("preserve", encoding="utf-8")

            result = self._render(QUALIFIED_FIXTURE, output_dir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output_dir must not already exist", result.stdout + result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")
            self.assertEqual([path.name for path in output_dir.iterdir()], ["sentinel.txt"])

    def test_market_context_never_changes_technical_evidence_or_chart(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)
            without_context = directory / "without-context"
            with_context = directory / "with-context"

            def add_context(fixture: dict[str, object]) -> None:
                fixture["market_context"] = {
                    "status": "available",
                    "as_of": "2026-06-22T08:30:00-04:00",
                    "source": "市场快照工件",
                    "timezone": "America/New_York",
                    "regime": "risk_on",
                    "summary": "风险偏好改善，但行业广度仍有分化。",
                    "same_run": True,
                }

            contextual_fixture = self._write_fixture(directory, add_context)
            plain_result = self._render(QUALIFIED_FIXTURE, without_context)
            context_result = self._render(contextual_fixture, with_context)

            self.assertEqual(
                plain_result.returncode, 0, plain_result.stdout + plain_result.stderr
            )
            self.assertEqual(
                context_result.returncode,
                0,
                context_result.stdout + context_result.stderr,
            )
            plain_evidence = json.loads(
                (without_context / "evidence.json").read_text(encoding="utf-8")
            )
            context_evidence = json.loads(
                (with_context / "evidence.json").read_text(encoding="utf-8")
            )
            context_markdown = (with_context / "analysis.md").read_text(
                encoding="utf-8"
            )
            plain_chart = (without_context / "chart.svg").read_bytes()
            context_chart = (with_context / "chart.svg").read_bytes()

        self.assertEqual(
            plain_evidence["evidence_id"], context_evidence["evidence_id"]
        )
        self.assertEqual(
            plain_evidence["indicators"], context_evidence["indicators"]
        )
        self.assertEqual(
            plain_evidence["key_levels"], context_evidence["key_levels"]
        )
        self.assertEqual(plain_chart, context_chart)
        self.assertIn("风险偏好改善，但行业广度仍有分化", context_markdown)
        self.assertIn("不改变图表、指标或关键位", context_markdown)

    def test_stale_market_context_degrades_to_technical_only_analysis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def add_stale_context(fixture: dict[str, object]) -> None:
                fixture["market_context"] = {
                    "status": "available",
                    "as_of": "2026-06-20T08:00:00-04:00",
                    "source": "市场快照工件",
                    "timezone": "America/New_York",
                    "regime": "neutral",
                    "summary": "该摘要已经过期。",
                    "same_run": False,
                }

            fixture_path = self._write_fixture(directory, add_stale_context)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")

        self.assertEqual(evidence["market_context"]["status"], "stale")
        self.assertIn("超过 24 小时有效期", markdown)
        self.assertIn("仅基于技术面证据", markdown)
        self.assertNotIn("该摘要已经过期", markdown)

    def test_each_blocking_ohlcv_quality_gate_fails_closed(self) -> None:
        def missing_volume(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["bars"][-1].pop("volume")

        def non_finite_close(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["bars"][-1]["close"] = float("nan")

        def nonpositive_volume(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["bars"][-1]["volume"] = 0

        def timezone_less(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["bars"][-1]["timestamp"] = "2026-06-19T16:00:00"

        def missing_timezone(fixture: dict[str, object]) -> None:
            fixture["ohlcv"].pop("timezone")

        def unadjusted(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["adjustment"] = "unadjusted"

        def out_of_order(fixture: dict[str, object]) -> None:
            bars = fixture["ohlcv"]["bars"]
            bars[-2], bars[-1] = bars[-1], bars[-2]

        def invalid_bounds(fixture: dict[str, object]) -> None:
            bar = fixture["ohlcv"]["bars"][-1]
            bar["low"] = bar["high"] + 1

        def uncovered_range(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["coverage_start"] = "2020-01-01"

        def reversed_range(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["coverage_start"] = "2026-06-19"
            fixture["ohlcv"]["coverage_end"] = "2025-04-01"

        def incomplete_middle_bar(fixture: dict[str, object]) -> None:
            fixture["ohlcv"]["bars"][-2]["complete"] = False

        cases = (
            (missing_volume, "numeric volume"),
            (non_finite_close, "finite close"),
            (nonpositive_volume, "positive volume"),
            (timezone_less, "timezone-aware timestamp"),
            (missing_timezone, "OHLCV requires text"),
            (unadjusted, "adjustment must be adjusted"),
            (out_of_order, "strictly increasing"),
            (invalid_bounds, "inconsistent price bounds"),
            (uncovered_range, "must exactly match actual bars"),
            (reversed_range, "coverage start must not follow coverage end"),
            (incomplete_middle_bar, "only the latest OHLCV bar may be incomplete"),
        )
        for mutate, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory(
                prefix="technical-analysis-test-"
            ) as temporary:
                directory = Path(temporary)
                fixture_path = self._write_fixture(directory, mutate)
                output_dir = directory / "artifacts"

                result = self._render(fixture_path, output_dir)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(
                    [path.name for path in output_dir.iterdir()],
                    ["analysis.md"],
                )
                markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")
                self.assertIn(reason, markdown)
                self.assertNotIn("## 技术结构", markdown)
                self.assertNotIn("## 关键位", markdown)
                self.assertNotIn("## 条件情景与失效", markdown)

    def test_latest_incomplete_bar_is_safely_removed_before_analysis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def add_incomplete_latest_bar(fixture: dict[str, object]) -> None:
                bars = fixture["ohlcv"]["bars"]
                extra = dict(bars[-1])
                extra["timestamp"] = "2026-06-20T16:00:00-04:00"
                extra["complete"] = False
                bars.append(extra)
                fixture["ohlcv"]["coverage_end"] = "2026-06-19"

            fixture_path = self._write_fixture(directory, add_incomplete_latest_bar)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")

        self.assertEqual(evidence["bars_used"], 319)
        self.assertTrue(evidence["stripped_incomplete_latest_bar"])
        self.assertIn("已安全剔除一根未完成的最新日线", markdown)

    def test_non_yfinance_provider_is_rejected_without_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def change_provider(fixture: dict[str, object]) -> None:
                fixture["provider"] = {
                    "name": "custom",
                    "kind": "custom",
                    "status": "available",
                    "as_of": "2026-06-19T16:00:00-04:00",
                }

            fixture_path = self._write_fixture(directory, change_provider)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("provider must be yfinance EOD", result.stdout + result.stderr)
            self.assertFalse(output_dir.exists())

    def test_zero_atr_fails_closed_instead_of_aborting_without_a_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)

            def flatten_prices(fixture: dict[str, object]) -> None:
                for bar in fixture["ohlcv"]["bars"]:
                    bar.update(
                        {
                            "open": 100,
                            "high": 100,
                            "low": 100,
                            "close": 100,
                        }
                    )

            fixture_path = self._write_fixture(directory, flatten_prices)
            output_dir = directory / "artifacts"

            result = self._render(fixture_path, output_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                [path.name for path in output_dir.iterdir()],
                ["analysis.md"],
            )
            markdown = (output_dir / "analysis.md").read_text(encoding="utf-8")

        self.assertIn("ATR14 requires positive price ranges", markdown)
        self.assertNotIn("## 技术结构", markdown)

    def test_yfinance_adapter_retries_once_with_a_larger_window(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "run_yfinance_analysis", YFINANCE_RUNTIME
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        source = json.loads(QUALIFIED_FIXTURE.read_text(encoding="utf-8"))
        bars = source["ohlcv"]["bars"]

        class FakeFrame:
            def __init__(self, fixture_bars: list[dict[str, object]]) -> None:
                self._bars = fixture_bars
                self.empty = not fixture_bars

            def iterrows(self):
                for bar in self._bars:
                    timestamp = datetime.fromisoformat(str(bar["timestamp"]))
                    yield timestamp, {
                        "Open": bar["open"],
                        "High": bar["high"],
                        "Low": bar["low"],
                        "Close": bar["close"],
                        "Volume": bar["volume"],
                    }

        class FakeTicker:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def history(self, **kwargs):
                self.calls.append(kwargs)
                selected = bars[-318:] if len(self.calls) == 1 else bars
                return FakeFrame(selected)

        ticker = FakeTicker()
        now = datetime.fromisoformat("2026-06-22T09:00:00-04:00")

        fixture = module.build_yfinance_fixture(
            "DEMO",
            ticker_factory=lambda symbol: ticker,
            now=now,
        )

        self.assertEqual(
            [call["period"] for call in ticker.calls],
            ["18mo", "3y"],
        )
        self.assertTrue(all(call["auto_adjust"] is True for call in ticker.calls))
        self.assertTrue(all(call["repair"] is False for call in ticker.calls))
        self.assertEqual(fixture["provider"]["name"], "yfinance EOD")
        self.assertEqual(fixture["provider"]["kind"], "public_best_effort")
        self.assertEqual(len(fixture["attempts"]), 2)
        self.assertEqual(len(fixture["attempts"][0]["bars"]), 318)
        self.assertEqual(len(fixture["attempts"][1]["bars"]), 319)
        self.assertNotIn("api_key", json.dumps(fixture).lower())

    def test_yfinance_network_failure_is_counted_before_a_successful_retry(
        self,
    ) -> None:
        spec = importlib.util.spec_from_file_location(
            "run_yfinance_analysis_retry", YFINANCE_RUNTIME
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = json.loads(QUALIFIED_FIXTURE.read_text(encoding="utf-8"))
        bars = source["ohlcv"]["bars"]

        class FakeFrame:
            empty = False

            def iterrows(self):
                for bar in bars:
                    yield datetime.fromisoformat(bar["timestamp"]), {
                        "Open": bar["open"],
                        "High": bar["high"],
                        "Low": bar["low"],
                        "Close": bar["close"],
                        "Volume": bar["volume"],
                    }

        class FlakyTicker:
            def __init__(self) -> None:
                self.calls = 0

            def history(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise TimeoutError("first request timed out")
                return FakeFrame()

        ticker = FlakyTicker()
        fixture = module.build_yfinance_fixture(
            "DEMO",
            ticker_factory=lambda symbol: ticker,
            now=datetime.fromisoformat("2026-06-22T09:00:00-04:00"),
        )

        self.assertEqual(ticker.calls, 2)
        self.assertEqual(fixture["source_attempts"], 2)
        self.assertTrue(fixture["expanded_window_retry_used"])
        self.assertEqual(len(fixture["attempts"]), 1)

        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            directory = Path(temporary)
            fixture_path = directory / "fixture.json"
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            output_dir = directory / "artifacts"
            result = self._render(fixture_path, output_dir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(
                (output_dir / "evidence.json").read_text(encoding="utf-8")
            )

        self.assertEqual(evidence["source"]["attempts"], 2)
        self.assertTrue(evidence["source"]["expanded_window_retry_used"])

    def test_unreadable_market_context_degrades_without_blocking(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "run_yfinance_analysis_context", YFINANCE_RUNTIME
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            missing = Path(temporary) / "missing.json"
            invalid = Path(temporary) / "invalid.json"
            invalid.write_text("{not-json", encoding="utf-8")

            missing_context = module.load_market_context(missing)
            invalid_context = module.load_market_context(invalid)

        self.assertEqual(missing_context["status"], "unavailable")
        self.assertIn("FileNotFoundError", missing_context["reason"])
        self.assertEqual(invalid_context["status"], "invalid")
        self.assertIn("JSONDecodeError", invalid_context["reason"])

    def test_readme_demo_is_generated_from_the_offline_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="technical-analysis-test-") as temporary:
            regenerated = Path(temporary) / "regenerated"

            result = self._render(QUALIFIED_FIXTURE, regenerated)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for artifact in ("analysis.md", "chart.svg", "evidence.json"):
                self.assertEqual(
                    (regenerated / artifact).read_bytes(),
                    (DEMO_ARTIFACTS / artifact).read_bytes(),
                    artifact,
                )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("离线示例，非当前市场数据", readme)
        self.assertIn("examples/technical-analysis-demo/chart.svg", readme)
        self.assertNotIn("# Mars Skills 1.", readme)


if __name__ == "__main__":
    unittest.main()
