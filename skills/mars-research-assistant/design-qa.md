# Macro Board Interactive Design QA

**Comparison target**

- Source visual truth: `/var/folders/b0/khtmft7d1cz0dw33dsc0dry80000gn/T/codex-clipboard-87a0a5e3-be41-42c6-8cfc-f57c3e16d6b7.png`
- Source pixels: 1200 × 900; desktop, light theme; initial `趋势` state.
- Implementation: `/private/tmp/mars-macro-fonts.6bN1YW/research-brief.html`
- Implementation screenshot: unavailable. The in-app browser policy rejected the
  local `file:` URL, so no browser-rendered pixels, CSS viewport or density
  normalization could be captured.
- Intended state: initial `趋势` panel with `NDX/RUT` selected; the same board
  also supplies `当前状态` with a factor-only exposure selector, `下周事件`, and
  `情景`.

**Findings**

- [P1] Rendered visual comparison is blocked.
  Location: full Board and all interactive states.
  Evidence: the supplied reference image was opened; navigation to the generated
  local Board was rejected by the in-app browser URL policy.
  Impact: fonts and typography, spacing and layout rhythm, colors and visual
  tokens, chart rendering, copy wrapping, and interactive selected states cannot
  be visually compared at the same viewport.
  Fix: open the generated Board manually in the already available local browser,
  then capture and compare the initial Trend, Current Status, Event, Scenario,
  and exposure-selector states.

**Required fidelity surfaces**

- Fonts and typography: blocked; no implementation capture.
- Spacing and layout rhythm: blocked; no implementation capture.
- Colors and visual tokens: blocked; no implementation capture.
- Image quality and asset fidelity: the reference contains no separate raster,
  logo, icon or illustration asset to reproduce; chart output is data-driven.
  Rendered comparison remains blocked.
- Copy and content: static review confirms the new copy distinguishes frozen
  observations, conditional scenarios, and factor sensitivity from holdings.
  Rendered wrapping remains blocked.

**Primary interaction checks**

- Static Macro selftest passed for the four panels, trend controls, exposure
  selector, conditional-scenario label, source/as_of evidence, and the
  no-holdings boundary.
- Generated JavaScript passed syntax parsing.
- Browser interaction and console-error checks are blocked with the rendered
  capture.

**Comparison history**

- No P0/P1/P2 visual iteration has been completed because the first rendered
  implementation capture is unavailable.
- Typography refinement pending visual capture: the Board now prefers PingFang
  SC and other native CJK sans fallbacks, disables synthesized glyph weights,
  tightens the title hierarchy, and uses tabular numerals for market data. The
  new generated script passed syntax checking, but its rendered typography has
  not been browser-captured.

**Implementation Checklist**

1. Manually open the generated Board and confirm the initial Trend view against
   the reference layout.
2. Switch each tab and the factor selector; check the selected state and
   responsive layout.
3. Record the visual result, then replace this blocked QA report with captured
   comparison evidence.

final result: blocked
