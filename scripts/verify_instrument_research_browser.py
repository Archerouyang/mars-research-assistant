#!/usr/bin/env python3
"""Run reproducible browser acceptance against one local Instrument artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import sync_playwright


WIDTHS = (1200, 700, 320)
VIEWS = ("overview", "price-setup", "industry-peers", "catalysts-flows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "dailytrades-instrument-browser-acceptance",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    html = args.html.resolve()
    browser_path = args.browser.resolve()
    if not html.is_file():
        raise SystemExit("--html must reference a generated Instrument Research HTML artifact")
    if not browser_path.is_file():
        raise SystemExit("--browser must reference a Chrome or Chromium executable")
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
            page.on(
                "console",
                lambda message: errors.append(message.text) if message.type == "error" else None,
            )
            page.on(
                "request",
                lambda request: external_requests.append(request.url)
                if not request.url.startswith(("file:", "data:", "about:"))
                else None,
            )
            page.goto(html.as_uri(), wait_until="load")
            page.wait_for_function("window.__dailytradesBoardReady === true")

            for view_index, view in enumerate(VIEWS):
                if view_index == 0:
                    page.locator(f'[data-view-target="{view}"]').click()
                else:
                    page.keyboard.press("ArrowRight")
                page.wait_for_timeout(150 if view == "price-setup" else 25)
                state = page.evaluate(
                    """activeView => {
                      const panel = document.querySelector(`[data-view="${activeView}"]`);
                      const selected = document.querySelector('[data-view-target][aria-selected="true"]');
                      const visiblePanels = [...document.querySelectorAll('[data-view]')]
                        .filter(node => !node.hidden).map(node => node.dataset.view);
                      const chart = document.getElementById('instrument-price-chart');
                      const canvases = [...chart.querySelectorAll('canvas')];
                      const pixelVariation = canvases.map(canvas => {
                        const context = canvas.getContext('2d');
                        if (!context || !canvas.width || !canvas.height) return 0;
                        const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
                        const first = [data[0], data[1], data[2], data[3]].join(',');
                        let changed = 0;
                        for (let index = 0; index < data.length; index += 400) {
                          const sample = [data[index], data[index + 1], data[index + 2], data[index + 3]].join(',');
                          if (sample !== first) changed += 1;
                        }
                        return changed;
                      });
                      return {
                        panelVisible: Boolean(panel && !panel.hidden),
                        selected: selected?.dataset.viewTarget,
                        visiblePanels,
                        overflow: document.documentElement.scrollWidth - window.innerWidth,
                        chartStatus: chart.dataset.renderStatus || '',
                        canvasCount: canvases.length,
                        pixelVariation,
                        panelText: panel?.textContent.trim().length || 0,
                      };
                    }""",
                    view,
                )
                checks += 1
                invalid_view = (
                    not state["panelVisible"]
                    or state["selected"] != view
                    or state["visiblePanels"] != [view]
                    or state["overflow"] > 1
                    or state["panelText"] < 120
                )
                invalid_chart = view == "price-setup" and (
                    state["chartStatus"] != "ready"
                    or state["canvasCount"] < 1
                    or not any(value > 10 for value in state["pixelVariation"])
                )
                if invalid_view or invalid_chart:
                    failures.append(
                        {
                            "width": width,
                            "view": view,
                            "state": state,
                            "errors": errors,
                            "external_requests": external_requests,
                        }
                    )
                page.screenshot(
                    path=str(args.screenshot_dir / f"{width}-{view}.png"),
                    full_page=True,
                )
            if errors or external_requests:
                failures.append(
                    {"width": width, "errors": errors, "external_requests": external_requests}
                )
            page.close()
        browser.close()

    result = {"checks": checks, "widths": WIDTHS, "views": VIEWS}
    if failures:
        raise SystemExit(json.dumps({**result, "failures": failures}, indent=2))
    print(json.dumps({**result, "status": "passed"}))


if __name__ == "__main__":
    main()
