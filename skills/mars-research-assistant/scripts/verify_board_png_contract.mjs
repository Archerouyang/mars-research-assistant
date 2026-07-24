#!/usr/bin/env node

import assert from "node:assert/strict";

import { assertStandaloneDocument } from "./export_board_png.mjs";


assert.doesNotThrow(() =>
  assertStandaloneDocument("<!doctype html><html><body>Board</body></html>"),
);
assert.throws(
  () => assertStandaloneDocument('<div class="dt-board">fragment</div>'),
  /only a complete standalone Board document/,
);
assert.throws(
  () => assertStandaloneDocument("<html><body>missing doctype</body></html>"),
  /only a complete standalone Board document/,
);

process.stdout.write("Board PNG contract ok\n");
