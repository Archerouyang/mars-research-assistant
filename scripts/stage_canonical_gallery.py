#!/usr/bin/env python3
"""Stage or verify the proposed canonical research Board Gallery.

Generation writes only a fresh staging directory. It never edits the active
README Gallery, legacy SVG paths, private runtime, or broker state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "trading-research-system"
sys.path.insert(0, str(SKILL / "scripts"))

from canonical_gallery import (  # noqa: E402
    BOARD_BY_ID,
    GalleryError,
    inspect_png,
    stage_gallery,
    verify_gallery,
    verify_reproduced_gallery,
)


DEFAULT_OUTPUT = REPO / "docs" / "staging" / "canonical-gallery-v1"
FIXTURES = SKILL / "assets" / "fixtures" / "input"
PROTECTED_OUTPUTS = {(REPO / "docs" / "assets" / "readme").resolve()}


class BrowserCapture:
    """Capture approved views from exact canonical HTML without transformation."""

    def __init__(self, browser_path: Path) -> None:
        startup = time.perf_counter()
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(
                headless=True,
                executable_path=str(browser_path.resolve()),
            )
        except Exception:
            self._playwright.stop()
            raise
        self._startup_ms = round((time.perf_counter() - startup) * 1000, 2)
        self._pages: dict[tuple[Path, int, int], tuple[object, list[str], list[str], float, float]] = {}
        self._exercised_boards: set[str] = set()
        self._no_js_boards: set[str] = set()
        self._complete_views_checked = 0
        self._no_js_overviews_checked = 0

    def close(self) -> None:
        try:
            for page, *_rest in self._pages.values():
                page.close()
            self._browser.close()
        finally:
            self._playwright.stop()

    def __enter__(self) -> "BrowserCapture":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def report(self) -> dict[str, object]:
        return {
            "mode": "browser",
            "complete_views_checked": self._complete_views_checked,
            "no_js_overviews_checked": self._no_js_overviews_checked,
        }

    @staticmethod
    def _view_state(page: object, view_id: str) -> dict[str, object]:
        return page.evaluate(
            """viewId => {
              const selected = document.querySelector('[data-view-target][aria-selected="true"]');
              const panel = document.querySelector(`[data-view="${viewId}"]`);
              const text = document.body.innerText;
              return {
                boardReady: window.__dailytradesBoardReady === true,
                selected: selected?.dataset.viewTarget || '',
                panelVisible: Boolean(panel && !panel.hidden),
                panelText: panel?.innerText.trim().length || 0,
                synthetic: /synthetic/i.test(text),
                overflow: document.documentElement.scrollWidth - window.innerWidth,
              };
            }""",
            view_id,
        )

    def _exercise_all_views(self, page: object, board_id: str) -> None:
        if board_id in self._exercised_boards:
            return
        for _label, view_id in BOARD_BY_ID[board_id].view_ids:
            page.locator(f'[data-view-target="{view_id}"]').click()
            page.wait_for_timeout(30)
            state = self._view_state(page, view_id)
            if (
                not state["boardReady"]
                or state["selected"] != view_id
                or not state["panelVisible"]
                or state["panelText"] < 120
                or state["overflow"] > 1
            ):
                raise GalleryError("browser_complete_views_invalid")
            self._complete_views_checked += 1
        self._exercised_boards.add(board_id)

    def _check_no_js_overview(self, html_path: Path, board_id: str) -> None:
        if board_id in self._no_js_boards:
            return
        snapshot = json.loads((html_path.parent / "snapshot.canonical.json").read_text(encoding="utf-8"))
        payload = snapshot.get("payload", {})
        source_registry = snapshot.get("source_registry", [])
        source_alias = source_registry[0].get("alias", "") if source_registry else ""
        context = self._browser.new_context(
            java_script_enabled=False,
            viewport={"width": 700, "height": 840},
        )
        page = context.new_page()
        try:
            page.goto(html_path.resolve().as_uri(), wait_until="domcontentloaded")
            body = page.locator("body").inner_text()
            overview = page.locator('[data-view="overview"]')
            first_secondary = BOARD_BY_ID[board_id].view_ids[1][1]
            selected = page.locator('[data-view-target][aria-selected="true"]').get_attribute(
                "data-view-target"
            )
            tabs_visible = page.locator(".view-tabs").is_visible()
            selected_after = selected
            if tabs_visible:
                page.locator(f'[data-view-target="{first_secondary}"]').click()
                selected_after = page.locator(
                    '[data-view-target][aria-selected="true"]'
                ).get_attribute("data-view-target")
            required = (
                str(payload.get("decision", "")),
                str(snapshot.get("decision_cutoff", "")),
                str(snapshot.get("evidence_state", "")),
                str(source_alias),
                "Decision cutoff",
                "Evidence rail",
                "Coverage",
                "gap",
            )
            if (
                any(not value or value.lower() not in body.lower() for value in required)
                or not overview.is_visible()
                or selected != "overview"
                or selected_after != "overview"
            ):
                raise GalleryError("browser_no_js_invalid")
        finally:
            context.close()
        self._no_js_boards.add(board_id)
        self._no_js_overviews_checked += 1

    def __call__(self, spec, html_path: Path):
        view_id = BOARD_BY_ID[spec.board_id].view_id(spec.view)
        page_key = (html_path.resolve(), spec.width, spec.height)
        if page_key not in self._pages:
            page = self._browser.new_page(viewport={"width": spec.width, "height": spec.height})
            page_errors: list[str] = []
            external_requests: list[str] = []
            artifact_uri = html_path.resolve().as_uri()
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "console",
                lambda message: page_errors.append(message.text) if message.type == "error" else None,
            )
            page.on(
                "request",
                lambda request: external_requests.append(request.url)
                if request.url != artifact_uri
                and not request.url.startswith(("file:", "data:", "about:"))
                else None,
            )
            semantic_start = time.perf_counter()
            page.goto(artifact_uri, wait_until="domcontentloaded")
            semantic_ready_ms = round((time.perf_counter() - semantic_start) * 1000, 2)
            controls_start = time.perf_counter()
            page.wait_for_function("window.__dailytradesBoardReady === true", timeout=2000)
            controls_ready_ms = round((time.perf_counter() - controls_start) * 1000, 2)
            self._pages[page_key] = (
                page,
                page_errors,
                external_requests,
                semantic_ready_ms,
                controls_ready_ms,
            )
        page, page_errors, external_requests, semantic_ready_ms, controls_ready_ms = self._pages[page_key]
        if spec.width == 1200:
            self._exercise_all_views(page, spec.board_id)
            self._check_no_js_overview(html_path, spec.board_id)
        capture_start = time.perf_counter()
        page.locator(f'[data-view-target="{view_id}"]').click()
        page.wait_for_timeout(120 if view_id in {"price-setup", "cross-asset-impact", "stress-tests"} else 25)
        state = self._view_state(page, view_id)
        if (
            page_errors
            or external_requests
            or not state["boardReady"]
            or state["selected"] != view_id
            or not state["panelVisible"]
            or state["panelText"] < 120
            or not state["synthetic"]
            or state["overflow"] > 1
        ):
            raise GalleryError("browser_capture_invalid")
        page.evaluate(
            """identity => {
              let banner = document.querySelector('[data-capture-identity]');
              if (!banner) {
                banner = document.createElement('div');
                banner.dataset.captureIdentity = 'true';
                Object.assign(banner.style, {
                  position: 'fixed', top: '0', left: '0', right: '0', zIndex: '9999',
                  minHeight: '34px', padding: '7px 12px', boxSizing: 'border-box',
                  borderBottom: '1px solid #c8ccd0', background: '#ffffff', color: '#202326',
                  font: '600 12px/20px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'
                });
                document.body.appendChild(banner);
              }
              banner.textContent = identity;
            }""",
            f"{BOARD_BY_ID[spec.board_id].slug.replace('-', ' ').title()} · {spec.view} · Synthetic fixture · non-interactive capture",
        )
        if view_id != "overview":
            page.evaluate(
                """viewId => {
                  const panel = document.querySelector(`[data-view="${viewId}"]`);
                  window.scrollTo(0, panel.getBoundingClientRect().top + window.scrollY - 46);
                }""",
                view_id,
            )
        else:
            page.evaluate("window.scrollTo(0, 0)")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            screenshot_path = Path(handle.name)
        try:
            page.screenshot(path=str(screenshot_path), full_page=False)
            png = screenshot_path.read_bytes()
        finally:
            screenshot_path.unlink(missing_ok=True)
        capture_ms = round((time.perf_counter() - capture_start) * 1000, 2)
        metadata = inspect_png(png)
        if metadata["width"] != spec.width or metadata["height"] != spec.height:
            raise GalleryError("capture_dimensions_invalid")
        return png, {
            "browser_startup_ms": self._startup_ms,
            "capture_ms": capture_ms,
            "controls_ready_ms": controls_ready_ms,
            "semantic_ready_ms": semantic_ready_ms,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--browser", type=Path)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify an existing stage without generating or opening a browser",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir.resolve()
    try:
        if args.verify_only:
            manifest = verify_gallery(output)
            if args.browser is not None:
                if not args.browser.is_file():
                    raise GalleryError("browser_required")
                with BrowserCapture(args.browser) as capture:
                    verify_reproduced_gallery(
                        output_dir=output,
                        fixtures_dir=FIXTURES,
                        capture=capture,
                        documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
                    )
            print(
                f"canonical Gallery verified: {len(manifest['boards'])} Boards, "
                f"{len(manifest['captures'])} captures"
            )
            return 0
        if output == REPO.resolve() or any(
            output == protected or output.is_relative_to(protected)
            for protected in PROTECTED_OUTPUTS
        ):
            raise GalleryError("public_cutover_not_authorized")
        if args.browser is None or not args.browser.is_file():
            raise GalleryError("browser_required")
        with BrowserCapture(args.browser) as capture:
            stage_gallery(
                fixtures_dir=FIXTURES,
                output_dir=output,
                capture=capture,
                documentation_sources=(REPO / "README.md", REPO / "README.zh-CN.md"),
            )
    except (GalleryError, OSError, PlaywrightError) as exc:
        code = str(exc) if isinstance(exc, GalleryError) else "gallery_generation_failed"
        print(f"canonical Gallery failed: {code}", file=sys.stderr)
        return 1
    print(f"canonical Gallery staged: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
