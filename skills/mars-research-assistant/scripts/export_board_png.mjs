#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

const DEFAULT_BROWSER =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PRIVATE_SENTINELS = [
  "/Users/",
  "account_id",
  "account_number",
  "api_key",
  "authorization",
  "bearer ",
  "broker_response",
  "credential",
  "password",
  "private_runtime",
  "secret",
  "token",
];

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
}

function parseArgs(argv) {
  const options = {
    browser: process.env.CHROME_PATH || DEFAULT_BROWSER,
    checkInteraction: false,
    public: false,
    scale: 1,
    width: 1200,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--public") {
      options.public = true;
      continue;
    }
    if (argument === "--check-interaction") {
      options.checkInteraction = true;
      continue;
    }
    if (!["--browser", "--input", "--output", "--scale", "--width"].includes(argument)) {
      throw new Error(`unknown argument: ${argument}`);
    }
    const value = argv[index + 1];
    if (!value) throw new Error(`missing value for ${argument}`);
    index += 1;
    options[argument.slice(2)] = value;
  }

  if (!options.input || !options.output) {
    throw new Error(
      "usage: export_board_png.mjs --input PANEL.html --output PANEL.png [--width 1200] [--scale 1] [--public] [--check-interaction]",
    );
  }

  options.width = Number(options.width);
  options.scale = Number(options.scale);
  if (!Number.isInteger(options.width) || options.width < 640 || options.width > 2400) {
    throw new Error("--width must be an integer between 640 and 2400");
  }
  if (!Number.isFinite(options.scale) || options.scale < 1 || options.scale > 2) {
    throw new Error("--scale must be between 1 and 2");
  }
  return options;
}

function assertPublicSafe(source) {
  const normalized = source.toLowerCase();
  if (!/data-public-fixture=["']true["']/i.test(source)) {
    throw new Error(
      "public export requires data-public-fixture=true from a validated synthetic fixture",
    );
  }
  const matches = PRIVATE_SENTINELS.filter((sentinel) =>
    normalized.includes(sentinel.toLowerCase()),
  );
  if (matches.length) {
    throw new Error(`public export blocked by private sentinel(s): ${matches.join(", ")}`);
  }
}

export function assertStandaloneDocument(source) {
  if (
    !/^\s*<!doctype html>/i.test(source) ||
    !/<html\b/i.test(source) ||
    !/<\/html>\s*$/i.test(source)
  ) {
    throw new Error("PNG export accepts only a complete standalone Board document");
  }
}

async function waitForFile(file, timeoutMs = 20_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      await stat(file);
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  }
  throw new Error(`timed out waiting for Chrome DevTools: ${file}`);
}

async function waitForTarget(port, timeoutMs = 20_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      const targets = await response.json();
      const target = targets.find((candidate) => candidate.type === "page");
      if (target?.webSocketDebuggerUrl) return target.webSocketDebuggerUrl;
    } catch {
      // Chrome may not have opened its first page yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("timed out waiting for a Chrome page target");
}

async function connectCdp(url) {
  const socket = new WebSocket(url);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", () => reject(new Error("CDP connection failed")), {
      once: true,
    });
  });

  let nextId = 1;
  const pending = new Map();
  const listeners = new Map();

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data));
    if (message.id) {
      const request = pending.get(message.id);
      if (!request) return;
      pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result);
      return;
    }
    const waiting = listeners.get(message.method) || [];
    listeners.delete(message.method);
    waiting.forEach((resolve) => resolve(message.params));
  });

  function send(method, params = {}) {
    const id = nextId;
    nextId += 1;
    return new Promise((resolve, reject) => {
      pending.set(id, { reject, resolve });
      socket.send(JSON.stringify({ id, method, params }));
    });
  }

  function wait(method, timeoutMs = 10_000) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error(`timed out waiting for ${method}`)), timeoutMs);
      const wrapped = (params) => {
        clearTimeout(timeout);
        resolve(params);
      };
      listeners.set(method, [...(listeners.get(method) || []), wrapped]);
    });
  }

  return { close: () => socket.close(), send, wait };
}

async function exportPng(options) {
  const input = path.resolve(options.input);
  const output = path.resolve(options.output);
  const browser = path.resolve(options.browser);
  const source = await readFile(input, "utf8");
  assertStandaloneDocument(source);
  if (options.public) assertPublicSafe(source);
  await stat(browser).catch(() => {
    throw new Error(`Chrome/Chromium executable not found: ${browser}`);
  });
  await mkdir(path.dirname(output), { recursive: true });

  const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), "mars-research-assistant-png-"));
  const profile = path.join(temporaryRoot, "chrome-profile");
  const page = path.join(temporaryRoot, "panel.html");
  await writeFile(page, source, "utf8");

  const chrome = spawn(
    browser,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-debugging-port=0",
      `--user-data-dir=${profile}`,
      "about:blank",
    ],
    { stdio: "ignore" },
  );

  let cdp;
  try {
    const activePort = path.join(profile, "DevToolsActivePort");
    await waitForFile(activePort);
    const [port] = (await readFile(activePort, "utf8")).trim().split("\n");
    cdp = await connectCdp(await waitForTarget(port));
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      deviceScaleFactor: options.scale,
      height: 900,
      mobile: false,
      width: options.width,
    });

    const loaded = cdp.wait("Page.loadEventFired");
    await cdp.send("Page.navigate", { url: pathToFileURL(page).href });
    await loaded;
    if (options.checkInteraction) {
      const interaction = await cdp.send("Runtime.evaluate", {
        awaitPromise: true,
        expression: `(async () => {
          const buttons = [...document.querySelectorAll('button[data-view],button[data-scenario]')];
          const target = buttons.find(button => button.getAttribute('aria-pressed') === 'false');
          if (!target) return { ok: false, reason: 'no inactive interaction target' };
          const attribute = target.hasAttribute('data-view') ? 'data-view' : 'data-scenario';
          const previous = buttons.find(button =>
            button.hasAttribute(attribute) && button.getAttribute('aria-pressed') === 'true'
          );
          target.click();
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          return {
            ok: target.getAttribute('aria-pressed') === 'true' &&
              (!previous || previous.getAttribute('aria-pressed') === 'false'),
            reason: 'interaction state did not change'
          };
        })()`,
        returnByValue: true,
      });
      if (!interaction.result.value?.ok) {
        throw new Error(interaction.result.value?.reason || "Board interaction smoke failed");
      }
    }
    const measurement = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      expression: `(async () => {
        if (document.fonts?.ready) await document.fonts.ready;
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        return {
          width: Math.ceil(Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)),
          height: Math.ceil(Math.max(document.documentElement.scrollHeight, document.body.scrollHeight))
        };
      })()`,
      returnByValue: true,
    });
    const dimensions = measurement.result.value;
    if (!dimensions || dimensions.height < 200 || dimensions.height > 16_000) {
      throw new Error(`unexpected panel height: ${dimensions?.height ?? "missing"}`);
    }
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      deviceScaleFactor: options.scale,
      height: dimensions.height,
      mobile: false,
      width: options.width,
    });
    const screenshot = await cdp.send("Page.captureScreenshot", {
      captureBeyondViewport: true,
      clip: {
        height: dimensions.height,
        scale: 1,
        width: options.width,
        x: 0,
        y: 0,
      },
      format: "png",
      fromSurface: true,
    });
    await writeFile(output, Buffer.from(screenshot.data, "base64"));
    const result = await stat(output);
    if (result.size < 10_000) throw new Error(`PNG export is unexpectedly small: ${result.size} bytes`);
    return { bytes: result.size, height: dimensions.height, width: options.width };
  } finally {
    cdp?.close();
    chrome.kill("SIGTERM");
    await rm(temporaryRoot, { force: true, recursive: true });
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
    const result = await exportPng(options);
    process.stdout.write(
      `PNG exported: ${path.resolve(options.output)} (${result.width}x${result.height} CSS px, ${result.bytes} bytes)\n`,
    );
  } catch (error) {
    fail(error instanceof Error ? error.message : String(error));
  }
}
