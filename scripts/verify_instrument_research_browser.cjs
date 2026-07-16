#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { chromium } = require("playwright");

function option(name, fallback) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const htmlPath = path.resolve(option("html", ""));
const browserPath = option(
  "browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
);
const screenshotDir = path.resolve(
  option("screenshot-dir", path.join(os.tmpdir(), "dailytrades-instrument-browser-acceptance")),
);

function isFile(filePath) {
  return fs.existsSync(filePath) && fs.statSync(filePath).isFile();
}

if (!htmlPath || !isFile(htmlPath)) {
  throw new Error("--html must reference a generated Instrument Research HTML artifact");
}
if (!isFile(browserPath)) {
  throw new Error("--browser must reference a Chrome or Chromium executable");
}
fs.mkdirSync(screenshotDir, { recursive: true });

const widths = [1200, 700, 320];
const views = ["overview", "price-setup", "industry-peers", "catalysts-flows"];

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: browserPath });
  const target = new URL(`file://${htmlPath}`).href;
  const failures = [];
  let checks = 0;

  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height: 840 } });
    const errors = [];
    const externalRequests = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", message => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("request", request => {
      if (!/^(file|data|about):/.test(request.url())) externalRequests.push(request.url());
    });
    await page.goto(target, { waitUntil: "load" });
    await page.waitForFunction(() => window.__dailytradesBoardReady === true);

    for (let viewIndex = 0; viewIndex < views.length; viewIndex += 1) {
      const view = views[viewIndex];
      if (viewIndex === 0) {
        await page.locator(`[data-view-target="${view}"]`).click();
      } else {
        await page.keyboard.press("ArrowRight");
      }
      await page.waitForTimeout(view === "price-setup" ? 150 : 25);
      const state = await page.evaluate(activeView => {
        const panel = document.querySelector(`[data-view="${activeView}"]`);
        const selected = document.querySelector('[data-view-target][aria-selected="true"]');
        const visiblePanels = [...document.querySelectorAll("[data-view]")]
          .filter(node => !node.hidden)
          .map(node => node.dataset.view);
        const chart = document.getElementById("instrument-price-chart");
        const canvases = [...chart.querySelectorAll("canvas")];
        const pixelVariation = canvases.map(canvas => {
          const context = canvas.getContext("2d");
          if (!context || !canvas.width || !canvas.height) return 0;
          const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
          const first = [data[0], data[1], data[2], data[3]].join(",");
          let changed = 0;
          for (let index = 0; index < data.length; index += 400) {
            const sample = [data[index], data[index + 1], data[index + 2], data[index + 3]].join(",");
            if (sample !== first) changed += 1;
          }
          return changed;
        });
        return {
          panelVisible: Boolean(panel && !panel.hidden),
          selected: selected?.dataset.viewTarget,
          visiblePanels,
          overflow: document.documentElement.scrollWidth - window.innerWidth,
          chartStatus: chart.dataset.renderStatus || "",
          canvasCount: canvases.length,
          pixelVariation,
          panelText: panel?.textContent.trim().length || 0,
        };
      }, view);
      checks += 1;
      if (
        !state.panelVisible ||
        state.selected !== view ||
        state.visiblePanels.join(",") !== view ||
        state.overflow > 1 ||
        state.panelText < 120
      ) {
        failures.push({ width, view, state, errors, externalRequests });
      }
      if (
        view === "price-setup" &&
        (state.chartStatus !== "ready" ||
          state.canvasCount < 1 ||
          !state.pixelVariation.some(value => value > 10))
      ) {
        failures.push({ width, view, chart: state, errors, externalRequests });
      }
      await page.screenshot({
        path: path.join(screenshotDir, `${width}-${view}.png`),
        fullPage: true,
      });
    }
    if (errors.length || externalRequests.length) failures.push({ width, errors, externalRequests });
    await page.close();
  }

  await browser.close();
  if (failures.length) {
    console.error(JSON.stringify({ checks, failures }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({ checks, widths, views, status: "passed" }));
})().catch(error => {
  console.error(error.stack || error.message);
  process.exit(1);
});
