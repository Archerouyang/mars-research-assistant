#!/usr/bin/env python3
"""Run reproducible browser acceptance against one local Macro Board artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import sync_playwright


WIDTHS = (1200, 700, 320)
VIEWS = ("overview", "rates-liquidity", "inflation-growth", "cross-asset-impact", "event-scenarios")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "dailytrades-macro-browser-acceptance",
    )
    args = parser.parse_args()
    html = args.html.resolve()
    browser_path = args.browser.resolve()
    if not html.is_file() or not browser_path.is_file():
        raise SystemExit("--html and --browser must reference local files")
    args.screenshot_dir.mkdir(parents=True, exist_ok=True)

    failures: list[dict[str, object]] = []
    checks = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(browser_path))
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 840})
            errors: list[str] = []
            external_requests: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: external_requests.append(request.url) if not request.url.startswith(("file:", "data:", "about:")) else None)
            page.goto(html.as_uri(), wait_until="load")
            page.wait_for_function("window.__dailytradesBoardReady === true")
            for view in VIEWS:
                page.locator(f'[data-view-target="{view}"]').click()
                page.wait_for_timeout(100 if view == "cross-asset-impact" else 25)
                state = page.evaluate(
                    """activeView => {
                      const panel = document.querySelector(`[data-view="${activeView}"]`);
                      const selected = document.querySelector('[data-view-target][aria-selected="true"]');
                      const visible = [...document.querySelectorAll('[data-view]')].filter(item => !item.hidden).map(item => item.dataset.view);
                      const chart = document.querySelector('#macro-cross-asset-chart svg');
                      return {
                        panelVisible: Boolean(panel && !panel.hidden),
                        selected: selected?.dataset.viewTarget,
                        visible,
                        overflow: document.documentElement.scrollWidth - window.innerWidth,
                        panelText: panel?.textContent.trim().length || 0,
                        chartPaths: chart ? chart.querySelectorAll('path').length : 0,
                        chartBox: chart ? chart.getBoundingClientRect().width * chart.getBoundingClientRect().height : 0,
                      };
                    }""",
                    view,
                )
                checks += 1
                invalid = (
                    not state["panelVisible"]
                    or state["selected"] != view
                    or state["visible"] != [view]
                    or state["overflow"] > 1
                    or state["panelText"] < 120
                    or (view == "cross-asset-impact" and (state["chartPaths"] < 3 or state["chartBox"] < 10000))
                )
                if invalid:
                    failures.append({"width": width, "view": view, "state": state, "errors": errors, "external_requests": external_requests})
                page.screenshot(path=str(args.screenshot_dir / f"{width}-{view}.png"), full_page=True)
            page.locator('[data-view-target="overview"]').focus()
            page.keyboard.press("ArrowRight")
            if page.locator('[data-view-target][aria-selected="true"]').get_attribute("data-view-target") != "rates-liquidity":
                failures.append({"width": width, "keyboard": "arrow navigation did not select Rates & Liquidity"})
            if errors or external_requests:
                failures.append({"width": width, "errors": errors, "external_requests": external_requests})
            page.close()

        no_js = browser.new_context(java_script_enabled=False, viewport={"width": 700, "height": 840})
        page = no_js.new_page()
        page.goto(html.as_uri(), wait_until="load")
        body = page.locator("body").inner_text()
        if not all(text in body for text in ("Current plan decision", "Evidence rail", "Decision cutoff", "Visible gaps")):
            failures.append({"no_js": "Overview semantic decision content is incomplete"})
        if page.evaluate("document.documentElement.scrollWidth - window.innerWidth") > 1:
            failures.append({"no_js": "Overview has horizontal overflow"})
        no_js.close()
        browser.close()

    result = {"checks": checks, "widths": WIDTHS, "views": VIEWS}
    if failures:
        raise SystemExit(json.dumps({**result, "failures": failures}, indent=2))
    print(json.dumps({**result, "status": "passed"}))


if __name__ == "__main__":
    main()
