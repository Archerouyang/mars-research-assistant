#!/usr/bin/env python3
"""Fail-closed acceptance primitives for canonical research Board visuals.

The module is repository tooling. It consumes committed public fixtures and
generated static artifacts only; it never reads a broker, private runtime, or
order API.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import time
from typing import Iterable, Mapping, Sequence


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
SKILL_SCRIPTS = SKILL / "scripts"

import sys

if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from canonical_gallery import APPROVED_CAPTURES, BOARD_SPECS  # noqa: E402
from artifact_packet import build_artifact_packet, write_artifact_packet  # noqa: E402


COMPLETE_WIDTHS = (1200, 700, 736, 320)
DEGRADED_WIDTHS = (736, 320)
DEGRADED_STATES = ("partial", "stale", "source_error")
DARK_WIDTHS = (736, 320)


class AcceptanceError(ValueError):
    """Stable fail-closed error code for release-gate violations."""


def build_acceptance_matrix() -> dict[str, list[dict[str, object]]]:
    """Return the approved, deterministic #58 browser and Gallery matrices."""

    complete = [
        _case(spec.board_id, spec.slug, "complete", view, width, "light")
        for spec in BOARD_SPECS
        for view, _view_id in spec.view_ids
        for width in COMPLETE_WIDTHS
    ]
    degraded = [
        _case(spec.board_id, spec.slug, state, view, width, "light")
        for spec in BOARD_SPECS
        for state in DEGRADED_STATES
        for view, _view_id in spec.view_ids
        for width in DEGRADED_WIDTHS
    ]
    dark_complete = [
        _case(spec.board_id, spec.slug, "complete", view, width, "dark")
        for spec in BOARD_SPECS
        for view, _view_id in spec.view_ids
        for width in DARK_WIDTHS
    ]
    dark_degraded = [
        _case(spec.board_id, spec.slug, state, "Overview", width, "dark")
        for spec in BOARD_SPECS
        for state in DEGRADED_STATES
        for width in DARK_WIDTHS
    ]
    gallery = [
        {
            "board": item.board_id,
            "board_slug": item.board_slug,
            "height": item.height,
            "view": item.view,
            "width": item.width,
        }
        for item in APPROVED_CAPTURES
    ]
    return {
        "complete": complete,
        "degraded": degraded,
        "dark": dark_complete + dark_degraded,
        "gallery": gallery,
    }


def _case(
    board: str,
    board_slug: str,
    state: str,
    view: str,
    width: int,
    theme: str,
) -> dict[str, object]:
    return {
        "board": board,
        "board_slug": board_slug,
        "height": 840,
        "state": state,
        "theme": theme,
        "view": view,
        "width": width,
    }


_PRIVACY_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("private_absolute_path", re.compile(rb"(?:/Users/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)")),
    ("credential", re.compile(rb"(?i)(?:api[_-]?(?:key|secret)|access[_-]?token|client[_-]?secret|token)\s*[\"']?\s*[:=]+\s*[\"']?(?:ghp_[A-Za-z0-9_-]{8,}|private[-_A-Za-z0-9]{6,})")),
    ("private_account", re.compile(rb"(?i)(?:account[_-]?id|PRIVATE-ACCOUNT)[\s\"':=-]+[A-Za-z0-9_-]{6,}")),
    ("broker_raw_response", re.compile(rb"(?i)broker[_-]?raw[_-]?response")),
    ("private_runtime", re.compile(rb"(?i)(?:dailytrades-runtime|private[_-]?runtime|private[_-]?watchlist|user[_-]?generated[_-]?chart)")),
)


def scan_privacy_corpus(
    root: Path,
    *,
    include_suffixes: Sequence[str] = (".json", ".html", ".md", ".png"),
) -> dict[str, object]:
    """Scan public visual artifacts, docs, and PNG bytes for private sentinels."""

    root = root.resolve()
    if not root.exists():
        raise AcceptanceError("privacy_scan_root_missing")
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in include_suffixes
        and ".git" not in path.parts
    )
    findings: list[dict[str, str]] = []
    for path in files:
        data = path.read_bytes()
        for code, pattern in _PRIVACY_PATTERNS:
            if pattern.search(data):
                findings.append({"code": code, "path": path.relative_to(root).as_posix()})
    if findings:
        raise AcceptanceError("privacy_scan_failed")
    return {"files_scanned": len(files), "findings": findings}


def scan_privacy_paths(paths: Iterable[Path], *, root: Path) -> dict[str, object]:
    """Scan an explicit visual-document allowlist without traversing private files."""

    root = root.resolve()
    files = sorted({path.resolve() for path in paths})
    findings: list[dict[str, str]] = []
    checked = 0
    for path in files:
        if not path.is_file() or not path.is_relative_to(root):
            raise AcceptanceError("privacy_scan_path_invalid")
        checked += 1
        data = path.read_bytes()
        for code, pattern in _PRIVACY_PATTERNS:
            if pattern.search(data):
                findings.append({"code": code, "path": path.relative_to(root).as_posix()})
    if findings:
        raise AcceptanceError("privacy_scan_failed")
    return {"files_scanned": checked, "findings": findings}


def generate_public_artifact_corpus(fixtures_dir: Path, output_dir: Path) -> dict[str, object]:
    """Build all twelve public fixture packets into one fresh atomic directory."""

    fixtures_dir = fixtures_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise AcceptanceError("output_not_fresh")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    packet_rows: list[dict[str, str]] = []
    try:
        for spec in BOARD_SPECS:
            for state in ("complete", "partial", "source_error", "stale"):
                fixture = fixtures_dir / f"{spec.fixture_prefix}-{state.replace('_', '-')}.json"
                if not fixture.is_file():
                    raise AcceptanceError("fixture_missing")
                try:
                    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
                    packet = build_artifact_packet(snapshot)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise AcceptanceError("fixture_invalid") from exc
                if (
                    snapshot.get("board") != spec.board_id
                    or snapshot.get("evidence_state") != state
                    or snapshot.get("privacy") != "public_fixture"
                ):
                    raise AcceptanceError("fixture_contract_invalid")
                relative = Path(spec.slug) / state.replace("_", "-")
                write_artifact_packet(packet, temporary / relative)
                packet_rows.append(
                    {
                        "board": spec.board_id,
                        "path": relative.as_posix(),
                        "state": state,
                    }
                )
        _write_json(
            temporary / "corpus.manifest.json",
            {"packets": packet_rows, "privacy": "public_fixture", "version": "1.0"},
        )
        temporary.replace(output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "boards": len(BOARD_SPECS),
        "packets": len(packet_rows),
        "states": 4,
        "output_dir": str(output_dir),
    }


_FORBIDDEN_ARTIFACT_APIS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("fetch", re.compile(rb"\bfetch\s*\(")),
    ("xml_http_request", re.compile(rb"\bXMLHttpRequest\b")),
    ("web_socket", re.compile(rb"\bWebSocket\s*\(")),
    ("event_source", re.compile(rb"\bEventSource\s*\(")),
    ("send_beacon", re.compile(rb"\bsendBeacon\s*\(")),
    ("runtime", re.compile(rb"\b(?:runtime_health|private_runtime|dailytrades_runtime)\s*\(")),
    ("broker", re.compile(rb"\bbroker\s*\.\s*(?:get|read|positions|balances|orders)")),
    ("order_mutation", re.compile(rb"\b(?:placeOrder|createOrder|modifyOrder|cancelOrder|submitOrder)\s*\(")),
)


def scan_static_artifact_apis(root: Path) -> dict[str, object]:
    """Reject network, runtime, broker, and order-capable code from static HTML."""

    root = root.resolve()
    files = sorted(root.rglob("*.html"))
    if not files:
        raise AcceptanceError("artifact_html_missing")
    findings: list[dict[str, str]] = []
    for path in files:
        data = path.read_bytes()
        for code, pattern in _FORBIDDEN_ARTIFACT_APIS:
            if pattern.search(data):
                findings.append({"code": code, "path": path.relative_to(root).as_posix()})
    if findings:
        raise AcceptanceError("forbidden_artifact_api")
    return {"files_scanned": len(files), "findings": findings}


def verify_distribution_mirrors(
    canonical: Path,
    mirrors: Sequence[Path],
) -> dict[str, object]:
    """Compare complete portable/native trees recursively and byte-for-byte."""

    canonical = canonical.resolve()
    expected = _tree_hashes(canonical)
    if not expected:
        raise AcceptanceError("distribution_mirror_invalid")
    for mirror in mirrors:
        if _tree_hashes(mirror.resolve()) != expected:
            raise AcceptanceError("distribution_mirror_mismatch")
    return {
        "files_checked": len(expected),
        "mirrors_checked": len(mirrors),
        "status": "pass",
    }


def verify_gallery_matches_corpus(
    corpus_dir: Path,
    gallery_dir: Path,
    gallery_manifest: Mapping[str, object],
) -> dict[str, object]:
    """Bind staged complete Gallery HTML to the current fresh renderer output."""

    rows = gallery_manifest.get("boards")
    if not isinstance(rows, list) or len(rows) != len(BOARD_SPECS):
        raise AcceptanceError("gallery_renderer_drift")
    row_by_board = {
        row.get("board"): row for row in rows if isinstance(row, Mapping)
    }
    checked = 0
    for spec in BOARD_SPECS:
        row = row_by_board.get(spec.board_id)
        if not isinstance(row, Mapping) or not isinstance(row.get("html_path"), str):
            raise AcceptanceError("gallery_renderer_drift")
        current = corpus_dir / spec.slug / "complete" / "research-brief.html"
        staged = gallery_dir / str(row["html_path"])
        if not current.is_file() or not staged.is_file() or current.read_bytes() != staged.read_bytes():
            raise AcceptanceError("gallery_renderer_drift")
        checked += 1
    return {"boards_checked": checked, "status": "pass"}


def verify_degraded_identity(corpus_dir: Path) -> dict[str, object]:
    """Reject fresh-looking complete HTML substituted for degraded artifacts."""

    checked = 0
    for spec in BOARD_SPECS:
        complete = corpus_dir / spec.slug / "complete" / "research-brief.html"
        if not complete.is_file():
            raise AcceptanceError("artifact_html_missing")
        complete_bytes = complete.read_bytes()
        for state in DEGRADED_STATES:
            state_dir = corpus_dir / spec.slug / state.replace("_", "-")
            html = state_dir / "research-brief.html"
            snapshot_path = state_dir / "snapshot.canonical.json"
            try:
                html_bytes = html.read_bytes()
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise AcceptanceError("stale_fallback_substitution") from exc
            text = html_bytes.decode("utf-8", errors="ignore").lower()
            visible_state = state in text or state.replace("_", " ") in text
            if (
                html_bytes == complete_bytes
                or snapshot.get("evidence_state") != state
                or snapshot.get("privacy") != "public_fixture"
                or not visible_state
                or not re.search(r"gap|missing|stale|source.error|partial", text)
            ):
                raise AcceptanceError("stale_fallback_substitution")
            checked += 1
    return {"artifacts_checked": checked, "status": "pass"}


def validate_matrix_results(
    results: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    """Require one passing result for every approved browser matrix identity."""

    expected = build_acceptance_matrix()
    counts: dict[str, int] = {}
    for group in ("complete", "degraded", "dark"):
        expected_ids = {_matrix_identity(case) for case in expected[group]}
        rows = results.get(group)
        if not isinstance(rows, Sequence):
            raise AcceptanceError("browser_matrix_incomplete")
        actual_ids: set[tuple[object, ...]] = set()
        for row in rows:
            if not isinstance(row, Mapping) or row.get("status") != "pass":
                raise AcceptanceError("browser_matrix_failed")
            actual_ids.add(_matrix_identity(row))
        if actual_ids != expected_ids or len(rows) != len(expected_ids):
            raise AcceptanceError("browser_matrix_incomplete")
        counts[group] = len(rows)
    return {**counts, "status": "pass"}


def run_browser_matrix(
    *,
    corpus_dir: Path,
    browser_path: Path | None,
    failure_dir: Path,
    playwright_factory: object | None = None,
) -> dict[str, object]:
    """Exercise every approved case in Chromium and preserve failures."""

    if playwright_factory is None:
        from playwright.sync_api import sync_playwright

        playwright_factory = sync_playwright

    corpus_dir = corpus_dir.resolve()
    failure_dir = failure_dir.resolve()
    matrix = build_acceptance_matrix()
    grouped: dict[tuple[str, str, str, int], list[tuple[str, Mapping[str, object]]]] = {}
    for group in ("complete", "degraded", "dark"):
        for case in matrix[group]:
            key = (
                str(case["board"]),
                str(case["state"]),
                str(case["theme"]),
                int(case["width"]),
            )
            grouped.setdefault(key, []).append((group, case))

    results: dict[str, list[dict[str, object]]] = {
        "complete": [],
        "degraded": [],
        "dark": [],
    }
    failures: list[dict[str, object]] = []
    dom_offenders: list[dict[str, object]] = []
    screenshots: dict[str, bytes] = {}
    no_js_checks = 0
    control_checks = 0
    browser_startup_ms: float | None = None
    browser = None
    active_page = None
    startup_begin = time.perf_counter()
    try:
        with playwright_factory() as playwright:
            launch_kwargs: dict[str, object] = {"headless": True}
            if browser_path is not None:
                resolved_browser = browser_path.resolve()
                if not resolved_browser.is_file():
                    raise AcceptanceError("browser_missing")
                launch_kwargs["executable_path"] = str(resolved_browser)
            browser = playwright.chromium.launch(**launch_kwargs)
            browser_startup_ms = round((time.perf_counter() - startup_begin) * 1000, 2)
            for (board, state, theme, width), cases in sorted(grouped.items()):
                spec = next(item for item in BOARD_SPECS if item.board_id == board)
                html = corpus_dir / spec.slug / state.replace("_", "-") / "research-brief.html"
                if not html.is_file():
                    raise AcceptanceError("artifact_html_missing")
                context = browser.new_context(
                    color_scheme=theme,
                    viewport={"width": width, "height": 840},
                )
                page = context.new_page()
                active_page = page
                page_errors: list[str] = []
                external_requests: list[str] = []
                artifact_uri = html.as_uri()
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on(
                    "console",
                    lambda message: page_errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.on(
                    "request",
                    lambda request: external_requests.append(request.url)
                    if request.url != artifact_uri
                    and not request.url.startswith(("file:", "data:", "about:", "blob:"))
                    else None,
                )
                semantic_start = time.perf_counter()
                page.goto(artifact_uri, wait_until="domcontentloaded", timeout=5000)
                semantic_ready_ms = round((time.perf_counter() - semantic_start) * 1000, 2)
                controls_start = time.perf_counter()
                page.wait_for_function("window.__dailytradesBoardReady === true", timeout=2000)
                controls_ready_ms = round((time.perf_counter() - controls_start) * 1000, 2)
                if semantic_ready_ms > 1000 or controls_ready_ms > 2000:
                    page_errors.append("performance_budget_exceeded")

                for group, case in sorted(cases, key=lambda item: str(item[1]["view"])):
                    view_id = spec.view_id(str(case["view"]))
                    started = time.perf_counter()
                    page.locator(f'[data-view-target="{view_id}"]').click()
                    page.wait_for_timeout(130 if _is_chart_view(board, view_id) else 25)
                    state_report = _browser_view_state(page, board, view_id, state, theme)
                    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                    case_failures = _view_failures(
                        state_report,
                        page_errors=page_errors,
                        external_requests=external_requests,
                        elapsed_ms=elapsed_ms,
                    )
                    result = {
                        **case,
                        "controls_ready_ms": controls_ready_ms,
                        "semantic_ready_ms": semantic_ready_ms,
                        "view_ready_ms": elapsed_ms,
                        "status": "pass" if not case_failures else "fail",
                    }
                    results[group].append(result)
                    if case_failures:
                        failure = {
                            **result,
                            "external_requests": list(external_requests),
                            "failures": case_failures,
                            "page_errors": list(page_errors),
                            "state_report": state_report,
                        }
                        failures.append(failure)
                        for offender in state_report.get("offenders", []):
                            dom_offenders.append({**case, **offender})
                        name = _failure_screenshot_name(case)
                        screenshots[name] = page.screenshot(full_page=True)

                if (board, state, theme, width) in _control_probe_keys():
                    control_failures = _probe_controls(page, spec)
                    control_checks += 1
                    if control_failures:
                        failures.append(
                            {
                                "board": board,
                                "state": state,
                                "theme": theme,
                                "width": width,
                                "control_failures": control_failures,
                            }
                        )
                        screenshots[f"controls-{board}-{state}-{theme}-{width}.png"] = page.screenshot(
                            full_page=True
                        )
                context.close()
                active_page = None

            for spec in BOARD_SPECS:
                for state in ("complete", "partial", "stale", "source_error"):
                    html = corpus_dir / spec.slug / state.replace("_", "-") / "research-brief.html"
                    no_js_failure = _probe_no_js(browser, html, spec, state)
                    no_js_checks += 1
                    if no_js_failure:
                        failures.append(no_js_failure)
            browser.close()
            browser = None
    except Exception as exc:
        if active_page is not None:
            try:
                screenshots["browser-infrastructure-failure.png"] = active_page.screenshot(
                    full_page=True
                )
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        failures.append(
            {
                "error": str(exc),
                "error_type": type(exc).__name__,
                "infrastructure": "browser_acceptance_infrastructure_failed",
            }
        )
        write_failure_bundle(
            failure_dir,
            report={
                "browser_startup_ms": browser_startup_ms,
                "failures": failures,
                "status": "fail",
            },
            dom_offenders=dom_offenders,
            manifest_diff=_matrix_manifest_diff(matrix, results),
            screenshots=screenshots,
        )
        raise AcceptanceError("browser_acceptance_infrastructure_failed") from exc

    try:
        matrix_report = validate_matrix_results(results)
    except AcceptanceError as exc:
        failures.append({"matrix": str(exc)})
        matrix_report = {group: len(rows) for group, rows in results.items()}
    if failures:
        write_failure_bundle(
            failure_dir,
            report={
                "browser_startup_ms": browser_startup_ms,
                "failures": failures,
                "status": "fail",
            },
            dom_offenders=dom_offenders,
            manifest_diff=_matrix_manifest_diff(matrix, results),
            screenshots=screenshots,
        )
        raise AcceptanceError("browser_acceptance_failed")
    return {
        "browser_startup_ms": browser_startup_ms,
        "control_probes": control_checks,
        "matrix": matrix_report,
        "no_js_overviews": no_js_checks,
        "status": "pass",
    }


def _matrix_manifest_diff(
    matrix: Mapping[str, Sequence[Mapping[str, object]]],
    results: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    expected_ids = {
        group: sorted(_identity_string(case) for case in matrix[group])
        for group in ("complete", "degraded", "dark")
    }
    passing_ids = {
        group: sorted(
            _identity_string(row) for row in results.get(group, ()) if row.get("status") == "pass"
        )
        for group in expected_ids
    }
    return {
        group: {
            "missing_or_failed": sorted(set(expected_ids[group]) - set(passing_ids[group])),
            "unexpected": sorted(set(passing_ids[group]) - set(expected_ids[group])),
        }
        for group in expected_ids
    }


def _browser_view_state(
    page: object,
    board: str,
    view_id: str,
    evidence_state: str,
    theme: str,
) -> dict[str, object]:
    return page.evaluate(
        r"""input => {
          const panel = document.querySelector(`[data-view="${input.viewId}"]`);
          const selected = document.querySelector('[data-view-target][aria-selected="true"]');
          const visible = [...document.querySelectorAll('[data-view]')]
            .filter(node => !node.hidden && node.getClientRects().length)
            .map(node => node.dataset.view);
          const critical = [
            document.querySelector('header'),
            document.querySelector('.view-tabs'),
            document.querySelector('.decision-card'),
            panel,
            document.querySelector('.evidence-rail'),
            ...document.querySelectorAll(
              '[data-view]:not([hidden]) .module-row,[data-view]:not([hidden]) .ledger-row,' +
              '[data-view]:not([hidden]) .timeline-row,[data-view]:not([hidden]) .scenario,' +
              '[data-view]:not([hidden]) .evidence-row,[data-view]:not([hidden]) .cascade-row,' +
              '[data-view]:not([hidden]) .exposure:not([hidden]),[data-view]:not([hidden]) .spine-row,' +
              '[data-view]:not([hidden]) .aggregation-row,[data-view]:not([hidden]) .product-detail,' +
              '[data-view]:not([hidden]) .broker-row,[data-view]:not([hidden]) .stress-row,' +
              '[data-view]:not([hidden]) .exclusions,[data-view]:not([hidden]) .chart-shell,' +
              '[data-view]:not([hidden]) .chart'
            ),
          ].filter(Boolean);
          const offenders = [];
          for (const node of critical) {
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            if (rect.width < 1 || rect.height < 1) {
              offenders.push({selector: node.id || node.className || node.tagName, reason: 'hidden_critical'});
            }
            const clipsX = ['hidden', 'clip', 'auto', 'scroll'].includes(style.overflowX);
            const clipsY = ['hidden', 'clip', 'auto', 'scroll'].includes(style.overflowY);
            if ((clipsX && node.scrollWidth > node.clientWidth + 1) || (clipsY && node.scrollHeight > node.clientHeight + 1)) {
              offenders.push({selector: node.id || node.className || node.tagName, reason: 'clipped'});
            }
          }
          for (const container of document.querySelectorAll(
            '.view-tabs,.summary,.board-layout,.fact-grid,.data-grid,.exposure-control,' +
            '.aggregation-list,.product-grid,.broker-list,.stress-list,.cascade,.evidence-list,.scenario-list'
          )) {
            const children = [...container.children].filter(node => node.getClientRects().length);
            for (let leftIndex = 0; leftIndex < children.length; leftIndex += 1) {
              const left = children[leftIndex].getBoundingClientRect();
              for (let rightIndex = leftIndex + 1; rightIndex < children.length; rightIndex += 1) {
                const right = children[rightIndex].getBoundingClientRect();
                const overlapWidth = Math.min(left.right, right.right) - Math.max(left.left, right.left);
                const overlapHeight = Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top);
                if (overlapWidth > 1 && overlapHeight > 1) {
                  offenders.push({selector: container.className || container.tagName, reason: 'overlap'});
                }
              }
            }
          }
          let chart = {ready: true, nonblank: true};
          if (input.board === 'instrument_research' && input.viewId === 'price-setup') {
            const host = document.getElementById('instrument-price-chart');
            const canvases = host ? [...host.querySelectorAll('canvas')] : [];
            const variations = canvases.map(canvas => {
              const context = canvas.getContext('2d');
              if (!context || !canvas.width || !canvas.height) return 0;
              const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
              const first = [data[0], data[1], data[2], data[3]].join(',');
              let changed = 0;
              const stride = Math.max(4, Math.floor(data.length / 500 / 4) * 4);
              for (let index = 0; index < data.length; index += stride) {
                const sample = [data[index], data[index + 1], data[index + 2], data[index + 3]].join(',');
                if (sample !== first) changed += 1;
              }
              return changed;
            });
            chart = {
              ready: Boolean(host && host.dataset.renderStatus === 'ready' && canvases.length),
              nonblank: variations.some(value => value > 10),
            };
          }
          if (input.board === 'macro_regime' && input.viewId === 'cross-asset-impact') {
            const svg = document.querySelector('#macro-cross-asset-chart svg');
            const box = svg?.getBoundingClientRect();
            chart = {ready: Boolean(svg), nonblank: Boolean(svg && svg.querySelectorAll('path').length >= 3 && box.width * box.height > 10000)};
          }
          if (input.board === 'portfolio_risk' && input.viewId === 'stress-tests') {
            const svg = document.querySelector('#portfolio-stress-chart svg');
            const box = svg?.getBoundingClientRect();
            chart = {ready: Boolean(svg), nonblank: Boolean(svg && svg.querySelectorAll('path').length >= 3 && box.width * box.height > 10000)};
          }
          const body = document.body.innerText;
          const normalizedState = input.evidenceState.replace('_', ' ');
          const bodyStyle = getComputedStyle(document.body);
          const parseRgb = value => {
            const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
            return match ? match.slice(1, 4).map(Number) : null;
          };
          const luminance = rgb => {
            const values = rgb.map(value => {
              const channel = value / 255;
              return channel <= .03928 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
            });
            return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
          };
          const foreground = parseRgb(bodyStyle.color);
          const background = parseRgb(bodyStyle.backgroundColor);
          const contrast = foreground && background
            ? (Math.max(luminance(foreground), luminance(background)) + .05) /
              (Math.min(luminance(foreground), luminance(background)) + .05)
            : 0;
          return {
            boardReady: window.__dailytradesBoardReady === true,
            chart,
            chartNonblankRequired: input.evidenceState !== 'source_error',
            contrast,
            evidenceVisible: input.evidenceState === 'complete' || body.toLowerCase().includes(normalizedState) || body.toLowerCase().includes(input.evidenceState),
            gapVisible: input.evidenceState === 'complete' || /gap|missing|stale|source.error|partial/i.test(body),
            offenders,
            overflow: document.documentElement.scrollWidth - window.innerWidth,
            panelText: panel?.innerText.trim().length || 0,
            panelVisible: Boolean(panel && !panel.hidden && panel.getClientRects().length),
            selected: selected?.dataset.viewTarget || '',
            themeMatches: matchMedia(`(prefers-color-scheme: ${input.theme})`).matches,
            visible,
          };
        }""",
        {
            "board": board,
            "evidenceState": evidence_state,
            "theme": theme,
            "viewId": view_id,
        },
    )


def _view_failures(
    state: Mapping[str, object],
    *,
    page_errors: Sequence[str],
    external_requests: Sequence[str],
    elapsed_ms: float,
) -> list[str]:
    failures: list[str] = []
    if page_errors:
        failures.append("page_error")
    if external_requests:
        failures.append("external_request")
    if not state.get("boardReady"):
        failures.append("board_not_ready")
    if not state.get("panelVisible") or int(state.get("panelText", 0)) < 40:
        failures.append("critical_content_hidden")
    if state.get("selected") not in state.get("visible", []):
        failures.append("selected_state_mismatch")
    if len(state.get("visible", [])) != 1:
        failures.append("visible_panel_count_invalid")
    if float(state.get("overflow", 0)) > 1:
        failures.append("horizontal_overflow")
    if state.get("offenders"):
        failures.append("layout_offender")
    chart = state.get("chart", {})
    if not chart.get("ready") or (
        state.get("chartNonblankRequired") and not chart.get("nonblank")
    ):
        failures.append("chart_invalid")
    if not state.get("evidenceVisible") or not state.get("gapVisible"):
        failures.append("degraded_evidence_hidden")
    if not state.get("themeMatches"):
        failures.append("theme_invalid")
    if float(state.get("contrast", 0)) < 4.5:
        failures.append("contrast_invalid")
    if elapsed_ms > 5000:
        failures.append("view_budget_exceeded")
    return failures


def _probe_controls(page: object, spec: object) -> list[str]:
    failures: list[str] = []
    view_ids = [view_id for _label, view_id in spec.view_ids]
    selected_locator = page.locator('[data-view-target][aria-selected="true"]')
    for index, view_id in enumerate(view_ids):
        target = page.locator(f'[data-view-target="{view_id}"]')
        target.click()
        if selected_locator.get_attribute("data-view-target") != view_id:
            failures.append(f"click_selected_state_mismatch:{view_id}")

        alternate_id = view_ids[(index + 1) % len(view_ids)]
        page.locator(f'[data-view-target="{alternate_id}"]').click()
        target.focus()
        page.keyboard.press("Enter")
        if selected_locator.get_attribute("data-view-target") != view_id:
            failures.append(f"enter_selected_state_mismatch:{view_id}")

        page.locator(f'[data-view-target="{alternate_id}"]').click()
        target.focus()
        page.keyboard.press("Space")
        if selected_locator.get_attribute("data-view-target") != view_id:
            failures.append(f"space_selected_state_mismatch:{view_id}")

        target.focus()
        page.keyboard.press("ArrowRight")
        focus_state = page.evaluate(
            """() => {
              const node = document.activeElement;
              const style = getComputedStyle(node);
              return {
                active: node?.dataset.viewTarget || '',
                visible: style.outlineStyle !== 'none' || style.boxShadow !== 'none',
              };
            }"""
        )
        if focus_state.get("active") != alternate_id:
            failures.append(f"arrow_focus_mismatch:{view_id}")
        if not focus_state.get("visible"):
            failures.append(f"visible_focus_missing:{view_id}")
        if selected_locator.get_attribute("data-view-target") != alternate_id:
            failures.append(f"arrow_selected_state_mismatch:{view_id}")

    first = page.locator(f'[data-view-target="{view_ids[0]}"]')
    first.focus()
    for expected_id in view_ids[1:]:
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement?.dataset.viewTarget || ''") != expected_id:
            failures.append(f"tab_order_invalid:{expected_id}")
            break
    for expected_id in reversed(view_ids[:-1]):
        page.keyboard.press("Shift+Tab")
        if page.evaluate("document.activeElement?.dataset.viewTarget || ''") != expected_id:
            failures.append(f"shift_tab_order_invalid:{expected_id}")
            break
    selects = page.locator("select[data-exposure-select]")
    for index in range(selects.count()):
        select = selects.nth(index)
        owning_view = select.evaluate(
            "node => node.closest('[data-view]')?.dataset.view || ''"
        )
        if owning_view:
            page.locator(f'[data-view-target="{owning_view}"]').click()
        options = select.locator("option").evaluate_all(
            "nodes => nodes.map(node => ({value: node.value, label: node.textContent.trim()}))"
        )
        values = [option["value"] for option in options]
        if len(values) < 2:
            failures.append("select_options_missing")
            continue
        before = select.input_value()
        after = next(value for value in values if value != before)
        keyboard_option = next(option for option in options if option["value"] == after)
        try:
            select.focus()
            page.keyboard.press("Shift+Tab")
            page.keyboard.press("Tab")
            focus_state = select.evaluate(
                """node => {
                  const style = getComputedStyle(node);
                  return {
                    active: document.activeElement === node,
                    visible: style.outlineStyle !== 'none' || style.boxShadow !== 'none',
                  };
                }"""
            )
            if not focus_state.get("active") or not focus_state.get("visible"):
                failures.append("select_visible_focus_missing")
            page.keyboard.press(keyboard_option["label"][0].lower())
            if select.input_value() != after:
                failures.append("select_keyboard_interaction_failed")
            select.select_option(before, timeout=2000)
            if select.input_value() != before:
                failures.append("select_pointer_interaction_failed")
            select.select_option(after, timeout=2000)
        except Exception:
            failures.append("select_interaction_failed")
            continue
        if select.input_value() != after:
            failures.append("select_pointer_interaction_failed")
        page.wait_for_timeout(1100)
    return failures


def _probe_no_js(browser: object, html: Path, spec: object, state: str) -> dict[str, object] | None:
    snapshot = json.loads((html.parent / "snapshot.canonical.json").read_text(encoding="utf-8"))
    context = browser.new_context(java_script_enabled=False, viewport={"width": 736, "height": 840})
    page = context.new_page()
    external_requests: list[str] = []
    artifact_uri = html.as_uri()
    page.on(
        "request",
        lambda request: external_requests.append(request.url)
        if request.url != artifact_uri
        and not request.url.startswith(("file:", "data:", "about:", "blob:"))
        else None,
    )
    try:
        page.goto(artifact_uri, wait_until="domcontentloaded", timeout=5000)
        body = page.locator("body").inner_text()
        overview = page.locator('[data-view="overview"]')
        selected = page.locator('[data-view-target][aria-selected="true"]').get_attribute(
            "data-view-target"
        )
        sources = snapshot.get("source_registry", [])
        source_alias = sources[0].get("alias", "") if sources else ""
        required = (
            str(snapshot.get("payload", {}).get("decision", "")),
            str(snapshot.get("decision_cutoff", "")),
            str(snapshot.get("evidence_state", "")),
            str(source_alias),
            "Decision cutoff",
            "Evidence rail",
            "Coverage",
            "gap",
        )
        invalid = (
            any(not value or value.lower() not in body.lower() for value in required)
            or not overview.is_visible()
            or selected != "overview"
            or page.evaluate("document.documentElement.scrollWidth - window.innerWidth") > 1
            or page.locator(".view-tabs").is_visible()
            or bool(external_requests)
        )
        if invalid:
            return {
                "board": spec.board_id,
                "external_requests": external_requests,
                "no_js": "semantic_or_inert_contract_failed",
                "state": state,
            }
        return None
    finally:
        context.close()


def _control_probe_keys() -> set[tuple[str, str, str, int]]:
    return {
        (spec.board_id, state, "light", 736)
        for spec in BOARD_SPECS
        for state in ("complete", "partial", "stale", "source_error")
    }


def _is_chart_view(board: str, view_id: str) -> bool:
    return (board, view_id) in {
        ("instrument_research", "price-setup"),
        ("macro_regime", "cross-asset-impact"),
        ("portfolio_risk", "stress-tests"),
    }


def _identity_string(case: Mapping[str, object]) -> str:
    return "|".join(str(value) for value in _matrix_identity(case))


def _failure_screenshot_name(case: Mapping[str, object]) -> str:
    values = (
        case["board"],
        case["state"],
        case["theme"],
        case["width"],
        case["view"],
    )
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", "-".join(map(str, values))).strip("-") + ".png"


def write_failure_bundle(
    output_dir: Path,
    *,
    report: Mapping[str, object],
    dom_offenders: Sequence[Mapping[str, object]],
    manifest_diff: Mapping[str, object],
    screenshots: Mapping[str, bytes],
) -> Path:
    """Preserve the mandatory diagnostics for a failed CI/browser run."""

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "failure-report.json", report)
    _write_json(output_dir / "dom-offenders.json", list(dom_offenders))
    _write_json(output_dir / "manifest-diff.json", manifest_diff)
    screenshot_dir = output_dir / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)
    for name, content in sorted(screenshots.items()):
        safe_name = Path(name).name
        if safe_name != name or not safe_name.lower().endswith(".png"):
            raise AcceptanceError("failure_screenshot_name_invalid")
        (screenshot_dir / safe_name).write_bytes(content)
    return output_dir


def validate_codex_inline_evidence(
    evidence: Mapping[str, object],
    expected_hashes: Mapping[str, str],
) -> dict[str, object]:
    """Validate human-recorded real Codex inline evidence for all Boards."""

    records = evidence.get("records")
    if not isinstance(records, list) or len(records) != len(expected_hashes):
        raise AcceptanceError("codex_inline_evidence_invalid")
    by_board: dict[str, Mapping[str, object]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise AcceptanceError("codex_inline_evidence_invalid")
        board = record.get("board")
        if not isinstance(board, str) or board in by_board:
            raise AcceptanceError("codex_inline_evidence_invalid")
        by_board[board] = record
    if set(by_board) != set(expected_hashes):
        raise AcceptanceError("codex_inline_evidence_invalid")
    for board, expected_hash in expected_hashes.items():
        record = by_board[board]
        valid = (
            record.get("host") == "codex_inline"
            and record.get("browser_wrapper") is False
            and record.get("html_sha256") == expected_hash
            and record.get("default_view") == "Overview"
            and record.get("all_views_switched") is True
            and record.get("keyboard_pass") is True
            and record.get("responsive_pass") is True
            and record.get("page_errors") == []
            and record.get("external_requests") == []
            and isinstance(record.get("reviewer"), str)
            and bool(str(record.get("reviewer")).strip())
            and _is_rfc3339_utc(record.get("reviewed_at"))
        )
        if not valid:
            raise AcceptanceError("codex_inline_evidence_invalid")
    return {"boards_checked": len(by_board), "status": "pass"}


def verify_legacy_visual_inventory(root: Path, inventory_path: Path) -> dict[str, object]:
    """Prove #58 did not mutate unrelated SVG/Mermaid visual sources."""

    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError("legacy_visual_inventory_invalid") from exc
    rows = inventory.get("files")
    if not isinstance(rows, list) or not rows:
        raise AcceptanceError("legacy_visual_inventory_invalid")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise AcceptanceError("legacy_visual_inventory_invalid")
        relative = row.get("path")
        expected = row.get("sha256")
        if not isinstance(relative, str) or relative in seen or not _safe_relative(relative):
            raise AcceptanceError("legacy_visual_inventory_invalid")
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise AcceptanceError("legacy_visual_inventory_mismatch")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise AcceptanceError("legacy_visual_inventory_mismatch")
        seen.add(relative)
    return {"files_checked": len(seen), "status": "pass"}


def _safe_relative(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and value not in {"", "."} and ".." not in path.parts


def _tree_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def _matrix_identity(case: Mapping[str, object]) -> tuple[object, ...]:
    return (
        case.get("board"),
        case.get("state"),
        case.get("view"),
        case.get("width"),
        case.get("height"),
        case.get("theme"),
    )


def _is_rfc3339_utc(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ) is not None


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
