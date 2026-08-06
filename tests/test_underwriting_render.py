"""Contract tests for the v1.0.3 underwriting renderer (render_underwriting.py)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "mars-research-assistant"
    / "skills"
    / "deep-equity-research"
    / "scripts"
    / "render_underwriting.py"
)
RUNTIME_PACKAGE = ROOT / "skills" / "mars-research-assistant"
FIXTURES = ROOT / "tests" / "fixtures"

CHAPTER_HEADINGS = (
    "## 1. 研究范围、预注册命题与交易结论",
    "## 2. 公司、业务模式与价值驱动",
    "## 3. 行业结构、竞争与行业专属反证",
    "## 4. 管理层、治理与资本配置",
    "## 5. 财务、分部/KPI 与财报质量",
    "## 6. 预期差、催化剂、基准率与跟踪清单",
    "## 7. 可复算估值与“现价定价了什么”",
    "## 8. 反方论证、事前风险预演与可证伪条件",
    "## 9. 来源、数据对账、时间戳、假设与数据缺口",
)
TRADE_DIRECTIVE_WORDS = ("买入", "卖出", "增持", "减持", "加仓", "减仓", "建仓", "平仓")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def run_renderer(fixture: dict, directory: Path, html: bool = False) -> subprocess.CompletedProcess:
    input_path = directory / "inputs.json"
    input_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    evidence = json.loads(
        (FIXTURES / "technical-evidence.json").read_text(encoding="utf-8")
    )
    # Each fixture may reference a different observation timestamp while
    # reusing the same identity/evidence id.  Stage an artifact whose payload
    # agrees with that explicit reference, preserving the renderer's exact
    # path-and-timestamp integrity check.
    evidence_ref = fixture.get("technical_evidence_ref")
    if isinstance(evidence_ref, dict) and isinstance(evidence_ref.get("as_of"), str):
        evidence["as_of"] = evidence_ref["as_of"]
    (directory / "technical-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False), encoding="utf-8"
    )
    command = [
        sys.executable,
        str(SCRIPT),
        "--input",
        str(input_path),
        "--output",
        str(directory / "underwriting.md"),
    ]
    if html:
        command += ["--html", str(directory / "underwriting.html")]
    return subprocess.run(command, capture_output=True, text=True)


class UnderwritingRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.workdir = Path(self.tempdir.name)

    def render(self, fixture_name: str = "underwriting-inputs-initial.json", html: bool = False):
        fixture = load_fixture(fixture_name)
        result = run_renderer(fixture, self.workdir, html=html)
        self.assertEqual(result.returncode, 0, result.stderr)
        return fixture, (self.workdir / "underwriting.md").read_text(encoding="utf-8")

    def test_initial_render_nine_chapters_identity_and_content(self) -> None:
        fixture, markdown = self.render()
        self.assertTrue(markdown.startswith("# 深度研究：CLEAN.US"))
        for heading in CHAPTER_HEADINGS:
            self.assertIn(heading, markdown)
        for field in (
            "issuer_id=issuer-cleanco",
            "listing_id=CLEAN.US",
            "case_id=case-underwriting-001",
            "artifact_version=1",
        ):
            self.assertIn(field, markdown)
        # 行业注册表摘要（software_internet 条目）。
        self.assertIn("软件与互联网", markdown)
        self.assertIn("行业专属反证框架", markdown)
        # A–D 级别。
        self.assertIn("财报质量级别：**A**", markdown)
        # 概率加权公允价值与内嵌 artifact 重算一致。
        scenarios = fixture["valuation"]["results"]["dcf"]["scenarios"]
        weighted = sum(item["probability"] * item["per_share"] for item in scenarios)
        self.assertIn(f"{weighted:.6f}", markdown)
        # 交易结论使用条件式语言。
        self.assertIn("入场区间：11.50 – 12.50 USD", markdown)
        self.assertIn("失效条件", markdown)
        for word in TRADE_DIRECTIVE_WORDS:
            self.assertNotIn(word, markdown)

    def test_earnings_update_without_prior_model_degrades(self) -> None:
        _, markdown = self.render("underwriting-inputs-earnings-no-prior.json")
        self.assertIn("财报更新模式", markdown)
        self.assertIn("自动降级为首次承保", markdown)

    def test_short_baseline_records_gap_in_chapter_nine(self) -> None:
        _, markdown = self.render("underwriting-inputs-short-baseline.json")
        chapter_nine = markdown.split(CHAPTER_HEADINGS[8], 1)[1]
        self.assertIn("基线缺口", chapter_nine)
        self.assertIn("年度基线仅 2 年", chapter_nine)

    def test_html_view_matches_markdown_numbers(self) -> None:
        fixture, markdown = self.render(html=True)
        html_view = (self.workdir / "underwriting.html").read_text(encoding="utf-8")
        # 三个关键数值同时存在于 md 与 html。
        scenarios = fixture["valuation"]["results"]["dcf"]["scenarios"]
        weighted = f"{sum(item['probability'] * item['per_share'] for item in scenarios):.6f}"
        grade = fixture["earnings_quality"]["grade"]
        entry_low = f"{fixture['trade_plan']['entry_plan']['zone']['low']:.2f}"
        for needle in (weighted, grade, entry_low):
            self.assertIn(needle, markdown)
            self.assertIn(needle, html_view)
        # 关键数据卡片。
        self.assertIn(f'<div class="card-value">{grade}</div>', html_view)
        self.assertIn('<div class="card-value">entry_plan</div>', html_view)
        # 目录锚点与折叠区块。
        self.assertIn('href="#chapter-7"', html_view)
        self.assertIn("<details>", html_view)
        # 单文件离线：无外部 src=/href= 引用。
        self.assertNotIn('src="http', html_view)
        self.assertNotIn("src='http", html_view)
        self.assertNotIn('href="http', html_view)
        self.assertNotIn("href='http", html_view)

    def test_case_id_mismatch_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["valuation"]["identity"]["case_id"] = "case-other-999"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("case_id mismatch", result.stderr)

    def test_watch_trade_plan_renders_veto_and_waiting_conditions(self) -> None:
        _, markdown = self.render("underwriting-inputs-watch.json")
        self.assertIn("方案状态：watch", markdown)
        # veto 的 gate 与 reason 均保留。
        self.assertIn("否决原因：technical_evidence——", markdown)
        self.assertIn("技术证据 as_of 2026-07-20T14:30:00Z 早于有效期下限，已过期。", markdown)
        # entry_plan.reason 与 what_would_change 各条件均保留。
        self.assertIn("未产出入场方案的原因：", markdown)
        for condition in (
            "更新技术证据（质量门合格且 as_of 在有效期内）后重估。",
            "等待价格回到价值带与技术支持区的交集，或价值区间上修后重估。",
            "等待基本面目标与失效位之间的距离改善至收益风险比达标后重估。",
        ):
            self.assertIn(condition, markdown)
        # 交易结论内不输出价格区间。
        conclusion = markdown.split("### 交易结论", 1)[1].split("## 2. ", 1)[0]
        self.assertNotIn("入场区间：", conclusion)
        self.assertNotIn("11.50", conclusion)
        self.assertNotIn("12.50", conclusion)
        for word in TRADE_DIRECTIVE_WORDS:
            self.assertNotIn(word, markdown)

    def test_watch_computed_dcf_html_shows_valuation_anchor_and_zone(self) -> None:
        # watch + 已计算 DCF：摘要卡展示估值 artifact 已有的非行动性参考值，
        # 不得再显示“未计算”，也不得标注为交易目标或入场价值带。
        fixture, _ = self.render("underwriting-inputs-watch.json", html=True)
        html_view = (self.workdir / "underwriting.html").read_text(encoding="utf-8")
        dcf = fixture["valuation"]["results"]["dcf"]
        weighted = f"{dcf['probability_weighted_per_share']:.6f}".rstrip("0").rstrip(".")
        zone_low = f"{dcf['value_zone']['low']:.6f}".rstrip("0").rstrip(".")
        zone_high = f"{dcf['value_zone']['high']:.6f}".rstrip("0").rstrip(".")
        self.assertIn('<div class="card-title">基本面估值锚</div>', html_view)
        self.assertIn(
            f'<div class="card-value">{weighted} USD</div>', html_view
        )
        self.assertIn('<div class="card-title">DCF 估值参考区间</div>', html_view)
        self.assertIn(
            f'<div class="card-value">{zone_low} – {zone_high} USD</div>', html_view
        )
        # 四张卡无一为“未计算”，且不使用交易目标类措辞。
        self.assertNotIn('<div class="card-value">未计算</div>', html_view)
        self.assertNotIn('<div class="card-title">基本面目标</div>', html_view)
        self.assertNotIn('<div class="card-title">价值区间</div>', html_view)
        self.assertNotIn("入场价值带", html_view)

    def test_watch_html_shows_finite_values_without_renderer_thresholds(self) -> None:
        # 渲染层不设 >0 / low<=high 之类新规则：有限数值一律原样展示，
        # 仅缺失或非有限才“未计算”。
        fixture = load_fixture("underwriting-inputs-watch.json")
        dcf = fixture["valuation"]["results"]["dcf"]
        dcf["probability_weighted_per_share"] = 0
        dcf["value_zone"] = {"low": 16.560666, "high": 13.097573}
        result = run_renderer(fixture, self.workdir, html=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        html_view = (self.workdir / "underwriting.html").read_text(encoding="utf-8")
        self.assertIn('<div class="card-value">0 USD</div>', html_view)
        self.assertIn(
            '<div class="card-value">16.560666 – 13.097573 USD</div>', html_view
        )
        self.assertNotIn('<div class="card-value">未计算</div>', html_view)

    def test_watch_fallback_uses_non_actionable_labels(self) -> None:
        # DCF 不可用、EPV/EVA/SOTP 各自 computed 的 fallback：只显示该模型
        # 有限点估值锚、不构造区间（恰一张“估值参考区间”未计算卡），标签仍为
        # 非行动性的“基本面估值锚 / 估值参考区间”，无交易化措辞。
        for model, key in (
            ("epv", "epv_per_share"),
            ("eva", "residual_income_per_share"),
            ("sotp", "per_share"),
        ):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as directory:
                workdir = Path(directory)
                fixture = load_fixture("underwriting-inputs-watch.json")
                fixture["valuation"]["results"]["dcf"] = {
                    "status": "missing_inputs",
                    "missing": ["price"],
                }
                for other, _ in (
                    ("epv", "epv_per_share"),
                    ("eva", "residual_income_per_share"),
                    ("sotp", "per_share"),
                ):
                    if other != model:
                        fixture["valuation"]["results"][other] = {
                            "status": "missing_inputs",
                            "missing": ["price"],
                        }
                result = run_renderer(fixture, workdir, html=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                html_view = (workdir / "underwriting.html").read_text(encoding="utf-8")
                anchor = fixture["valuation"]["results"][model][key]
                anchor_text = f"{anchor:.6f}".rstrip("0").rstrip(".")
                self.assertIn('<div class="card-title">基本面估值锚</div>', html_view)
                self.assertIn(
                    f'<div class="card-value">{anchor_text} USD</div>', html_view
                )
                self.assertIn('<div class="card-title">估值参考区间</div>', html_view)
                self.assertEqual(
                    html_view.count('<div class="card-value">未计算</div>'), 1
                )
                self.assertNotIn('<div class="card-title">基本面目标</div>', html_view)
                self.assertNotIn('<div class="card-title">价值区间</div>', html_view)
                self.assertNotIn("DCF 估值参考区间", html_view)
                self.assertNotIn("入场价值带", html_view)

    def test_watch_markdown_trade_conclusion_has_no_executable_prices(self) -> None:
        # watch 的 Markdown 交易结论仍不得出现入场/目标/失效价格。
        _, markdown = self.render("underwriting-inputs-watch.json")
        conclusion = markdown.split("### 交易结论", 1)[1].split("## 2. ", 1)[0]
        self.assertIn("方案状态：watch", conclusion)
        self.assertIn("不产生方案", conclusion)
        self.assertNotIn("入场区间：", conclusion)
        self.assertNotIn("目标区间", conclusion)
        self.assertNotIn("失效条件", conclusion)
        self.assertNotIn("13.097573", conclusion)
        self.assertNotIn("16.560666", conclusion)

    def test_dcf_key_inputs_and_scenario_paths_visible_in_markdown(self) -> None:
        # 第 7 章展示 DCF 关键输入与三情景 FCF 路径，数值、来源（名称/URL/
        # as_of）、推导与会计期逐项来自 fixture 的 inputs_provenance，不重算。
        fixture, markdown = self.render("underwriting-inputs-watch.json")
        chapter_seven = markdown.split("## 7. ", 1)[1].split("## 8. ", 1)[0]
        self.assertIn("### DCF 关键输入与情景假设", chapter_seven)
        provenance = fixture["valuation"]["results"]["dcf"]["inputs_provenance"]
        price = provenance["price"]
        self.assertIn(
            f"现价（price）：{price['value']} USD；"
            f"来源：[CLEAN.US 收盘行情](https://example.com/quote/CLEAN)"
            f"（as_of：{price['source']['as_of']}）；推导：未获取到；会计期：未获取到",
            chapter_seven,
        )
        shares = provenance["shares_outstanding"]
        self.assertIn(
            f"总股本（shares_outstanding）：{shares['value']}；"
            f"来源：[CLEAN.US 10-K](https://example.com/sec/cleanco-10k)"
            f"（as_of：{shares['source']['as_of']}）；推导：未获取到；会计期：FY2025",
            chapter_seven,
        )
        net_debt = provenance["net_debt"]
        self.assertIn(
            f"净债务（net_debt）：{net_debt['value']}；"
            f"来源：[CLEAN.US 10-K](https://example.com/sec/cleanco-10k)"
            f"（as_of：{net_debt['source']['as_of']}）；"
            f"推导：总债务减现金及等价物。；会计期：FY2025",
            chapter_seven,
        )
        self.assertIn(f"WACC（wacc）：{provenance['wacc']['value']:.2%}", chapter_seven)
        self.assertIn(
            f"永续增长率（terminal_growth）：{provenance['terminal_growth']['value']:.2%}",
            chapter_seven,
        )
        self.assertIn(
            f"长期增长上限（long_run_growth_cap）："
            f"{provenance['long_run_growth_cap']['value']:.2%}",
            chapter_seven,
        )
        self.assertIn(
            f"成熟期利润率基准（mature_margin_benchmark）："
            f"{provenance['mature_margin_benchmark']['value']:.2%}",
            chapter_seven,
        )
        for name in ("bear", "base", "bull"):
            scenario = provenance["scenarios"][name]
            flows = ", ".join(f"{value:g}" for value in scenario["free_cash_flows"]["value"])
            margins = ", ".join(
                f"{value:.2%}" for value in scenario["margins"]["value"]
            )
            row = (
                f"| {name} | {scenario['probability']['value']:.2%} | {flows} "
                f"| {margins} | {scenario['reinvestment_rate']['value']:.2%} "
                f"| {scenario['roic']['value']:.2%} |"
            )
            self.assertIn(row, chapter_seven)
            source_text = (
                f"[分析师估值假设：CLEAN {name} 情景]"
                f"(https://example.com/assumptions/clean-{name})"
                f"（as_of：{scenario['probability']['source']['as_of']}）"
            )
            for field in (
                "probability",
                "free_cash_flows",
                "margins",
                "reinvestment_rate",
                "roic",
            ):
                self.assertIn(f"- {name}.{field}：来源：{source_text}", chapter_seven)
            # 有推导的字段原样展示，无推导/会计期的字段明示未获取到。
            self.assertIn(
                f"- {name}.reinvestment_rate：来源：{source_text}；"
                "推导：终值期再投资率按 terminal_growth / ROIC 约束。；会计期：未获取到",
                chapter_seven,
            )
            self.assertIn(
                f"- {name}.roic：来源：{source_text}；"
                "推导：终值期资本回报率假设。；会计期：未获取到",
                chapter_seven,
            )
            self.assertIn(
                f"- {name}.probability：来源：{source_text}；"
                "推导：未获取到；会计期：未获取到",
                chapter_seven,
            )

    def test_dcf_inputs_missing_metadata_marked_unavailable(self) -> None:
        # 来源/推导/会计期缺元数据时逐项明示“未获取到”，不伪造。
        fixture = load_fixture("underwriting-inputs-watch.json")
        provenance = fixture["valuation"]["results"]["dcf"]["inputs_provenance"]
        provenance["net_debt"]["source"] = None
        provenance["net_debt"]["derivation"] = None
        provenance["net_debt"]["accounting_period"] = None
        provenance["scenarios"]["base"]["roic"]["source"] = None
        result = run_renderer(fixture, self.workdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        markdown = (self.workdir / "underwriting.md").read_text(encoding="utf-8")
        chapter_seven = markdown.split("## 7. ", 1)[1].split("## 8. ", 1)[0]
        self.assertIn(
            "净债务（net_debt）：200；来源：未获取到；推导：未获取到；会计期：未获取到",
            chapter_seven,
        )
        self.assertIn(
            "- base.roic：来源：未获取到；推导：终值期资本回报率假设。；会计期：未获取到",
            chapter_seven,
        )

    def test_watch_without_computed_valuation_html_cards_fail_closed(self) -> None:
        # 无任何已计算适用模型时，两项估值卡 fail closed 显示“未计算”，
        # 且统一使用非行动标签，不出现“基本面目标 / 价值区间”。
        fixture = load_fixture("underwriting-inputs-watch.json")
        for model in ("dcf", "epv", "eva", "sotp"):
            fixture["valuation"]["results"][model] = {
                "status": "missing_inputs",
                "missing": ["price"],
            }
        result = run_renderer(fixture, self.workdir, html=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        html_view = (self.workdir / "underwriting.html").read_text(encoding="utf-8")
        self.assertEqual(html_view.count('<div class="card-value">未计算</div>'), 2)
        self.assertIn('<div class="card-title">基本面估值锚</div>', html_view)
        self.assertIn('<div class="card-title">估值参考区间</div>', html_view)
        self.assertNotIn('<div class="card-title">基本面目标</div>', html_view)
        self.assertNotIn('<div class="card-title">价值区间</div>', html_view)
        self.assertNotIn("DCF 估值参考区间", html_view)

    def test_dcf_inputs_section_shows_for_noncomputed_status(self) -> None:
        # dcf 非 computed（missing_inputs）时关键输入节仍出现；无
        # inputs_provenance 时逐项“未获取到”，不伪造、不重算。
        fixture = load_fixture("underwriting-inputs-watch.json")
        fixture["valuation"]["results"]["dcf"] = {
            "status": "missing_inputs",
            "missing": ["price"],
        }
        result = run_renderer(fixture, self.workdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        markdown = (self.workdir / "underwriting.md").read_text(encoding="utf-8")
        chapter_seven = markdown.split("## 7. ", 1)[1].split("## 8. ", 1)[0]
        self.assertIn("### DCF 关键输入与情景假设", chapter_seven)
        for label in (
            "现价（price）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "总股本（shares_outstanding）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "净债务（net_debt）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "WACC（wacc）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "永续增长率（terminal_growth）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "长期增长上限（long_run_growth_cap）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
            "成熟期利润率基准（mature_margin_benchmark）：未获取到；来源：未获取到；推导：未获取到；会计期：未获取到",
        ):
            self.assertIn(label, chapter_seven)
        for name in ("bear", "base", "bull"):
            self.assertIn(
                f"| {name} | 未获取到 | 未获取到 | 未获取到 | 未获取到 | 未获取到 |",
                chapter_seven,
            )
            for field in (
                "probability",
                "free_cash_flows",
                "margins",
                "reinvestment_rate",
                "roic",
            ):
                self.assertIn(
                    f"- {name}.{field}：来源：未获取到；推导：未获取到；会计期：未获取到",
                    chapter_seven,
                )

    def test_baseline_annual_years_alias_accepted(self) -> None:
        fixture = load_fixture("underwriting-inputs-short-baseline.json")
        baseline = fixture["accounting_baseline"]
        baseline["annual_years"] = baseline.pop("annual")
        result = run_renderer(fixture, self.workdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        markdown = (self.workdir / "underwriting.md").read_text(encoding="utf-8")
        chapter_nine = markdown.split(CHAPTER_HEADINGS[8], 1)[1]
        self.assertIn("年度基线仅 2 年", chapter_nine)

    def test_baseline_annual_alias_conflict_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        baseline = tampered["accounting_baseline"]
        baseline["annual_years"] = baseline["annual"]
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("both annual and annual_years", result.stderr)

    def test_artifact_issuer_id_mismatch_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["valuation"]["identity"]["issuer_id"] = "issuer-other"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("issuer_id mismatch", result.stderr)

    def test_artifact_listing_id_mismatch_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["earnings_quality"]["identity"]["listing_id"] = "OTHER.US"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("listing_id mismatch", result.stderr)

    def test_artifact_missing_schema_version_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        del tampered["valuation"]["identity"]["schema_version"]
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("schema_version", result.stderr)

    def test_artifact_non_one_schema_version_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["trade_plan"]["identity"]["schema_version"] = 2
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("schema_version must be 1", result.stderr)

    def test_artifact_missing_artifact_version_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        del tampered["earnings_quality"]["identity"]["artifact_version"]
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact_version", result.stderr)

    def test_root_identity_schema_version_must_be_one(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["identity"]["schema_version"] = 2
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("identity schema_version must be 1", result.stderr)

    def test_artifact_non_one_artifact_version_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["valuation"]["identity"]["artifact_version"] = 2
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact_version must be 1", result.stderr)

    def test_technical_evidence_ref_requires_complete_identity(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        del tampered["technical_evidence_ref"]["identity"]
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("technical_evidence_ref identity", result.stderr)

    def test_trade_plan_status_must_be_entry_plan_or_watch(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["trade_plan"]["status"] = "hold"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("entry_plan or watch", result.stderr)

    def test_trade_plan_direction_must_be_long_only(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["trade_plan"]["direction"] = "long_short"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("long_only", result.stderr)

    def test_trade_plan_horizon_must_be_within_one_to_six(self) -> None:
        for horizon in ({"min": 0, "max": 6}, {"min": 1, "max": 7}):
            with self.subTest(horizon=horizon):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                tampered["trade_plan"]["horizon_months"] = horizon
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("horizon_months", result.stderr)

    def test_absolute_artifact_path_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["technical_evidence_ref"]["artifact_path"] = (
            "/tmp/evidence/technical-evidence.json"
        )
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("portable relative path", result.stderr)
        self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_unportable_artifact_path_variants_rejected(self) -> None:
        for name, path in (
            ("dotdot", "evidence/../technical-evidence.json"),
            ("backslash", "evidence\\technical-evidence.json"),
            ("colon", "C:evidence/technical-evidence.json"),
        ):
            with self.subTest(case=name):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                tampered["technical_evidence_ref"]["artifact_path"] = path
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("portable relative path", result.stderr)
                self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_embedded_artifact_top_level_schema_version_required(self) -> None:
        for name, mutate in (
            ("missing", lambda artifact: artifact.pop("schema_version")),
            ("two", lambda artifact: artifact.update(schema_version=2)),
            ("bool", lambda artifact: artifact.update(schema_version=True)),
        ):
            with self.subTest(case=name):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                mutate(tampered["valuation"])
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("schema_version must be 1", result.stderr)
                self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_earnings_veto_must_match_grade(self) -> None:
        for name, mutation, expected in (
            (
                "forged-veto-false",
                {"grade": "C", "long_entry_veto": False},
                "contradicts grade",
            ),
            (
                "forged-veto-true",
                {"grade": "A", "long_entry_veto": True},
                "contradicts grade",
            ),
            (
                "non-boolean-veto",
                {"long_entry_veto": "false"},
                "requires a boolean",
            ),
        ):
            with self.subTest(case=name):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                tampered["earnings_quality"].update(mutation)
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_artifact_computed_as_of_after_research_as_of_rejected(self) -> None:
        for name in ("valuation", "earnings_quality", "trade_plan"):
            with self.subTest(artifact=name):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                tampered[name]["computed_as_of"] = "2026-08-02T00:00:00Z"
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"{name} computed_as_of is after research as_of", result.stderr
                )
                self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_technical_evidence_ref_as_of_after_research_as_of_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["technical_evidence_ref"]["as_of"] = "2026-08-02T00:00:00Z"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "technical_evidence_ref as_of is after research as_of", result.stderr
        )
        self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_vetoed_earnings_grade_forbids_entry_plan(self) -> None:
        for grade in ("C", "D"):
            with self.subTest(grade=grade):
                fixture = load_fixture("underwriting-inputs-initial.json")
                tampered = copy.deepcopy(fixture)
                tampered["earnings_quality"]["grade"] = grade
                tampered["earnings_quality"]["long_entry_veto"] = True
                result = run_renderer(tampered, self.workdir)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("forbids", result.stderr)
                self.assertIn("entry_plan", result.stderr)
                self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_failed_dcf_terminal_check_cannot_render_entry_plan(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        fixture["valuation"]["results"]["dcf"]["terminal_value_checks"][
            "long_run_growth"
        ]["status"] = "fail"
        result = run_renderer(fixture, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valuation gate must fail", result.stderr)
        self.assertFalse((self.workdir / "underwriting.md").exists())

    def test_short_directive_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["sections"]["company_business_model_value_drivers"][0][
            "statement"
        ] = "建议做空该公司。"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trade directive", result.stderr)

    def test_none_technical_target_renders_unavailable(self) -> None:
        # 防御性渲染：技术目标缺失时展示“不可用”，不得把 None 传给金额格式化。
        fixture = load_fixture("underwriting-inputs-initial.json")
        fixture["trade_plan"]["target_plan"]["technical_target"]["level"] = None
        result = run_renderer(fixture, self.workdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        markdown = (self.workdir / "underwriting.md").read_text(encoding="utf-8")
        self.assertIn("技术目标 不可用 USD", markdown)

    def test_epv_basis_trade_plan_renders_basis_label(self) -> None:
        # 金融类 fallback：基本面目标标签由 basis 驱动，不写死概率加权。
        fixture, markdown = self.render("underwriting-inputs-epv-basis.json", html=True)
        self.assertIn("基本面目标（EPV 每股公允价值）13.5 USD", markdown)
        self.assertIn("入场区间：11.50 – 12.50 USD", markdown)
        conclusion = markdown.split("### 交易结论", 1)[1].split("## 2. ", 1)[0]
        self.assertNotIn("概率加权", conclusion)
        html_view = (self.workdir / "underwriting.html").read_text(encoding="utf-8")
        self.assertIn('<div class="card-title">EPV 每股公允价值</div>', html_view)
        self.assertIn('<div class="card-value">13.5 USD</div>', html_view)
        self.assertIn(
            '<div class="card-value">9.75375 – 13.19625 USD</div>', html_view
        )
        self.assertNotIn('<div class="card-title">概率加权公允价值</div>', html_view)
        self.assertEqual(fixture["trade_plan"]["target_plan"]["fundamental_target"]["basis"], "epv")
        for word in TRADE_DIRECTIVE_WORDS:
            self.assertNotIn(word, markdown)

    def test_source_as_of_after_research_as_of_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["sources"][0]["as_of"] = "2027-01-01T00:00:00Z"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source as_of is after research as_of", result.stderr)

    def test_trade_directive_word_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        tampered = copy.deepcopy(fixture)
        tampered["sections"]["company_business_model_value_drivers"][0]["statement"] = "建议买入该公司。"
        result = run_renderer(tampered, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trade directive", result.stderr)

    def test_existing_output_path_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        first = run_renderer(fixture, self.workdir)
        self.assertEqual(first.returncode, 0, first.stderr)
        second = run_renderer(fixture, self.workdir)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("File exists", second.stderr)

    def test_output_inside_runtime_package_rejected(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        input_path = self.workdir / "inputs.json"
        input_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        target = RUNTIME_PACKAGE / "underwriting-should-not-exist.md"
        self.assertFalse(target.exists())
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(input_path),
                "--output",
                str(target),
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Skill runtime package", result.stderr)
        self.assertFalse(target.exists())

    def test_render_performance_under_one_second(self) -> None:
        fixture = load_fixture("underwriting-inputs-initial.json")
        start = time.perf_counter()
        result = run_renderer(fixture, self.workdir, html=True)
        elapsed = time.perf_counter() - start
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
